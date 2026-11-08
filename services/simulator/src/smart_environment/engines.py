"""Small analytical baseline; advanced adapters must never silently fall back to it."""

import hashlib
import importlib.metadata
import json
import math
import shutil
import time
from collections.abc import Callable
from typing import NamedTuple

from .backhaul import access_point_connections
from .models import (
    Device, DirectionResult, Link, LinkResult, Material, Point, Project, Radio, ScenarioAssumptions,
    SimulationResult, Wall,
)

LIMITATIONS = [
    "Estimación analítica no calibrada: no garantiza conexión ni compatibilidad funcional.",
    "Solo trayecto directo y cruces de paredes verticales; sin forjados, reflexiones, difracción ni fading.",
    "Sin interferencias, tráfico, ACK, reintentos, velocidad útil, BER ni latencia.",
    "Materiales empíricos por bandas 2.4/5 GHz; fuera de esas bandas el motor rechaza el cálculo.",
    "Antena aproximada en azimut; no representa patrones tridimensionales medidos.",
    "Cruces por superficies y esquinas son aproximados; equipos dentro de paredes no se modelan.",
]
# 0.2.0 (B-122/B-126): positions outside the model are never favourable and wall ends no longer depend
# on drawing direction. Results saved with another version are stale (see /api/projects/fingerprint).
ENGINE_VERSION = "0.2.0"
# Interaction kinds of smart_environment.references that this engine claims to model.
MODELLED_INTERACTIONS = ("free-space", "log-distance", "wall-penetration")


def input_hash(project: Project) -> str:
    """SHA-256 of the canonical project JSON; identifies the scenario of a result or measurement.

    The plan reference image is a display aid that no solver reads, so it is left out: adding or
    moving it neither changes the hash of existing projects nor invalidates their results.
    Optional fields added later (door state, material uncertainty) count only when set, so
    projects that do not use them keep the hash they had before those fields existed. Radio
    provenance labels describe values without changing them, so they never enter the hash.
    Power outlets and network sockets only limit placement searches, which hash them separately.
    """
    data = project.model_dump(mode="json", exclude={"plan_reference": True,
                                                    "building": {"power_outlets", "network_ports"}})
    for device in data["devices"]:
        for radio in device["radios"]:
            radio.pop("provenance", None)
        if device.get("data_connection") is None:
            device.pop("data_connection", None)
    for wall in data["building"]["walls"]:
        if wall.get("door") is None:
            wall.pop("door", None)
    for material in data["building"]["materials"]:
        if material.get("uncertainty") is None:
            material.pop("uncertainty", None)
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def engine_capabilities() -> list[dict]:
    try:
        version = importlib.metadata.version("sionna-rt")
    except importlib.metadata.PackageNotFoundError:
        version = None
    return [
        {"id": "quick-estimate", "name": "Estimación rápida", "implemented": True,
         "available": True, "verified": False, "version": ENGINE_VERSION,
         "interactions": list(MODELLED_INTERACTIONS),
         "description": "Modelo analítico probado con casos sintéticos y con el trayecto directo de Java "
                        "(B-121); sin validación experimental."},
        {"id": "sionna-rt", "name": "Sionna RT", "implemented": False,
         "available": False, "verified": False, "version": version,
         "description": "Adaptador de evaluación (B-102) contrastado con casos analíticos en WSL/CPU; "
                        "no integrado en la API (decisión del 2026-11-08, ADR-008) ni validado con medidas. "
                        "Instalar el paquete no lo activa."},
        {"id": "ns-3", "name": "ns-3", "implemented": False,
         "available": False, "verified": False, "version": None,
         "executable_detected": shutil.which("ns3") is not None,
         "description": "Adaptador y modelos de protocolos pendientes de integración y validación."},
    ]


END_TOLERANCE = 1e-9  # along the wall, as a fraction of its length


def crossing_parameter(a: Point, b: Point, wall: Wall) -> tuple[float, float] | None:
    """Where segment a→b meets a wall's centre line within its height: (t along a→b, u along the wall).

    ``u`` includes both wall ends; ``crossed_walls`` decides what a hit on an end means. Endpoints of
    a→b and rays running along a wall (rasante) are not crossings.
    """
    dx, dy = b.x - a.x, b.y - a.y
    wx, wy = wall.end.x - wall.start.x, wall.end.y - wall.start.y
    determinant = dx * wy - dy * wx
    if abs(determinant) < 1e-10:
        return None
    qx, qy = wall.start.x - a.x, wall.start.y - a.y
    t = (qx * wy - qy * wx) / determinant
    u = (qx * dy - qy * dx) / determinant
    if not (1e-9 < t < 1 - 1e-9 and -END_TOLERANCE <= u <= 1 + END_TOLERANCE):
        return None
    z = a.z + t * (b.z - a.z)
    return (t, u) if wall.start.z <= z <= wall.start.z + wall.height_m else None


def crossed_walls(a: Point, b: Point, walls: list[Wall], loss: Callable[[Wall], float]) -> list[Wall]:
    """Walls that segment a→b crosses, in the given order, whatever direction each wall was drawn in (B-126).

    A wall crossed between its ends counts once. Where the segment passes exactly through wall ends
    (a corner, a junction or a free wall end), the walls ending there are split by the side of the
    segment they lie on, and only the side with fewer walls counts, as if the segment were shifted
    infinitesimally towards the more open side: touching a free end or the outside of a corner is a
    graze, a corner or a straight joint counts once, a four-way junction counts twice. On a tie the side
    with more loss counts, then the side holding the earliest wall, so both directions agree.
    """
    dx, dy = b.x - a.x, b.y - a.y
    chosen: dict[int, Wall] = {}
    ends: dict[tuple[float, float], list[tuple[int, Wall, float]]] = {}
    for order, wall in enumerate(walls):
        hit = crossing_parameter(a, b, wall)
        if hit is None:
            continue
        u = hit[1]
        if END_TOLERANCE < u < 1 - END_TOLERANCE:
            chosen[order] = wall
            continue
        here, other = (wall.start, wall.end) if u <= END_TOLERANCE else (wall.end, wall.start)
        side = dx * (other.y - here.y) - dy * (other.x - here.x)
        if side != 0:
            ends.setdefault((round(here.x, 6), round(here.y, 6)), []).append((order, wall, side))
    for group in ends.values():
        left = [(order, wall) for order, wall, side in group if side > 0]
        right = [(order, wall) for order, wall, side in group if side < 0]
        if len(left) != len(right):
            counted = min(left, right, key=len)
        else:
            counted = max(left, right, key=lambda side: (sum(loss(wall) for _, wall in side),
                                                         -min(order for order, _ in side)))
        chosen.update(counted)
    return [chosen[order] for order in sorted(chosen)]


def inside_wall(point: Point, wall: Wall) -> bool:
    """Point within half the wall thickness of its centre line and within its height."""
    if not wall.start.z <= point.z <= wall.start.z + wall.height_m:
        return False
    ax, ay, bx, by = wall.start.x, wall.start.y, wall.end.x, wall.end.y
    length_sq = (bx - ax) ** 2 + (by - ay) ** 2
    t = max(0.0, min(1.0, ((point.x - ax) * (bx - ax) + (point.y - ay) * (by - ay)) / length_sq))
    return math.hypot(point.x - (ax + t * (bx - ax)), point.y - (ay + t * (by - ay))) < wall.thickness_m / 2


def wall_heights(project: Project) -> tuple[float, float] | None:
    """Lowest wall base and highest wall top: the storey the walls describe, or None without walls."""
    walls = project.building.walls
    if not walls:
        return None
    return min(w.start.z for w in walls), max(w.start.z + w.height_m for w in walls)


def geometry_issue(project: Project, point: Point, label: str) -> str | None:
    """Why a position lies outside what the estimator models (B-122); None when it is inside."""
    if wall := next((w for w in project.building.walls if inside_wall(point, w)), None):
        return f"{label} está dentro de la pared {wall.id}: un equipo empotrado no se modela."
    if (heights := wall_heights(project)) is not None:
        low, top = heights
        if point.z > top:
            return (f"{label} está a {point.z:g} m, por encima de todas las paredes ({top:g} m): otra planta o "
                    "falso techo; los forjados no se modelan.")
        if point.z < low:
            return (f"{label} está a {point.z:g} m, por debajo de todas las paredes ({low:g} m): otra planta; "
                    "los forjados no se modelan.")
    return None


def antenna_gain(radio: Radio, peak_gain: float, angle_deg: float) -> float:
    if radio.antenna == "omnidirectional" or radio.beamwidth_deg >= 360:
        return peak_gain
    delta = abs((angle_deg - radio.orientation_deg + 180) % 360 - 180)
    half = max(1, radio.beamwidth_deg / 2)
    floor = peak_gain - radio.side_lobe_attenuation_db
    if delta <= half:
        amplitude = max(math.cos(delta / half * math.pi / 2), 1e-3) ** radio.pattern_sharpness
        return max(peak_gain + 20 * math.log10(amplitude), floor)
    return floor - 6 * min(1, (delta - half) / max(1, 180 - half))


def material_loss_db(material: Material, frequency_hz: float, bound: str = "nominal") -> float:
    """Loss per crossing before thickness; 'low'/'high' use the uncertainty range when present."""
    high_band = frequency_hz >= 3e9
    u = material.uncertainty
    if bound == "nominal" or u is None:
        return material.loss_db_5ghz if high_band else material.loss_db_24ghz
    if bound == "low":
        return u.loss_db_5ghz_low if high_band else u.loss_db_24ghz_low
    return u.loss_db_5ghz_high if high_band else u.loss_db_24ghz_high


class Budget(NamedTuple):
    """Terms of a one-way budget in dB; ``received_dbm`` adds them in the original order."""

    distance_m: float
    tx_power_dbm: float
    tx_gain_db: float
    rx_gain_db: float
    system_gain_db: float
    path_loss_db: float
    walls: list[tuple[str, float]]  # crossed wall id and its loss, in project order
    extra_loss_db: float
    polarization_loss_db: float

    @property
    def wall_loss_db(self) -> float:
        total = 0.0
        for _, loss in self.walls:
            total += loss
        return total

    @property
    def received_dbm(self) -> float:
        return (self.tx_power_dbm + self.tx_gain_db + self.rx_gain_db + self.system_gain_db
                - self.path_loss_db - self.wall_loss_db - self.extra_loss_db - self.polarization_loss_db)


def budget(project: Project, tx: Device, tx_radio: Radio, rx: Device, rx_radio: Radio,
           scenario: ScenarioAssumptions | None = None) -> Budget | None:
    """Every term of the one-way budget, or None without transmit power. Open doors add no loss."""
    if tx_radio.tx_power_dbm is None:
        return None
    distance = math.dist((tx.position.x, tx.position.y, tx.position.z),
                         (rx.position.x, rx.position.y, rx.position.z))
    # Log-distance anchored to Friis at 1 m; distances < 1 m remain free-space.
    d = max(distance, 0.1)
    fspl_1m = 20 * math.log10(4 * math.pi * tx_radio.frequency_hz / 299_792_458)
    path_loss = fspl_1m + (20 if d < 1 else 10 * project.settings.path_loss_exponent) * math.log10(d)
    materials = {m.id: m for m in project.building.materials}

    def loss(wall: Wall) -> float:
        material = materials[wall.material_id]
        bound = scenario.materials.get(material.id, "nominal") if scenario else "nominal"
        return material_loss_db(material, tx_radio.frequency_hz, bound) + wall.thickness_m * 100 * material.extra_loss_db_per_cm

    closed = [wall for wall in project.building.walls
              if ((scenario.doors.get(wall.id) if scenario else None) or wall.door) != "open"]
    walls = [(wall.id, loss(wall)) for wall in crossed_walls(tx.position, rx.position, closed, loss)]
    angle = math.degrees(math.atan2(rx.position.y - tx.position.y, rx.position.x - tx.position.x))
    polarization = -20 * math.log10(max(abs(math.cos(math.radians(
        tx_radio.polarization_deg - rx_radio.polarization_deg))), .05))
    return Budget(distance_m=distance, tx_power_dbm=tx_radio.tx_power_dbm,
                  tx_gain_db=antenna_gain(tx_radio, tx_radio.tx_gain_dbi, angle),
                  rx_gain_db=antenna_gain(rx_radio, rx_radio.rx_gain_dbi, angle + 180),
                  system_gain_db=project.settings.system_gain_db, path_loss_db=path_loss, walls=walls,
                  extra_loss_db=project.settings.extra_loss_db_per_m * distance, polarization_loss_db=polarization)


def direction(project: Project, tx: Device, tx_radio: Radio, rx: Device, rx_radio: Radio,
              scenario: ScenarioAssumptions | None = None) -> DirectionResult | None:
    """One-way budget. ``scenario`` overrides door states and material bounds; open doors add no loss."""
    terms = budget(project, tx, tx_radio, rx, rx_radio, scenario)
    if terms is None:
        return None
    received = terms.received_dbm
    noise = -174 + 10 * math.log10(rx_radio.bandwidth_hz) + rx_radio.noise_figure_db
    return DirectionResult(tx_device_id=tx.id, rx_device_id=rx.id, distance_m=terms.distance_m,
                           path_loss_db=terms.path_loss_db, wall_loss_db=terms.wall_loss_db,
                           crossed_wall_ids=[wall_id for wall_id, _ in terms.walls],
                           received_power_dbm=received, noise_dbm=noise, snr_db=received - noise,
                           margin_db=None if rx_radio.sensitivity_dbm is None else received - rx_radio.sensitivity_dbm)


def radio_pair_check(a: Radio, b: Radio) -> tuple[str, str | None, list[str]]:
    """Radio compatibility and model scope: (compatibility, blocking status or None, reasons)."""
    reasons = []
    compatibility = "radio-compatible"
    if a.protocol != "unknown" and b.protocol != "unknown" and a.protocol != b.protocol:
        compatibility = "incompatible"
        reasons.append("Los protocolos de radio son distintos; se necesita una ruta o puente adecuado.")
    if abs(a.frequency_hz - b.frequency_hz) > 1 or (a.channel is not None and b.channel is not None and a.channel != b.channel):
        compatibility = "incompatible"
        reasons.append("Las radios no usan la misma frecuencia/canal configurado.")
    if compatibility == "incompatible":
        return compatibility, "incompatible", reasons
    if a.protocol == "unknown" or b.protocol == "unknown" or a.channel is None or b.channel is None:
        compatibility = "unverified"
        reasons.append("Falta verificar protocolo o canal; el presupuesto físico no demuestra compatibilidad.")
    if abs(a.bandwidth_hz - b.bandwidth_hz) > 1:
        return "unverified", "unsupported", reasons + ["Anchos de banda diferentes: negociación aún no modelada."]
    # The legacy material model has two empirical bands only.
    if not (2.4e9 <= a.frequency_hz <= 2.5e9 or 5e9 <= a.frequency_hz <= 5.9e9):
        return compatibility, "unsupported", reasons + ["La frecuencia queda fuera de las bandas empíricas del estimador."]
    return compatibility, None, reasons


def sensitivity_note(radio: Radio, device_id: str) -> str | None:
    """Flag a margin that rests on a sensitivity nobody measured or declared for this device."""
    origin = (radio.provenance or {}).get("sensitivity_dbm")
    if origin is None:
        return None
    if origin.provenance == "standard-minimum":
        return (f"El margen hacia {device_id} usa la sensibilidad mínima del estándar, no la del producto "
                "(prudente, no garantiza funcionamiento).")
    if origin.provenance == "inferred":
        return f"El margen hacia {device_id} usa una sensibilidad inferida, no medida ni declarada."
    return None


def link_result(project: Project, link: Link) -> LinkResult:
    """Both directions of one project link, with every missing value stated."""
    devices = {d.id: d for d in project.devices}
    source, target = devices[link.source_device_id], devices[link.target_device_id]
    a = next(r for r in source.radios if r.id == link.source_radio_id)
    b = next(r for r in target.radios if r.id == link.target_radio_id)
    compatibility, blocked, reasons = radio_pair_check(a, b)
    if blocked is not None:
        return LinkResult(id=link.id, compatibility=compatibility, status=blocked, reasons=reasons)
    forward = direction(project, source, a, target, b)
    reverse = direction(project, target, b, source, a)
    for result, tx in [(forward, source), (reverse, target)]:
        if result is None:
            reasons.append(f"Falta potencia de transmisión de {tx.name}; no se calcula esa dirección.")
        elif result.margin_db is None:
            reasons.append(f"Falta sensibilidad del receptor {result.rx_device_id}.")
        elif note := sensitivity_note(b if result.rx_device_id == target.id else a, result.rx_device_id):
            reasons.append(note)
        elif result.distance_m < 0.1:
            reasons.append("Distancia inferior a 0.1 m: fuera del alcance del modelo; pérdida acotada.")
    complete = (forward is not None and reverse is not None and forward.margin_db is not None
                and reverse.margin_db is not None and forward.distance_m >= .1)
    outside = [issue for device in (source, target)
               if (issue := geometry_issue(project, device.position, device.name)) is not None]
    reasons += outside
    if any(d is not None and d.margin_db is not None and d.margin_db < 0 for d in (forward, reverse)):
        status = "below-threshold"
    elif complete and compatibility == "radio-compatible" and not outside:
        status = "above-threshold"
    else:
        status = "unverified"
    return LinkResult(id=link.id, compatibility=compatibility, status=status,
                      forward=forward, reverse=reverse, reasons=reasons)


def simulate(project: Project) -> SimulationResult:
    started = time.perf_counter()
    results = [link_result(project, link) for link in project.links]
    by_id = {result.id: result for result in results}
    return SimulationResult(engine="quick-estimate", engine_version=ENGINE_VERSION,
                            input_hash=input_hash(project),
                            elapsed_ms=(time.perf_counter() - started) * 1000,
                            scope="Presupuesto de enlace directo; compatibilidad funcional no evaluada",
                            limitations=LIMITATIONS, links=results,
                            access_points=access_point_connections(project, by_id.__getitem__))
