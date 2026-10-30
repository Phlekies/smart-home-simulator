"""Access-point placement among allowed places (B-105): bounded exhaustive search.

Each allowed position is evaluated with the same direct-path budget as links, in both
directions, for every priority device linked to the AP radio. Candidates are ordered by
(1) more devices with complete margins, (2) the best worst-case limiting margin and (3) the
best mean. Missing data is reported, never filled, and does not produce a ranking.
"""

from __future__ import annotations

import hashlib
import json
import statistics
import time
from typing import NamedTuple

from .coverage import inside_wall
from .engines import LIMITATIONS, direction, input_hash, radio_pair_check
from .models import (
    CandidateEvaluation, Device, ExcludedCandidate, Link, PlacementSearchRequest, PlacementSearchResult, Point,
    Project, Radio, TargetEvaluation,
)

ENGINE_VERSION = "0.1.0"
MAX_WORK = 2_000_000  # candidates × targets × walls
TOP = 50
PLACEMENT_LIMITATIONS = LIMITATIONS + [
    "Solo se mueve el AP elegido; añadir un AP exige definir su enlace de datos y no se evalúa aquí.",
    "Los lugares permitidos los declara la persona: alimentación, cableado y montaje no se verifican.",
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


def request_hash(request: PlacementSearchRequest) -> str:
    parameters = request.model_dump(mode="json", exclude={"project"})
    canonical = json.dumps({"project": input_hash(request.project), "parameters": parameters},
                           sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def preflight(request: PlacementSearchRequest) -> list[Target]:
    """Links between the AP radio and each priority device; rejects unbounded or empty searches."""
    project = request.project
    devices = {d.id: d for d in project.devices}
    ap = devices[request.access_point_device_id]
    ap_radio = next(r for r in ap.radios if r.id == request.access_point_radio_id)
    wanted = set(request.target_device_ids)
    found = []
    for link in project.links:
        ends = {(link.source_device_id, link.source_radio_id), (link.target_device_id, link.target_radio_id)}
        if (ap.id, ap_radio.id) not in ends:
            continue
        other_id, other_radio_id = next(end for end in ends if end != (ap.id, ap_radio.id))
        if wanted and other_id not in wanted:
            continue
        other = devices[other_id]
        radio = next(r for r in other.radios if r.id == other_radio_id)
        _, blocked, notes = radio_pair_check(ap_radio, radio)
        found.append(Target(link, other, ap_radio, radio, " ".join(notes) if blocked else None,
                            [] if blocked else notes))
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
    for link, other, ap_radio, other_radio, blocked, _ in targets:
        if blocked:
            out.append(TargetEvaluation(device_id=other.id, link_id=link.id, forward_margin_db=None,
                                        reverse_margin_db=None, limiting_margin_db=None, limiting_direction=None,
                                        status="not-computed", reason=blocked))
            continue
        p, q = other.position, place
        if ((p.x - q.x) ** 2 + (p.y - q.y) ** 2 + (p.z - q.z) ** 2) ** 0.5 < 0.1:
            out.append(TargetEvaluation(device_id=other.id, link_id=link.id, forward_margin_db=None,
                                        reverse_margin_db=None, limiting_margin_db=None, limiting_direction=None,
                                        status="not-computed", reason="too-close"))
            continue
        forward = direction(project, moved, ap_radio, other, other_radio)
        reverse = direction(project, other, other_radio, moved, ap_radio)
        f = None if forward is None else forward.margin_db
        r = None if reverse is None else reverse.margin_db
        if f is not None and r is not None:
            (limiting, side), status = min((f, "forward"), (r, "reverse")), "complete"
        else:
            limiting, side, status = None, None, "incomplete"
        out.append(TargetEvaluation(device_id=other.id, link_id=link.id, forward_margin_db=f, reverse_margin_db=r,
                                    limiting_margin_db=limiting, limiting_direction=side, status=status,
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
        if wall is not None:
            excluded.append(ExcludedCandidate(candidate_id=candidate_id, position=place,
                                              reason=f"inside-wall:{wall.id}"))
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
    if not ranked:
        reasons.append("Ningún lugar tiene márgenes completos: no se ordenan los candidatos.")
    if excluded:
        reasons.append(f"{len(excluded)} lugares descartados por quedar dentro de una pared.")
    for target in targets:
        reasons += [note for note in target.notes if note not in reasons]
        if target.blocked:
            reasons.append(f"{target.device.id}: no evaluable con esta radio del AP. {target.blocked}")
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
