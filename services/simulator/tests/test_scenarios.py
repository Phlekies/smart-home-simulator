"""Scenarios of unresolved doors and materials (B-108): exact extremes, no probabilities."""

import math

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from smart_environment.api import app, example
from smart_environment.engines import input_hash, simulate
from smart_environment.models import (
    Building, Device, Link, Material, MaterialUncertainty, Point, Project, Radio, ScenarioRequest, Settings, Wall,
)
from smart_environment.scenarios import automatic_scenarios, evaluate

client = TestClient(app)
UNCERTAIN = MaterialUncertainty(loss_db_24ghz_low=1, loss_db_24ghz_high=8, loss_db_5ghz_low=2, loss_db_5ghz_high=12,
                                source="Tabique de composición desconocida")


def radio(**changes):
    return Radio(**{"id": "r", "protocol": "wifi", "channel": 1, "frequency_hz": 2.412e9, "bandwidth_hz": 20e6,
                    "tx_power_dbm": 20, "sensitivity_dbm": -90, **changes})


def project(sensitivity=-90, door="unknown"):
    materials = [Material(id="partition", name="Tabique", loss_db_24ghz=3, loss_db_5ghz=5, uncertainty=UNCERTAIN),
                 Material(id="wood", name="Wood", loss_db_24ghz=3, loss_db_5ghz=5)]
    walls = [Wall(id="wall-partition", start=Point(x=3, y=-2), end=Point(x=3, y=2), material_id="partition",
                  thickness_m=0.1),
             Wall(id="door-1", start=Point(x=7, y=-0.5), end=Point(x=7, y=0.5), material_id="wood",
                  thickness_m=0.04, door=door),
             Wall(id="far", start=Point(x=0, y=5), end=Point(x=10, y=5), material_id="partition")]
    devices = [Device(id="ap", name="AP", position=Point(x=0, y=0, z=1), radios=[radio()]),
               Device(id="s", name="Sensor", position=Point(x=10, y=0, z=1),
                      radios=[radio(sensitivity_dbm=sensitivity)])]
    return Project(building=Building(materials=materials, walls=walls), devices=devices,
                   links=[Link(id="l", source_device_id="s", source_radio_id="r", target_device_id="ap",
                               target_radio_id="r")],
                   settings=Settings(path_loss_exponent=2))


def free_space_dbm(distance=10.0):
    return 20 - 20 * math.log10(4 * math.pi * distance / (299_792_458 / 2.412e9))


def test_automatic_scenarios_only_vary_unresolved_hypotheses():
    nominal, best, worst = automatic_scenarios(project())
    assert (nominal.id, best.id, worst.id) == ("nominal", "best", "worst")
    assert best.doors == {"door-1": "open"} and worst.doors == {"door-1": "closed"}
    assert best.materials == {"partition": "low"} and worst.materials == {"partition": "high"}
    assert automatic_scenarios(project(door="closed"))[1].doors == {}


def test_extremes_match_hand_computed_losses():
    link = evaluate(ScenarioRequest(project=project())).links[0]
    outcomes = {o.scenario_id: o for o in link.outcomes}
    # partition 3 dB + 0.1 m thickness (no extra/cm) and door 3 dB; best: 1 + open; worst: 8 + 3.
    assert outcomes["nominal"].forward.received_power_dbm == pytest.approx(free_space_dbm() - 6)
    assert outcomes["best"].forward.received_power_dbm == pytest.approx(free_space_dbm() - 1)
    assert outcomes["worst"].forward.received_power_dbm == pytest.approx(free_space_dbm() - 11)
    assert link.forward_range_dbm == pytest.approx([free_space_dbm() - 11, free_space_dbm() - 1])
    assert link.hypotheses == ["wall-partition", "door-1"]  # 'far' is uncertain but not crossed
    assert "door-1" not in outcomes["best"].forward.crossed_wall_ids


def test_open_door_adds_no_loss_in_the_nominal_estimate():
    closed = simulate(project(door="closed")).links[0].forward
    opened = simulate(project(door="open")).links[0].forward
    assert opened.received_power_dbm == pytest.approx(closed.received_power_dbm + 3)
    assert "door-1" not in opened.crossed_wall_ids and "door-1" in closed.crossed_wall_ids
    assert simulate(project(door="unknown")).links[0].forward.received_power_dbm == pytest.approx(
        closed.received_power_dbm)


@pytest.mark.parametrize("sensitivity,expected", [(-90, "consistent"), (-35, "consistent"), (None, "incomplete")])
def test_margin_sign_when_hypotheses_do_not_matter(sensitivity, expected):
    assert evaluate(ScenarioRequest(project=project(sensitivity))).links[0].margin_sign == expected


def test_margin_sign_depends_on_hypotheses():
    # Sensitivity between the worst (free space − 11 dB) and best (− 1 dB) forward power: the sign flips.
    link = evaluate(ScenarioRequest(project=project(sensitivity=free_space_dbm() - 5))).links[0]
    assert link.margin_sign == "depends-on-hypotheses"
    assert any("hipótesis no resueltas" in r for r in link.reasons)


def test_named_scenarios_and_validation():
    request = ScenarioRequest(project=project(), scenarios=[
        {"id": "door-open-thick", "name": "Puerta abierta, tabique grueso", "doors": {"door-1": "open"},
         "materials": {"partition": "high"}}])
    outcome = next(o for o in evaluate(request).links[0].outcomes if o.scenario_id == "door-open-thick")
    assert outcome.forward.received_power_dbm == pytest.approx(free_space_dbm() - 8)
    for bad in [{"id": "best", "name": "x"}, {"id": "a", "name": "x", "doors": {"wall-partition": "open"}},
                {"id": "a", "name": "x", "materials": {"wood": "high"}}]:
        with pytest.raises(ValidationError):
            ScenarioRequest(project=project(), scenarios=[bad])
    with pytest.raises(ValidationError):
        ScenarioRequest(project=project(), scenarios=[{"id": "a", "name": "x"}, {"id": "a", "name": "y"}])


def test_nominal_loss_must_lie_within_the_range():
    with pytest.raises(ValidationError):
        Material(id="m", name="m", loss_db_24ghz=9, loss_db_5ghz=5, uncertainty=UNCERTAIN)


def test_new_optional_fields_keep_old_hashes_and_count_when_set():
    base = example("apartment")
    reference = input_hash(base)
    dumped = base.model_dump(mode="json")
    assert "door" in dumped["building"]["walls"][0] and dumped["building"]["walls"][0]["door"] is None
    changed = base.model_copy(deep=True)
    changed.building.walls[0].door = "unknown"
    assert input_hash(changed) != reference
    changed = base.model_copy(deep=True)
    material = changed.building.materials[0]
    material.uncertainty = MaterialUncertainty(loss_db_24ghz_low=material.loss_db_24ghz,
                                               loss_db_24ghz_high=material.loss_db_24ghz + 1,
                                               loss_db_5ghz_low=material.loss_db_5ghz,
                                               loss_db_5ghz_high=material.loss_db_5ghz + 1, source="test")
    assert input_hash(changed) != reference
    for model, field in [(Wall, "door"), (Material, "uncertainty")]:
        assert field not in model.model_json_schema(mode="serialization").get("required", [])


def test_incompatible_link_has_no_scenarios():
    p = project()
    p.devices[1].radios[0].channel = 6
    link = evaluate(ScenarioRequest(project=p)).links[0]
    assert link.compatibility == "incompatible" and link.outcomes == [] and link.margin_sign == "incomplete"


def test_api_endpoint():
    body = {"project": project().model_dump(mode="json")}
    response = client.post("/api/scenario-simulations", json=body)
    assert response.status_code == 200
    assert [s["id"] for s in response.json()["scenarios"]] == ["nominal", "best", "worst"]
    assert client.post("/api/scenario-simulations", json={**body, "engine": "sionna-rt"}).status_code == 501
    bad = {**body, "scenarios": [{"id": "x", "name": "x", "doors": {"far": "open"}}]}
    assert client.post("/api/scenario-simulations", json=bad).status_code == 422
