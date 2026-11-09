"""Coverage classification (B-139): favourable / marginal / insufficient / no data with a 10 dB reserve.

Geometry used throughout: AP at x=0 and sensor at x=10 (2.412 GHz, exponent 2, 20 dBm both ways,
about 60.1 dB of free-space loss), crossing an uncertain partition (3 dB nominal, 1–8 dB) and an
interior door of unknown state (3 dB, treated as closed except in the best case). The received
power is then about −46.1 dBm as drawn and −51.1 dBm with the partition at its maximum.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from smart_environment.api import app
from smart_environment.classification import (
    DESIGN_RESERVE_DB, POLICY, classify_link, classify_margin, classify_outcome,
)
from smart_environment.coverage import compute
from smart_environment.engines import simulate
from smart_environment.models import (
    Building, CoverageMapRequest, Device, Link, Material, MaterialUncertainty, Point, Project, Radio,
    ReceiverProfile, ScenarioRequest, Settings, Wall,
)
from smart_environment.scenarios import evaluate

ROOT = Path(__file__).resolve().parents[3]
client = TestClient(app)
UNCERTAIN = MaterialUncertainty(loss_db_24ghz_low=1, loss_db_24ghz_high=8, loss_db_5ghz_low=2, loss_db_5ghz_high=12,
                                source="Tabique de composición desconocida")


def radio(**changes):
    return Radio(**{"id": "r", "protocol": "wifi", "channel": 1, "frequency_hz": 2.412e9, "bandwidth_hz": 20e6,
                    "tx_power_dbm": 20, "sensitivity_dbm": -90, **changes})


def project(sensor=None, ap=None, sensor_at=(10, 0, 1)):
    materials = [Material(id="partition", name="Tabique", loss_db_24ghz=3, loss_db_5ghz=5, uncertainty=UNCERTAIN),
                 Material(id="wood", name="Madera", loss_db_24ghz=3, loss_db_5ghz=5)]
    walls = [Wall(id="wall-partition", start=Point(x=3, y=-2), end=Point(x=3, y=2), material_id="partition",
                  thickness_m=0.1),
             Wall(id="door-1", start=Point(x=7, y=-0.5), end=Point(x=7, y=0.5), material_id="wood",
                  thickness_m=0.04, door="unknown")]
    x, y, z = sensor_at
    devices = [Device(id="ap", name="Router", role="access-point", position=Point(x=0, y=0, z=1),
                      radios=[radio(**(ap or {}))]),
               Device(id="s", name="Sensor", position=Point(x=x, y=y, z=z), radios=[radio(**(sensor or {}))])]
    return Project(building=Building(materials=materials, walls=walls), devices=devices,
                   links=[Link(id="l", source_device_id="s", source_radio_id="r", target_device_id="ap",
                               target_radio_id="r")],
                   settings=Settings(path_loss_exponent=2))


def link(**kwargs):
    return simulate(project(**kwargs)).links[0]


@pytest.mark.parametrize("margin, expected", [
    (None, "no-data"), (-0.001, "insufficient"), (0.0, "marginal"), (9.999, "marginal"),
    (DESIGN_RESERVE_DB, "favourable"), (40.0, "favourable")])
def test_margin_boundaries(margin, expected):
    assert classify_margin(margin) == expected


def test_link_rule_needs_the_reserve_as_drawn_and_in_the_worst_case():
    assert classify_link("above-threshold", 12, 12) == "favourable"
    assert classify_link("above-threshold", 12, None) == "favourable"  # no open hypotheses on the path
    assert classify_link("above-threshold", 12, 9) == "marginal"
    assert classify_link("above-threshold", 5, 5) == "marginal"
    assert classify_link("below-threshold", None, None) == "insufficient"
    for status in ("unverified", "incompatible", "unsupported"):
        assert classify_link(status, 30, 30) == "no-data"


def test_strong_link_is_favourable_and_states_the_policy():
    result = simulate(project())
    item = result.links[0]
    assert item.coverage_class == "favourable"
    assert item.limiting_margin_db == pytest.approx(43.9, abs=0.1)
    assert item.worst_case_limiting_margin_db == pytest.approx(38.9, abs=0.1)
    assert result.classification == POLICY and result.classification.calibrated is False


def test_weak_return_of_a_low_power_sensor_is_insufficient():
    """Acceptance case: the sensor hears the router well, but the router does not hear the sensor."""
    item = link(sensor={"tx_power_dbm": -30})
    assert item.reverse.margin_db > 40 and item.forward.margin_db < 0
    assert item.coverage_class == "insufficient"


def test_margin_below_the_reserve_is_marginal():
    assert link(sensor={"sensitivity_dbm": -50}).coverage_class == "marginal"  # about 3.9 dB


def test_reserve_lost_only_under_hypotheses_is_marginal_with_a_reason():
    item = link(sensor={"sensitivity_dbm": -58})  # about 11.9 dB as drawn, 6.9 dB with the partition at 8 dB
    assert item.limiting_margin_db >= DESIGN_RESERVE_DB > item.worst_case_limiting_margin_db
    assert item.coverage_class == "marginal"
    assert any("peor caso" in reason for reason in item.reasons)


def test_negative_margin_is_insufficient():
    assert link(sensor={"sensitivity_dbm": -40}).coverage_class == "insufficient"


def test_missing_sensitivity_gives_no_data_unless_the_other_direction_already_fails():
    """Acceptance case: unknown sensitivity of the candidate gives a partial budget and no class."""
    assert link(sensor={"sensitivity_dbm": None}).coverage_class == "no-data"
    assert link(sensor={"sensitivity_dbm": None, "tx_power_dbm": -30}).coverage_class == "insufficient"


@pytest.mark.parametrize("sensor", [
    {"protocol": "zigbee"},                                                # incompatible radios
    {"protocol": "unknown"},                                               # compatibility not verified
    {"frequency_hz": 868e6, "channel": None},                              # incompatible frequency
])
def test_unverifiable_or_incompatible_radios_give_no_data(sensor):
    assert link(sensor=sensor).coverage_class == "no-data"


def test_unsupported_band_gives_no_data():
    item = link(sensor={"frequency_hz": 868e6}, ap={"frequency_hz": 868e6})
    assert item.status == "unsupported" and item.coverage_class == "no-data"


def test_position_outside_the_model_gives_no_data():
    item = link(sensor_at=(10, 0, 9))  # above every wall: another storey
    assert item.status == "unverified" and item.coverage_class == "no-data"


def test_scenarios_classify_each_case_and_agree_with_the_simulation():
    request = ScenarioRequest(project=project(sensor={"sensitivity_dbm": -58}))
    result = evaluate(request)
    classes = {o.scenario_id: o.coverage_class for o in result.links[0].outcomes}
    assert classes == {"nominal": "favourable", "best": "favourable", "worst": "marginal"}
    assert result.links[0].coverage_class == simulate(request.project).links[0].coverage_class == "marginal"
    assert result.classification == POLICY


def map_request(**profile):
    data = project()
    radio_data = {"id": "p", "protocol": "wifi", "channel": 1, "frequency_hz": 2.412e9, "bandwidth_hz": 20e6,
                  "tx_power_dbm": 5, "sensitivity_dbm": -85, **profile}
    return CoverageMapRequest(project=data, access_point_device_id="ap", access_point_radio_id="r",
                              profile=ReceiverProfile(id="p", name="Sensor", radio=Radio(**radio_data)),
                              # Cell centres at whole x metres: the column at x=3 lies inside the partition.
                              grid={"width_m": 12, "depth_m": 4, "origin_x_m": -0.5, "origin_y_m": -2,
                                    "resolution_m": 1, "height_m": 1},
                              points=[{"x": 10, "y": 0, "z": 1}, {"x": 10, "y": 0, "z": 9}])


def test_map_cells_follow_their_limiting_margin():
    result = compute(map_request())
    cells = result.cells
    assert result.classification == POLICY and len(cells.coverage_class) == len(cells.status)
    for f, r, status, value in zip(cells.forward_margin_db, cells.reverse_margin_db, cells.status,
                                   cells.coverage_class):
        assert value == (classify_margin(min(f, r)) if status == "computed" else "no-data")
    assert {"favourable", "no-data"} <= set(cells.coverage_class)  # cells inside the walls are not computed
    inside, above = result.points
    assert inside.coverage_class == classify_margin(min(inside.forward_margin_db, inside.reverse_margin_db))
    assert above.coverage_class == "no-data"  # this exact point is outside the storey the walls describe


def test_partial_cells_are_never_favourable_or_marginal():
    cells = compute(map_request(tx_power_dbm=None)).cells
    assert "partial" in cells.status
    assert all(value in ("no-data", "insufficient") for value, status in zip(cells.coverage_class, cells.status)
               if status == "partial")


def test_unverified_map_is_left_without_classes():
    result = compute(map_request(protocol="unknown"))
    assert result.compatibility == "unverified" and set(result.cells.coverage_class) == {"no-data"}
    assert any(reason.startswith("Sin clasificación") for reason in result.reasons)


def test_demo_project_shows_each_kind_of_result():
    """The README demo: a strong link, a one-way failure and a camera with little return margin."""
    demo = Project.model_validate_json((ROOT / "docs/images/demo-apartment.shsim.json").read_text(encoding="utf-8"))
    names = {d.id: d.name for d in demo.devices}
    classes = {names[link.source_device_id]: item.coverage_class
               for link, item in zip(demo.links, simulate(demo).links)}
    assert classes["Thermostat"] == "favourable"
    assert classes["Window sensor"] == "insufficient"
    assert classes["Security camera"] == "marginal"


def test_api_returns_classes_and_policy():
    body = {"project": project(sensor={"sensitivity_dbm": -50}).model_dump(mode="json")}
    data = client.post("/api/simulations", json=body).json()
    assert data["links"][0]["coverage_class"] == "marginal"
    assert data["classification"]["design_reserve_db"] == DESIGN_RESERVE_DB


def test_outcome_rule_is_bounded_by_the_link_status():
    assert classify_outcome("unverified", [30, 30]) == "no-data"
    assert classify_outcome("unverified", [30, -1]) == "insufficient"
    assert classify_outcome("below-threshold", [30, 15]) == "favourable"  # another scenario of a failing link


def test_placement_targets_use_the_same_classes_as_the_simulation():
    from test_placement import request as placement_request  # same fixtures as the placement tests
    from smart_environment.placement import search

    search_request = placement_request()
    result = search(search_request)
    links = {item.id: item for item in simulate(search_request.project).links}
    for target in result.baseline.targets:
        assert target.coverage_class == links[target.link_id].coverage_class
    assert result.ranking and all(t.coverage_class is not None for c in result.ranking for t in c.targets)


def test_failure_criterion_constant_matches_the_policy_text():
    from smart_environment.measurements import LOW_TRAFFIC_CRITERION

    assert (LOW_TRAFFIC_CRITERION.method, LOW_TRAFFIC_CRITERION.direction) == ("icmp-echo", "round-trip")
    assert LOW_TRAFFIC_CRITERION.min_packets == 300 and LOW_TRAFFIC_CRITERION.min_delivery_ratio == 0.95
    assert LOW_TRAFFIC_CRITERION.frozen_on is None  # provisional: a campaign freezes its own copy
    assert "≥ 300 paquetes" in POLICY.failure_criterion and "95 %" in POLICY.failure_criterion


def test_profiles_state_their_link_requirement():
    from smart_environment.profiles import CATALOG

    notes = {profile.id: profile.notes[0] for profile in CATALOG if "client" in profile.roles}
    assert "bajo tráfico" in notes["wifi4-ht20-mcs0"] and "low-traffic-v1" in notes["wifi4-ht20-mcs0"]
    assert "cámaras" in notes["wifi4-ht20-mcs7"] and "no se evalúan" in notes["wifi4-ht20-mcs7"]
