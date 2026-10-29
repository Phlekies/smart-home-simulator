"""Independent analytical cases and migration/API acceptance, not just implementation mirrors."""

import json
import math
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from smart_environment.api import app
from smart_environment.engines import simulate
from smart_environment.legacy import import_project
from smart_environment.models import Building, Device, Link, Material, Point, Project, Radio, Settings, Wall

ROOT = Path(__file__).resolve().parents[3]
client = TestClient(app)


@pytest.fixture
def project():
    def device(identifier, x, tx, sensitivity):
        return Device(id=identifier, name=identifier, role="endpoint", position=Point(x=x, y=0, z=1),
                      radios=[Radio(id="r", protocol="wifi", channel=1, frequency_hz=2.412e9,
                                    bandwidth_hz=20e6, tx_power_dbm=tx, sensitivity_dbm=sensitivity)])
    return Project(building=Building(materials=[Material(id="test", name="Test wall", loss_db_24ghz=10,
                                                        loss_db_5ghz=15)]),
                   devices=[device("a", 0, 20, -90), device("b", 10, 0, -70)],
                   links=[Link(id="a-b", source_device_id="a", source_radio_id="r",
                               target_device_id="b", target_radio_id="r")],
                   settings=Settings(path_loss_exponent=2))


def test_free_space_and_asymmetric_radios(project):
    result = simulate(project).links[0]
    # Independent Friis wavelength expression at 10 m.
    expected_loss = 20 * math.log10(4 * math.pi * 10 / (299_792_458 / 2.412e9))
    assert result.forward.received_power_dbm == pytest.approx(20 - expected_loss)
    assert result.reverse.received_power_dbm == pytest.approx(-expected_loss)
    assert result.forward.margin_db == pytest.approx(90 - expected_loss)
    assert result.reverse.margin_db == pytest.approx(90 - expected_loss)
    assert result.status == "above-threshold"
    assert result.forward.noise_dbm == pytest.approx(-93.9897000434)


def test_return_path_can_fail_even_when_uplink_passes(project):
    project.devices[1].radios[0].tx_power_dbm = -40
    link = simulate(project).links[0]
    assert link.forward.margin_db > 0
    assert link.reverse.margin_db < 0
    assert link.status == "below-threshold"


def test_wall_penetration_and_height(project):
    wall = Wall(id="w", start=Point(x=5, y=-1), end=Point(x=5, y=1), material_id="test", height_m=2)
    open_power = simulate(project).links[0].forward.received_power_dbm
    project.building.walls = [wall]
    assert simulate(project).links[0].forward.received_power_dbm == pytest.approx(open_power - 10)
    for device in project.devices:
        device.position.z = 3
    assert simulate(project).links[0].forward.received_power_dbm == pytest.approx(open_power)


def test_distance_uses_height(project):
    project.devices[1].position = Point(x=3, y=0, z=5)
    assert simulate(project).links[0].forward.distance_m == 5


def test_missing_transmit_power_never_invented(project):
    project.devices[1].radios[0].tx_power_dbm = None
    link = simulate(project).links[0]
    assert link.forward is not None
    assert link.reverse is None
    assert link.status == "unverified"


@pytest.mark.parametrize("field,value", [("protocol", "thread"), ("channel", 6), ("frequency_hz", 5.2e9)])
def test_incompatible_radios_have_no_fake_link_budget(project, field, value):
    setattr(project.devices[1].radios[0], field, value)
    link = simulate(project).links[0]
    assert link.status == "incompatible"
    assert link.forward is None and link.reverse is None


def test_unknown_protocol_does_not_become_compatible(project):
    project.devices[0].radios[0].protocol = "unknown"
    link = simulate(project).links[0]
    assert link.compatibility == "unverified" and link.status == "unverified"


def test_unsupported_material_band_is_rejected(project):
    for device in project.devices:
        device.radios[0].frequency_hz = 868e6
    assert simulate(project).links[0].status == "unsupported"


def test_different_bandwidth_not_assumed_to_negotiate(project):
    project.devices[0].radios[0].bandwidth_hz = 40e6
    assert simulate(project).links[0].status == "unsupported"


def test_hash_is_reproducible_and_tracks_changes(project):
    assert simulate(project).input_hash == simulate(project).input_hash
    original = simulate(project).input_hash
    project.devices[0].position.x = .25
    assert simulate(project).input_hash != original


def test_no_theoretical_capacity_disguised_as_throughput(project):
    output = simulate(project).model_dump_json()
    assert '"capacity_mbps"' not in output and '"latency_ms"' not in output and '"ber"' not in output


@pytest.mark.parametrize("filename", ["smart-apartment", "office-floor", "warehouse"])
def test_all_original_examples_import_without_losing_source(filename):
    data = json.loads((ROOT / "examples" / f"{filename}.shsim.json").read_text())
    imported = import_project(data)
    assert imported.legacy_source == data
    assert len(imported.devices) == len(data["sensors"]) + 1
    assert len(imported.building.walls) == len(data["walls"])
    assert imported.devices[-1].radios[0].tx_power_dbm is None
    assert all(link.status != "above-threshold" for link in simulate(imported).links)
    assert Project.model_validate_json(imported.model_dump_json()) == imported


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(version=2),
    lambda d: d.update(version=True),
    lambda d: d["devices"][0]["position"].update(x=1e300),
    lambda d: d["building"]["materials"][0].update(loss_db_24ghz=1e300),
    lambda d: d["devices"][0]["position"].update(x=float("nan")),
    lambda d: d["devices"][0]["radios"][0].update(bandwidth_hz=0),
    lambda d: d["links"][0].update(target_device_id="missing"),
    lambda d: d["devices"].append(d["devices"][0]),
    lambda d: d.update(unexpected=True),
])
def test_contract_rejects_invalid_projects(project, mutate):
    data = project.model_dump()
    mutate(data)
    with pytest.raises(ValidationError):
        Project.model_validate(data)


def test_degenerate_wall_rejected():
    with pytest.raises(ValidationError):
        Wall(id="w", start=Point(x=1, y=1), end=Point(x=1, y=1), material_id="m")


def test_api_example_edit_simulate_export_import():
    response = client.get("/api/examples/apartment")
    assert response.status_code == 200
    project = response.json()
    project["devices"][0]["position"]["x"] = 7.125
    imported = client.post("/api/projects/import", json=project)
    assert imported.status_code == 200
    result = client.post("/api/simulations", json={"project": imported.json()})
    assert result.status_code == 200 and len(result.json()["links"]) == 6
    assert imported.json()["devices"][0]["position"]["x"] == 7.125


@pytest.mark.parametrize("engine", ["sionna-rt", "ns-3"])
def test_unimplemented_engine_never_falls_back(project, engine):
    response = client.post("/api/simulations", json={"project": project.model_dump(), "engine": engine})
    assert response.status_code == 501
    assert "no fallback" in response.json()["detail"]


def test_invalid_import_returns_actionable_error():
    assert client.post("/api/projects/import", json={"format": "wrong"}).status_code == 422
    assert client.get("/api/examples/missing").status_code == 404


def test_oversize_payload_rejected():
    response = client.post("/api/projects/import", content='{"padding":"' + "a" * 2_000_000 + '"}',
                           headers={"Content-Type": "application/json"})
    assert response.status_code == 413
