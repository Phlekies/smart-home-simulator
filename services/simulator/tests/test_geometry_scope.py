"""Geometry outside the model and weak return paths never yield a favourable status (B-122)."""

import pytest

from smart_environment.coverage import compute
from smart_environment.engines import geometry_issue, simulate
from smart_environment.models import (
    Building, CoverageMapRequest, Device, Link, Material, PlacementSearchRequest, Point, Project, Radio,
    ReceiverProfile, Wall,
)
from smart_environment.placement import search


def radio(**changes):
    return Radio(**{"id": "r", "protocol": "wifi", "channel": 1, "frequency_hz": 2.412e9, "bandwidth_hz": 20e6,
                    "tx_power_dbm": 20, "sensitivity_dbm": -90, **changes})


def project(sensor_at=Point(x=6, y=2, z=1), sensor_radio=None, walls=True):
    """AP at x=1 and a sensor; a brick wall at x=4 between them, 2.6 m high from the floor."""
    return Project(building=Building(width_m=10, depth_m=5, materials=[
                       Material(id="brick", name="Brick", loss_db_24ghz=6, loss_db_5ghz=9)],
                       walls=[Wall(id="w", start=Point(x=4, y=0), end=Point(x=4, y=5), material_id="brick",
                                   thickness_m=0.2)] if walls else []),
                   devices=[Device(id="ap", name="AP", role="access-point", position=Point(x=1, y=2, z=2),
                                   radios=[radio()]),
                            Device(id="s", name="Sensor", role="endpoint", position=sensor_at,
                                   radios=[sensor_radio or radio()])],
                   links=[Link(id="l", source_device_id="s", source_radio_id="r", target_device_id="ap",
                               target_radio_id="r")])


def link(p):
    return simulate(p).links[0]


def test_reference_link_is_above_threshold():
    assert link(project()).status == "above-threshold"


@pytest.mark.parametrize("position, text", [
    (Point(x=4.05, y=2, z=1), "dentro de la pared w"),
    (Point(x=6, y=2, z=3.5), "por encima de todas las paredes"),
    (Point(x=6, y=2, z=-1), "por debajo de todas las paredes"),
])
def test_positions_outside_the_model_are_not_favourable(position, text):
    result = link(project(position))
    assert result.status == "unverified" and any(text in reason for reason in result.reasons)
    assert result.forward is not None and result.forward.margin_db > 0, "values are still reported"


def test_without_walls_there_is_no_storey_to_leave():
    assert geometry_issue(project(walls=False), Point(x=6, y=2, z=30), "x") is None


def test_a_weak_return_path_prevents_a_favourable_status():
    """P2 rule: a good AP→device direction never hides an insufficient device→AP direction."""
    weak = link(project(sensor_radio=radio(tx_power_dbm=-60)))
    assert weak.forward.margin_db < 0 < weak.reverse.margin_db or weak.reverse.margin_db < 0 < weak.forward.margin_db
    assert weak.status == "below-threshold"
    unknown = link(project(sensor_radio=radio(tx_power_dbm=None)))
    assert unknown.status == "unverified" and unknown.forward is None and unknown.reverse.margin_db > 0
    assert any("Falta potencia de transmisión de Sensor" in reason for reason in unknown.reasons)
    no_sensitivity = link(project(sensor_radio=radio(sensitivity_dbm=None)))
    assert no_sensitivity.status == "unverified"


def test_map_states_positions_and_heights_outside_the_model():
    p = project()
    p.devices[0].position = Point(x=4.05, y=2, z=1)
    profile = ReceiverProfile(id="p", name="Perfil", radio=radio(id="p"))
    grid = {"width_m": 4, "depth_m": 4, "resolution_m": 2, "height_m": 3.2, "origin_x_m": 5}
    reasons = compute(CoverageMapRequest(project=p, access_point_device_id="ap", access_point_radio_id="r",
                                         profile=profile, grid=grid)).reasons
    assert any("AP está dentro de la pared w" in reason for reason in reasons)
    assert any("La altura del mapa (3.2 m) queda fuera de las paredes (0–2.6 m)" in reason for reason in reasons)
    inside = compute(CoverageMapRequest(project=project(), access_point_device_id="ap", access_point_radio_id="r",
                                        profile=profile, grid={**grid, "height_m": 1})).reasons
    assert not any("fuera de las paredes" in reason or "dentro de la pared" in reason for reason in inside)


def test_placement_drops_places_above_every_wall():
    request = PlacementSearchRequest(project=project(), access_point_device_id="ap", access_point_radio_id="r",
                                     candidates=[{"id": "ceiling-void", "label": "Falso techo",
                                                  "position": {"x": 1, "y": 2, "z": 3}},
                                                 {"id": "shelf", "label": "Estante",
                                                  "position": {"x": 1, "y": 2, "z": 2.2}}])
    result = search(request)
    assert [c.candidate_id for c in result.ranking] == ["shelf"]
    assert [(e.candidate_id, e.reason) for e in result.excluded] == [("ceiling-void", "outside-wall-heights:0-2.6m")]
    assert any("altura sin paredes ni forjados" in reason for reason in result.reasons)
