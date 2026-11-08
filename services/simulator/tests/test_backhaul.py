"""Data connection of access points (B-117): declared, followed hop by hop, never assumed."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from smart_environment.api import app, example
from smart_environment.coverage import compute
from smart_environment.engines import input_hash, simulate
from smart_environment.models import (
    Building, CoverageMapRequest, DataConnection, Device, Link, Material, PlacementSearchRequest, Point, Project,
    Radio, ReceiverProfile, Wall,
)
from smart_environment.placement import search
from smart_environment.report import ReportRequest, build_report, to_markdown

client = TestClient(app)


def radio(**changes):
    return Radio(**{"id": "r", "protocol": "wifi", "channel": 1, "frequency_hz": 2.412e9, "bandwidth_hz": 20e6,
                    "tx_power_dbm": 20, "sensitivity_dbm": -82, **changes})


def mesh(router=None, node=None, extra_links=()):
    """Router at x=1, mesh node at x=12 behind a brick wall, sensor at x=18 served by the node."""
    devices = [Device(id="router", name="Router", role="router", position=Point(x=1, y=4, z=1), radios=[radio()],
                      data_connection=router),
               Device(id="node", name="Nodo", role="access-point", position=Point(x=12, y=4, z=1),
                      radios=[radio(), radio(id="r2")], data_connection=node),
               Device(id="s", name="Sensor", role="endpoint", position=Point(x=18, y=4, z=1), radios=[radio()])]
    links = [Link(id="backhaul", source_device_id="node", source_radio_id="r2", target_device_id="router",
                  target_radio_id="r"),
             Link(id="sensor", source_device_id="s", source_radio_id="r", target_device_id="node",
                  target_radio_id="r"), *extra_links]
    return Project(building=Building(width_m=20, depth_m=8, materials=[
                       Material(id="brick", name="Brick", loss_db_24ghz=6, loss_db_5ghz=9)],
                       walls=[Wall(id="w", start=Point(x=6, y=0), end=Point(x=6, y=8), material_id="brick")]),
                   devices=devices, links=links)


GATEWAY = DataConnection(kind="gateway", note="Router del operador")
WIRELESS = DataConnection(kind="wireless", link_id="backhaul")


def paths(project):
    return {path.device_id: path for path in simulate(project).access_points}


def test_wireless_node_reaches_the_gateway_with_the_backhaul_margin():
    project = mesh(GATEWAY, WIRELESS)
    result = simulate(project)
    backhaul = next(link for link in result.links if link.id == "backhaul")
    node = paths(project)["node"]
    assert node.kind == "wireless" and node.ends_at == "gateway" and node.end_device_id == "router"
    assert [(h.link_id, h.from_device_id, h.to_device_id) for h in node.hops] == [("backhaul", "node", "router")]
    assert node.weakest_margin_db == pytest.approx(min(backhaul.forward.margin_db, backhaul.reverse.margin_db))
    assert paths(project)["router"].ends_at == "gateway" and paths(project)["router"].hops == []
    assert "s" not in paths(project), "endpoints are not network devices"


def test_missing_power_on_a_hop_leaves_the_path_without_a_margin():
    project = mesh(GATEWAY, WIRELESS)
    project.devices[0].radios[0].tx_power_dbm = None  # router cannot answer: reverse direction missing
    node = paths(project)["node"]
    assert node.hops[0].limiting_margin_db is None and node.weakest_margin_db is None
    assert any("sin margen en ambos sentidos" in reason for reason in node.reasons)


def test_undefined_unknown_and_wired_are_reported_not_assumed():
    undefined = paths(mesh(None, WIRELESS))
    assert undefined["router"].kind == "undefined" and "sin definir" in undefined["router"].reasons[0]
    assert undefined["node"].ends_at == "undefined" and undefined["node"].end_device_id == "router"
    unknown = paths(mesh(DataConnection(kind="unknown"), WIRELESS))["node"]
    assert unknown.ends_at == "unknown" and unknown.weakest_margin_db is not None
    wired = paths(mesh(GATEWAY, DataConnection(kind="wired", note="Ethernet")))["node"]
    assert wired.hops == [] and wired.ends_at == "wired" and "no evaluada" in wired.reasons[0]


def test_a_loop_never_reaches_a_gateway():
    loop = Link(id="loop", source_device_id="router", source_radio_id="r", target_device_id="node",
                target_radio_id="r")
    node = paths(mesh(DataConnection(kind="wireless", link_id="loop"), WIRELESS, [loop]))["node"]
    assert node.ends_at == "loop" and len(node.hops) == 2


def test_contract_rejects_inconsistent_connections():
    with pytest.raises(ValidationError):
        DataConnection(kind="wireless")
    with pytest.raises(ValidationError):
        DataConnection(kind="wired", link_id="backhaul")
    with pytest.raises(ValidationError, match="unknown data link"):
        mesh(GATEWAY, DataConnection(kind="wireless", link_id="missing"))
    with pytest.raises(ValidationError, match="does not reach"):
        mesh(DataConnection(kind="wireless", link_id="sensor"), WIRELESS)


def test_legacy_projects_keep_their_hash_and_results():
    project = example("apartment")
    data = project.model_dump(mode="json")
    assert "data_connection" in data["devices"][0] and data["devices"][0]["data_connection"] is None
    without = {**data, "devices": [{k: v for k, v in d.items() if k != "data_connection"} for d in data["devices"]]}
    assert input_hash(Project.model_validate(without)) == input_hash(project)
    assert simulate(project).access_points == [], "the Java hub is a controller, not an access point"
    assert input_hash(mesh(GATEWAY, WIRELESS)) != input_hash(mesh(GATEWAY, None)), "a connection changes results"


def test_placement_moves_the_backhaul_with_the_access_point():
    project = mesh(GATEWAY, WIRELESS)
    request = PlacementSearchRequest(project=project, access_point_device_id="node", access_point_radio_id="r",
                                     target_device_ids=["s"],
                                     candidates=[{"id": "near-router", "label": "Cerca del router",
                                                  "position": {"x": 4, "y": 4, "z": 1}}])
    result = search(request)
    baseline = {t.link_id: t for t in result.baseline.targets}
    assert set(baseline) == {"sensor", "backhaul"} and baseline["backhaul"].backhaul
    assert not baseline["sensor"].backhaul and baseline["backhaul"].device_id == "router"
    link = next(link for link in simulate(project).links if link.id == "backhaul")
    assert baseline["backhaul"].forward_margin_db == pytest.approx(link.forward.margin_db)
    moved = {t.link_id: t for t in result.ranking[0].targets}
    assert moved["backhaul"].limiting_margin_db > baseline["backhaul"].limiting_margin_db
    assert any("se mueve con él" in reason for reason in result.reasons)
    undefined = search(request.model_copy(update={"project": mesh(GATEWAY, None)}))
    assert {t.link_id for t in undefined.baseline.targets} == {"sensor"}
    assert any("sin definir" in reason for reason in undefined.reasons)


def test_coverage_map_and_report_state_the_access_point_path():
    project = mesh(GATEWAY, None)
    profile = ReceiverProfile(id="p", name="Perfil", radio=radio(id="p"))
    grid = {"width_m": 4, "depth_m": 4, "resolution_m": 2, "height_m": 1, "origin_x_m": 14}
    request = CoverageMapRequest(project=project, access_point_device_id="node", access_point_radio_id="r",
                                 profile=profile, grid=grid)
    assert any("Camino de datos del AP" in reason and "sin definir" in reason for reason in compute(request).reasons)
    defined = request.model_copy(update={"project": mesh(GATEWAY, WIRELESS)})
    assert not any("Camino de datos" in reason for reason in compute(defined).reasons)
    report = build_report(ReportRequest(project=mesh(GATEWAY, WIRELESS)))
    assert [p.device_id for p in report.access_points] == ["router", "node"]
    text = to_markdown(report)
    assert "## Conexión de datos de los AP" in text and "backhaul (" in text and "pasarela (router)" in text


def test_api_returns_access_points():
    response = client.post("/api/simulations", json={"project": mesh(GATEWAY, WIRELESS).model_dump(mode="json")})
    assert response.status_code == 200
    assert [p["device_id"] for p in response.json()["access_points"]] == ["router", "node"]
