"""AP placement under uncertainty (B-134): the order of places can depend on unresolved hypotheses."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from smart_environment.api import app
from smart_environment.models import (
    Building, Device, Link, Material, MaterialUncertainty, PlacementSearchRequest, Point, Project, Radio,
    ScenarioAssumptions, ScenarioRequest, Wall,
)
from smart_environment.placement import request_hash, search
from smart_environment.scenarios import evaluate

client = TestClient(app)
WORST = ScenarioAssumptions(id="worst", name="Peor caso", materials={"partition": "high"})


def radio():
    return Radio(id="r", protocol="wifi", channel=1, frequency_hz=2.412e9, bandwidth_hz=20e6, tx_power_dbm=20,
                 sensitivity_dbm=-90)


def home():
    """Sensor at (10, 5). Place A reaches it through an uncertain partition, place B through known brick."""
    materials = [Material(id="partition", name="Tabique", loss_db_24ghz=3, loss_db_5ghz=5,
                          uncertainty=MaterialUncertainty(loss_db_24ghz_low=1, loss_db_24ghz_high=15,
                                                          loss_db_5ghz_low=2, loss_db_5ghz_high=20,
                                                          source="Composición desconocida")),
                 Material(id="brick", name="Ladrillo", loss_db_24ghz=8, loss_db_5ghz=10)]
    walls = [Wall(id="partition", start=Point(x=7, y=3), end=Point(x=7, y=7), material_id="partition"),
             Wall(id="brick", start=Point(x=8, y=8), end=Point(x=12, y=8), material_id="brick")]
    devices = [Device(id="ap", name="AP", role="access-point", position=Point(x=1, y=1, z=2), radios=[radio()]),
               Device(id="s", name="Sensor", role="endpoint", position=Point(x=10, y=5, z=1), radios=[radio()])]
    return Project(building=Building(width_m=14, depth_m=12, materials=materials, walls=walls), devices=devices,
                   links=[Link(id="l", source_device_id="s", source_radio_id="r", target_device_id="ap",
                               target_radio_id="r")])


def request(**changes):
    return PlacementSearchRequest(
        project=home(), access_point_device_id="ap", access_point_radio_id="r",
        candidates=[{"id": "A", "label": "Tras el tabique", "position": {"x": 4, "y": 5, "z": 2}},
                    {"id": "B", "label": "Tras el ladrillo", "position": {"x": 10, "y": 11, "z": 2}}], **changes)


def margins(result):
    return {c.candidate_id: c.worst_margin_db for c in result.ranking}


def test_the_best_place_can_change_under_the_worst_case():
    nominal, worst = search(request()), search(request(scenario=WORST))
    assert [c.candidate_id for c in nominal.ranking] == ["A", "B"]
    assert [c.candidate_id for c in worst.ranking] == ["B", "A"]
    assert margins(worst)["A"] == pytest.approx(margins(nominal)["A"] - 12), "partition 3 → 15 dB"
    assert margins(worst)["B"] == pytest.approx(margins(nominal)["B"]), "known brick is not a hypothesis"
    assert any("Peor caso" in reason and "hipótesis" in reason for reason in worst.reasons)
    assert "escenario «Peor caso»" in worst.scope and "escenario" not in nominal.scope


def test_the_worst_case_from_scenario_simulations_can_be_used_as_is():
    automatic = next(s for s in evaluate(ScenarioRequest(project=home())).scenarios if s.id == "worst")
    assert [c.candidate_id for c in search(request(scenario=automatic)).ranking] == ["B", "A"]


def test_scenarios_follow_the_same_rules_as_maps():
    with pytest.raises(ValidationError, match="materials without an uncertainty range"):
        request(scenario=ScenarioAssumptions(id="x", name="x", materials={"brick": "high"}))
    with pytest.raises(ValidationError, match="walls that are not doors"):
        request(scenario=ScenarioAssumptions(id="x", name="x", doors={"partition": "open"}))


def test_the_scenario_is_part_of_the_request_identity():
    plain = request()
    assert request_hash(plain) == request_hash(PlacementSearchRequest.model_validate(
        {k: v for k, v in plain.model_dump(mode="json").items() if k != "scenario"})), "older hashes unchanged"
    assert request_hash(request(scenario=WORST)) != request_hash(plain)


def test_api_searches_under_a_scenario():
    body = request(scenario=WORST).model_dump(mode="json")
    response = client.post("/api/placement-searches", json=body)
    assert response.status_code == 200
    assert [c["candidate_id"] for c in response.json()["ranking"]] == ["B", "A"]
    assert response.json()["parameters"]["scenario"]["id"] == "worst"
