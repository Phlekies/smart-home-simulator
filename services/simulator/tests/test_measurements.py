"""Measurement-campaign format: provenance, partitions and absence of invented results.

Values in these tests are synthetic fixtures for the validators, not measurements.
"""

import json
from datetime import date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from smart_environment.api import example
from smart_environment.engines import input_hash
from smart_environment.measurements import (
    DeliveryTest, FailureCriterion, MeasurementCampaign, ParameterValue, RssiObservation, delivery_outcome,
    partition_issues, project_issues, summarize,
)

TEMPLATE = Path(__file__).resolve().parents[1] / "examples" / "measurement-campaign.template.json"


def campaign(**changes):
    data = {
        "id": "c1", "site_id": "home-a", "split": "pilot", "synthetic": False, "purpose": "Validator fixture",
        "project": {"name": "Fixture", "input_hash": "0" * 64},
        "collected_from": "2026-11-02", "collected_to": "2026-11-03",
        "instruments": [{"id": "ap", "kind": "access-point"}, {"id": "dev", "kind": "same-model-as-candidate",
                                                               "rssi_reporting": "dbm"}],
        "access_points": [{"id": "ap-1", "project_device_id": "H1", "project_radio_id": "radio-1",
                           "instrument_id": "ap", "frequency_hz": 2.412e9, "channel": 1, "bandwidth_hz": 20e6,
                           "tx_power_dbm": {"value": 20, "provenance": "declared", "source": "router UI"}}],
        "conditions": [{"id": "closed", "doors": {}}],
        "criteria": [{"id": "ping", "description": "Fixture criterion", "method": "icmp-echo",
                      "direction": "round-trip", "min_packets": 100, "min_delivery_ratio": 0.9,
                      "frozen_on": "2026-11-01"}],
        "points": [{"id": "p1", "status": "measured", "position": {"x": 5, "y": 4, "z": 1.2},
                    "device_instrument_id": "dev", "access_point_id": "ap-1", "conditions_id": "closed",
                    "measured_at": "2026-11-02T10:00:00",
                    "rssi": [{"direction": "ap-to-device", "receiver_instrument_id": "dev",
                              "samples_dbm": [-61, -63, -60]},
                             {"direction": "device-to-ap", "receiver_instrument_id": "ap", "samples_dbm": [-70]}],
                    "delivery": [{"criterion_id": "ping", "method": "icmp-echo", "direction": "round-trip",
                                  "payload_bytes": 64, "interval_s": 0.2, "sent": 100, "received": 97}]}],
    }
    data.update(changes)
    return data


def test_valid_campaign_round_trips():
    parsed = MeasurementCampaign.model_validate(campaign())
    assert MeasurementCampaign.model_validate_json(parsed.model_dump_json()) == parsed


def test_template_is_a_synthetic_plan_of_the_apartment_example():
    template = MeasurementCampaign.model_validate(json.loads(TEMPLATE.read_text(encoding="utf-8")))
    assert template.synthetic and template.split == "format-example"
    assert all(p.status == "planned" and not p.rssi and not p.delivery for p in template.points)
    assert {p.position.z for p in template.points} == {0.3, 1.2, 2.2}
    assert project_issues(template, example("apartment")) == []
    assert summarize(template) == []


@pytest.mark.parametrize("payload", [{"value": 20}, {"provenance": "measured"}, {"value": 1, "provenance": "unknown"}])
def test_parameter_value_requires_provenance_matching_presence(payload):
    with pytest.raises(ValidationError):
        ParameterValue.model_validate(payload)
    assert ParameterValue().value is None and ParameterValue().provenance == "unknown"


def mutate(path_change):
    data = campaign()
    path_change(data)
    return data


@pytest.mark.parametrize("change", [
    lambda d: d.update(synthetic=True),
    lambda d: d.update(split="format-example"),
    lambda d: d["points"][0].update(status="planned"),
    lambda d: d["points"][0].update(rssi=[], delivery=[]),
    lambda d: d["points"][0].update(measured_at=None),
    lambda d: d["points"][0].update(status="excluded"),
    lambda d: d["points"][0].update(measured_at="2026-11-05T10:00:00"),
    lambda d: d["points"][0].update(device_instrument_id="missing"),
    lambda d: d["points"][0]["rssi"][0].update(receiver_instrument_id="missing"),
    lambda d: d["points"][0]["rssi"][0].update(samples_dbm=[]),
    lambda d: d["points"][0]["rssi"][0].update(samples_dbm=[12]),
    lambda d: d["points"][0]["delivery"][0].update(received=101),
    lambda d: d["points"][0]["delivery"][0].update(criterion_id="missing"),
    lambda d: d["access_points"][0].update(instrument_id="missing"),
    lambda d: d["instruments"].append({"id": "ap", "kind": "phone"}),
    lambda d: d.update(collected_from=None, collected_to=None),
    lambda d: d.update(collected_to="2026-11-01"),
    lambda d: d["project"].update(input_hash="not-a-hash"),
    lambda d: d.update(split="validation", criteria=[{**d["criteria"][0], "frozen_on": None}]),
    lambda d: d.update(split="validation", criteria=[{**d["criteria"][0], "frozen_on": "2026-11-03"}]),
    lambda d: d.update(unexpected=True),
])
def test_campaign_rejects_inconsistent_or_invented_data(change):
    with pytest.raises(ValidationError):
        MeasurementCampaign.model_validate(mutate(change))


def test_validation_with_frozen_criterion_is_accepted():
    MeasurementCampaign.model_validate(campaign(split="validation"))


def test_excluded_point_keeps_its_reason():
    data = mutate(lambda d: d["points"][0].update(status="excluded", exclusion_reason="Router rebooted"))
    assert MeasurementCampaign.model_validate(data).points[0].exclusion_reason == "Router rebooted"


def test_delivery_outcome_is_derived_from_raw_counts():
    criterion = FailureCriterion(id="c", description="d", method="icmp-echo", direction="round-trip",
                                 min_packets=100, min_delivery_ratio=0.95, frozen_on=date(2026, 11, 1))

    def test(**changes):
        return DeliveryTest(**{"criterion_id": "c", "method": "icmp-echo", "direction": "round-trip",
                               "payload_bytes": 64, "interval_s": 0.2, "sent": 100, "received": 95, **changes})

    assert delivery_outcome(test(), criterion) == "pass"
    assert delivery_outcome(test(received=94), criterion) == "fail"
    assert delivery_outcome(test(sent=50, received=50), criterion) == "inconclusive"
    assert delivery_outcome(test(direction="ap-to-device"), criterion) == "inconclusive"
    assert "outcome" not in DeliveryTest.model_fields


def test_summary_reports_only_what_was_measured():
    row = summarize(MeasurementCampaign.model_validate(campaign()))[0]
    assert row["rssi"]["ap-to-device"] == {"samples": 3, "median_dbm": -61, "min_dbm": -63, "max_dbm": -60}
    assert row["rssi"]["device-to-ap"]["samples"] == 1
    assert row["delivery"][0]["outcome"] == "pass"
    assert "predicted" not in json.dumps(row)


def test_project_mismatches_are_reported():
    project = example("apartment")
    data = campaign(project={"name": project.name, "input_hash": input_hash(project)})
    assert project_issues(MeasurementCampaign.model_validate(data), project) == []
    data["access_points"][0]["project_device_id"] = "missing"
    data["conditions"][0]["doors"] = {"door-x": "open"}
    issues = project_issues(MeasurementCampaign.model_validate(data), project)
    assert len(issues) == 2
    project.devices[0].position.x += 0.5
    assert any("hash" in issue for issue in project_issues(MeasurementCampaign.model_validate(campaign()), project))


def test_partition_is_checked_per_home():
    base = MeasurementCampaign.model_validate(campaign())
    calibration = base.model_copy(update={"id": "cal", "split": "calibration"})
    validation = base.model_copy(update={"id": "val", "split": "validation"})
    other_home = validation.model_copy(update={"site_id": "home-b"})
    assert partition_issues([calibration, other_home]) == []
    assert len(partition_issues([calibration, validation])) == 1
    assert len(partition_issues([base, other_home, other_home])) == 1
    assert any("piloto" in issue for issue in partition_issues([base, validation]))


def test_rssi_observation_alone_needs_dbm_values():
    RssiObservation(direction="ap-to-device", receiver_instrument_id="x", samples_dbm=[-90.5])
    with pytest.raises(ValidationError):
        RssiObservation(direction="ap-to-device", receiver_instrument_id="x", samples_dbm=[float("nan")])


def test_point_timestamp_is_a_datetime():
    parsed = MeasurementCampaign.model_validate(campaign())
    assert parsed.points[0].measured_at == datetime(2026, 11, 2, 10)
