"""Coverage maps under a scenario (B-114): the same hypotheses as B-108, applied to every cell."""

import time

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from smart_environment.api import app
from smart_environment.coverage import compute
from smart_environment.models import CoverageMapRequest
from smart_environment.scenarios import automatic_scenarios
from test_scenarios import project as scenario_project

client = TestClient(app)


def map_request(scenario=None, **changes):
    project = scenario_project()
    ap = project.devices[0]
    data = {"project": project.model_dump(mode="json"), "access_point_device_id": ap.id,
            "access_point_radio_id": ap.radios[0].id,
            "profile": {"id": "p", "name": "Perfil", "radio": ap.radios[0].model_dump(mode="json")},
            "grid": {"origin_x_m": 0, "origin_y_m": -1, "width_m": 12, "depth_m": 2, "resolution_m": 1,
                     "height_m": 1}, "scenario": scenario}
    data.update(changes)
    return data


def test_worst_nominal_best_order_behind_the_uncertain_walls():
    nominal, best, worst = (compute(CoverageMapRequest.model_validate(map_request(s.model_dump() if s else None)))
                            for s in [None, *automatic_scenarios(scenario_project())[1:]])
    behind = [i for i in range(nominal.columns * nominal.rows)
              if nominal.cells.status[i] != "not-computed" and (i % nominal.columns) >= 8]
    assert behind
    for i in behind:
        assert worst.cells.forward_dbm[i] <= nominal.cells.forward_dbm[i] <= best.cells.forward_dbm[i]
    assert worst.cells.forward_dbm[behind[0]] < best.cells.forward_dbm[behind[0]]
    assert "bajo el escenario" in worst.scope and "Hipótesis desfavorables" in worst.scope
    assert any("no una medida" in r for r in worst.reasons)
    assert worst.request_hash != nominal.request_hash


def test_map_without_scenario_is_unchanged():
    data = map_request()
    del data["scenario"]
    first, second = (compute(CoverageMapRequest.model_validate(d)) for d in (data, map_request()))
    assert first.cells == second.cells and first.scope == second.scope


@pytest.mark.parametrize("scenario", [
    {"id": "x", "name": "x", "doors": {"wall-partition": "open"}},
    {"id": "x", "name": "x", "materials": {"wood": "high"}},
])
def test_invalid_scenarios_are_rejected(scenario):
    with pytest.raises(ValidationError):
        CoverageMapRequest.model_validate(map_request(scenario))


def test_worst_case_map_through_the_api():
    project = scenario_project().model_dump(mode="json")
    worst = next(s for s in client.post("/api/scenario-simulations", json={"project": project}).json()["scenarios"]
                 if s["id"] == "worst")
    job = client.post("/api/coverage-maps", json=map_request(worst)).json()
    deadline = time.monotonic() + 30
    while job["state"] not in ("done", "failed", "cancelled") and time.monotonic() < deadline:
        time.sleep(0.02)
        job = client.get(f"/api/coverage-maps/{job['job_id']}").json()
    assert job["state"] == "done" and job["result"]["parameters"]["scenario"]["id"] == "worst"
