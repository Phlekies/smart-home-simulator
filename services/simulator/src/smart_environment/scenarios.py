"""Scenarios for unresolved hypotheses (B-108): unknown doors and uncertain materials.

Only hypotheses the project leaves open are varied: doors marked ``unknown`` and materials
with an uncertainty range. Doors stated open or closed are facts and stay fixed. For the
direct-path estimator the received power falls monotonically with every crossing loss, so the
automatic best and worst scenarios are the exact extremes of those hypotheses. The ranges
are scenario bounds, not probability intervals.
"""

from __future__ import annotations

import hashlib
import json
import time

from .engines import LIMITATIONS, crossing_parameter, direction, input_hash, radio_pair_check
from .models import (
    LinkScenarioResult, Project, ScenarioAssumptions, ScenarioOutcome, ScenarioRequest, ScenarioResult,
)

ENGINE_VERSION = "0.1.0"
SCENARIO_LIMITATIONS = LIMITATIONS + [
    "Mejor y peor caso solo varían puertas desconocidas y materiales con rango declarado.",
    "Los rangos son límites de escenario razonados, no intervalos de probabilidad.",
    "Con un motor multipath el peor caso no tiene por qué coincidir con todas las pérdidas máximas.",
]


def request_hash(request: ScenarioRequest) -> str:
    parameters = request.model_dump(mode="json", exclude={"project"})
    canonical = json.dumps({"project": input_hash(request.project), "parameters": parameters},
                           sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def automatic_scenarios(project: Project) -> list[ScenarioAssumptions]:
    unknown_doors = [w.id for w in project.building.walls if w.door == "unknown"]
    uncertain = [m.id for m in project.building.materials if m.uncertainty is not None]
    return [
        ScenarioAssumptions(id="nominal", name="Proyecto tal cual: puertas desconocidas cerradas, materiales nominales"),
        ScenarioAssumptions(id="best", name="Hipótesis favorables: puertas desconocidas abiertas, materiales en su mínimo",
                            doors={d: "open" for d in unknown_doors}, materials={m: "low" for m in uncertain}),
        ScenarioAssumptions(id="worst", name="Hipótesis desfavorables: puertas desconocidas cerradas, materiales en su máximo",
                            doors={d: "closed" for d in unknown_doors}, materials={m: "high" for m in uncertain}),
    ]


def _range(values: list[float | None]) -> list[float] | None:
    return None if not values or any(v is None for v in values) else [min(values), max(values)]


def evaluate(request: ScenarioRequest) -> ScenarioResult:
    started = time.perf_counter()
    project = request.project
    scenarios = automatic_scenarios(project) + list(request.scenarios)
    devices = {d.id: d for d in project.devices}
    materials = {m.id: m for m in project.building.materials}
    results = []
    for link in project.links:
        source, target = devices[link.source_device_id], devices[link.target_device_id]
        a = next(r for r in source.radios if r.id == link.source_radio_id)
        b = next(r for r in target.radios if r.id == link.target_radio_id)
        compatibility, blocked, reasons = radio_pair_check(a, b)
        if blocked is not None:
            results.append(LinkScenarioResult(id=link.id, compatibility=compatibility, outcomes=[],
                                              forward_range_dbm=None, reverse_range_dbm=None, hypotheses=[],
                                              margin_sign="incomplete", reasons=reasons))
            continue
        outcomes = [ScenarioOutcome(scenario_id=s.id, forward=direction(project, source, a, target, b, s),
                                    reverse=direction(project, target, b, source, a, s)) for s in scenarios]
        hypotheses = [w.id for w in project.building.walls
                      if (w.door == "unknown" or materials[w.material_id].uncertainty is not None)
                      and crossing_parameter(source.position, target.position, w) is not None]
        limiting = []
        for outcome in outcomes:
            margins = [d.margin_db if d is not None else None for d in (outcome.forward, outcome.reverse)]
            limiting.append(None if None in margins else min(margins))
        if None in limiting:
            sign = "incomplete"
            reasons.append("Falta potencia o sensibilidad en algún sentido: no se puede decir si el margen "
                           "depende de las hipótesis.")
        elif all(m >= 0 for m in limiting) or all(m < 0 for m in limiting):
            sign = "consistent"
        else:
            sign = "depends-on-hypotheses"
            reasons.append("El signo del margen limitante cambia entre escenarios: la conclusión depende de "
                           "hipótesis no resueltas (" + ", ".join(hypotheses or ["escenarios pedidos"]) + ").")
        results.append(LinkScenarioResult(
            id=link.id, compatibility=compatibility, outcomes=outcomes,
            forward_range_dbm=_range([o.forward.received_power_dbm if o.forward else None for o in outcomes]),
            reverse_range_dbm=_range([o.reverse.received_power_dbm if o.reverse else None for o in outcomes]),
            hypotheses=hypotheses, margin_sign=sign, reasons=reasons))
    return ScenarioResult(engine="quick-estimate", engine_version=ENGINE_VERSION, input_hash=input_hash(project),
                          scenarios=scenarios, links=results, elapsed_ms=(time.perf_counter() - started) * 1000,
                          scope="Escenarios de puertas y materiales sobre el trayecto directo; "
                                "compatibilidad funcional no evaluada",
                          limitations=SCENARIO_LIMITATIONS)
