"""Closed-form propagation references, deliberately independent of ``engines.py``.

They check an engine against textbook expressions: Friis, ITU-R P.2040 slabs and
image-method specular reflection. They are idealised physics or model-consistency checks,
not measurements, and never prove accuracy in a real home.
"""

from __future__ import annotations

import argparse
import cmath
import json
import math
import sys
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass, field
from typing import Literal

from .models import Building, Device, Link, Material, Point, Project, Radio, Settings, SimulationResult, Wall

SPEED_OF_LIGHT_MPS = 299_792_458.0
VACUUM_PERMITTIVITY_F_PER_M = 8.8541878188e-12  # CODATA 2022

Polarization = Literal["TE", "TM"]
Interaction = Literal["free-space", "log-distance", "wall-penetration", "specular-reflection"]
CaseKind = Literal["physical-reference", "model-consistency"]
Verdict = Literal["agrees", "deviates", "not-modelled", "no-result"]


def wavelength_m(frequency_hz: float) -> float:
    return SPEED_OF_LIGHT_MPS / frequency_hz


def free_space_loss_db(distance_m: float, frequency_hz: float) -> float:
    """Friis free-space loss between isotropic antennas, 20·log10(4πd/λ), far field only."""
    if distance_m <= 0:
        raise ValueError("Free-space loss needs a positive distance")
    return 20 * math.log10(4 * math.pi * distance_m / wavelength_m(frequency_hz))


def log_distance_loss_db(distance_m: float, frequency_hz: float, exponent: float,
                         reference_m: float = 1.0) -> float:
    """Empirical log-distance model anchored to Friis at ``reference_m``; not a physical law."""
    if distance_m < reference_m:
        raise ValueError("Log-distance reference only defined beyond the anchor distance")
    return free_space_loss_db(reference_m, frequency_hz) + 10 * exponent * math.log10(distance_m / reference_m)


def fresnel_zone_radius_m(d1_m: float, d2_m: float, frequency_hz: float, zone: int = 1) -> float:
    """Radius of the n-th Fresnel zone at a point d1/d2 from the terminals."""
    return math.sqrt(zone * wavelength_m(frequency_hz) * d1_m * d2_m / (d1_m + d2_m))


@dataclass(frozen=True)
class ItuMaterial:
    """ITU-R P.2040-3 Table 3: η' = a·f^b and σ = c·f^d, with f in GHz."""

    id: str
    name: str
    a: float
    b: float
    c: float
    d: float
    min_ghz: float
    max_ghz: float

    def relative_permittivity(self, frequency_hz: float) -> complex:
        f_ghz = frequency_hz / 1e9
        if not self.min_ghz <= f_ghz <= self.max_ghz:
            raise ValueError(f"{self.name}: {f_ghz:g} GHz outside the tabulated {self.min_ghz:g}-{self.max_ghz:g} GHz")
        conductivity = self.c * f_ghz ** self.d
        return complex(self.a * f_ghz ** self.b,
                       -conductivity / (2 * math.pi * frequency_hz * VACUUM_PERMITTIVITY_F_PER_M))


# Checked on 2026-10-30 against the P.2040-3 table reproduced by MathWorks
# (buildingMaterialPermittivity); the ITU PDF link returned 404. See docs/simulation.
ITU_P2040_3 = {m.id: m for m in [
    ItuMaterial("concrete", "Concrete", 5.24, 0, 0.0462, 0.7822, 1, 100),
    ItuMaterial("brick", "Brick", 3.91, 0, 0.0238, 0.16, 1, 10),
    ItuMaterial("plasterboard", "Plasterboard", 2.73, 0, 0.0085, 0.9395, 1, 100),
    ItuMaterial("wood", "Wood", 1.99, 0, 0.0047, 1.0718, 0.001, 100),
    ItuMaterial("glass", "Glass", 6.31, 0, 0.0036, 1.3394, 0.1, 100),
    ItuMaterial("ceiling-board", "Ceiling board", 1.48, 0, 0.0011, 1.0750, 1, 100),
    ItuMaterial("chipboard", "Chipboard", 2.58, 0, 0.0217, 0.78, 1, 100),
    ItuMaterial("plywood", "Plywood", 2.71, 0, 0.33, 0, 1, 40),
    ItuMaterial("marble", "Marble", 7.074, 0, 0.0055, 0.9262, 1, 60),
    ItuMaterial("floorboard", "Floorboard", 3.66, 0, 0.0044, 1.3515, 50, 100),
    ItuMaterial("metal", "Metal", 1, 0, 1e7, 0, 1, 100),
]}


def _cos_transmitted(eta: complex, incidence_deg: float) -> complex:
    # Principal branch: with the e^{jωt} convention a lossy medium has Im < 0 (decaying wave).
    return cmath.sqrt(eta - math.sin(math.radians(incidence_deg)) ** 2)


def interface_reflection(eta: complex, incidence_deg: float, polarization: Polarization) -> complex:
    """Air→medium Fresnel field coefficient. TE: E normal to the plane of incidence.

    TM uses the ε-weighted form (Γ_TM = −Γ_TE at normal incidence); only |Γ| enters the
    power references except the coherent TE two-ray sum.
    """
    if not 0 <= incidence_deg < 90:
        raise ValueError("Incidence angle must be in [0, 90) degrees")
    cos_i = math.cos(math.radians(incidence_deg))
    root = _cos_transmitted(eta, incidence_deg)
    if polarization == "TE":
        return (cos_i - root) / (cos_i + root)
    return (eta * cos_i - root) / (eta * cos_i + root)


def slab_coefficients(material: ItuMaterial, thickness_m: float, frequency_hz: float,
                      incidence_deg: float = 0.0, polarization: Polarization = "TE") -> tuple[complex, complex]:
    """Homogeneous single-layer slab in air, all internal bounces summed: (R, T) field coefficients.

    q = (2πd/λ)·√(η − sin²θ); R = R'(1 − e^{−2jq}) / (1 − R'²e^{−2jq});
    T = (1 − R'²)e^{−jq} / (1 − R'²e^{−2jq}). Only |T| and |R| are used as references:
    the lateral offset of an oblique ray inside the slab is not part of the phase.
    """
    if thickness_m < 0:
        raise ValueError("Slab thickness cannot be negative")
    eta = material.relative_permittivity(frequency_hz)
    r = interface_reflection(eta, incidence_deg, polarization)
    q = 2 * math.pi * thickness_m / wavelength_m(frequency_hz) * _cos_transmitted(eta, incidence_deg)
    one_way, round_trip = cmath.exp(-1j * q), cmath.exp(-2j * q)
    denominator = 1 - r * r * round_trip
    return r * (1 - round_trip) / denominator, (1 - r * r) * one_way / denominator


def slab_loss_db(material: ItuMaterial, thickness_m: float, frequency_hz: float,
                 incidence_deg: float = 0.0, polarization: Polarization = "TE") -> float:
    _, transmission = slab_coefficients(material, thickness_m, frequency_hz, incidence_deg, polarization)
    if abs(transmission) < 1e-30:
        raise ValueError("Slab is opaque for this reference; an infinite slab does not represent gaps or frames")
    return -20 * math.log10(abs(transmission))


@dataclass(frozen=True)
class Reflection:
    point: tuple[float, float, float]
    path_length_m: float
    incidence_deg: float


def specular_reflection(tx: Point, rx: Point, wall: Wall) -> Reflection | None:
    """Image method on the vertical plane of a finite wall; None if the bounce misses it."""
    sx, sy = wall.start.x, wall.start.y
    wx, wy = wall.end.x - sx, wall.end.y - sy
    length = math.hypot(wx, wy)
    nx, ny = -wy / length, wx / length
    side_tx = (tx.x - sx) * nx + (tx.y - sy) * ny
    side_rx = (rx.x - sx) * nx + (rx.y - sy) * ny
    if side_tx * side_rx <= 0:
        return None  # terminals on opposite sides or on the plane: no specular bounce
    image = (tx.x - 2 * side_tx * nx, tx.y - 2 * side_tx * ny, tx.z)
    t = side_tx / (side_tx + side_rx)  # fraction of the image→rx segment where it meets the plane
    hit = tuple(i + t * (r - i) for i, r in zip(image, (rx.x, rx.y, rx.z)))
    u = ((hit[0] - sx) * wx + (hit[1] - sy) * wy) / length ** 2
    if not (0 <= u <= 1 and wall.start.z <= hit[2] <= wall.start.z + wall.height_m):
        return None
    path = math.dist(image, (rx.x, rx.y, rx.z))
    normal_component = abs(side_tx) + abs(side_rx)
    return Reflection(point=hit, path_length_m=path,
                      incidence_deg=math.degrees(math.acos(min(1.0, normal_component / path))))


def two_ray_received_dbm(tx_power_dbm: float, frequency_hz: float, direct_m: float, reflected_m: float,
                         gamma: complex, coherent: bool = True) -> float:
    """Direct + one reflected ray between isotropic antennas; coherent phasor or power sum."""
    k = 2 * math.pi / wavelength_m(frequency_hz)
    direct = cmath.exp(-1j * k * direct_m) / direct_m
    reflected = gamma * cmath.exp(-1j * k * reflected_m) / reflected_m
    power = abs(direct + reflected) ** 2 if coherent else abs(direct) ** 2 + abs(reflected) ** 2
    return tx_power_dbm + 20 * math.log10(wavelength_m(frequency_hz) / (4 * math.pi)) + 10 * math.log10(power)


# --- Reference scenarios ------------------------------------------------------------

FREQUENCY_HZ = 2.412e9  # Wi-Fi channel 1, the initial product band
TX_POWER_DBM = 20.0
TOLERANCE_DB = 0.01  # numerical agreement for the same model (float32 engines), not an accuracy target
COMMON_ASSUMPTIONS = (
    "Antenas isotrópicas de 0 dBi, polarización vertical coincidente y sin pérdidas del sistema.",
    "Campo lejano: distancias de al menos 1 m (≈ 8 λ a 2.412 GHz).",
)


@dataclass(frozen=True)
class ReferenceCase:
    id: str
    title: str
    interaction: Interaction
    kind: CaseKind
    project: Project
    expected_dbm: float
    formula: str
    source: str
    assumptions: tuple[str, ...]
    components: dict[str, float] = field(default_factory=dict)
    # Project material id → ITU material id, for engines that consume permittivity/conductivity.
    itu_materials: dict[str, str] = field(default_factory=dict)
    tolerance_db: float = TOLERANCE_DB


def _radio(frequency_hz: float) -> Radio:
    return Radio(id="r", protocol="wifi", channel=1 if frequency_hz < 2.43e9 else 11, frequency_hz=frequency_hz,
                 bandwidth_hz=20e6, tx_power_dbm=TX_POWER_DBM, sensitivity_dbm=None)


def _project(name: str, tx: Point, rx: Point, walls: list[Wall] = (), materials: list[Material] = (),
             exponent: float = 2.0, frequency_hz: float = FREQUENCY_HZ) -> Project:
    materials = list(materials) or [Material(id="unused", name="Unused", loss_db_24ghz=0, loss_db_5ghz=0)]
    return Project(
        name=f"Referencia · {name}",
        building=Building(width_m=40, depth_m=30, walls=list(walls), materials=materials),
        devices=[Device(id="tx", name="Emisor", role="access-point", position=tx, radios=[_radio(frequency_hz)],
                        evidence="Reference scenario; not a product"),
                 Device(id="rx", name="Receptor", role="endpoint", position=rx, radios=[_radio(frequency_hz)],
                        evidence="Reference scenario; not a product")],
        links=[Link(id="ref", source_device_id="tx", source_radio_id="r", target_device_id="rx", target_radio_id="r")],
        settings=Settings(path_loss_exponent=exponent),
        migration_notes=["Escenario analítico sintético: no representa una vivienda ni contiene medidas."],
    )


def _wall_across(x: float, material_id: str, thickness_m: float, angle_deg: float = 90, wall_id: str = "w1") -> Wall:
    """Wall through (x, 0), long and tall enough to act as an infinite plane for the direct ray."""
    half = 8.0
    c, s = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
    return Wall(id=wall_id, start=Point(x=x - half * c, y=-half * s), end=Point(x=x + half * c, y=half * s),
                height_m=3, thickness_m=thickness_m, material_id=material_id)


# Legacy Java table as imported by legacy.py (dB at 2.4 GHz, extra dB/cm), copied here on
# purpose so a change in the importer shows up as a changed comparison, not a silent pass.
LEGACY_24GHZ = {"drywall": ("Drywall", 3, 0), "brick": ("Brick", 6, .1), "concrete": ("Concrete", 10, .2),
                "glass": ("Glass", 2, 0), "wood": ("Wood", 3, .05)}
LEGACY_TO_ITU = {"drywall": "plasterboard", "brick": "brick", "concrete": "concrete", "glass": "glass", "wood": "wood"}


def reference_cases() -> list[ReferenceCase]:
    cases: list[ReferenceCase] = []
    friis = "P = P_tx − 20·log10(4πd/λ)"
    friis_source = "Friis; ITU-R P.525 (espacio libre)"

    for distance in (1.0, 5.0, 10.0, 30.0):
        cases.append(ReferenceCase(
            id=f"FS-{distance:g}m", title=f"Espacio libre a {distance:g} m, 2.412 GHz", interaction="free-space",
            kind="physical-reference",
            project=_project(f"espacio libre {distance:g} m", Point(x=0, y=0, z=1.2), Point(x=distance, y=0, z=1.2)),
            expected_dbm=TX_POWER_DBM - free_space_loss_db(distance, FREQUENCY_HZ),
            formula=friis, source=friis_source, assumptions=COMMON_ASSUMPTIONS))
    cases.append(ReferenceCase(
        id="FS-ch11", title="Espacio libre a 10 m, canal 11 (2.462 GHz)", interaction="free-space",
        kind="physical-reference",
        project=_project("canal 11", Point(x=0, y=0, z=1.2), Point(x=10, y=0, z=1.2), frequency_hz=2.462e9),
        expected_dbm=TX_POWER_DBM - free_space_loss_db(10, 2.462e9),
        formula=friis, source=friis_source, assumptions=COMMON_ASSUMPTIONS))
    slant = math.dist((0, 0, 2.5), (6, 0, 0.3))
    cases.append(ReferenceCase(
        id="FS-3D", title="Espacio libre con AP a 2.5 m y sensor a 0.3 m", interaction="free-space",
        kind="physical-reference",
        project=_project("altura", Point(x=0, y=0, z=2.5), Point(x=6, y=0, z=0.3)),
        expected_dbm=TX_POWER_DBM - free_space_loss_db(slant, FREQUENCY_HZ),
        formula=friis + " con d tridimensional", source=friis_source,
        assumptions=COMMON_ASSUMPTIONS + ("Sin suelo ni techo: sin reflexiones en forjados.",),
        components={"distance_m": slant}))
    cases.append(ReferenceCase(
        id="LD-n3", title="Log-distance n = 3 a 10 m", interaction="log-distance", kind="model-consistency",
        project=_project("log-distance", Point(x=0, y=0, z=1.2), Point(x=10, y=0, z=1.2), exponent=3.0),
        expected_dbm=TX_POWER_DBM - log_distance_loss_db(10, FREQUENCY_HZ, 3.0),
        formula="PL = FSPL(1 m) + 10·n·log10(d / 1 m)", source="Modelo empírico log-distance (ITU-R P.1238, forma general)",
        assumptions=COMMON_ASSUMPTIONS + ("El exponente es una hipótesis de ajuste, no una propiedad física.",)))

    # Slab references: η from ITU-R P.2040-3, normal incidence unless stated otherwise.
    distance = 10.0
    open_dbm = TX_POWER_DBM - free_space_loss_db(distance, FREQUENCY_HZ)
    slab_formula = "P = P_tx − FSPL(d) + 20·log10|T|, T de losa homogénea con rebotes internos"
    slab_source = "ITU-R P.2040-3: tabla 3 y coeficientes de una capa"
    slab_assumptions = COMMON_ASSUMPTIONS + (
        "Pared homogénea e infinita; sin montantes, armaduras, huecos, humedad ni marcos.",
        "Polarización vertical frente a pared vertical con rayo horizontal: TE.",
        "La longitud del trayecto ignora el desplazamiento del rayo dentro de la pared.")
    for legacy_id, thickness in (("concrete", .10), ("concrete", .20), ("brick", .10), ("drywall", .0125),
                                 ("glass", .006), ("wood", .04)):
        itu = ITU_P2040_3[LEGACY_TO_ITU[legacy_id]]
        loss = slab_loss_db(itu, thickness, FREQUENCY_HZ)
        name, base, per_cm = LEGACY_24GHZ[legacy_id]
        material = Material(id=legacy_id, name=name, loss_db_24ghz=base, loss_db_5ghz=base, extra_loss_db_per_cm=per_cm)
        cases.append(ReferenceCase(
            id=f"WALL-{legacy_id}-{thickness * 1000:g}mm", title=f"{itu.name} {thickness * 100:g} cm, incidencia normal",
            interaction="wall-penetration", kind="physical-reference",
            project=_project(f"{itu.name} {thickness * 100:g} cm", Point(x=0, y=0, z=1.2), Point(x=distance, y=0, z=1.2),
                             [_wall_across(5, legacy_id, thickness)], [material]),
            expected_dbm=open_dbm - loss, formula=slab_formula, source=slab_source, assumptions=slab_assumptions,
            components={"slab_loss_db": loss, "legacy_loss_db": base + thickness * 100 * per_cm},
            itu_materials={legacy_id: itu.id}))
    concrete = ITU_P2040_3["concrete"]
    oblique = slab_loss_db(concrete, .10, FREQUENCY_HZ, 60, "TE")
    cases.append(ReferenceCase(
        id="WALL-concrete-100mm-60deg", title="Hormigón 10 cm, incidencia 60° (TE)",
        interaction="wall-penetration", kind="physical-reference",
        project=_project("hormigón oblicuo", Point(x=0, y=0, z=1.2), Point(x=distance, y=0, z=1.2),
                         [_wall_across(5, "concrete", .10, angle_deg=30)],
                         [Material(id="concrete", name="Concrete", loss_db_24ghz=10, loss_db_5ghz=15,
                                   extra_loss_db_per_cm=.2)]),
        expected_dbm=open_dbm - oblique, formula=slab_formula, source=slab_source, assumptions=slab_assumptions,
        components={"slab_loss_db": oblique, "normal_incidence_loss_db": slab_loss_db(concrete, .10, FREQUENCY_HZ),
                    "legacy_loss_db": 10 + 10 * .2},
        itu_materials={"concrete": "concrete"}))

    # Consistency: the engine receives the slab loss as its own material parameter.
    plaster = ITU_P2040_3["plasterboard"]
    concrete_loss, plaster_loss = slab_loss_db(concrete, .20, FREQUENCY_HZ), slab_loss_db(plaster, .0125, FREQUENCY_HZ)
    fitted = [Material(id="concrete-fit", name="Concrete (ITU slab value)", loss_db_24ghz=concrete_loss,
                       loss_db_5ghz=concrete_loss, evidence="Reference value from ITU-R P.2040-3 slab, not measured"),
              Material(id="plaster-fit", name="Plasterboard (ITU slab value)", loss_db_24ghz=plaster_loss,
                       loss_db_5ghz=plaster_loss, evidence="Reference value from ITU-R P.2040-3 slab, not measured")]
    cases.append(ReferenceCase(
        id="WALL-fit-single", title="Pérdida de losa introducida como parámetro del material",
        interaction="wall-penetration", kind="model-consistency",
        project=_project("losa como parámetro", Point(x=0, y=0, z=1.2), Point(x=distance, y=0, z=1.2),
                         [_wall_across(5, "concrete-fit", .20)], fitted[:1]),
        expected_dbm=open_dbm - concrete_loss, formula="P = P_tx − FSPL(d) − L_material",
        source="Coherencia del cruce de paredes; valor de losa P.2040-3 como entrada",
        assumptions=COMMON_ASSUMPTIONS, components={"wall_loss_db": concrete_loss},
        itu_materials={"concrete-fit": "concrete"}))
    cases.append(ReferenceCase(
        id="WALL-fit-series", title="Dos paredes en serie con pérdidas de losa como parámetro",
        interaction="wall-penetration", kind="model-consistency",
        project=_project("dos paredes", Point(x=0, y=0, z=1.2), Point(x=distance, y=0, z=1.2),
                         [_wall_across(3, "concrete-fit", .20), _wall_across(7, "plaster-fit", .0125, wall_id="w2")],
                         fitted),
        expected_dbm=open_dbm - concrete_loss - plaster_loss, formula="P = P_tx − FSPL(d) − ΣL_material",
        source="Coherencia del cruce de paredes; sin acoplamiento entre paredes",
        assumptions=COMMON_ASSUMPTIONS + ("Ignora reflexiones múltiples entre las dos paredes.",),
        components={"wall_loss_db": concrete_loss + plaster_loss},
        itu_materials={"concrete-fit": "concrete", "plaster-fit": "plasterboard"}))

    # Specular reflection on a long concrete wall, TX/RX at equal height (pure TE).
    reflection_material = [Material(id="concrete", name="Concrete", loss_db_24ghz=10, loss_db_5ghz=15,
                                    extra_loss_db_per_cm=.2)]
    for case_id, title, tx, rx in (
            ("REFL-grazing", "Reflexión rasante en pared de hormigón paralela al enlace",
             Point(x=0, y=1, z=1.2), Point(x=10, y=1, z=1.2)),
            ("REFL-steep", "Reflexión casi normal frente a pared de hormigón",
             Point(x=2, y=3, z=1.2), Point(x=4, y=3, z=1.2))):
        wall = Wall(id="w1", start=Point(x=-20, y=0), end=Point(x=30, y=0), height_m=3, thickness_m=.20,
                    material_id="concrete")
        bounce = specular_reflection(tx, rx, wall)
        direct = math.dist((tx.x, tx.y, tx.z), (rx.x, rx.y, rx.z))
        gamma, _ = slab_coefficients(concrete, wall.thickness_m, FREQUENCY_HZ, bounce.incidence_deg, "TE")
        cases.append(ReferenceCase(
            id=case_id, title=title, interaction="specular-reflection", kind="physical-reference",
            project=_project(title, tx, rx, [wall], reflection_material),
            expected_dbm=two_ray_received_dbm(TX_POWER_DBM, FREQUENCY_HZ, direct, bounce.path_length_m, gamma),
            formula="Suma fasorial directo + R_TE·e^{−jkd₂}/d₂ (método de imágenes, R de losa)",
            source="Coeficiente de reflexión de una capa; materiales ITU-R P.2040-3",
            assumptions=slab_assumptions[:3] + (
                "Pared de 0.20 m como losa homogénea: R incluye los rebotes internos.",
                "Sin otras paredes, suelo ni techo: solo un rebote.",
                "La suma coherente es sensible a desplazamientos de centímetros (desvanecimiento)."),
            components={"direct_only_dbm": TX_POWER_DBM - free_space_loss_db(direct, FREQUENCY_HZ),
                        "reflected_only_dbm": TX_POWER_DBM - free_space_loss_db(bounce.path_length_m, FREQUENCY_HZ)
                        + 20 * math.log10(abs(gamma)),
                        "incoherent_sum_dbm": two_ray_received_dbm(TX_POWER_DBM, FREQUENCY_HZ, direct,
                                                                   bounce.path_length_m, gamma, coherent=False),
                        "incidence_deg": bounce.incidence_deg, "gamma_abs": abs(gamma),
                        "reflected_path_m": bounce.path_length_m},
            itu_materials={"concrete": "concrete"}))
    short = Wall(id="w1", start=Point(x=-1, y=0), end=Point(x=2, y=0), height_m=3, thickness_m=.20, material_id="concrete")
    cases.append(ReferenceCase(
        id="REFL-miss", title="Pared finita fuera del punto de reflexión especular",
        interaction="specular-reflection", kind="physical-reference",
        project=_project("reflexión fuera de pared", Point(x=0, y=1, z=1.2), Point(x=10, y=1, z=1.2), [short],
                         reflection_material),
        expected_dbm=TX_POWER_DBM - free_space_loss_db(10, FREQUENCY_HZ),
        formula=friis + "; el punto especular (x = 5 m) queda fuera de la pared", source="Método de imágenes",
        assumptions=COMMON_ASSUMPTIONS + ("Sin difracción en el extremo de la pared.",),
        itu_materials={"concrete": "concrete"}))
    return cases


# --- Engine comparison ----------------------------------------------------------------

@dataclass(frozen=True)
class CaseResult:
    case_id: str
    interaction: Interaction
    kind: CaseKind
    verdict: Verdict
    expected_dbm: float
    engine_dbm: float | None
    delta_db: float | None
    note: str = ""


Prediction = tuple[float | None, str]  # forward received power (dBm) or None, and why


def compare(cases: Iterable[ReferenceCase], run: Callable[[Project], SimulationResult],
            modelled: Iterable[Interaction]) -> list[CaseResult]:
    """Run each case through an engine and classify the forward received power."""
    def predict(case: ReferenceCase) -> Prediction:
        link = run(case.project).links[0]
        if link.forward is None:
            return None, f"Estado del motor: {link.status}"
        return link.forward.received_power_dbm, ""

    return compare_predictions(cases, predict, modelled)


def compare_predictions(cases: Iterable[ReferenceCase], predict: Callable[[ReferenceCase], Prediction],
                        modelled: Iterable[Interaction]) -> list[CaseResult]:
    """Classify any predictor of forward received power, e.g. an adapter under evaluation."""
    modelled = set(modelled)
    results = []
    for case in cases:
        value, reason = predict(case)
        if value is None:
            results.append(CaseResult(case.id, case.interaction, case.kind, "no-result", case.expected_dbm, None, None,
                                      reason))
            continue
        delta = value - case.expected_dbm
        notes = [f"coincide con {key}" for key, component in case.components.items()
                 if key.endswith("_dbm") and abs(value - component) <= case.tolerance_db]
        if abs(delta) <= case.tolerance_db:
            verdict: Verdict = "agrees"
            if case.interaction not in modelled:
                notes.append("interacción no modelada: coincidencia trivial")
        elif case.interaction not in modelled:
            verdict = "not-modelled"
        else:
            verdict = "deviates"
        results.append(CaseResult(case.id, case.interaction, case.kind, verdict, case.expected_dbm, value, delta,
                                  "; ".join(notes)))
    return results


def markdown_table(results: Iterable[CaseResult]) -> str:
    rows = ["| Caso | Tipo | Referencia (dBm) | Motor (dBm) | Δ (dB) | Veredicto | Nota |",
            "|---|---|---:|---:|---:|---|---|"]
    for r in results:
        engine = "—" if r.engine_dbm is None else f"{r.engine_dbm:.3f}"
        delta = "—" if r.delta_db is None else f"{r.delta_db:+.3f}"
        rows.append(f"| {r.case_id} | {r.kind} | {r.expected_dbm:.3f} | {engine} | {delta} | {r.verdict} | {r.note} |")
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> None:
    from .engines import MODELLED_INTERACTIONS, simulate

    parser = argparse.ArgumentParser(description="Compare the quick estimator with the analytical references")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to a legacy code page
    cases = reference_cases()
    results = compare(cases, simulate, MODELLED_INTERACTIONS)
    if args.json:
        print(json.dumps({"engine": "quick-estimate", "results": [asdict(r) for r in results],
                          "cases": [{"id": c.id, "components": c.components, "itu_materials": c.itu_materials}
                                    for c in cases]}, indent=2, ensure_ascii=False))
    else:
        print(markdown_table(results))


if __name__ == "__main__":
    main()
