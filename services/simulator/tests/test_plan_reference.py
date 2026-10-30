"""Plan reference persistence (B-104): additive, local image, never a solver input."""

import math

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from smart_environment.api import app, example
from smart_environment.engines import input_hash, simulate
from smart_environment.models import PlanReference, Project

client = TestClient(app)
SHA = "ab" * 32


def reference(**changes):
    data = {"file_name": "plano.png", "media_type": "image/png", "sha256": SHA, "width_px": 2000,
            "height_px": 1500, "meters_per_pixel": 0.01, "origin_x_m": -1.5, "origin_y_m": 2,
            "calibration": {"point_a_px": {"x": 100, "y": 100}, "point_b_px": {"x": 700, "y": 900},
                            "distance_m": 10.0}}
    data.update(changes)
    return data


def test_valid_reference_round_trips_inside_a_project():
    project = example("apartment")
    project.plan_reference = PlanReference.model_validate(reference())
    again = Project.model_validate_json(project.model_dump_json())
    assert again == project and again.plan_reference.width_px * again.plan_reference.meters_per_pixel == 20


def test_existing_projects_and_generated_clients_need_no_field():
    assert example("apartment").plan_reference is None
    for mode in ("validation", "serialization"):
        schema = Project.model_json_schema(mode=mode)
        assert "plan_reference" in schema["properties"] and "plan_reference" not in schema.get("required", [])
    data = example("apartment").model_dump(mode="json")
    del data["plan_reference"]
    assert Project.model_validate(data).plan_reference is None


def test_reference_does_not_change_the_scenario_hash_or_results():
    project = example("apartment")
    before, links = input_hash(project), simulate(project).links
    project.plan_reference = PlanReference.model_validate(reference())
    assert input_hash(project) == before
    assert simulate(project).input_hash == before and simulate(project).links == links


@pytest.mark.parametrize("changes", [
    {"sha256": "AB" * 32}, {"sha256": "ab" * 31}, {"media_type": "image/gif"}, {"file_name": ""},
    {"width_px": 0}, {"height_px": 16385}, {"width_px": 16000, "height_px": 1001, "calibration": None},
    {"meters_per_pixel": 0}, {"meters_per_pixel": 1e-7, "calibration": None},
    {"origin_x_m": 9990, "calibration": None},
    {"calibration": {"point_a_px": {"x": 100, "y": 100}, "point_b_px": {"x": 2100, "y": 100}, "distance_m": 20}},
    {"calibration": {"point_a_px": {"x": 100, "y": 100}, "point_b_px": {"x": 101, "y": 100}, "distance_m": 0.01}},
    {"calibration": {"point_a_px": {"x": 100, "y": 100}, "point_b_px": {"x": 700, "y": 900}, "distance_m": 11}},
    {"opacity": 0.5},
])
def test_invalid_references_are_rejected(changes):
    with pytest.raises(ValidationError):
        PlanReference.model_validate(reference(**changes))


def test_scale_without_calibration_is_allowed():
    assert PlanReference.model_validate(reference(calibration=None, meters_per_pixel=0.02)).calibration is None


def test_calibration_matches_the_editor_formula():
    # A's editor computes meters_per_pixel = distance / hypot(b - a) with exact image coordinates.
    a, b, distance = (12.5, 40.25), (812.75, 640.5), 7.3
    mpp = distance / math.hypot(b[0] - a[0], b[1] - a[1])
    PlanReference.model_validate(reference(meters_per_pixel=mpp, calibration={
        "point_a_px": {"x": a[0], "y": a[1]}, "point_b_px": {"x": b[0], "y": b[1]}, "distance_m": distance}))


def test_api_import_keeps_the_reference_without_image_bytes():
    project = example("apartment").model_dump(mode="json")
    project["plan_reference"] = reference()
    response = client.post("/api/projects/import", json=project)
    assert response.status_code == 200 and response.json()["plan_reference"]["sha256"] == SHA
    project["plan_reference"]["data"] = "iVBORw0KGgo="
    assert client.post("/api/projects/import", json=project).status_code == 422
