"""B-102 runner: Sionna RT against the analytical references, plus a first cost benchmark.

Run it with an isolated environment that has ``sionna-rt`` installed, never the app's venv:

    .local/sionna-venv/Scripts/python.exe services/simulator/benchmarks/sionna_evaluation.py \
        --output docs/simulation/evidence/sionna-rt-cpu.json

CPU execution needs LLVM >= 18 (``DRJIT_LIBLLVM_PATH`` pointing to ``LLVM-C.dll`` on Windows).
If Sionna cannot start, the report records the error and the process exits with status 2:
nothing falls back to the quick estimator.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import platform
import statistics
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "simulator" / "src"))

from smart_environment.engines import simulate  # noqa: E402
from smart_environment.legacy import import_project  # noqa: E402
from smart_environment.references import compare_predictions, markdown_table, reference_cases  # noqa: E402
from smart_environment.sionna_adapter import (  # noqa: E402
    EngineUnavailable, SionnaRT, run_link_forward, scene_spec,
)

# Sionna RT is a physical ray tracer: the empirical log-distance exponent is not one of its inputs.
SIONNA_INTERACTIONS = ("free-space", "wall-penetration", "specular-reflection")


def peak_memory_mb() -> float | None:
    if os.name == "nt":
        class Counters(ctypes.Structure):
            _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        counters = Counters(cb=ctypes.sizeof(Counters))
        process = ctypes.windll.kernel32.GetCurrentProcess()
        if ctypes.windll.psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb):
            return counters.PeakWorkingSetSize / 2 ** 20
        return None
    import resource
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return peak / 2 ** 20 if sys.platform == "darwin" else peak / 2 ** 10


def environment() -> dict:
    cpu = platform.processor()
    total_ram_gb = None
    if os.name == "nt":
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
            cpu = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()

        class Status(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        status = Status(dwLength=ctypes.sizeof(Status))
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            total_ram_gb = round(status.ullTotalPhys / 2 ** 30, 1)
    elif Path("/proc/cpuinfo").exists():
        names = [line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines()
                 if line.startswith("model name")]
        cpu = names[0] if names else cpu
        total = [line.split()[1] for line in Path("/proc/meminfo").read_text().splitlines()
                 if line.startswith("MemTotal:")]
        total_ram_gb = round(int(total[0]) / 2 ** 20, 1) if total else None
    return {"os": platform.platform(), "python": platform.python_version(), "cpu": cpu,
            "logical_cpus": os.cpu_count(), "total_ram_gb": total_ram_gb,
            "drjit_libllvm_path": os.environ.get("DRJIT_LIBLLVM_PATH"), "versions": SionnaRT.versions()}


def evaluate_references(engine: SionnaRT) -> tuple[list[dict], list[dict], str]:
    cases = reference_cases()
    details: dict[str, dict] = {}

    def predict(case):
        estimate = run_link_forward(engine, case.project, case.itu_materials)
        details[case.id] = {"elapsed_ms": estimate.elapsed_ms,
                            "incoherent_power_dbm": estimate.incoherent_power_dbm,
                            "wideband_power_dbm": estimate.wideband_power_dbm,
                            "paths": [asdict(p) for p in estimate.paths], "reasons": list(estimate.reasons)}
        return estimate.received_power_dbm, "; ".join(estimate.reasons)

    results = compare_predictions(cases, predict, SIONNA_INTERACTIONS)
    return [asdict(r) for r in results], [{"case_id": k, **v} for k, v in details.items()], markdown_table(results)


def benchmark_example(engine: SionnaRT, example: str) -> dict:
    data = json.loads((ROOT / "examples" / f"{example}.shsim.json").read_text(encoding="utf-8"))
    project = import_project(data)
    quick = {link.id: link for link in simulate(project).links}
    links, timings = [], []
    started = time.perf_counter()
    for index, link in enumerate(project.links):
        estimate = run_link_forward(engine, project, link_index=index)
        timings.append(estimate.elapsed_ms)
        quick_forward = quick[link.id].forward
        links.append({"link_id": link.id, "sionna_coherent_dbm": estimate.received_power_dbm,
                      "sionna_incoherent_dbm": estimate.incoherent_power_dbm,
                      "sionna_wideband_dbm": estimate.wideband_power_dbm,
                      "quick_estimate_dbm": None if quick_forward is None else quick_forward.received_power_dbm,
                      "num_paths": len(estimate.paths), "elapsed_ms": estimate.elapsed_ms,
                      "reasons": list(estimate.reasons)})
    spec = scene_spec(project, project.devices[0].radios[0].frequency_hz)
    return {"example": example, "walls": len(project.building.walls), "links": len(project.links),
            "material_mapping": spec.material_provenance, "max_depth": engine.max_depth,
            "diffraction": engine.diffraction, "edge_diffraction": engine.edge_diffraction,
            "total_s": time.perf_counter() - started,
            "first_link_ms": timings[0] if timings else None,
            "median_link_ms": statistics.median(timings) if timings else None,
            "links_detail": links}


def benchmark_receiver_grid(engine: SionnaRT, example: str, spacing_m: float, height_m: float) -> dict:
    """Point receivers on a regular grid around the hub: deterministic paths per point, cost only."""
    import tempfile

    import mitsuba as mi
    import numpy as np
    import sionna.rt as rt

    project = import_project(json.loads((ROOT / "examples" / f"{example}.shsim.json").read_text(encoding="utf-8")))
    hub = next(d for d in project.devices if d.role == "controller")
    xs = np.arange(spacing_m / 2, project.building.width_m, spacing_m)
    ys = np.arange(spacing_m / 2, project.building.depth_m, spacing_m)
    frequency = hub.radios[0].frequency_hz
    with tempfile.TemporaryDirectory(prefix="sionna-grid-") as workdir:
        scene = engine.build_scene(scene_spec(project, frequency), Path(workdir))
        scene.add(rt.Transmitter("tx", position=mi.Point3f(hub.position.x, hub.position.y, hub.position.z)))
        for index, (x, y) in enumerate((x, y) for y in ys for x in xs):
            scene.add(rt.Receiver(f"rx-{index}", position=mi.Point3f(float(x), float(y), height_m)))
        started = time.perf_counter()
        paths = rt.PathSolver()(scene, max_depth=engine.max_depth, samples_per_src=engine.samples_per_src,
                                synthetic_array=True, refraction=engine.refraction, seed=engine.seed)
        a = np.asarray(paths.a[0], dtype=np.float64) + 1j * np.asarray(paths.a[1], dtype=np.float64)
        tau = np.asarray(paths.tau, dtype=np.float64)
        valid = np.asarray(paths.valid).astype(bool)
        elapsed = time.perf_counter() - started
    receivers = xs.size * ys.size
    a, tau, valid = (v.reshape(receivers, -1) for v in (a, tau, valid))
    carrier = np.where(valid, a * np.exp(-2j * np.pi * frequency * tau), 0).sum(1)
    reached = valid.any(1)
    gain = abs(carrier[reached]) ** 2
    return {"example": example, "height_m": height_m, "spacing_m": spacing_m, "receivers": int(receivers),
            "max_depth": engine.max_depth, "receivers_without_paths": int((~reached).sum()),
            "max_paths_per_receiver": int(valid.sum(1).max()) if receivers else 0,
            "median_coherent_path_gain_db": float(10 * np.log10(np.median(gain))) if gain.size else None,
            "elapsed_s": elapsed, "note": "Coste de cálculo de trayectos a puntos; no es una evaluación de cobertura."}


def benchmark_radio_map(engine: SionnaRT, example: str, cell_m: float, height_m: float, samples: int) -> dict:
    """Path-gain map around the hub: cost only. Path gain needs no transmit power, so none is invented."""
    import tempfile

    import mitsuba as mi
    import numpy as np
    import sionna.rt as rt

    project = import_project(json.loads((ROOT / "examples" / f"{example}.shsim.json").read_text(encoding="utf-8")))
    hub = next(d for d in project.devices if d.role == "controller")
    width, depth = project.building.width_m, project.building.depth_m
    with tempfile.TemporaryDirectory(prefix="sionna-map-") as workdir:
        scene = engine.build_scene(scene_spec(project, hub.radios[0].frequency_hz), Path(workdir))
        scene.add(rt.Transmitter("tx", position=mi.Point3f(hub.position.x, hub.position.y, hub.position.z)))
        started = time.perf_counter()
        radio_map = rt.RadioMapSolver()(scene, center=mi.Point3f(width / 2, depth / 2, height_m),
                                        orientation=mi.Point3f(0, 0, 0), size=mi.Point2f(width, depth),
                                        cell_size=mi.Point2f(cell_m, cell_m), samples_per_tx=samples,
                                        max_depth=engine.max_depth, refraction=engine.refraction)
        gain = np.asarray(radio_map.path_gain, dtype=np.float64).reshape(-1)
        elapsed = time.perf_counter() - started
    reached = gain > 0
    return {"example": example, "height_m": height_m, "cell_m": cell_m, "samples_per_tx": samples,
            "max_depth": engine.max_depth, "cells": int(gain.size), "cells_without_rays": int((~reached).sum()),
            "median_path_gain_db": float(10 * np.log10(np.median(gain[reached]))) if reached.any() else None,
            "elapsed_s": elapsed,
            "note": "Coste de cálculo; el mapa no se presenta como cobertura ni se compara con medidas."}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--map-cell", type=float, default=0.25)
    parser.add_argument("--map-samples", type=int, default=1_000_000)
    parser.add_argument("--grid-spacing", type=float, default=0.5)
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    report = {"runner": "services/simulator/benchmarks/sionna_evaluation.py",
              "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "environment": environment()}
    started = time.perf_counter()
    try:
        engine = SionnaRT(max_depth=args.max_depth)
    except EngineUnavailable as error:
        report.update(status="unavailable", error=str(error))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Sionna RT no disponible: {error}")
        return 2
    report["import_s"] = time.perf_counter() - started
    report["variant"] = engine.variant()
    results, details, table = evaluate_references(engine)
    report["references"] = {"interactions": list(SIONNA_INTERACTIONS), "results": results, "details": details}
    examples = ("smart-apartment", "office-floor", "warehouse")
    report["examples"] = [benchmark_example(engine, name) for name in examples]
    diffracting = SionnaRT(max_depth=args.max_depth, diffraction=True, edge_diffraction=True)
    report["examples_with_diffraction"] = [benchmark_example(diffracting, name) for name in examples]
    report["receiver_grid"] = benchmark_receiver_grid(engine, "smart-apartment", args.grid_spacing, 1.2)
    report["depth_sweep"] = [{"max_depth": depth, **benchmark_example(SionnaRT(max_depth=depth), "warehouse")}
                             for depth in (3, 5, 8)]
    report["radio_map"] = [benchmark_radio_map(engine, "smart-apartment", args.map_cell, 1.2, samples)
                           for samples in (args.map_samples, args.map_samples * 10, args.map_samples * 100)]
    report["peak_working_set_mb"] = peak_memory_mb()
    report["status"] = "executed"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                           encoding="utf-8")
    print(table)
    print(json.dumps({k: report[k] for k in ("variant", "import_s", "peak_working_set_mb")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
