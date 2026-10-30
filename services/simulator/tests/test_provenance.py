"""Per-parameter radio provenance (B-113): documented origins, no effect on numbers or hashes."""

import pytest
from pydantic import ValidationError

from smart_environment.engines import input_hash, simulate
from smart_environment.models import Building, Device, Link, Material, Point, Project, Radio
from smart_environment.profiles import CATALOG


def radio(**changes):
    return Radio(**{"id": "r", "protocol": "wifi", "channel": 1, "frequency_hz": 2.412e9, "bandwidth_hz": 20e6,
                    "tx_power_dbm": 20, "sensitivity_dbm": -82, **changes})


def project(sensor_provenance=None):
    return Project(building=Building(materials=[Material(id="m", name="m", loss_db_24ghz=3, loss_db_5ghz=5)]),
                   devices=[Device(id="ap", name="AP", position=Point(x=0, y=0, z=2), radios=[radio()]),
                            Device(id="s", name="S", position=Point(x=8, y=0, z=1),
                                   radios=[radio(provenance=sensor_provenance)])],
                   links=[Link(id="l", source_device_id="ap", source_radio_id="r", target_device_id="s",
                               target_radio_id="r")])


@pytest.mark.parametrize("fields,provenance", [
    ({"tx_power_dbm": 20}, {"tx_power_dbm": {"provenance": "unknown"}}),
    ({"tx_power_dbm": None}, {"tx_power_dbm": {"provenance": "declared", "source": "datasheet"}}),
    ({"sensitivity_dbm": None}, {"sensitivity_dbm": {"provenance": "standard-minimum"}}),
    ({"protocol": "unknown"}, {"protocol": {"provenance": "measured"}}),
    ({}, {"bandwidth_hz": {"provenance": "declared"}}),
])
def test_inconsistent_provenance_is_rejected(fields, provenance):
    with pytest.raises(ValidationError):
        radio(**fields, provenance=provenance)


def test_consistent_provenance_is_accepted_and_optional_in_the_schema():
    r = radio(tx_power_dbm=None, provenance={"tx_power_dbm": {"provenance": "unknown"},
                                              "sensitivity_dbm": {"provenance": "declared", "source": "ficha v2"}})
    assert r.provenance["sensitivity_dbm"].source == "ficha v2"
    for mode in ("validation", "serialization"):
        assert "provenance" not in Radio.model_json_schema(mode=mode).get("required", [])


def test_labels_change_neither_numbers_nor_hash():
    plain = project()
    labelled = project({"sensitivity_dbm": {"provenance": "measured", "source": "banco de pruebas"}})
    assert input_hash(plain) == input_hash(labelled)
    assert simulate(plain).links[0].forward == simulate(labelled).links[0].forward


@pytest.mark.parametrize("origin,fragment", [
    ("standard-minimum", "sensibilidad mínima del estándar"),
    ("inferred", "sensibilidad inferida"),
])
def test_margins_on_unverified_sensitivity_are_flagged(origin, fragment):
    reasons = simulate(project({"sensitivity_dbm": {"provenance": origin}})).links[0].reasons
    assert any(fragment in r and "hacia s" in r for r in reasons)


@pytest.mark.parametrize("origin", [None, "declared", "measured"])
def test_declared_or_measured_sensitivity_adds_no_warning(origin):
    provenance = None if origin is None else {"sensitivity_dbm": {"provenance": origin}}
    assert not any("sensibilidad" in r for r in simulate(project(provenance)).links[0].reasons)


def test_catalogue_profiles_carry_their_provenance():
    profile = CATALOG[0].receiver_profile(radio())
    origins = {k: v.provenance for k, v in profile.radio.provenance.items()}
    assert origins == {"tx_power_dbm": "unknown", "tx_gain_dbi": "inferred", "rx_gain_dbi": "inferred",
                       "sensitivity_dbm": "standard-minimum", "noise_figure_db": "inferred"}
    assert "802.11-2020" in profile.radio.provenance["sensitivity_dbm"].source
