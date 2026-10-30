"""Small analytical baseline; advanced adapters must never silently fall back to it."""

import hashlib
import importlib.metadata
import json
import math
import shutil
import time

from .models import Device, DirectionResult, LinkResult, Point, Project, Radio, SimulationResult, Wall

LIMITATIONS = [
    "Estimación analítica no calibrada: no garantiza conexión ni compatibilidad funcional.",
    "Solo trayecto directo y cruces de paredes verticales; sin forjados, reflexiones, difracción ni fading.",
    "Sin interferencias, tráfico, ACK, reintentos, velocidad útil, BER ni latencia.",
    "Materiales empíricos por bandas 2.4/5 GHz; fuera de esas bandas el motor rechaza el cálculo.",
    "Antena aproximada en azimut; no representa patrones tridimensionales medidos.",
    "Cruces por superficies y esquinas son aproximados; equipos dentro de paredes no se modelan.",
]
# Interaction kinds of smart_environment.references that this engine claims to model.
MODELLED_INTERACTIONS = ("free-space", "log-distance", "wall-penetration")


def input_hash(project: Project) -> str:
    """SHA-256 of the canonical project JSON; identifies the scenario of a result or measurement."""
    canonical = json.dumps(project.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def engine_capabilities() -> list[dict]:
    try:
        version = importlib.metadata.version("sionna-rt")
    except importlib.metadata.PackageNotFoundError:
        version = None
    return [
        {"id": "quick-estimate", "name": "Estimación rápida", "implemented": True,
         "available": True, "verified": False, "version": "0.1.0",
         "interactions": list(MODELLED_INTERACTIONS),
         "description": "Modelo analítico probado con casos sintéticos; sin validación experimental."},
        {"id": "sionna-rt", "name": "Sionna RT", "implemented": False,
         "available": False, "verified": False, "version": version,
         "description": "Adaptador pendiente; instalar el paquete no verifica el motor ni el hardware."},
        {"id": "ns-3", "name": "ns-3", "implemented": False,
         "available": False, "verified": False, "version": None,
         "executable_detected": shutil.which("ns3") is not None,
         "description": "Adaptador y modelos de protocolos pendientes de integración y validación."},
    ]


def crossing_parameter(a: Point, b: Point, wall: Wall) -> float | None:
    """Segment/vertical-wall crossing; shared wall endpoints use a half-open convention."""
    dx, dy = b.x - a.x, b.y - a.y
    wx, wy = wall.end.x - wall.start.x, wall.end.y - wall.start.y
    determinant = dx * wy - dy * wx
    if abs(determinant) < 1e-10:
        return None
    qx, qy = wall.start.x - a.x, wall.start.y - a.y
    t = (qx * wy - qy * wx) / determinant
    u = (qx * dy - qy * dx) / determinant
    if not (1e-9 < t < 1 - 1e-9 and 0 <= u < 1):
        return None
    z = a.z + t * (b.z - a.z)
    return t if wall.start.z <= z <= wall.start.z + wall.height_m else None


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


def direction(project: Project, tx: Device, tx_radio: Radio,
              rx: Device, rx_radio: Radio) -> DirectionResult | None:
    if tx_radio.tx_power_dbm is None:
        return None
    distance = math.dist((tx.position.x, tx.position.y, tx.position.z),
                         (rx.position.x, rx.position.y, rx.position.z))
    # Log-distance anchored to Friis at 1 m; distances < 1 m remain free-space.
    d = max(distance, 0.1)
    fspl_1m = 20 * math.log10(4 * math.pi * tx_radio.frequency_hz / 299_792_458)
    path_loss = fspl_1m + (20 if d < 1 else 10 * project.settings.path_loss_exponent) * math.log10(d)
    materials = {m.id: m for m in project.building.materials}
    wall_loss = 0.0
    crossed = []
    for wall in project.building.walls:
        if crossing_parameter(tx.position, rx.position, wall) is not None:
            material = materials[wall.material_id]
            base = material.loss_db_24ghz if tx_radio.frequency_hz < 3e9 else material.loss_db_5ghz
            wall_loss += base + wall.thickness_m * 100 * material.extra_loss_db_per_cm
            crossed.append(wall.id)
    angle = math.degrees(math.atan2(rx.position.y - tx.position.y, rx.position.x - tx.position.x))
    tx_gain = antenna_gain(tx_radio, tx_radio.tx_gain_dbi, angle)
    rx_gain = antenna_gain(rx_radio, rx_radio.rx_gain_dbi, angle + 180)
    polarization = -20 * math.log10(max(abs(math.cos(math.radians(
        tx_radio.polarization_deg - rx_radio.polarization_deg))), .05))
    received = (tx_radio.tx_power_dbm + tx_gain + rx_gain + project.settings.system_gain_db
                - path_loss - wall_loss - project.settings.extra_loss_db_per_m * distance - polarization)
    noise = -174 + 10 * math.log10(rx_radio.bandwidth_hz) + rx_radio.noise_figure_db
    return DirectionResult(tx_device_id=tx.id, rx_device_id=rx.id, distance_m=distance,
                           path_loss_db=path_loss, wall_loss_db=wall_loss, crossed_wall_ids=crossed,
                           received_power_dbm=received, noise_dbm=noise, snr_db=received - noise,
                           margin_db=None if rx_radio.sensitivity_dbm is None else received - rx_radio.sensitivity_dbm)


def simulate(project: Project) -> SimulationResult:
    started = time.perf_counter()
    devices = {d.id: d for d in project.devices}
    results = []
    for link in project.links:
        source, target = devices[link.source_device_id], devices[link.target_device_id]
        a = next(r for r in source.radios if r.id == link.source_radio_id)
        b = next(r for r in target.radios if r.id == link.target_radio_id)
        reasons = []
        compatibility = "radio-compatible"
        if a.protocol != "unknown" and b.protocol != "unknown" and a.protocol != b.protocol:
            compatibility = "incompatible"
            reasons.append("Los protocolos de radio son distintos; se necesita una ruta o puente adecuado.")
        if abs(a.frequency_hz - b.frequency_hz) > 1 or (a.channel is not None and b.channel is not None and a.channel != b.channel):
            compatibility = "incompatible"
            reasons.append("Las radios no usan la misma frecuencia/canal configurado.")
        if compatibility == "incompatible":
            results.append(LinkResult(id=link.id, compatibility=compatibility, status="incompatible", reasons=reasons))
            continue
        if a.protocol == "unknown" or b.protocol == "unknown" or a.channel is None or b.channel is None:
            compatibility = "unverified"
            reasons.append("Falta verificar protocolo o canal; el presupuesto físico no demuestra compatibilidad.")
        if abs(a.bandwidth_hz - b.bandwidth_hz) > 1:
            results.append(LinkResult(id=link.id, compatibility="unverified", status="unsupported",
                                      reasons=reasons + ["Anchos de banda diferentes: negociación aún no modelada."]))
            continue
        # The legacy material model has two empirical bands only.
        if not (2.4e9 <= a.frequency_hz <= 2.5e9 or 5e9 <= a.frequency_hz <= 5.9e9):
            results.append(LinkResult(id=link.id, compatibility=compatibility, status="unsupported",
                                      reasons=reasons + ["La frecuencia queda fuera de las bandas empíricas del estimador."]))
            continue
        forward = direction(project, source, a, target, b)
        reverse = direction(project, target, b, source, a)
        for result, tx in [(forward, source), (reverse, target)]:
            if result is None:
                reasons.append(f"Falta potencia de transmisión de {tx.name}; no se calcula esa dirección.")
            elif result.margin_db is None:
                reasons.append(f"Falta sensibilidad del receptor {result.rx_device_id}.")
            elif result.distance_m < 0.1:
                reasons.append("Distancia inferior a 0.1 m: fuera del alcance del modelo; pérdida acotada.")
        complete = (forward is not None and reverse is not None and forward.margin_db is not None
                    and reverse.margin_db is not None and forward.distance_m >= .1)
        if any(d is not None and d.margin_db is not None and d.margin_db < 0 for d in (forward, reverse)):
            status = "below-threshold"
        elif complete and compatibility == "radio-compatible":
            status = "above-threshold"
        else:
            status = "unverified"
        results.append(LinkResult(id=link.id, compatibility=compatibility, status=status,
                                  forward=forward, reverse=reverse, reasons=reasons))
    return SimulationResult(engine="quick-estimate", engine_version="0.1.0",
                            input_hash=input_hash(project),
                            elapsed_ms=(time.perf_counter() - started) * 1000,
                            scope="Presupuesto de enlace directo; compatibilidad funcional no evaluada",
                            limitations=LIMITATIONS, links=results)
