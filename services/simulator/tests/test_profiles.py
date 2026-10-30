"""Generic radio profiles (B-106): traceable values, unknowns kept unknown."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from smart_environment.api import app, example
from smart_environment.coverage import compute
from smart_environment.models import CoverageMapRequest, ProfileValue, Radio
from smart_environment.profiles import CATALOG

client = TestClient(app)


def ap_radio(**changes):
    return Radio(**{"id": "ap", "protocol": "wifi", "channel": 6, "frequency_hz": 2.437e9, "bandwidth_hz": 20e6,
                    "tx_power_dbm": 20, "sensitivity_dbm": -90, **changes})


def test_catalog_values_and_provenance():
    by_id = {p.id: p for p in CATALOG}
    assert {k: by_id[k].sensitivity_dbm.value for k in by_id} == {
        "wifi4-ht20-mcs0": -82, "wifi4-ht20-mcs3": -74, "wifi4-ht20-mcs7": -64}
    for profile in CATALOG:
        assert profile.sensitivity_dbm.provenance == "standard-minimum"
        assert "802.11-2020" in profile.sensitivity_dbm.source and "no se ha cotejado" in profile.sensitivity_dbm.source
        assert profile.tx_power_dbm.value is None and profile.tx_power_dbm.provenance == "unknown"
        assert profile.antenna_gain_dbi.provenance == profile.noise_figure_db.provenance == "inferred"
        assert profile.band == "2.4GHz" and profile.bandwidth_hz == 20e6


def test_higher_rates_need_stronger_signals():
    values = [p.sensitivity_dbm.value for p in sorted(CATALOG, key=lambda p: int(p.id.rsplit("mcs", 1)[1]))]
    assert values == sorted(values)


@pytest.mark.parametrize("payload", [{"value": 1}, {"provenance": "declared"}, {"value": 1, "provenance": "unknown"}])
def test_profile_value_requires_matching_provenance(payload):
    with pytest.raises(ValidationError):
        ProfileValue.model_validate(payload)


def test_receiver_profile_follows_the_access_point_channel():
    profile = CATALOG[0].receiver_profile(ap_radio())
    assert (profile.radio.frequency_hz, profile.radio.channel) == (2.437e9, 6)
    assert profile.radio.sensitivity_dbm == -82 and profile.radio.tx_power_dbm is None
    assert "standard-minimum" in profile.evidence and "tx power unknown" in profile.evidence
    with pytest.raises(ValueError):
        CATALOG[0].receiver_profile(ap_radio(frequency_hz=5.2e9, channel=40))
    with pytest.raises(ValueError):
        CATALOG[0].receiver_profile(ap_radio(bandwidth_hz=40e6))


def test_profile_in_a_map_leaves_the_return_path_uncomputed():
    project = example("apartment")
    hub = next(d for d in project.devices if d.role == "controller")
    hub.radios[0] = ap_radio(id=hub.radios[0].id, frequency_hz=hub.radios[0].frequency_hz)
    request = CoverageMapRequest(project=project, access_point_device_id=hub.id,
                                 access_point_radio_id=hub.radios[0].id,
                                 profile=CATALOG[0].receiver_profile(hub.radios[0]),
                                 grid={"width_m": 6, "depth_m": 4, "resolution_m": 1, "height_m": 1.2})
    result = compute(request)
    computed = [i for i, s in enumerate(result.cells.status) if s != "not-computed"]
    assert computed and all(result.cells.status[i] == "partial" for i in computed)
    assert all(result.cells.reverse_dbm[i] is None for i in computed)
    assert all(result.cells.forward_margin_db[i] is not None for i in computed)


def test_api_lists_the_catalog():
    response = client.get("/api/profiles")
    assert response.status_code == 200
    assert [p["id"] for p in response.json()] == [p.id for p in CATALOG]
