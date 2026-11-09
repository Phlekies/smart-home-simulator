"""B-121 runner: Java parity of directional antennas and polarization, and contrast with Java multipath.

Extracts the original Java model, physics and simulation sources from the git tag
``java-desktop-final`` (Java left ``main`` in ADR-009), compiles them with the harness
``java_parity/JavaParity.java`` in a temporary directory, runs them and writes the evidence:

    .venv/Scripts/python.exe services/simulator/benchmarks/java_parity.py \
        --output docs/simulation/evidence/java-parity.json

Needs ``javac``/``java`` on PATH and the tag in the local clone (``git fetch --tags``); nothing is
installed or downloaded. ``test_java_parity.py`` re-checks the stored Java values against the current
Python estimator without a JDK.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import platform
import statistics
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "simulator" / "src"))

from smart_environment.engines import direction  # noqa: E402
from smart_environment.legacy import MATERIALS, import_project  # noqa: E402
from smart_environment.models import Building, Device, Point, Project, Radio, Settings, Wall  # noqa: E402

JAVA_REF = "java-desktop-final"  # tag of the last main commit that still had the Java application
PACKAGES = ("model", "physics", "simulation")
EXAMPLES = ("smart-apartment", "office-floor", "warehouse")
PARITY_TOLERANCE_DB = 0.01  # Java's FSPL uses the rounded 32.45 dB constant: about 0.002 dB apart
JAVA_FLOOR_DBM = -150.0  # PropagationEngine.MIN_POWER_MW: Java reports no weaker power
JAVA_CULLING_DBM = -115.0  # default culling threshold of the Java multipath modes
DEFAULT_ENV = {"freq_mhz": 2400.0, "bandwidth_hz": 20e6, "noise_figure_db": 7.0, "alpha_db_per_m": 0.0,
               "system_gain_db": 0.0}


def _sensor(sensor_id, x, y, tx=10.0, gain=3.0, antenna="DIRECTIONAL", orientation=0.0, beamwidth=60.0,
            sharpness=1.8, side_lobe=18.0, polarization=0.0):
    return {"id": sensor_id, "x": x, "y": y, "tx_power_dbm": tx, "tx_gain_dbi": gain, "antenna": antenna,
            "orientation_deg": orientation, "beamwidth_deg": beamwidth, "pattern_sharpness": sharpness,
            "side_lobe_db": side_lobe, "polarization_deg": polarization}


def _around(sensor, angles, distance=6.0):
    return [{"id": f"a{angle:g}", "x": sensor["x"] + distance * math.cos(math.radians(angle)),
             "y": sensor["y"] + distance * math.sin(math.radians(angle))} for angle in angles]


def parity_cases() -> list[dict]:
    """Direct-path cases; angles avoid exact beam edges, probes avoid wall endpoints."""
    angles = [0, 10, 25, 29, 31, 45, 59, 61, 90, 135, 180, 225, 300, 330]
    cases = []
    for k, (orientation, beamwidth, sharpness, side_lobe) in enumerate(
            [(0, 60, 1.8, 18), (45, 120, 4, 10), (-30, 90, 1.8, 25), (200, 30, 1, 18)]):
        sensor = _sensor("S", 10, 10, orientation=orientation, beamwidth=beamwidth, sharpness=sharpness,
                         side_lobe=side_lobe)
        cases.append({"id": f"pattern-{k}", "env": DEFAULT_ENV, "exponent": 2.1, "receiver_gain_dbi": 0.0,
                      "receiver_polarization_deg": 0.0, "walls": [], "sensor": sensor,
                      "probes": _around(sensor, angles)})
    for tx_pol in (0, 30, 60, 89, 90, 135):
        for rx_pol in (0, 90):
            sensor = _sensor("S", 10, 10, antenna="OMNIDIRECTIONAL", beamwidth=360, polarization=tx_pol)
            cases.append({"id": f"polarization-{tx_pol}-{rx_pol}", "env": DEFAULT_ENV, "exponent": 2.1,
                          "receiver_gain_dbi": 2.0, "receiver_polarization_deg": rx_pol, "walls": [],
                          "sensor": sensor, "probes": [{"id": "p", "x": 16.5, "y": 11.25}]})
    walls = [{"x1": 13.0, "y1": 4.0, "x2": 13.0, "y2": 16.0, "material": "Brick", "thickness_cm": 12.0},
             {"x1": 15.5, "y1": 4.0, "x2": 15.5, "y2": 16.0, "material": "Concrete", "thickness_cm": 20.0}]
    for freq in (2400.0, 5200.0):
        sensor = _sensor("S", 10, 10, orientation=10, beamwidth=90, polarization=45)
        cases.append({"id": f"walls-{freq:g}MHz", "env": {**DEFAULT_ENV, "freq_mhz": freq, "alpha_db_per_m": 0.2,
                                                          "system_gain_db": -1.5},
                      "exponent": 2.6, "receiver_gain_dbi": 1.0, "receiver_polarization_deg": 15, "walls": walls,
                      "sensor": sensor, "probes": _around(sensor, [0, 20, 40, -20], distance=8.0)})
    return cases


def _harness_lines(case: dict, mode: str) -> list[str]:
    env, s = case["env"], case["sensor"]
    lines = [f"case {case['id']}",
             f"env {env['freq_mhz']!r} {env['bandwidth_hz']!r} {env['noise_figure_db']!r} "
             f"{env['alpha_db_per_m']!r} {env['system_gain_db']!r}",
             f"mode {mode} {case['exponent']!r} {case['receiver_gain_dbi']!r} {case['receiver_polarization_deg']!r}"]
    lines += [f"wall {w['x1']!r} {w['y1']!r} {w['x2']!r} {w['y2']!r} {w['material'].replace(' ', '_')} "
              f"{w['thickness_cm']!r}" for w in case["walls"]]
    lines.append(f"sensor {s['id']} {s['x']} {s['y']} {s['tx_power_dbm']!r} {s['tx_gain_dbi']!r} {s['antenna']} "
                 f"{s['orientation_deg']!r} {s['beamwidth_deg']!r} {s['pattern_sharpness']!r} {s['side_lobe_db']!r} "
                 f"{s['polarization_deg']!r}")
    lines += [f"probe {p['id']} {s['id']} {p['x']!r} {p['y']!r}" for p in case["probes"]]
    return lines


def python_dbm(case: dict, probe: dict, height_m: float = 1.4) -> float:
    """Same case with the Python estimator, both ends at the same height so distances match Java's 2D."""
    env, s = case["env"], case["sensor"]
    materials = {m.name: m for m in MATERIALS}
    walls = [Wall(id=f"w{k}", start=Point(x=w["x1"], y=w["y1"]), end=Point(x=w["x2"], y=w["y2"]),
                  material_id=materials[w["material"]].id, thickness_m=w["thickness_cm"] / 100)
             for k, w in enumerate(case["walls"])]
    freq = env["freq_mhz"] * 1e6
    tx_radio = Radio(id="r", frequency_hz=freq, bandwidth_hz=env["bandwidth_hz"], tx_power_dbm=s["tx_power_dbm"],
                     tx_gain_dbi=s["tx_gain_dbi"], noise_figure_db=env["noise_figure_db"],
                     antenna=s["antenna"].lower(), orientation_deg=s["orientation_deg"],
                     beamwidth_deg=s["beamwidth_deg"], pattern_sharpness=s["pattern_sharpness"],
                     side_lobe_attenuation_db=s["side_lobe_db"], polarization_deg=s["polarization_deg"])
    rx_radio = Radio(id="r", frequency_hz=freq, bandwidth_hz=env["bandwidth_hz"],
                     rx_gain_dbi=case["receiver_gain_dbi"], noise_figure_db=env["noise_figure_db"],
                     polarization_deg=case["receiver_polarization_deg"])
    tx = Device(id="tx", name="tx", position=Point(x=s["x"], y=s["y"], z=height_m), radios=[tx_radio])
    rx = Device(id="rx", name="rx", position=Point(x=probe["x"], y=probe["y"], z=height_m), radios=[rx_radio])
    project = Project(building=Building(width_m=40, depth_m=40, walls=walls,
                                        materials=[m.model_copy() for m in MATERIALS]),
                      devices=[tx, rx], settings=Settings(path_loss_exponent=case["exponent"],
                                                          extra_loss_db_per_m=env["alpha_db_per_m"],
                                                          system_gain_db=env["system_gain_db"]))
    return direction(project, tx, tx_radio, rx, rx_radio).received_power_dbm


def example_cases(name: str) -> list[dict]:
    """One case per sensor of a Java example, received at the hub, as the Java app's sensor link does."""
    data = json.loads((ROOT / "examples" / f"{name}.shsim.json").read_text(encoding="utf-8"))
    env, settings, hub = data["environment"], data["settings"], data["hub"]
    walls = [{"x1": w["x1"], "y1": w["y1"], "x2": w["x2"], "y2": w["y2"], "material": w["material"],
              "thickness_cm": w["thicknessCm"]} for w in data["walls"]]
    return [{"id": f"{name}:{s['id']}", "example": name, "sensor_id": s["id"],
             "env": {"freq_mhz": env["frequencyMHz"], "bandwidth_hz": env["bandwidthHz"],
                     "noise_figure_db": env["noiseFigureDb"], "alpha_db_per_m": env["extraLossDbPerMeter"],
                     "system_gain_db": env["systemGainDb"]},
             "exponent": settings["pathLossExponent"], "receiver_gain_dbi": hub["receiverGainDb"],
             "receiver_polarization_deg": hub["polarizationDeg"], "walls": walls,
             "sensor": _sensor(s["id"], s["x"], s["y"], tx=s["txPowerDbm"], gain=s["txGainDb"], antenna=s["antenna"],
                               orientation=s["orientationDeg"], beamwidth=s["beamwidthDeg"],
                               sharpness=s["patternSharpness"], side_lobe=s["sideLobeAttenuationDb"],
                               polarization=s["polarizationDeg"]),
             "probes": [{"id": "hub", "x": float(hub["x"]), "y": float(hub["y"])}]}
            for s in data["sensors"]]


def imported_forward_dbm(name: str) -> dict[str, float]:
    """Sensor→hub received power of the imported project, as the app computes it (heights 1.4/1.3 m)."""
    project = import_project(json.loads((ROOT / "examples" / f"{name}.shsim.json").read_text(encoding="utf-8")))
    devices = {d.id: d for d in project.devices}
    out = {}
    for link in project.links:
        source, target = devices[link.source_device_id], devices[link.target_device_id]
        out[source.id] = direction(project, source, source.radios[0], target, target.radios[0]).received_power_dbm
    return out


def java_sources(target: Path, ref: str = JAVA_REF) -> Path:
    """Copy src/main/java of the given git reference into target; the working tree no longer has it."""
    archive = subprocess.run(["git", "-C", str(ROOT), "archive", "--format=tar", ref, "src/main/java"],
                             capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(target, filter="data")
    return target / "src" / "main" / "java"


def run_java(cases_by_mode: list[tuple[str, dict]], ref: str = JAVA_REF) -> dict[tuple[str, str, str], tuple[float, int]]:
    with tempfile.TemporaryDirectory(prefix="shsim-java-parity-") as tmp, \
            tempfile.TemporaryDirectory(prefix="shsim-java-sources-") as sources_dir:
        java_root = java_sources(Path(sources_dir), ref)
        # The engine needs neither the UI nor JavaFX; classes that reference them are left out.
        sources = [str(p) for package in PACKAGES
                   for p in (java_root / "io" / "github" / "phlekies" / "smarthome" / package).rglob("*.java")
                   if not any(marker in p.read_text(encoding="utf-8")
                              for marker in ("smarthome.ui.", "javafx.", "Format::"))]
        sources.append(str(Path(__file__).parent / "java_parity" / "JavaParity.java"))
        subprocess.run(["javac", "-nowarn", "-encoding", "UTF-8", "-d", tmp, *sources], check=True)
        out = {}
        for mode in ("direct", "rays", "waves"):
            lines = [line for m, case in cases_by_mode if m == mode for line in _harness_lines(case, mode)]
            if not lines:
                continue
            run = subprocess.run(["java", "-cp", tmp, "JavaParity"], input="\n".join(lines) + "\n",
                                 capture_output=True, text=True, check=True, encoding="utf-8")
            for row in run.stdout.splitlines():
                case_id, probe_id, dbm, paths = row.split()
                out[(mode, case_id, probe_id)] = (float(dbm), int(paths))
    return out


def _spread(values: list[float | None]) -> dict:
    known = [v for v in values if v is not None]
    return {"links": len(known), "not_comparable": len(values) - len(known),
            **({"mean": statistics.fmean(known), "min": min(known), "max": max(known)} if known else {})}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--java-ref", default=JAVA_REF, help="git reference that still has src/main/java")
    args = parser.parse_args(argv)
    parity, examples = parity_cases(), [c for name in EXAMPLES for c in example_cases(name)]
    java = run_java([("direct", c) for c in parity + examples] + [(m, c) for m in ("rays", "waves") for c in examples],
                    args.java_ref)
    parity_rows = []
    for case in parity:
        for probe in case["probes"]:
            java_dbm = java[("direct", case["id"], probe["id"])][0]
            python = python_dbm(case, probe)
            parity_rows.append({"case": case["id"], "probe": probe["id"], "java_dbm": java_dbm,
                                "python_dbm": python, "difference_db": python - java_dbm})
    contrast_rows = []
    for name in EXAMPLES:
        imported = imported_forward_dbm(name)
        for case in (c for c in examples if c["example"] == name):
            key = case["id"], "hub"
            row = {"example": name, "sensor_id": case["sensor_id"],
                   "python_imported_dbm": imported[case["sensor_id"]],
                   "python_same_height_dbm": python_dbm(case, case["probes"][0]),
                   "java_direct_dbm": java[("direct", *key)][0]}
            row["java_direct_at_floor"] = row["java_direct_dbm"] <= JAVA_FLOOR_DBM
            for mode in ("rays", "waves"):
                row[f"java_{mode}_dbm"], row[f"java_{mode}_paths"] = java[(mode, *key)]
                # Every path culled (or a floor value) says nothing about multipath: no difference is stated.
                comparable = row[f"java_{mode}_paths"] > 0 and not row["java_direct_at_floor"]
                row[f"{mode}_minus_direct_db"] = (row[f"java_{mode}_dbm"] - row["java_direct_dbm"]
                                                  if comparable else None)
            contrast_rows.append(row)
    java_version = subprocess.run(["java", "-version"], capture_output=True, text=True).stderr.splitlines()[0]
    commit = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%H", args.java_ref, "--", "src/main/java"],
                            capture_output=True, text=True).stdout.strip()
    report = {
        "task": "B-121", "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "java": java_version, "java_sources_commit": commit, "python": platform.python_version(),
        "command": "python services/simulator/benchmarks/java_parity.py --output docs/simulation/evidence/java-parity.json",
        "tolerance_db": PARITY_TOLERANCE_DB, "java_floor_dbm": JAVA_FLOOR_DBM, "java_culling_dbm": JAVA_CULLING_DBM,
        "parity_cases": parity, "parity": parity_rows,
        "parity_summary": {"probes": len(parity_rows),
                           "max_abs_difference_db": max(abs(r["difference_db"]) for r in parity_rows)},
        "examples": examples, "contrast": contrast_rows,
        "contrast_summary": {name: {mode: _spread([r[f"{mode}_minus_direct_db"] for r in contrast_rows
                                                   if r["example"] == name]) for mode in ("rays", "waves")}
                             for name in EXAMPLES},
    }
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"parity": report["parity_summary"], "contrast": report["contrast_summary"]}, indent=2))
    return 0 if report["parity_summary"]["max_abs_difference_db"] <= PARITY_TOLERANCE_DB else 1


if __name__ == "__main__":
    sys.exit(main())
