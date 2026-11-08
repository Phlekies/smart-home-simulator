"""Installation report (B-115): faithful to the computed results, explicit gaps, no verdict."""

import pytest
from fastapi.testclient import TestClient

from smart_environment.api import app, example
from smart_environment.engines import input_hash, simulate
from smart_environment.models import RadioValueSource, ScenarioRequest
from smart_environment.report import PENDING_DECISIONS, InstallationReport, ReportRequest, build_report, to_markdown
from smart_environment.scenarios import evaluate
from test_scenarios import project as scenario_project

client = TestClient(app)


def test_values_match_simulation_and_scenarios():
    project = scenario_project(sensitivity=-77)
    report = build_report(ReportRequest(project=project))
    link, simulated = report.links[0], simulate(project).links[0]
    scenario = evaluate(ScenarioRequest(project=project)).links[0]
    assert link.forward.received_power_dbm == pytest.approx(simulated.forward.received_power_dbm)
    assert link.reverse.margin_db == pytest.approx(simulated.reverse.margin_db)
    assert link.forward_range_dbm == scenario.forward_range_dbm and link.margin_sign == scenario.margin_sign
    assert link.hypotheses == ["wall-partition", "door-1"]
    assert [w.door for w in link.forward.walls] == [None, "unknown"]
    assert report.input_hash == input_hash(project) and report.pending_decisions == PENDING_DECISIONS


def test_limiting_direction_is_the_smaller_margin():
    link = build_report(ReportRequest(project=scenario_project(sensitivity=-77))).links[0]
    smaller = min((link.forward.margin_db, "forward"), (link.reverse.margin_db, "reverse"))
    assert (link.limiting_margin_db, link.limiting_direction) == smaller


def test_missing_data_is_reported_not_filled():
    project = example("apartment")  # Java import: hub power and sensor sensitivities unknown
    report = build_report(ReportRequest(project=project))
    assert report.counts["both_margins"] == 0 and report.counts["incomplete"] == len(project.links)
    assert all(link.limiting_direction is None for link in report.links)
    assert any("Falta potencia" in note for link in report.links for note in link.notes)


def test_sensitivity_provenance_comes_from_the_link_radio():
    project = scenario_project(sensitivity=-77)
    target = next(d for d in project.devices if d.id == project.links[0].target_device_id)  # forward receiver
    target.radios[0].provenance = {"sensitivity_dbm": RadioValueSource(provenance="standard-minimum")}
    link = build_report(ReportRequest(project=project)).links[0]
    assert link.forward.to_device_id == target.id and link.forward.sensitivity_provenance == "standard-minimum"
    assert link.reverse.to_device_id != target.id and link.reverse.sensitivity_provenance == "sin etiqueta"


def test_markdown_escapes_names_and_never_issues_a_verdict():
    project = scenario_project(sensitivity=-77)
    project.devices[1].name = "Sensor | baño"
    text = to_markdown(build_report(ReportRequest(project=project, title="Mi casa")))
    assert text.startswith("# Mi casa") and "Sensor \\| baño" in text
    assert "| Ida |" in text and "| Vuelta |" in text and "Decisiones pendientes" in text
    assert "no garantiza el funcionamiento" in text
    for verdict in ("cobertura favorable", "cobertura insuficiente", "compra recomendada"):
        assert verdict not in text.lower()
    assert "classification" not in InstallationReport.model_json_schema()["properties"]


def test_api_endpoints():
    body = {"project": scenario_project(sensitivity=-77).model_dump(mode="json"), "title": "Prueba"}
    data = client.post("/api/reports", json=body)
    assert data.status_code == 200 and data.json()["title"] == "Prueba"
    markdown = client.post("/api/reports/markdown", json=body)
    assert markdown.status_code == 200 and markdown.headers["content-type"].startswith("text/markdown")
    assert markdown.text.startswith("# Prueba")
    assert client.post("/api/reports", json={**body, "scenarios": [{"id": "best", "name": "x"}]}).status_code == 422
