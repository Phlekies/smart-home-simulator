"""Installation report per link (B-115, P5): what was computed, what it rests on, what is missing.

It only gathers results the API already produces (link budget in both directions and the
scenarios of unresolved doors/materials) and states the decisions that are still open. It never
issues a coverage verdict: the failure criterion and design reserve are not defined yet.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .engines import LIMITATIONS, input_hash, simulate
from .models import DirectionResult, Model, Project, Radio, ScenarioAssumptions, ScenarioRequest
from .scenarios import evaluate as evaluate_scenarios

PENDING_DECISIONS = [
    "Umbral del criterio activo de fallo del enlace (proporción de paquetes entregados): sin decidir.",
    "Reserva de diseño para clasificar la cobertura (favorable, marginal, insuficiente): sin decidir.",
    "Validación experimental en viviendas: sin medidas todavía; las cifras son del estimador.",
]
NOT_EVALUATED = [
    "Tráfico, velocidad útil, latencia y estabilidad del enlace.",
    "Interferencias de otras redes y equipos.",
    "Compatibilidad funcional con aplicaciones, asistentes o automatizaciones.",
    "Reflexiones, difracción y desvanecimiento: el estimador usa el trayecto directo.",
]


class ReportRequest(Model):
    project: Project
    scenarios: list[ScenarioAssumptions] = Field(default_factory=list, max_length=16)
    title: str | None = Field(default=None, max_length=160)

    @model_validator(mode="after")
    def valid_scenarios(self) -> ReportRequest:
        ScenarioRequest(project=self.project, scenarios=self.scenarios)  # same rules, rejected as 422
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


class InstallationReport(Model):
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
            notes=list(dict.fromkeys(result.reasons + scenario.reasons))))
    counts = {"links": len(links),
              "both_margins": sum(link.limiting_margin_db is not None for link in links),
              "incomplete": sum(link.limiting_margin_db is None and link.compatibility != "incompatible"
                                for link in links),
              "incompatible": sum(link.compatibility == "incompatible" for link in links),
              "depends_on_hypotheses": sum(link.margin_sign == "depends-on-hypotheses" for link in links)}
    return InstallationReport(
        title=request.title or f"Informe de instalación · {project.name}", project_name=project.name,
        input_hash=input_hash(project), engine=simulation.engine, engine_version=simulation.engine_version,
        scope=simulation.scope + ". El informe no clasifica la cobertura ni recomienda compras.",
        links=links, counts=counts, pending_decisions=PENDING_DECISIONS, not_evaluated=NOT_EVALUATED,
        limitations=LIMITATIONS)


DOOR_LABELS = {"open": "abierta", "closed": "cerrada", "unknown": "estado desconocido"}
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
    for link in report.links:
        out += [f"## {_cell(' ↔ '.join(link.devices))} (`{_cell(link.link_id)}`)", "",
                *[f"- {_cell(r)}" for r in link.radios],
                f"- Compatibilidad de radio: {link.compatibility}; estado del cálculo: {link.status}", "",
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
    out += ["## Decisiones pendientes", "", *[f"- {d}" for d in report.pending_decisions], "",
            "## No evaluado", "", *[f"- {n}" for n in report.not_evaluated], "",
            "## Limitaciones del motor", "", *[f"- {_cell(item)}" for item in report.limitations], ""]
    return "\n".join(out)
