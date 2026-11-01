"""Power outlets and network sockets limit the AP search (B-119) without claiming a cable fits."""

import math

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from smart_environment.api import app
from smart_environment.engines import input_hash, simulate
from smart_environment.models import DataConnection, Fixture, PlacementSearchRequest, Point, Project
from smart_environment.placement import request_hash, search

from test_placement import home

client = TestClient(app)
CANDIDATES = [{"id": "hall", "label": "Pasillo", "position": {"x": 10, "y": 5, "z": 2}},
              {"id": "corner", "label": "Rincón", "position": {"x": 0.5, "y": 0.5, "z": 2}},
              {"id": "far", "label": "Fondo", "position": {"x": 18, "y": 9, "z": 2}}]


def wired_home(outlets=(), ports=()):
    project = home()
    project.building.power_outlets = [Fixture(id=f"o{i}", label="Enchufe", position=Point(**p))
                                      for i, p in enumerate(outlets)]
    project.building.network_ports = [Fixture(id=f"n{i}", label="Toma RJ45", position=Point(**p))
                                      for i, p in enumerate(ports)]
    return Project.model_validate(project.model_dump())


def request(project, **limits):
    return PlacementSearchRequest(project=project, access_point_device_id="ap", access_point_radio_id="r",
                                  candidates=CANDIDATES, **limits)


def test_outlets_never_change_link_results_or_their_hash():
    plain, wired = home(), wired_home([{"x": 10, "y": 5, "z": 0.3}], [{"x": 1, "y": 1, "z": 0.3}])
    assert input_hash(wired) == input_hash(plain)
    assert simulate(wired).links == simulate(plain).links
    assert request_hash(request(wired)) != request_hash(request(plain)), "the search must not reuse a stale result"
    assert request_hash(request(plain)) == request_hash(PlacementSearchRequest.model_validate(
        {**request(plain).model_dump(mode="json"), "max_power_distance_m": None})), "unset limits keep old hashes"


def test_places_beyond_the_straight_line_limit_are_discarded():
    outlet = {"x": 10, "y": 5, "z": 0.3}
    result = search(request(wired_home([outlet]), max_power_distance_m=3))
    assert [c.candidate_id for c in result.ranking] == ["hall"]
    excluded = {e.candidate_id: e.reason for e in result.excluded}
    assert excluded == {"corner": "no-power-outlet-within:3m", "far": "no-power-outlet-within:3m"}
    assert math.dist((10, 5, 2), (10, 5, 0.3)) <= 3 < math.dist((0.5, 0.5, 2), (10, 5, 0.3))
    assert any("2 lugares descartados por no tener un enchufe a 3 m" in r for r in result.reasons)
    assert any("cable real recorre paredes" in r for r in result.reasons)
    assert any("posición actual no cumple" in r for r in result.reasons), "the AP at x=1 is 9 m from the outlet"


def test_network_sockets_limit_independently_of_outlets():
    project = wired_home([{"x": 10, "y": 5, "z": 0.3}], [{"x": 1, "y": 1, "z": 0.3}])
    result = search(request(project, max_power_distance_m=20, max_network_distance_m=2))
    assert [c.candidate_id for c in result.ranking] == ["corner"]
    assert {e.reason for e in result.excluded} == {"no-network-port-within:2m"}
    nothing = search(request(project, max_power_distance_m=0.5))
    assert nothing.ranking == [] and not nothing.ranked
    assert any("Ningún lugar permitido queda" in r for r in nothing.reasons)


def test_a_wired_access_point_asks_for_the_socket_limit():
    project = home()
    project.devices[0].data_connection = DataConnection(kind="wired", note="Ethernet")
    result = search(request(Project.model_validate(project.model_dump())))
    assert any("indica la distancia máxima a una toma de red" in r for r in result.reasons)


def test_limits_without_fixtures_or_duplicate_ids_are_rejected():
    with pytest.raises(ValidationError, match="power outlet"):
        request(home(), max_power_distance_m=3)
    with pytest.raises(ValidationError, match="network socket"):
        request(home(), max_network_distance_m=3)
    with pytest.raises(ValidationError, match="Duplicate outlet/port"):
        project = home().model_dump()
        project["building"]["power_outlets"] = [{"id": "x", "label": "A", "position": {"x": 1, "y": 1}}]
        project["building"]["network_ports"] = [{"id": "x", "label": "B", "position": {"x": 2, "y": 1}}]
        Project.model_validate(project)


def test_api_applies_the_limits():
    project = wired_home([{"x": 10, "y": 5, "z": 0.3}])
    body = request(project, max_power_distance_m=3).model_dump(mode="json")
    response = client.post("/api/placement-searches", json=body)
    assert response.status_code == 200
    assert response.json()["parameters"]["max_power_distance_m"] == 3
    assert [c["candidate_id"] for c in response.json()["ranking"]] == ["hall"]
    body["project"]["building"]["power_outlets"] = []
    assert client.post("/api/placement-searches", json=body).status_code == 422
