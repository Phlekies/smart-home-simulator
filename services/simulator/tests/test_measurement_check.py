"""Measurement campaign check through the API (B-116). Sample values are validator fixtures."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from smart_environment.api import app, example
from smart_environment.calibration import MeasurementCheckRequest, check
from test_calibration import campaign, predictions, project

TEMPLATE = Path(__file__).resolve().parents[1] / "examples" / "measurement-campaign.template.json"
client = TestClient(app)


def test_campaign_with_its_project_gets_summary_and_residuals():
    truth = predictions()
    result = check(MeasurementCheckRequest(campaign=campaign("home-a", "pilot", [t - 4 for t in truth]),
                                           project=project()))
    assert result.points == {"planned": 0, "measured": 6, "excluded": 0}
    assert len(result.summary) == 6 and result.summary[0].rssi["ap-to-device"].samples == 3
    assert result.project_issues == [] and len(result.residuals) == 6
    assert all(abs(r.residual_db + 4) < 1e-9 for r in result.residuals)


def test_without_project_only_describes_the_campaign():
    result = check(MeasurementCheckRequest(campaign=campaign("home-a", "pilot", predictions())))
    assert result.project_issues is None and result.residuals is None
    assert any("Sin proyecto" in note for note in result.notes)


def test_synthetic_template_or_wrong_project_give_no_residuals():
    template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    result = check(MeasurementCheckRequest.model_validate({"campaign": template,
                                                           "project": example("apartment").model_dump(mode="json")}))
    assert result.synthetic and result.points["planned"] == len(template["points"]) and result.summary == []
    assert result.residuals is None and any("sintética" in note for note in result.notes)
    mismatch = check(MeasurementCheckRequest(campaign=campaign("home-a", "pilot", predictions()),
                                             project=project(door="open")))
    assert mismatch.project_issues and mismatch.residuals is None


def test_api_endpoint_and_validation():
    body = {"campaign": json.loads(campaign("home-a", "pilot", predictions()).model_dump_json()),
            "project": json.loads(project().model_dump_json())}
    response = client.post("/api/measurements/check", json=body)
    assert response.status_code == 200 and len(response.json()["residuals"]) == 6
    body["campaign"]["points"][0]["rssi"][0]["samples_dbm"] = [12]
    assert client.post("/api/measurements/check", json=body).status_code == 422


# --- Stand-in instruments (B-124) ----------------------------------------------------------

def test_phone_readings_are_explained_against_the_candidate():
    result = check(MeasurementCheckRequest(campaign=campaign("home-a", "pilot", predictions()), project=project()))
    notes = [note for note in result.notes if "es un móvil" in note]
    assert len(notes) == 1 and "no para concluir que el candidato funcionará" in notes[0]
    assert all(r.device_instrument_kind == "phone" for r in result.residuals)
    alone = check(MeasurementCheckRequest(campaign=campaign("home-a", "pilot", predictions())))
    assert any("es un móvil" in note for note in alone.notes), "explained even without a project"


def test_the_candidate_itself_needs_no_stand_in_note():
    data = campaign("home-a", "pilot", predictions()).model_dump(mode="json")
    for instrument in data["instruments"]:
        if instrument["kind"] == "phone":
            instrument["kind"] = "candidate-device"
    result = check(MeasurementCheckRequest.model_validate({"campaign": data, "project": project().model_dump()}))
    assert not any("es un" in note and "candidato" in note for note in result.notes)
    assert all(not any("medido con" in a for a in r.assumptions) for r in result.residuals)
