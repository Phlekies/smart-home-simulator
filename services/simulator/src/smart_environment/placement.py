"""Access-point placement among allowed places (B-105): bounded exhaustive search.

Each allowed position is evaluated with the same direct-path budget as links, in both
directions, for every priority device linked to the AP radio. Candidates are ordered by
(1) more devices with complete margins, (2) the best worst-case limiting margin and (3) the
best mean. Missing data is reported, never filled, and does not produce a ranking.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
import time
from typing import NamedTuple

from .backhaul import is_network_device
from .engines import LIMITATIONS, direction, geometry_issue, input_hash, inside_wall, radio_pair_check, wall_heights
from .models import (
    CandidateEvaluation, Device, ExcludedCandidate, Fixture, Link, PlacementSearchRequest, PlacementSearchResult,
    Point, Project, Radio, TargetEvaluation,
)

ENGINE_VERSION = "0.1.0"
MAX_WORK = 2_000_000  # candidates × targets × walls
TOP = 50
PLACEMENT_LIMITATIONS = LIMITATIONS + [
    "Solo se mueve el AP elegido; si su conexión de datos es inalámbrica, ese enlace se evalúa con él.",
    "Enchufes y tomas de red solo descartan lugares más lejanos, en línea recta, que el límite indicado; "
    "el recorrido real del cable y el montaje no se verifican.",
    "Ordenar por margen no clasifica cobertura ni recomienda compras; la reserva de diseño está pendiente.",
]


class PlacementLimitError(ValueError):
    """The search exceeds the bounded cost or has nothing comparable to evaluate."""


class Target(NamedTuple):
    link: Link
    device: Device
    ap_radio: Radio
    radio: Radio
    blocked: str | None  # why the pair cannot be evaluated at all
    notes: list[str]     # compatibility caveats that do not block the budget
    backhaul: bool       # the AP's own wireless data link, evaluated whatever the priorities


def request_hash(request: PlacementSearchRequest) -> str:
    """Project, parameters and outlets/sockets. Unset B-119 fields leave older hashes unchanged."""
    parameters = request.model_dump(mode="json", exclude={"project"})
    for key in ("max_power_distance_m", "max_network_distance_m"):
        if parameters.get(key) is None:
            parameters.pop(key, None)
    payload = {"project": input_hash(request.project), "parameters": parameters}
    building = request.project.building
    if building.power_outlets or building.network_ports:
        payload["fixtures"] = building.model_dump(mode="json", include={"power_outlets", "network_ports"})
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _nearest_m(place: Point, fixtures: list[Fixture]) -> float:
    return min(math.dist((place.x, place.y, place.z), (f.position.x, f.position.y, f.position.z)) for f in fixtures)


def _outside_storey(project: Project, place: Point) -> str | None:
    """Above or below every wall nothing is crossed, so such a place would look falsely good (B-122)."""
    heights = wall_heights(project)
    if heights is None or heights[0] <= place.z <= heights[1]:
        return None
    return f"outside-wall-heights:{heights[0]:g}-{heights[1]:g}m"


def _out_of_reach(request: PlacementSearchRequest, place: Point) -> str | None:
    """Straight line is the shortest possible cable: only places that surely cannot be reached are dropped."""
    building = request.project.building
    for limit, fixtures, label in ((request.max_power_distance_m, building.power_outlets, "power-outlet"),
                                   (request.max_network_distance_m, building.network_ports, "network-port")):
        if limit is not None and _nearest_m(place, fixtures) > limit:
            return f"no-{label}-within:{limit:g}m"
    return None


def preflight(request: PlacementSearchRequest) -> list[Target]:
    """Links between the AP radio and each priority device; rejects unbounded or empty searches."""
    project = request.project
    devices = {d.id: d for d in project.devices}
    ap = devices[request.access_point_device_id]
    ap_radio = next(r for r in ap.radios if r.id == request.access_point_radio_id)
    wanted = set(request.target_device_ids)
    data_link = ap.data_connection.link_id if ap.data_connection is not None else None
    found = []
    for link in project.links:
        ends = [(link.source_device_id, link.source_radio_id), (link.target_device_id, link.target_radio_id)]
        backhaul = link.id == data_link
        if (ap.id, ap_radio.id) not in ends and not backhaul:
            continue
        own_end = next(end for end in ends if end[0] == ap.id)
        other_id, other_radio_id = next(end for end in ends if end != own_end)
        if wanted and other_id not in wanted and not backhaul:
            continue
        own_radio = next(r for r in ap.radios if r.id == own_end[1])
        other = devices[other_id]
        radio = next(r for r in other.radios if r.id == other_radio_id)
        _, blocked, notes = radio_pair_check(own_radio, radio)
        found.append(Target(link, other, own_radio, radio, " ".join(notes) if blocked else None,
                            [] if blocked else notes, backhaul))
    if missing := sorted(wanted - {t.device.id for t in found}):
        raise PlacementLimitError(f"Sin enlace con la radio del AP para: {', '.join(missing)}")
    if all(t.blocked for t in found):
        raise PlacementLimitError("Ningún equipo prioritario tiene un enlace evaluable con la radio del AP.")
    positions = len(request.candidates) + sum(len(z.positions()) for z in request.zones) + 1
    work = positions * len(found) * max(1, len(request.project.building.walls))
    if work > MAX_WORK:
        raise PlacementLimitError(f"La búsqueda requiere {work} evaluaciones (máximo {MAX_WORK}); "
                                  "reduce lugares, paso de las zonas o equipos prioritarios.")
    return found


def _evaluate(project: Project, ap: Device, place: Point, targets: list[Target]) -> list[TargetEvaluation]:
    moved = ap.model_copy(update={"position": place})
    out = []
    for link, other, ap_radio, other_radio, blocked, _, backhaul in targets:
        if blocked:
            out.append(TargetEvaluation(device_id=other.id, link_id=link.id, backhaul=backhaul,
                                        forward_margin_db=None, reverse_margin_db=None, limiting_margin_db=None,
                                        limiting_direction=None, status="not-computed", reason=blocked))
            continue
        p, q = other.position, place
        if ((p.x - q.x) ** 2 + (p.y - q.y) ** 2 + (p.z - q.z) ** 2) ** 0.5 < 0.1:
            out.append(TargetEvaluation(device_id=other.id, link_id=link.id, backhaul=backhaul,
                                        forward_margin_db=None, reverse_margin_db=None, limiting_margin_db=None,
                                        limiting_direction=None, status="not-computed", reason="too-close"))
            continue
        forward = direction(project, moved, ap_radio, other, other_radio)
        reverse = direction(project, other, other_radio, moved, ap_radio)
        f = None if forward is None else forward.margin_db
        r = None if reverse is None else reverse.margin_db
        if f is not None and r is not None:
            (limiting, side), status = min((f, "forward"), (r, "reverse")), "complete"
        else:
            limiting, side, status = None, None, "incomplete"
        out.append(TargetEvaluation(device_id=other.id, link_id=link.id, backhaul=backhaul, forward_margin_db=f,
                                    reverse_margin_db=r, limiting_margin_db=limiting, limiting_direction=side,
                                    status=status,
                                    reason=None if status == "complete" else "missing-power-or-sensitivity"))
    return out


def _summarize(candidate_id: str, label: str, source: str, place: Point,
               targets: list[TargetEvaluation]) -> CandidateEvaluation:
    complete = [t for t in targets if t.status == "complete"]
    worst = min(complete, key=lambda t: t.limiting_margin_db) if complete else None
    return CandidateEvaluation(
        candidate_id=candidate_id, label=label, source=source, position=place, targets=targets,
        complete_targets=len(complete), worst_margin_db=None if worst is None else worst.limiting_margin_db,
        mean_margin_db=statistics.fmean(t.limiting_margin_db for t in complete) if complete else None,
        worst_target_id=None if worst is None else worst.device_id, delta_worst_margin_db=None)


def search(request: PlacementSearchRequest) -> PlacementSearchResult:
    started = time.perf_counter()
    targets = preflight(request)
    project = request.project
    ap = next(d for d in project.devices if d.id == request.access_point_device_id)
    places: list[tuple[str, str, str, Point]] = [
        (c.id, c.label, "candidate", c.position) for c in request.candidates]
    for zone in request.zones:
        places += [(f"{zone.id}@{x:g},{y:g}", zone.label, "zone", Point(x=x, y=y, z=zone.height_m))
                   for x, y in zone.positions()]
    baseline = _summarize("current", "Posición actual", "current", ap.position,
                          _evaluate(project, ap, ap.position, targets))
    evaluated, excluded = [], []
    for candidate_id, label, source, place in places:
        wall = next((w for w in project.building.walls if inside_wall(place, w)), None)
        reason = f"inside-wall:{wall.id}" if wall is not None else _outside_storey(project, place)             or _out_of_reach(request, place)
        if reason is not None:
            excluded.append(ExcludedCandidate(candidate_id=candidate_id, position=place, reason=reason))
            continue
        evaluated.append(_summarize(candidate_id, label, source, place, _evaluate(project, ap, place, targets)))
    ranked = any(c.complete_targets for c in evaluated)
    if ranked:
        evaluated.sort(key=lambda c: (-c.complete_targets,
                                      -(c.worst_margin_db if c.worst_margin_db is not None else -1e9),
                                      -(c.mean_margin_db if c.mean_margin_db is not None else -1e9)))
    for c in evaluated:
        if c.worst_margin_db is not None and baseline.worst_margin_db is not None \
                and c.complete_targets == baseline.complete_targets:
            c.delta_worst_margin_db = c.worst_margin_db - baseline.worst_margin_db
    reasons = []
    incomplete = sorted({t.device_id for t in baseline.targets if t.status == "incomplete"})
    if incomplete:
        reasons.append("Faltan potencia o sensibilidad para un margen bidireccional de: " + ", ".join(incomplete)
                       + ". Esos equipos no influyen en el orden.")
    if not evaluated:
        reasons.append("Ningún lugar permitido queda tras los descartes: no hay candidatos que comparar.")
    elif not ranked:
        reasons.append("Ningún lugar tiene márgenes completos: no se ordenan los candidatos.")
    for prefix, text in (("inside-wall", "por quedar dentro de una pared"),
                         ("outside-wall-heights", "por quedar a una altura sin paredes ni forjados modelados"),
                         ("no-power-outlet", f"por no tener un enchufe a {request.max_power_distance_m or 0:g} m "
                                             "o menos en línea recta"),
                         ("no-network-port", f"por no tener una toma de red a {request.max_network_distance_m or 0:g} m "
                                             "o menos en línea recta")):
        if count := sum(e.reason.startswith(prefix) for e in excluded):
            reasons.append(f"{count} lugares descartados {text}.")
    if issue := geometry_issue(project, ap.position, "La posición actual del AP"):
        reasons.append(issue)
    if (reach := _out_of_reach(request, ap.position)) is not None:
        reasons.append(f"La posición actual no cumple el límite de cableado ({reach}).")
    if (request.max_power_distance_m or request.max_network_distance_m) and evaluated:
        reasons.append("El cable real recorre paredes y techos: un lugar conservado puede seguir sin alcanzarse.")
    if ap.data_connection is not None and ap.data_connection.kind == "wired" and request.max_network_distance_m is None:
        reasons.append("El AP se conecta por cable: indica la distancia máxima a una toma de red para limitar "
                       "la búsqueda.")
    for target in targets:
        reasons += [note for note in target.notes if note not in reasons]
        if target.blocked:
            reasons.append(f"{target.device.id}: no evaluable con esta radio del AP. {target.blocked}")
        if target.backhaul:
            reasons.append(f"El enlace de datos {target.link.id} del AP se mueve con él: cuenta como un equipo "
                           "prioritario más.")
    if ap.data_connection is None and is_network_device(ap):
        reasons.append("Conexión de datos del AP sin definir: si fuera inalámbrica, su enlace también cambiaría "
                       "al moverlo.")
    return PlacementSearchResult(
        engine="quick-estimate", engine_version=ENGINE_VERSION, input_hash=input_hash(project),
        request_hash=request_hash(request), access_point_device_id=ap.id,
        access_point_radio_id=request.access_point_radio_id, parameters=request.model_dump(exclude={"project"}),
        criterion="max-min-bidirectional-margin",
        ranked=ranked, target_device_ids=[t.device.id for t in targets], baseline=baseline,
        ranking=evaluated[:TOP], evaluated=len(evaluated), excluded=excluded,
        elapsed_ms=(time.perf_counter() - started) * 1000,
        scope="Búsqueda exhaustiva entre lugares permitidos para el AP; trayecto directo; "
              "compatibilidad funcional no evaluada",
        limitations=PLACEMENT_LIMITATIONS, reasons=reasons)
