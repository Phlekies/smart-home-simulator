"""AP placement among allowed places (B-105): max-min of bidirectional margins, no invented data."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from smart_environment.api import app, example
from smart_environment.engines import input_hash, simulate
from smart_environment.models import (
    Building, Device, Link, Material, PlacementSearchRequest, PlacementZone, Point, Project, Radio, Wall,
)
from smart_environment.placement import MAX_WORK, PlacementLimitError, request_hash, search

client = TestClient(app)


def radio(**changes):
    return Radio(**{"id": "r", "protocol": "wifi", "channel": 1, "frequency_hz": 2.412e9, "bandwidth_hz": 20e6,
                    "tx_power_dbm": 20, "sensitivity_dbm": -90, **changes})


def home():
    """AP at x=1; sensor A at x=2 (easy), sensor B at x=19 behind a concrete wall (hard, weak radio)."""
    devices = [Device(id="ap", name="AP", role="access-point", position=Point(x=1, y=5, z=2), radios=[radio()]),
               Device(id="a", name="A", role="endpoint", position=Point(x=2, y=5, z=1), radios=[radio()]),
               Device(id="b", name="B", role="endpoint", position=Point(x=19, y=5, z=1),
                      radios=[radio(tx_power_dbm=0, sensitivity_dbm=-80)])]
    return Project(building=Building(width_m=20, depth_m=10, materials=[
                       Material(id="concrete", name="Concrete", loss_db_24ghz=12, loss_db_5ghz=15)],
                       walls=[Wall(id="w", start=Point(x=15, y=0), end=Point(x=15, y=10), material_id="concrete",
                                   thickness_m=0.2)]),
                   devices=devices,
                   links=[Link(id="l-a", source_device_id="a", source_radio_id="r", target_device_id="ap",
                               target_radio_id="r"),
                          Link(id="l-b", source_device_id="b", source_radio_id="r", target_device_id="ap",
                               target_radio_id="r")])


def request(**changes):
    data = {"project": home(), "access_point_device_id": "ap", "access_point_radio_id": "r",
            "candidates": [{"id": "hall", "label": "Enchufe pasillo", "position": {"x": 10, "y": 5, "z": 2}},
                           {"id": "corner", "label": "Rincón", "position": {"x": 0.5, "y": 0.5, "z": 2}}]}
    data.update(changes)
    return PlacementSearchRequest.model_validate(data)


def test_baseline_matches_the_link_budget():
    result = search(request())
    links = {link.id: link for link in simulate(home()).links}
    for target in result.baseline.targets:
        link = links[target.link_id]
        # Links run device → AP, so the AP's forward direction is the link's reverse one.
        assert target.forward_margin_db == pytest.approx(link.reverse.margin_db)
        assert target.reverse_margin_db == pytest.approx(link.forward.margin_db)
    assert result.input_hash == input_hash(home())


def test_max_min_prefers_the_place_that_helps_the_weakest_device():
    result = search(request())
    assert result.ranked and result.criterion == "max-min-bidirectional-margin"
    best = result.ranking[0]
    assert best.candidate_id == "hall" and best.worst_target_id == "b"
    assert best.worst_margin_db > result.baseline.worst_margin_db
    assert best.delta_worst_margin_db == pytest.approx(best.worst_margin_db - result.baseline.worst_margin_db)
    worst_b = next(t for t in best.targets if t.device_id == "b")
    assert worst_b.limiting_direction == "reverse"  # weak sensor radio limits the return path
    assert [c.candidate_id for c in result.ranking] == ["hall", "corner"]


def test_zones_are_sampled_and_places_inside_walls_excluded():
    zone = PlacementZone(id="z", label="Pared del salón", min_x_m=14, min_y_m=5, max_x_m=16, max_y_m=5,
                         height_m=2, step_m=0.5)
    assert [x for x, _ in zone.positions()] == [14, 14.5, 15, 15.5, 16]
    result = search(request(candidates=[], zones=[zone.model_dump()]))
    assert result.evaluated == 4 and [e.reason for e in result.excluded] == ["inside-wall:w"]
    assert all(c.source == "zone" and c.candidate_id.startswith("z@") for c in result.ranking)


def test_missing_data_is_reported_and_not_ranked():
    project = home()
    for device in project.devices:
        device.radios[0].sensitivity_dbm = None
    result = search(request(project=project))
    assert not result.ranked and all(c.worst_margin_db is None for c in result.ranking)
    assert any("no se ordenan" in r for r in result.reasons)
    assert {t.status for t in result.baseline.targets} == {"incomplete"}


def test_priority_subset_and_incompatible_targets():
    result = search(request(target_device_ids=["a"]))
    assert result.target_device_ids == ["a"] and result.ranking[0].worst_target_id == "a"
    project = home()
    project.devices[2].radios[0].channel = 6
    result = search(request(project=project))
    b = next(t for t in result.baseline.targets if t.device_id == "b")
    assert b.status == "not-computed" and "frecuencia/canal" in b.reason
    assert all(c.worst_target_id == "a" for c in result.ranking)
    project.devices[1].radios[0].channel = 6
    with pytest.raises(PlacementLimitError):
        search(request(project=project))


def test_too_close_target_is_not_computed():
    result = search(request(candidates=[{"id": "on-a", "label": "Junto a A", "position": {"x": 2, "y": 5, "z": 1}}]))
    a = next(t for t in result.ranking[0].targets if t.device_id == "a")
    assert a.status == "not-computed" and a.reason == "too-close"


@pytest.mark.parametrize("changes", [
    {"access_point_device_id": "x"}, {"access_point_radio_id": "x"}, {"candidates": [], "zones": []},
    {"target_device_ids": ["ghost"]},
    {"candidates": [{"id": "current", "label": "x", "position": {"x": 1, "y": 1}}]},
    {"zones": [{"id": "z", "label": "z", "min_x_m": 0, "min_y_m": 0, "max_x_m": 30, "max_y_m": 30,
                "height_m": 1, "step_m": 0.25}]},
    {"zones": [{"id": "z", "label": "z", "min_x_m": 5, "min_y_m": 0, "max_x_m": 1, "max_y_m": 1, "height_m": 1}]},
])
def test_invalid_requests_are_rejected(changes):
    with pytest.raises(ValidationError):
        request(**changes)


def test_unlinked_priority_device_and_work_limit():
    project = home()
    project.devices.append(Device(id="c", name="C", position=Point(x=5, y=5), radios=[radio()]))
    with pytest.raises(PlacementLimitError, match="Sin enlace"):
        search(request(project=project, target_device_ids=["c"]))
    project = home()
    project.building.walls += [Wall(id=f"x{k}", start=Point(x=k, y=20), end=Point(x=k, y=21), material_id="concrete")
                               for k in range(1, 1300)]
    zone = {"id": "z", "label": "z", "min_x_m": 0, "min_y_m": 0, "max_x_m": 19.5, "max_y_m": 9.5,
            "height_m": 2, "step_m": 0.5}
    big = request(project=project, candidates=[], zones=[zone])
    assert (len(big.zones[0].positions()) + 1) * 2 * len(project.building.walls) > MAX_WORK
    with pytest.raises(PlacementLimitError, match="evaluaciones"):
        search(big)


def test_request_hash_tracks_parameters():
    assert request_hash(request()) != request_hash(request(target_device_ids=["a"]))


def test_api_endpoint():
    body = request().model_dump(mode="json")
    response = client.post("/api/placement-searches", json=body)
    assert response.status_code == 200 and response.json()["ranking"][0]["candidate_id"] == "hall"
    assert client.post("/api/placement-searches", json={**body, "engine": "sionna-rt"}).status_code == 501
    assert client.post("/api/placement-searches", json={**body, "target_device_ids": ["ap"]}).status_code == 422


def test_java_example_without_sensitivities_is_not_ranked():
    project = example("apartment")
    hub = next(d for d in project.devices if d.role == "controller")
    result = search(PlacementSearchRequest(project=project, access_point_device_id=hub.id,
                                           access_point_radio_id=hub.radios[0].id,
                                           zones=[PlacementZone(id="z", label="Salón", min_x_m=4, min_y_m=4,
                                                                max_x_m=8, max_y_m=8, height_m=1.3, step_m=1)]))
    assert not result.ranked and len(result.target_device_ids) == 6
