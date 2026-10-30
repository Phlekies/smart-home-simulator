"""End-to-end API flows (B-111): import → edit → compute everything → export → reimport.

Radio values set here are declared test inputs so that every endpoint has data; they are not
product data or measurements.
"""

import copy
import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from smart_environment.api import app

ROOT = Path(__file__).resolve().parents[3]
EXAMPLES = {"apartment": "smart-apartment", "office": "office-floor", "warehouse": "warehouse"}
client = TestClient(app)


def ok(response, status=200):
    assert response.status_code == status, response.text
    return response.json()


def wait_map(job_id, timeout=60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = ok(client.get(f"/api/coverage-maps/{job_id}"))
        if job["state"] in ("done", "failed", "cancelled"):
            return job
        time.sleep(0.02)
    raise AssertionError("map did not finish")


def declare_wifi(project):
    """Declared test values: Wi-Fi channel 1 everywhere, AP power and every sensitivity."""
    hub = next(d for d in project["devices"] if d["role"] == "controller")
    for device in project["devices"]:
        for radio in device["radios"]:
            radio.update(protocol="wifi", channel=1)
            radio["sensitivity_dbm"] = radio["sensitivity_dbm"] if radio["sensitivity_dbm"] is not None else -85
    hub["radios"][0]["tx_power_dbm"] = 20
    return hub


@pytest.mark.parametrize("example_id", list(EXAMPLES))
def test_full_flow_on_each_java_example(example_id):
    original = json.loads((ROOT / "examples" / f"{EXAMPLES[example_id]}.shsim.json").read_text(encoding="utf-8"))

    # Import: the Java original travels untouched and the counts match.
    project = ok(client.post("/api/projects/import", json=original))
    assert project["legacy_source"] == original
    assert len(project["building"]["walls"]) == len(original["walls"])
    assert len(project["devices"]) == len(original["sensors"]) + 1

    # Edit: fractional coordinate, declared radios, an unknown door and an uncertain material.
    hub = declare_wifi(project)
    endpoint = next(d for d in project["devices"] if d["role"] == "endpoint")
    endpoint["position"]["x"] += 0.125
    project["building"]["walls"][0]["door"] = "unknown"
    material = project["building"]["materials"][0]
    material["uncertainty"] = {"loss_db_24ghz_low": material["loss_db_24ghz"] / 2,
                               "loss_db_24ghz_high": material["loss_db_24ghz"] * 2,
                               "loss_db_5ghz_low": material["loss_db_5ghz"] / 2,
                               "loss_db_5ghz_high": material["loss_db_5ghz"] * 2,
                               "source": "E2E test range"}
    project = ok(client.post("/api/projects/import", json=project))

    simulation = ok(client.post("/api/simulations", json={"project": project}))
    assert len(simulation["links"]) == len(project["links"])
    assert all(link["forward"] is not None for link in simulation["links"] if link["status"] != "incompatible")
    project_hash = simulation["input_hash"]

    # Coverage map with a catalogue profile placed on the AP channel, plus the exact edited point.
    catalogue = ok(client.get("/api/profiles"))
    profile = next(p for p in catalogue if p["id"] == "wifi4-ht20-mcs0")
    ap_radio = hub["radios"][0]
    profile_radio = {"id": "profile", "protocol": "wifi", "frequency_hz": ap_radio["frequency_hz"],
                     "bandwidth_hz": profile["bandwidth_hz"], "channel": ap_radio["channel"],
                     "tx_power_dbm": None, "sensitivity_dbm": profile["sensitivity_dbm"]["value"]}
    map_body = {"project": project, "access_point_device_id": hub["id"], "access_point_radio_id": ap_radio["id"],
                "profile": {"id": profile["id"], "name": profile["name"], "radio": profile_radio},
                "grid": {"width_m": project["building"]["width_m"], "depth_m": project["building"]["depth_m"],
                         "resolution_m": 1, "height_m": 1.2},
                "points": [endpoint["position"]]}
    job = wait_map(ok(client.post("/api/coverage-maps", json=map_body), 202)["job_id"])
    assert job["state"] == "done"
    result = job["result"]
    assert result["input_hash"] == project_hash and result["computed_cells"] == 0  # return path unknown
    assert result["partial_cells"] > 0 and result["points"][0]["forward_dbm"] is not None
    assert result["points"][0]["reverse_dbm"] is None

    # Placement among allowed places and scenarios over the unresolved hypotheses.
    placement = ok(client.post("/api/placement-searches", json={
        "project": project, "access_point_device_id": hub["id"], "access_point_radio_id": ap_radio["id"],
        "zones": [{"id": "z", "label": "Zona permitida", "min_x_m": 2, "min_y_m": 2, "max_x_m": 8, "max_y_m": 8,
                   "height_m": 1.3, "step_m": 2}]}))
    assert placement["input_hash"] == project_hash and placement["evaluated"] > 0
    scenarios = ok(client.post("/api/scenario-simulations", json={"project": project}))
    assert scenarios["input_hash"] == project_hash
    assert [s["id"] for s in scenarios["scenarios"]] == ["nominal", "best", "worst"]
    for link in scenarios["links"]:
        if link["forward_range_dbm"]:
            low, high = link["forward_range_dbm"]
            assert low <= high

    # Export and reimport: nothing lost, same hash; an edit gives a different hash.
    exported = json.loads(json.dumps(project))
    again = ok(client.post("/api/projects/import", json=exported))
    assert again == project
    assert ok(client.post("/api/simulations", json={"project": again}))["input_hash"] == project_hash
    edited = copy.deepcopy(again)
    edited["devices"][0]["position"]["y"] += 0.5
    assert ok(client.post("/api/simulations", json={"project": edited}))["input_hash"] != project_hash


def test_create_a_home_from_scratch():
    project = {
        "format": "smart-environment-simulator", "version": 1,
        "name": "Vivienda nueva", "building": {"width_m": 10, "depth_m": 8,
                                               "materials": [{"id": "brick", "name": "Brick", "loss_db_24ghz": 6,
                                                              "loss_db_5ghz": 9}],
                                               "walls": [{"id": "w", "start": {"x": 5, "y": 0}, "end": {"x": 5, "y": 8},
                                                          "material_id": "brick", "door": "closed"}]},
        "devices": [{"id": "router", "name": "Router", "role": "access-point", "position": {"x": 1, "y": 1, "z": 2},
                     "radios": [{"id": "r", "protocol": "wifi", "channel": 6, "frequency_hz": 2.437e9,
                                 "bandwidth_hz": 20e6, "tx_power_dbm": 20, "sensitivity_dbm": -90}]},
                    {"id": "plug", "name": "Enchufe", "role": "endpoint", "position": {"x": 9, "y": 7, "z": 0.3},
                     "radios": [{"id": "r", "protocol": "wifi", "channel": 6, "frequency_hz": 2.437e9,
                                 "bandwidth_hz": 20e6, "tx_power_dbm": 10, "sensitivity_dbm": -82}]}],
        "links": [{"id": "l", "source_device_id": "plug", "source_radio_id": "r", "target_device_id": "router",
                   "target_radio_id": "r"}]}
    imported = ok(client.post("/api/projects/import", json=project))
    link = ok(client.post("/api/simulations", json={"project": imported}))["links"][0]
    assert link["compatibility"] == "radio-compatible" and link["status"] == "above-threshold"
    assert "w" in link["forward"]["crossed_wall_ids"] and "w" in link["reverse"]["crossed_wall_ids"]
    imported["building"]["walls"][0]["door"] = "open"
    opened = ok(client.post("/api/simulations", json={"project": imported}))["links"][0]
    assert opened["forward"]["received_power_dbm"] > link["forward"]["received_power_dbm"]


def test_app_keeps_working_after_a_lifespan_cycle():
    with TestClient(app) as started:
        assert ok(started.get("/api/health"))["status"] == "ok"
    # The lifespan shut its job manager down; a later client must still be able to queue maps.
    project = ok(client.get("/api/examples/apartment"))
    hub = declare_wifi(project)
    radio = hub["radios"][0]
    body = {"project": project, "access_point_device_id": hub["id"], "access_point_radio_id": radio["id"],
            "profile": {"id": "p", "name": "p", "radio": {**radio, "id": "p"}},
            "grid": {"width_m": 4, "depth_m": 4, "resolution_m": 1, "height_m": 1.2}}
    assert wait_map(ok(client.post("/api/coverage-maps", json=body), 202)["job_id"])["state"] == "done"
