"""Coverage maps (B-103): same budget as links, explicit gaps, bounded and cancellable jobs."""

import time

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from smart_environment.api import app, example
from smart_environment.coverage import (
    MAX_WORK, Cancelled, CoverageJobs, CoverageLimitError, compute, inside_wall, preflight, request_hash,
)
from smart_environment.engines import input_hash, simulate
from smart_environment.models import CoverageMapRequest, Device, Link, Point, Radio, Wall

client = TestClient(app)


def wifi(**changes):
    return {"id": "r", "protocol": "wifi", "channel": 1, "frequency_hz": 2.412e9, "bandwidth_hz": 20e6,
            "tx_power_dbm": 20, "sensitivity_dbm": -90, **changes}


def request_data(project=None, **changes):
    project = project or example("apartment")
    ap = project.devices[-1]
    ap.radios[0] = Radio(**wifi(id=ap.radios[0].id))
    data = {"project": project.model_dump(mode="json"), "access_point_device_id": ap.id,
            "access_point_radio_id": ap.radios[0].id,
            "profile": {"id": "sensor", "name": "Sensor genérico", "radio": wifi(id="p", tx_power_dbm=5,
                                                                                 sensitivity_dbm=-85)},
            "grid": {"width_m": 10, "depth_m": 6, "resolution_m": 1, "height_m": 1.2},
            "points": [{"x": 7.125, "y": 3.3, "z": 0.4}]}
    data.update(changes)
    return data


def link_through_simulate(data, point):
    """Same scenario expressed as an ordinary link, to compare against the map evaluation."""
    request = CoverageMapRequest.model_validate(data)
    project = request.project.model_copy(deep=True)
    project.devices.append(Device(id="probe", name="probe", role="endpoint", position=point,
                                  radios=[request.profile.radio]))
    project.links = [Link(id="probe", source_device_id=request.access_point_device_id,
                          source_radio_id=request.access_point_radio_id, target_device_id="probe",
                          target_radio_id=request.profile.radio.id)]
    return simulate(project).links[0]


def test_exact_points_and_cells_match_the_link_budget():
    data = request_data()
    result = compute(CoverageMapRequest.model_validate(data))
    link = link_through_simulate(data, Point(x=7.125, y=3.3, z=0.4))
    sample = result.points[0]
    assert sample.forward_dbm == pytest.approx(link.forward.received_power_dbm)
    assert sample.reverse_dbm == pytest.approx(link.reverse.received_power_dbm)
    assert sample.forward_margin_db == pytest.approx(link.forward.margin_db)
    assert sample.reverse_margin_db == pytest.approx(link.reverse.margin_db)
    # Cell (i=3, j=2) is evaluated at its centre (3.5, 2.5) and stored row-major.
    index = 2 * result.columns + 3
    cell = link_through_simulate(data, Point(x=3.5, y=2.5, z=1.2))
    if result.cells.status[index] != "not-computed":
        assert result.cells.forward_dbm[index] == pytest.approx(cell.forward.received_power_dbm, abs=5e-4)
        assert result.cells.reverse_dbm[index] == pytest.approx(cell.reverse.received_power_dbm, abs=5e-4)
    assert (result.columns, result.rows) == (10, 6) and len(result.cells.status) == 60


def test_weak_return_path_is_visible_even_with_good_downlink():
    data = request_data(points=[{"x": 9, "y": 4, "z": 1.2}])
    data["profile"]["radio"]["tx_power_dbm"] = -60
    sample = compute(CoverageMapRequest.model_validate(data)).points[0]
    assert sample.forward_margin_db > 0 > sample.reverse_margin_db


def test_missing_profile_data_gives_partial_cells_and_reasons():
    data = request_data()
    data["profile"]["radio"]["sensitivity_dbm"] = None
    data["profile"]["radio"]["tx_power_dbm"] = None
    result = compute(CoverageMapRequest.model_validate(data))
    computed = [s for s in result.cells.status if s != "not-computed"]
    assert computed and set(computed) == {"partial"}
    assert all(v is None for v in result.cells.reverse_dbm) and all(v is None for v in result.cells.forward_margin_db)
    assert any("potencia de transmisión del perfil" in r for r in result.reasons)
    assert result.computed_cells == 0


def test_cells_inside_walls_or_at_the_access_point_are_not_computed():
    wall = Wall(id="w", start=Point(x=0, y=0), end=Point(x=4, y=0), thickness_m=0.2, height_m=2.6, material_id="m")
    assert inside_wall(Point(x=2, y=0.05, z=1), wall) and not inside_wall(Point(x=2, y=0.15, z=1), wall)
    assert not inside_wall(Point(x=2, y=0, z=3), wall)
    data = request_data()
    ap = next(d for d in data["project"]["devices"] if d["id"] == data["access_point_device_id"])
    data["points"] = [ap["position"]]
    sample = compute(CoverageMapRequest.model_validate(data)).points[0]
    assert sample.status == "not-computed" and sample.reason == "too-close-to-access-point"


def test_result_identifies_scenario_profile_height_and_metric():
    data = request_data()
    request = CoverageMapRequest.model_validate(data)
    result = compute(request)
    assert result.input_hash == input_hash(request.project) == simulate(request.project).input_hash
    assert result.request_hash == request_hash(request)
    assert result.parameters.profile.name == "Sensor genérico" and result.parameters.grid.height_m == 1.2
    assert result.metric == "direct-path-received-power" and result.frequency_hz == 2.412e9
    assert "classification" not in result.model_dump_json()
    other = CoverageMapRequest.model_validate({**data, "grid": {**data["grid"], "height_m": 2.0}})
    assert request_hash(other) != result.request_hash


@pytest.mark.parametrize("change", [
    lambda d: d.update(access_point_device_id="missing"),
    lambda d: d.update(access_point_radio_id="missing"),
    lambda d: d["grid"].update(resolution_m=0.1, width_m=100, depth_m=100),
    lambda d: d["grid"].update(resolution_m=0.05),
    lambda d: d.update(points=[{"x": 0, "y": 0}] * 257),
])
def test_invalid_requests_are_rejected(change):
    data = request_data()
    change(data)
    with pytest.raises(ValidationError):
        CoverageMapRequest.model_validate(data)


@pytest.mark.parametrize("radio_change", [{"protocol": "thread"}, {"channel": 6}, {"frequency_hz": 868e6},
                                          {"bandwidth_hz": 40e6}])
def test_incompatible_or_unsupported_profile_is_rejected_before_queueing(radio_change):
    data = request_data()
    data["profile"]["radio"].update(radio_change)
    with pytest.raises(CoverageLimitError):
        preflight(CoverageMapRequest.model_validate(data))


def test_work_limit_is_explicit():
    project = example("apartment")
    project.building.walls += [Wall(id=f"extra-{k}", start=Point(x=50 + k, y=0), end=Point(x=50 + k, y=5),
                                    material_id="drywall") for k in range(60)]
    data = request_data(project)
    data["grid"] = {"width_m": 199, "depth_m": 199, "resolution_m": 1, "height_m": 1.2}
    request = CoverageMapRequest.model_validate(data)
    assert request.grid.columns * request.grid.rows * len(request.project.building.walls) > MAX_WORK
    with pytest.raises(CoverageLimitError):
        preflight(request)


def test_compute_stops_when_cancelled():
    seen = []
    with pytest.raises(Cancelled):
        compute(CoverageMapRequest.model_validate(request_data()), seen.append, lambda: len(seen) >= 2)
    assert seen == sorted(seen) and len(seen) == 2


def wait(job_id, states=("done", "cancelled", "failed"), timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = client.get(f"/api/coverage-maps/{job_id}").json()
        if job["state"] in states:
            return job
        time.sleep(0.02)
    raise AssertionError(f"job {job_id} did not reach {states}")


def test_api_job_lifecycle():
    response = client.post("/api/coverage-maps", json=request_data())
    assert response.status_code == 202 and response.json()["state"] in ("queued", "running", "done")
    job = wait(response.json()["job_id"])
    assert job["state"] == "done" and job["progress"] == 1 and job["result"]["columns"] == 10
    assert job["request_hash"] == job["result"]["request_hash"]
    assert client.get("/api/coverage-maps/missing").status_code == 404
    assert client.delete("/api/coverage-maps/missing").status_code == 404


def test_api_rejections_are_explicit():
    assert client.post("/api/coverage-maps", json=request_data(engine="sionna-rt")).status_code == 501
    data = request_data()
    data["profile"]["radio"]["channel"] = 11
    assert client.post("/api/coverage-maps", json=data).status_code == 422
    assert client.post("/api/coverage-maps", json=request_data(access_point_device_id="x")).status_code == 422


def test_queued_job_is_cancelled_while_another_runs():
    jobs = CoverageJobs(max_jobs=4)
    long = request_data(example("warehouse"))
    long["grid"] = {"width_m": 190, "depth_m": 190, "resolution_m": 1, "height_m": 1.2}
    try:
        first = jobs.submit(CoverageMapRequest.model_validate(long))
        second = jobs.submit(CoverageMapRequest.model_validate(request_data()))
        assert jobs.cancel(second.job_id).state == "cancelled"
        jobs.cancel(first.job_id)
        deadline = time.monotonic() + 30
        while jobs.get(first.job_id).state not in ("cancelled", "done") and time.monotonic() < deadline:
            time.sleep(0.02)
        assert jobs.get(first.job_id).state in ("cancelled", "done")
        assert jobs.get(second.job_id).result is None
    finally:
        jobs.shutdown()


def test_history_is_bounded():
    jobs = CoverageJobs(max_jobs=2)
    try:
        ids = [jobs.submit(CoverageMapRequest.model_validate(request_data())).job_id for _ in range(2)]
        for job_id in ids:
            deadline = time.monotonic() + 30
            while jobs.get(job_id).state != "done" and time.monotonic() < deadline:
                time.sleep(0.02)
        third = jobs.submit(CoverageMapRequest.model_validate(request_data()))
        assert jobs.get(ids[0]) is None and jobs.get(third.job_id) is not None
    finally:
        jobs.shutdown()
