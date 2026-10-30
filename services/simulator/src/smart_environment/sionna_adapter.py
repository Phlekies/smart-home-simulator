"""Sionna RT adapter under technical evaluation (B-102); not exposed by the API.

Only the evaluation runner imports Sionna, lazily. A missing package, LLVM or GPU backend
raises ``EngineUnavailable``: there is never a fallback to the quick estimator.
Walls become single flat surfaces on their centre plane and the wall thickness is passed to
the ITU slab material, which is how Sionna RT models walls (one surface per wall).
"""

from __future__ import annotations

import cmath
import importlib.metadata
import math
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from .models import Device, Project, Radio, Wall

# Provisional mapping of the legacy Java material ids to ITU-R P.2040 types. It is an
# inference for the evaluation, not a measured property, and is reported as such.
LEGACY_ITU_TYPES = {"concrete": "concrete", "brick": "brick", "drywall": "plasterboard", "glass": "glass",
                    "wood": "wood", "metal-door": "metal"}
INTERACTION_NAMES = {1: "specular", 2: "diffuse", 4: "refraction", 8: "diffraction"}


class EngineUnavailable(RuntimeError):
    """Sionna RT or its Dr.Jit backend cannot run in this environment."""


class UnsupportedScene(ValueError):
    """The project uses something this adapter does not translate faithfully."""


Vertex = tuple[float, float, float]


@dataclass(frozen=True)
class Surface:
    wall_id: str
    material_id: str
    itu_type: str
    thickness_m: float
    vertices: tuple[Vertex, ...]
    faces: tuple[tuple[int, int, int], ...]


@dataclass(frozen=True)
class SceneSpec:
    frequency_hz: float
    surfaces: tuple[Surface, ...]
    material_provenance: dict[str, str]


def wall_surface(wall: Wall) -> tuple[tuple[Vertex, ...], tuple[tuple[int, int, int], ...]]:
    """Vertical rectangle on the wall's centre plane, two triangles."""
    z0, z1 = wall.start.z, wall.start.z + wall.height_m
    (ax, ay), (bx, by) = (wall.start.x, wall.start.y), (wall.end.x, wall.end.y)
    return ((ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1)), ((0, 1, 2), (0, 2, 3))


def obj_text(vertices, faces) -> str:
    return "".join([f"v {x!r} {y!r} {z!r}\n" for x, y, z in vertices]
                   + [f"f {a + 1} {b + 1} {c + 1}\n" for a, b, c in faces])


def scene_spec(project: Project, frequency_hz: float, itu_materials: dict[str, str] | None = None) -> SceneSpec:
    """Translate walls and materials; an unmapped material is an error, never a default."""
    explicit = itu_materials or {}
    provenance, surfaces = {}, []
    for wall in project.building.walls:
        if wall.material_id in explicit:
            itu_type, origin = explicit[wall.material_id], "given"
        elif wall.material_id in LEGACY_ITU_TYPES:
            itu_type, origin = LEGACY_ITU_TYPES[wall.material_id], "inferred-from-legacy-id"
        else:
            raise UnsupportedScene(f"Material {wall.material_id} sin tipo ITU conocido; no se asume ninguno")
        provenance[wall.material_id] = f"{itu_type} ({origin})"
        vertices, faces = wall_surface(wall)
        surfaces.append(Surface(wall.id, wall.material_id, itu_type, wall.thickness_m, vertices, faces))
    return SceneSpec(frequency_hz, tuple(surfaces), provenance)


def unsupported_radio_reasons(tx: Radio, rx: Radio) -> list[str]:
    reasons = []
    for radio in (tx, rx):
        if radio.antenna != "omnidirectional" or radio.beamwidth_deg < 360:
            reasons.append(f"Radio {radio.id}: patrón direccional sin traducir al adaptador.")
    if abs(((tx.polarization_deg - rx.polarization_deg) + 180) % 360 - 180) > 1e-9:
        reasons.append("Polarizaciones distintas: el adaptador solo usa antenas verticales coincidentes.")
    if abs(tx.frequency_hz - rx.frequency_hz) > 1:
        reasons.append("Las radios no comparten frecuencia.")
    if tx.tx_power_dbm is None:
        reasons.append(f"Radio {tx.id} sin potencia de transmisión: no se calcula ese sentido.")
    return reasons


def combine_paths(coefficients, delays_s, frequency_hz: float, bandwidth_hz: float,
                  subcarriers: int = 64) -> tuple[float, float, float]:
    """Linear power gains of a set of paths: coherent at the carrier, incoherent, wideband mean.

    Sionna's ``paths.a`` excludes the carrier phase of each path length, which is carried by
    ``tau``; the coherent sum must apply e^{−j2πf·τ}. The wideband value averages |H(f)|²
    over the channel, as an OFDM receiver does, and is less sensitive to a single fade.
    """
    paths = [(complex(a), float(tau)) for a, tau in zip(coefficients, delays_s)]
    if not paths:
        return 0.0, 0.0, 0.0

    def power_at(frequency: float) -> float:
        return abs(sum(a * cmath.exp(-2j * math.pi * frequency * tau) for a, tau in paths)) ** 2

    offsets = [(index + 0.5) / subcarriers - 0.5 for index in range(subcarriers)]
    wideband = sum(power_at(frequency_hz + offset * bandwidth_hz) for offset in offsets) / subcarriers
    return power_at(frequency_hz), sum(abs(a) ** 2 for a, _ in paths), wideband


@dataclass(frozen=True)
class PathDetail:
    interactions: tuple[str, ...]
    delay_ns: float
    power_db: float | None  # |a|² of this path in dB relative to the transmitted power; None if zero


@dataclass(frozen=True)
class DirectionEstimate:
    tx_device_id: str
    rx_device_id: str
    received_power_dbm: float | None  # coherent phasor sum of all paths at the carrier frequency
    incoherent_power_dbm: float | None
    wideband_power_dbm: float | None = None  # mean of |H(f)|² across the radio's channel bandwidth
    paths: tuple[PathDetail, ...] = ()
    elapsed_ms: float = 0.0
    reasons: tuple[str, ...] = ()


@dataclass
class SionnaRT:
    """Thin wrapper around Sionna RT's PathSolver with explicit interaction switches."""

    max_depth: int = 3
    specular_reflection: bool = True
    refraction: bool = True
    diffraction: bool = False
    edge_diffraction: bool = False
    samples_per_src: int = 1_000_000
    subcarriers: int = 64  # frequency samples for the wideband mean
    seed: int = 42
    _rt: object = field(init=False, repr=False)
    _mi: object = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            import mitsuba
            import sionna.rt as rt
        except Exception as error:  # ImportError or Dr.Jit backend initialisation errors
            raise EngineUnavailable(f"Sionna RT no se puede cargar: {error}") from error
        self._rt, self._mi = rt, mitsuba

    @staticmethod
    def versions() -> dict[str, str | None]:
        out = {}
        for package in ("sionna-rt", "mitsuba", "drjit"):
            try:
                out[package] = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                out[package] = None
        return out

    def variant(self) -> str:
        return self._mi.variant()

    def build_scene(self, spec: SceneSpec, workdir: Path):
        rt = self._rt
        scene = rt.load_scene()
        scene.frequency = spec.frequency_hz
        scene.tx_array = rt.PlanarArray(num_rows=1, num_cols=1, pattern="iso", polarization="V")
        scene.rx_array = rt.PlanarArray(num_rows=1, num_cols=1, pattern="iso", polarization="V")
        materials, objects = {}, []
        for surface in spec.surfaces:
            key = (surface.itu_type, surface.thickness_m)
            if key not in materials:
                materials[key] = rt.ITURadioMaterial(name=f"itu-{surface.itu_type}-{len(materials)}",
                                                     itu_type=surface.itu_type, thickness=surface.thickness_m)
            path = workdir / f"surface-{len(objects)}.obj"
            path.write_text(obj_text(surface.vertices, surface.faces), encoding="ascii")
            objects.append(rt.SceneObject(fname=str(path), name=f"wall-{len(objects)}",
                                          radio_material=materials[key]))
        if objects:
            scene.edit(add=objects)
        return scene

    def direction(self, scene, tx: Device, tx_radio: Radio, rx: Device, rx_radio: Radio) -> DirectionEstimate:
        import numpy as np

        reasons = unsupported_radio_reasons(tx_radio, rx_radio)
        if reasons:
            return DirectionEstimate(tx.id, rx.id, None, None, reasons=tuple(reasons))
        rt, mi = self._rt, self._mi
        for name in ("tx", "rx"):
            if name in scene.transmitters or name in scene.receivers:
                scene.remove(name)
        scene.add(rt.Transmitter("tx", position=mi.Point3f(tx.position.x, tx.position.y, tx.position.z),
                                 power_dbm=tx_radio.tx_power_dbm))
        scene.add(rt.Receiver("rx", position=mi.Point3f(rx.position.x, rx.position.y, rx.position.z)))
        started = time.perf_counter()
        paths = rt.PathSolver()(scene, max_depth=self.max_depth, samples_per_src=self.samples_per_src,
                                synthetic_array=True, los=True, specular_reflection=self.specular_reflection,
                                diffuse_reflection=False, refraction=self.refraction,
                                diffraction=self.diffraction, edge_diffraction=self.edge_diffraction,
                                seed=self.seed)
        a_real, a_imag = (np.asarray(part, dtype=np.float64).reshape(-1) for part in paths.a)
        valid = np.asarray(paths.valid).reshape(-1).astype(bool)
        delays = np.asarray(paths.tau, dtype=np.float64).reshape(-1)
        kinds = np.asarray(paths.interactions).reshape(self.max_depth, -1) if self.max_depth else None
        elapsed = (time.perf_counter() - started) * 1000
        coefficients = (a_real + 1j * a_imag)[valid]
        details = []
        for index in np.flatnonzero(valid):
            names = tuple(INTERACTION_NAMES.get(int(k), str(int(k))) for k in (kinds[:, index] if kinds is not None else [])
                          if int(k) != 0)
            power = abs(complex(a_real[index], a_imag[index])) ** 2
            details.append(PathDetail(names or ("line-of-sight",), float(delays[index] * 1e9),
                                      10 * math.log10(power) if power > 0 else None))
        coherent, incoherent, wideband = combine_paths(coefficients.tolist(), delays[valid].tolist(),
                                                       tx_radio.frequency_hz,
                                                       tx_radio.bandwidth_hz, self.subcarriers)

        def to_dbm(power: float) -> float | None:
            gains = tx_radio.tx_gain_dbi + rx_radio.rx_gain_dbi
            return tx_radio.tx_power_dbm + gains + 10 * math.log10(power) if power > 0 else None

        return DirectionEstimate(tx.id, rx.id, to_dbm(coherent), to_dbm(incoherent), to_dbm(wideband),
                                 tuple(details), elapsed,
                                 () if coefficients.size else (
                                     f"Sin trayectos con max_depth={self.max_depth}: cada pared atravesada cuenta "
                                     "como una interacción; no equivale a ausencia de señal.",))


def run_link_forward(engine: SionnaRT, project: Project, itu_materials: dict[str, str] | None = None,
                     link_index: int = 0) -> DirectionEstimate:
    """Forward direction of one link, building a fresh scene in a temporary directory."""
    link = project.links[link_index]
    devices = {d.id: d for d in project.devices}
    tx, rx = devices[link.source_device_id], devices[link.target_device_id]
    tx_radio = next(r for r in tx.radios if r.id == link.source_radio_id)
    rx_radio = next(r for r in rx.radios if r.id == link.target_radio_id)
    with tempfile.TemporaryDirectory(prefix="sionna-scene-") as workdir:
        scene = engine.build_scene(scene_spec(project, tx_radio.frequency_hz, itu_materials), Path(workdir))
        return engine.direction(scene, tx, tx_radio, rx, rx_radio)
