"""Installation report per link (B-115, P5): what was computed, what it rests on, what is missing.

It only gathers results the API already produces (link budget in both directions, the
scenarios of unresolved doors/materials and the coverage class of B-139) and states what is
still open. The class uses a provisional, uncalibrated design reserve; the report never
recommends a purchase.
"""

from __future__ import annotations

from typing import Literal

import statistics

from pydantic import ConfigDict, Field, model_validator

from .classification import DESIGN_RESERVE_DB, POLICY
from .coverage import MAX_WORK, compute, map_work, preflight
from .engines import LIMITATIONS, input_hash, simulate
from .models import (
    AccessPointConnection, ClassificationPolicy, CoverageClass, CoverageMapParameters, CoverageMapRequest,
    CoverageMapResult, DirectionResult, Model, Project, Radio, ScenarioAssumptions, ScenarioRequest,
    _optional_fields,
)
from .scenarios import evaluate as evaluate_scenarios

PENDING_DECISIONS = [
    f"Criterio de fallo (95 % de entrega en ≥ 300 ecos) y reserva de diseño ({DESIGN_RESERVE_DB:g} dB): provisionales "
    "desde el 2026-11-09; se revisan con el piloto y se congelan antes de la validación.",
    "Validación experimental en viviendas: sin medidas todavía; las cifras son del estimador.",
]
EVIDENCE_LEVELS = [
    ("consistency", "checked",
     "Casos analíticos de espacio libre, pared y reflexión (B-101), reglas de cruce de paredes (B-126) y trayecto "
     "directo igual al de Java en antenas y polarización (B-121). Comprueba que el modelo calcula lo que dice; no "
     "que acierte en una vivienda."),
    ("calibration", "none", "Sin campañas de calibración: ningún parámetro se ha ajustado con medidas."),
    ("validation", "none", "Sin medidas independientes en viviendas: el error frente a la realidad es desconocido."),
]
NOT_EVALUATED = [
    "Tráfico, velocidad útil, latencia y estabilidad del enlace.",
    "Interferencias de otras redes y equipos.",
    "Compatibilidad funcional con aplicaciones, asistentes o automatizaciones.",
    "Reflexiones, difracción y desvanecimiento: el estimador usa el trayecto directo.",
]


MAX_REPORT_MAPS = 4


class ReportRequest(Model):
    model_config = ConfigDict(json_schema_extra=_optional_fields("maps"))

    project: Project
    scenarios: list[ScenarioAssumptions] = Field(default_factory=list, max_length=16)
    title: str | None = Field(default=None, max_length=160)
    maps: list[CoverageMapParameters] = Field(default_factory=list, max_length=MAX_REPORT_MAPS, description=(
        "Coverage maps to compute and attach (B-120); together they share one map's cost bound"))

    @model_validator(mode="after")
    def valid_scenarios(self) -> ReportRequest:
        ScenarioRequest(project=self.project, scenarios=self.scenarios)  # same rules, rejected as 422
        total = 0
        for parameters in self.maps:
            request = CoverageMapRequest(project=self.project, **dict(parameters))
            if request.engine != "quick-estimate":
                raise ValueError(f"{request.engine}: map adapter not implemented or verified; no fallback executed")
            preflight(request)
            total += map_work(request)
        if total > MAX_WORK:
            raise ValueError(f"Los mapas del informe requieren {total} evaluaciones celda×pared (máximo {MAX_WORK}).")
        return self


class ReportWall(Model):
    wall_id: str
    material: str
    door: Literal["open", "closed", "unknown"] | None


class ReportDirection(Model):
    from_device_id: str
    to_device_id: str
    received_power_dbm: float
    margin_db: float | None
    sensitivity_provenance: str = Field(description="Origin of the receiver sensitivity, 'sin etiqueta' if not set")
    walls: list[ReportWall]


class ReportLink(Model):
    model_config = ConfigDict(json_schema_extra=_optional_fields("coverage_class", "worst_case_limiting_margin_db"))

    link_id: str
    devices: list[str] = Field(description="Names of both ends, source first")
    radios: list[str] = Field(description="Protocol, channel and frequency of each end")
    compatibility: str
    status: str
    forward: ReportDirection | None
    reverse: ReportDirection | None
    limiting_direction: Literal["forward", "reverse"] | None
    limiting_margin_db: float | None
    forward_range_dbm: list[float] | None
    reverse_range_dbm: list[float] | None
    margin_sign: str
    hypotheses: list[str]
    notes: list[str]
    coverage_class: CoverageClass | None = Field(default=None, description="Class of the link (B-139)")
    worst_case_limiting_margin_db: float | None = Field(default=None, description=(
        "Limiting margin with the open hypotheses at their worst"))


class EvidenceLevel(Model):
    """What kind of evidence backs the numbers (B-135); consistency is not accuracy."""

    level: Literal["consistency", "calibration", "validation"]
    status: Literal["checked", "none"]
    detail: str


class MapSummary(Model):
    """Counts and spread of a map; cell counts per class, not a coverage percentage of the home."""

    model_config = ConfigDict(json_schema_extra=_optional_fields("class_counts"))

    cells: int
    computed_cells: int
    partial_cells: int
    not_computed_cells: int
    limiting_margin_db: list[float] | None = Field(description=(
        "[min, median, max] of the lower margin of both directions over computed cells; None without any"))
    negative_limiting_cells: int = Field(description="Computed cells whose lower margin is below 0 dB")
    class_counts: dict[str, int] | None = Field(default=None, description="Cells per coverage class (B-139)")


class ReportMap(Model):
    title: str
    summary: MapSummary
    result: CoverageMapResult = Field(description="Full map, so the report file keeps it for drawing and staleness")


class InstallationReport(Model):
    model_config = ConfigDict(json_schema_extra=_optional_fields("access_points", "maps", "evidence_levels",
                                                                 "classification"))

    title: str
    project_name: str
    input_hash: str
    engine: str
    engine_version: str
    scope: str
    links: list[ReportLink]
    counts: dict[str, int]
    pending_decisions: list[str]
    not_evaluated: list[str]
    limitations: list[str]
    access_points: list[AccessPointConnection] = Field(default_factory=list, description=(
        "Data path of each access point (B-117), as in the simulation result"))
    maps: list[ReportMap] = Field(default_factory=list, description="Requested coverage maps (B-120)")
    evidence_levels: list[EvidenceLevel] = Field(default_factory=list, description=(
        "Consistency, calibration and validation behind these numbers, kept apart (B-135)"))
    classification: ClassificationPolicy | None = Field(default=None, description="Policy behind coverage_class")


def _direction(project: Project, result: DirectionResult | None, receiver: Radio) -> ReportDirection | None:
    if result is None:
        return None
    walls = {w.id: w for w in project.building.walls}
    materials = {m.id: m.name for m in project.building.materials}
    labelled = (receiver.provenance or {}).get("sensitivity_dbm")
    origin = labelled.provenance if labelled is not None else "sin etiqueta"
    return ReportDirection(
        from_device_id=result.tx_device_id, to_device_id=result.rx_device_id,
        received_power_dbm=result.received_power_dbm, margin_db=result.margin_db, sensitivity_provenance=origin,
        walls=[ReportWall(wall_id=w, material=materials[walls[w].material_id], door=walls[w].door)
               for w in result.crossed_wall_ids])


def _map(project: Project, parameters: CoverageMapParameters) -> ReportMap:
    result = compute(CoverageMapRequest(project=project, **dict(parameters)))
    cells = result.cells
    margins = sorted(min(f, r) for f, r, status in zip(cells.forward_margin_db, cells.reverse_margin_db, cells.status)
                     if status == "computed")
    title = (f"{parameters.profile.name} · {parameters.grid.height_m:g} m"
             + (f" · {parameters.scenario.name}" if parameters.scenario else ""))
    return ReportMap(title=title, result=result, summary=MapSummary(
        cells=len(cells.status), computed_cells=result.computed_cells, partial_cells=result.partial_cells,
        not_computed_cells=result.not_computed_cells,
        limiting_margin_db=[margins[0], statistics.median(margins), margins[-1]] if margins else None,
        negative_limiting_cells=sum(margin < 0 for margin in margins),
        class_counts={name: (cells.coverage_class or []).count(name) for name in CLASS_KEYS}))


def build_report(request: ReportRequest) -> InstallationReport:
    project = request.project
    simulation = simulate(project)
    scenarios = {link.id: link for link in evaluate_scenarios(ScenarioRequest(project=project,
                                                                              scenarios=request.scenarios)).links}
    devices = {d.id: d for d in project.devices}
    links = []
    for link, result in zip(project.links, simulation.links):
        ends = [(devices[link.source_device_id], link.source_radio_id),
                (devices[link.target_device_id], link.target_radio_id)]
        radios, link_radios = [], []
        for device, radio_id in ends:
            radio = next(r for r in device.radios if r.id == radio_id)
            link_radios.append(radio)
            radios.append(f"{device.name}: {radio.protocol}, canal {radio.channel if radio.channel is not None else '?'}, "
                          f"{radio.frequency_hz / 1e9:.3f} GHz")
        margins = [(d.margin_db, side) for d, side in ((result.forward, "forward"), (result.reverse, "reverse"))
                   if d is not None and d.margin_db is not None]
        limiting = min(margins) if len(margins) == 2 else None
        scenario = scenarios[link.id]
        links.append(ReportLink(
            link_id=link.id, devices=[device.name for device, _ in ends], radios=radios,
            compatibility=result.compatibility, status=result.status,
            forward=_direction(project, result.forward, link_radios[1]),
            reverse=_direction(project, result.reverse, link_radios[0]),
            limiting_direction=None if limiting is None else limiting[1],
            limiting_margin_db=None if limiting is None else limiting[0],
            forward_range_dbm=scenario.forward_range_dbm, reverse_range_dbm=scenario.reverse_range_dbm,
            margin_sign=scenario.margin_sign, hypotheses=scenario.hypotheses,
            notes=list(dict.fromkeys(result.reasons + scenario.reasons)),
            coverage_class=result.coverage_class, worst_case_limiting_margin_db=result.worst_case_limiting_margin_db))
    counts = {"links": len(links),
              "both_margins": sum(link.limiting_margin_db is not None for link in links),
              "incomplete": sum(link.limiting_margin_db is None and link.compatibility != "incompatible"
                                for link in links),
              "incompatible": sum(link.compatibility == "incompatible" for link in links),
              "depends_on_hypotheses": sum(link.margin_sign == "depends-on-hypotheses" for link in links),
              **{key.replace("-", "_"): sum(link.coverage_class == key for link in links) for key in CLASS_KEYS}}
    return InstallationReport(
        title=request.title or f"Informe de instalación · {project.name}", project_name=project.name,
        input_hash=input_hash(project), engine=simulation.engine, engine_version=simulation.engine_version,
        scope=simulation.scope + ". La clasificación es una predicción sin calibrar; el informe no recomienda compras.",
        links=links, counts=counts, pending_decisions=PENDING_DECISIONS, not_evaluated=NOT_EVALUATED,
        limitations=LIMITATIONS, access_points=simulation.access_points,
        maps=[_map(project, parameters) for parameters in request.maps],
        evidence_levels=[EvidenceLevel(level=level, status=status, detail=detail)
                         for level, status, detail in EVIDENCE_LEVELS],
        classification=POLICY)


CLASS_KEYS = ("favourable", "marginal", "insufficient", "no-data")
CLASS_LABELS = {"favourable": "Favorable", "marginal": "Marginal", "insufficient": "Insuficiente",
                "no-data": "Sin datos"}
DOOR_LABELS = {"open": "abierta", "closed": "cerrada", "unknown": "estado desconocido"}
EVIDENCE_LABELS = {"consistency": "Consistencia matemática", "calibration": "Calibración con medidas",
                   "validation": "Validación en viviendas"}
CONNECTION_LABELS = {"gateway": "pasarela", "wired": "cable (no evaluado)", "wireless": "inalámbrica",
                     "unknown": "desconocida", "undefined": "sin definir", "loop": "bucle"}
SIGN_LABELS = {"consistent": "mismo signo en todos los escenarios",
               "depends-on-hypotheses": "depende de hipótesis no resueltas",
               "incomplete": "no se puede evaluar (faltan datos)"}


def _cell(value: object) -> str:
    text = "—" if value is None else (f"{value:.1f}" if isinstance(value, float) else str(value))
    return text.replace("|", "\\|").replace("\n", " ")


def to_markdown(report: InstallationReport) -> str:
    out = [f"# {_cell(report.title)}", "",
           f"Proyecto: {_cell(report.project_name)} · motor {report.engine} {report.engine_version} · "
           f"huella `{report.input_hash[:12]}`", "", f"> {_cell(report.scope)}", "",
           f"Enlaces: {report.counts['links']} · con margen en ambos sentidos: {report.counts['both_margins']} · "
           f"incompletos: {report.counts['incomplete']} · incompatibles: {report.counts['incompatible']} · "
           f"dependen de hipótesis: {report.counts['depends_on_hypotheses']}", ""]
    if report.classification is not None:
        out += [f"Clasificación (reserva de diseño {report.classification.design_reserve_db:g} dB, sin calibrar): "
                + " · ".join(f"{CLASS_LABELS[key]} {report.counts.get(key.replace('-', '_'), 0)}" for key in CLASS_KEYS),
                "", f"> {_cell(report.classification.rule)}", ""]
    for link in report.links:
        out += [f"## {_cell(' ↔ '.join(link.devices))} (`{_cell(link.link_id)}`)", "",
                *[f"- {_cell(r)}" for r in link.radios],
                f"- Compatibilidad de radio: {link.compatibility}; estado del cálculo: {link.status}",
                *([f"- **Clasificación: {CLASS_LABELS[link.coverage_class]}**"] if link.coverage_class else []), "",
                "| Sentido | Potencia (dBm) | Margen (dB) | Sensibilidad | Paredes atravesadas |",
                "|---|---:|---:|---|---|"]
        for label, direction in (("Ida", link.forward), ("Vuelta", link.reverse)):
            if direction is None:
                out.append(f"| {label} | — | — | — | sin calcular (faltan datos) |")
                continue
            walls = ", ".join(f"{w.wall_id} ({w.material}{', puerta ' + DOOR_LABELS[w.door] if w.door else ''})"
                              for w in direction.walls) or "ninguna"
            out.append(f"| {label} | {_cell(direction.received_power_dbm)} | {_cell(direction.margin_db)} | "
                       f"{_cell(direction.sensitivity_provenance)} | {_cell(walls)} |")
        out.append("")
        if link.limiting_direction:
            out.append(f"Sentido limitante: {'ida' if link.limiting_direction == 'forward' else 'vuelta'} "
                       f"({_cell(link.limiting_margin_db)} dB). Un margen positivo no garantiza el funcionamiento.")
        if link.forward_range_dbm:
            out.append(f"Rango de escenarios, ida: {_cell(link.forward_range_dbm[0])} a "
                       f"{_cell(link.forward_range_dbm[1])} dBm; signo del margen: {SIGN_LABELS[link.margin_sign]}.")
        if link.hypotheses:
            out.append(f"Hipótesis que le afectan: {_cell(', '.join(link.hypotheses))}.")
        out += [f"- {_cell(note)}" for note in link.notes] + [""]
    if report.access_points:
        out += ["## Conexión de datos de los AP", "",
                "| Equipo | Conexión | Enlaces de datos (margen limitante, dB) | Llega a |", "|---|---|---|---|"]
        for path in report.access_points:
            hops = ", ".join(f"{hop.link_id} ({_cell(hop.limiting_margin_db)})" for hop in path.hops) or "—"
            out.append(f"| {_cell(path.device_id)} | {CONNECTION_LABELS[path.kind]} | {_cell(hops)} | "
                       f"{CONNECTION_LABELS[path.ends_at]} ({_cell(path.end_device_id)}) |")
        out.append("")
        out += [f"- {_cell(reason)}" for path in report.access_points for reason in path.reasons] + [""]
    if report.maps:
        out += ["## Mapas de cobertura", "",
                "Recuentos de celdas por clase, no un porcentaje de cobertura de la vivienda: dependen del área "
                "dibujada. La interfaz dibuja cada mapa a partir de su resultado completo.", ""]
        for item in report.maps:
            summary, parameters = item.summary, item.result.parameters
            grid = parameters.grid
            spread = ("—" if summary.limiting_margin_db is None
                      else " / ".join(_cell(value) for value in summary.limiting_margin_db))
            out += [f"### {_cell(item.title)}", "",
                    f"- AP `{_cell(parameters.access_point_device_id)}` · rejilla {grid.width_m:g} × {grid.depth_m:g} m "
                    f"cada {grid.resolution_m:g} m · huella `{item.result.request_hash[:12]}`",
                    f"- Celdas: {summary.cells} · calculadas {summary.computed_cells} · parciales "
                    f"{summary.partial_cells} · sin calcular {summary.not_computed_cells}",
                    f"- Margen limitante mínimo / mediana / máximo: {spread} dB · celdas con margen negativo: "
                    f"{summary.negative_limiting_cells}"]
            if summary.class_counts:
                out.append("- Celdas por clase: " + " · ".join(
                    f"{CLASS_LABELS[key]} {summary.class_counts.get(key, 0)}" for key in CLASS_KEYS))
            if item.result.points:
                out += ["", "| Punto (m) | Ida (dBm) | Vuelta (dBm) | Margen ida (dB) | Margen vuelta (dB) | Estado | Clase |",
                        "|---|---:|---:|---:|---:|---|---|"]
                for point, sample in zip(parameters.points, item.result.points):
                    out.append(f"| ({point.x:g}, {point.y:g}, {point.z:g}) | {_cell(sample.forward_dbm)} | "
                               f"{_cell(sample.reverse_dbm)} | {_cell(sample.forward_margin_db)} | "
                               f"{_cell(sample.reverse_margin_db)} | {_cell(sample.status)} | "
                               f"{CLASS_LABELS.get(sample.coverage_class or '', '—')} |")
            out += ["", *[f"- {_cell(reason)}" for reason in item.result.reasons], ""]
    if report.evidence_levels:
        out += ["## Nivel de evidencia", "", "| Nivel | Estado | Qué significa |", "|---|---|---|"]
        out += [f"| {EVIDENCE_LABELS[e.level]} | {'comprobado' if e.status == 'checked' else 'ninguno'} | "
                f"{_cell(e.detail)} |" for e in report.evidence_levels] + [""]
    if report.classification is not None:
        out += ["## Criterio de fallo y reserva de diseño", "",
                f"- Criterio de fallo real: {_cell(report.classification.failure_criterion)}",
                f"- Reserva de diseño: {report.classification.design_reserve_db:g} dB, "
                f"{'calibrada con medidas' if report.classification.calibrated else 'provisional, sin calibrar'}.", ""]
    out += ["## Decisiones pendientes", "", *[f"- {d}" for d in report.pending_decisions], "",
            "## No evaluado", "", *[f"- {n}" for n in report.not_evaluated], "",
            "## Limitaciones del motor", "", *[f"- {_cell(item)}" for item in report.limitations], ""]
    return "\n".join(out)
