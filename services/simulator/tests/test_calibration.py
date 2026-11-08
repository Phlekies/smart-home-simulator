"""Measured vs predicted (B-109). Sample values are synthetic validator fixtures, not measurements."""

import json
from pathlib import Path

import pytest

from smart_environment.api import example
from smart_environment.calibration import CalibrationError, calibrate, main, residuals
from smart_environment.engines import input_hash, simulate
from smart_environment.measurements import MeasurementCampaign
from smart_environment.models import Building, Device, Link, Material, Point, Project, Radio, Settings, Wall

TEMPLATE = Path(__file__).resolve().parents[1] / "examples" / "measurement-campaign.template.json"
OFFSET = -6.0  # e.g. an unknown phone antenna loss the calibration should absorb
JITTER = [0.4, -0.3, 0.2, -0.5, 0.1, 0.3]


def project(door="unknown"):
    radio = Radio(id="r", protocol="wifi", channel=1, frequency_hz=2.412e9, bandwidth_hz=20e6, tx_power_dbm=20)
    return Project(
        building=Building(materials=[Material(id="wood", name="Wood", loss_db_24ghz=3, loss_db_5ghz=5)],
                          walls=[Wall(id="door-1", start=Point(x=4, y=-1), end=Point(x=4, y=1), material_id="wood",
                                      thickness_m=0.04, door=door)]),
        devices=[Device(id="ap", name="AP", role="access-point", position=Point(x=0, y=0, z=2), radios=[radio])],
        settings=Settings(path_loss_exponent=2))


def campaign(site, split, samples, door_state="closed", reporting="dbm", device_tx=None, cid=None,
             proj=None, frozen="2026-11-01"):
    proj = proj or project()
    positions = [(2, 0), (6, 0), (8, 0.5), (3, 2), (9, -0.5), (6, 1)]
    points = []
    for k, ((x, y), value) in enumerate(zip(positions, samples)):
        points.append({"id": f"p{k}", "status": "measured", "position": {"x": x, "y": y, "z": 1},
                       "device_instrument_id": "phone", "access_point_id": "ap-1", "conditions_id": "c",
                       "measured_at": "2026-11-02T10:00:00",
                       "rssi": [{"direction": "ap-to-device", "receiver_instrument_id": "phone",
                                 "samples_dbm": [value - 0.5, value, value + 0.5]}]})
    phone = {"id": "phone", "kind": "phone", "rssi_reporting": reporting}
    if device_tx is not None:
        phone["radio"] = {"tx_power_dbm": {"value": device_tx, "provenance": "declared", "source": "fixture"}}
    return MeasurementCampaign.model_validate({
        "id": cid or f"{site}-{split}", "site_id": site, "split": split, "synthetic": False,
        "purpose": "Validator fixture for calibration tests",
        "project": {"name": proj.name, "input_hash": input_hash(proj)},
        "collected_from": "2026-11-02", "collected_to": "2026-11-02",
        "instruments": [{"id": "router", "kind": "access-point"}, phone],
        "access_points": [{"id": "ap-1", "project_device_id": "ap", "project_radio_id": "r", "instrument_id": "router",
                           "frequency_hz": 2.412e9, "channel": 1, "bandwidth_hz": 20e6,
                           "tx_power_dbm": {"value": 20, "provenance": "declared", "source": "router UI"}}],
        "conditions": [{"id": "c", "doors": {"door-1": door_state}}],
        "criteria": [{"id": "ping", "description": "fixture", "method": "icmp-echo", "direction": "round-trip",
                      "min_packets": 100, "min_delivery_ratio": 0.9, "frozen_on": frozen}],
        "points": points})


def predictions(proj=None, door_state="closed"):
    found, _ = residuals(campaign("probe", "pilot", [-50] * 6, door_state, proj=proj), proj or project())
    return [r.predicted_dbm for r in found]


def test_prediction_matches_an_equivalent_link():
    p = project(door="closed")
    p.devices.append(Device(id="s", name="S", position=Point(x=6, y=0, z=1),
                            radios=[Radio(id="r", protocol="wifi", channel=1, frequency_hz=2.412e9,
                                          bandwidth_hz=20e6)]))
    p.links = [Link(id="l", source_device_id="ap", source_radio_id="r", target_device_id="s", target_radio_id="r")]
    expected = simulate(p).links[0].forward.received_power_dbm
    assert predictions()[1] == pytest.approx(expected)


def test_recorded_door_state_is_used():
    closed, opened = predictions(door_state="closed"), predictions(door_state="open")
    assert opened[1] == pytest.approx(closed[1] + 3)  # the point at x=6 is behind the door
    assert opened[0] == pytest.approx(closed[0])      # the point at x=2 is not


def test_offset_is_fitted_on_calibration_and_judged_on_validation():
    truth = predictions()
    cal = campaign("home-a", "calibration", [t + OFFSET + j for t, j in zip(truth, JITTER)])
    val = campaign("home-b", "validation", [t + OFFSET - j for t, j in zip(truth, JITTER)])
    report = calibrate([(cal, project()), (val, project())])
    assert report.offset_db == pytest.approx(OFFSET + sum(JITTER) / len(JITTER))
    before = next(s for s in report.validation_before if s.group == "all")
    after = next(s for s in report.validation_after if s.group == "all")
    assert before.count == after.count == 6
    assert before.bias_db == pytest.approx(OFFSET - sum(JITTER) / len(JITTER))
    assert abs(after.bias_db) < 0.5 and after.rmse_db < before.rmse_db
    assert all("ganancia de antena" in a for r in report.residuals for a in r.assumptions)


def test_leakage_mismatch_and_synthetic_data_are_refused():
    truth = predictions()
    cal = campaign("home-a", "calibration", truth)
    with pytest.raises(CalibrationError, match="no es una evaluación independiente"):
        calibrate([(cal, project()), (campaign("home-a", "validation", truth), project())])
    with pytest.raises(CalibrationError, match="hash"):
        residuals(cal, project(door="open"))
    template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    with pytest.raises(CalibrationError, match="sintéticos"):
        residuals(MeasurementCampaign.model_validate(template), example("apartment"))


def test_uncomparable_observations_are_skipped_with_reasons():
    found, skipped = residuals(campaign("home-a", "pilot", [-50] * 6, reporting="vendor-scale"), project())
    assert not found and {s.reason for s in skipped} == {"el instrumento no informa en dBm"}
    c = campaign("home-a", "pilot", [-50] * 6)
    point = c.points[0].model_copy(update={"rssi": c.points[0].rssi + [
        c.points[0].rssi[0].model_copy(update={"direction": "device-to-ap", "receiver_instrument_id": "router"})]})
    c = c.model_copy(update={"points": [point]})
    c.instruments[0].rssi_reporting = "dbm"
    found, skipped = residuals(c, project())
    assert [r.direction for r in found] == ["ap-to-device"]
    assert skipped[0].reason == "falta la potencia de transmisión de ese sentido"


def test_without_calibration_points_nothing_is_fitted():
    report = calibrate([(campaign("home-b", "validation", predictions()), project())])
    assert report.offset_db is None and report.validation_after[2].count == 0
    assert report.validation_before[2].count == 6


def test_cli(tmp_path, capsys):
    truth = predictions()
    files = []
    for site, split in (("home-a", "calibration"), ("home-b", "validation")):
        c, p = tmp_path / f"{site}.json", tmp_path / f"{site}-project.json"
        c.write_text(campaign(site, split, [t + OFFSET for t in truth]).model_dump_json(), encoding="utf-8")
        p.write_text(project().model_dump_json(), encoding="utf-8")
        files.append(f"{c}={p}")
    assert main(files) == 0
    assert json.loads(capsys.readouterr().out)["offset_db"] == pytest.approx(OFFSET)
    assert main([files[0], files[0]]) == 2  # the same campaign twice is refused
