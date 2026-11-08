"""Saved maps and reports stay local files; the fingerprint tells whether they still describe the project (B-132)."""

from fastapi.testclient import TestClient

from smart_environment.api import app, example
from smart_environment.coverage import compute
from smart_environment.engines import ENGINE_VERSION, simulate
from smart_environment.models import CoverageMapRequest, Fixture, Point, Radio, ReceiverProfile
from smart_environment.report import ReportRequest, build_report

client = TestClient(app)


def fingerprint(project):
    response = client.post("/api/projects/fingerprint", json=project.model_dump(mode="json"))
    assert response.status_code == 200
    return response.json()


def saved_map(project):
    hub = next(d for d in project.devices if d.role == "controller")
    profile = ReceiverProfile(id="p", name="p", radio=Radio(id="p", frequency_hz=hub.radios[0].frequency_hz,
                                                            bandwidth_hz=hub.radios[0].bandwidth_hz, tx_power_dbm=10))
    request = CoverageMapRequest(project=project, access_point_device_id=hub.id, access_point_radio_id=hub.radios[0].id,
                                 profile=profile, grid={"width_m": 6, "depth_m": 4, "resolution_m": 1, "height_m": 1.2})
    return compute(request).model_dump(mode="json")  # what a person would keep as a local file


def current(saved, print_):
    return saved["input_hash"] == print_["input_hash"] and saved["engine_version"] == print_["engine_version"]


def test_fingerprint_matches_every_result_of_the_same_project():
    project = example("apartment")
    print_ = fingerprint(project)
    simulation = simulate(project)
    assert print_ == {"input_hash": simulation.input_hash, "engine": "quick-estimate",
                      "engine_version": simulation.engine_version}
    assert print_["engine_version"] == ENGINE_VERSION == "0.2.0"
    assert current(saved_map(project), print_)
    report = build_report(ReportRequest(project=project))
    assert (report.input_hash, report.engine_version) == (print_["input_hash"], print_["engine_version"])


def test_editing_the_plan_makes_a_saved_map_stale():
    project = example("apartment")
    saved = saved_map(project)
    project.building.walls[0].thickness_m = 0.3
    assert not current(saved, fingerprint(project))


def test_display_aids_and_outlets_do_not_make_results_stale():
    project = example("apartment")
    saved = saved_map(project)
    project.building.power_outlets = [Fixture(id="o", label="Enchufe", position=Point(x=1, y=1, z=0.3))]
    assert current(saved, fingerprint(project))


def test_results_from_another_engine_version_are_stale():
    project = example("apartment")
    saved = {**saved_map(project), "engine_version": "0.1.0"}
    assert not current(saved, fingerprint(project))


def test_invalid_projects_are_rejected():
    assert client.post("/api/projects/fingerprint", json={"building": {}}).status_code == 422
