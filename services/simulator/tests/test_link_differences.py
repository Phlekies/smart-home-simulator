"""Exact difference between two project versions (B-123): the terms add up, nothing is attributed by guess."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from smart_environment.api import app
from smart_environment.differences import DifferenceRequest, compare
from smart_environment.engines import simulate
from smart_environment.models import (
    Building, Device, Link, Material, MaterialUncertainty, Point, Project, Radio, Wall,
)

client = TestClient(app)


def radio(**changes):
    return Radio(**{"id": "r", "protocol": "wifi", "channel": 1, "frequency_hz": 2.412e9, "bandwidth_hz": 20e6,
                    "tx_power_dbm": 20, "sensitivity_dbm": -85, **changes})


def home(sensor=Point(x=8, y=2, z=1), ap_radio=None, sensor_radio=None):
    """AP at x=1. Brick wall at x=4 (y 0–4); an unknown door and an uncertain partition at y=6."""
    materials = [Material(id="brick", name="Brick", loss_db_24ghz=6, loss_db_5ghz=9, extra_loss_db_per_cm=0.1),
                 Material(id="wood", name="Wood", loss_db_24ghz=3, loss_db_5ghz=5),
                 Material(id="partition", name="Tabique", loss_db_24ghz=3, loss_db_5ghz=5,
                          uncertainty=MaterialUncertainty(loss_db_24ghz_low=1, loss_db_24ghz_high=8,
                                                          loss_db_5ghz_low=2, loss_db_5ghz_high=12,
                                                          source="Composición desconocida"))]
    walls = [Wall(id="brick-wall", start=Point(x=4, y=0), end=Point(x=4, y=4), material_id="brick"),
             Wall(id="door", start=Point(x=0, y=6), end=Point(x=3, y=6), material_id="wood", door="unknown"),
             Wall(id="partition", start=Point(x=3, y=6), end=Point(x=10, y=6), material_id="partition")]
    devices = [Device(id="ap", name="AP", position=Point(x=1, y=2, z=1), radios=[ap_radio or radio()]),
               Device(id="s", name="Sensor", position=sensor, radios=[sensor_radio or radio()])]
    return Project(building=Building(width_m=12, depth_m=10, materials=materials, walls=walls), devices=devices,
                   links=[Link(id="l", source_device_id="s", source_radio_id="r", target_device_id="ap",
                               target_radio_id="r")])


def difference(base, alternative):
    return compare(DifferenceRequest(base=base, alternative=alternative)).links[0]


def test_terms_add_up_to_the_change_and_match_simulations():
    base, alternative = home(), home(sensor=Point(x=3, y=3, z=1))
    result = difference(base, alternative)
    simulated_base, simulated_alternative = simulate(base).links[0], simulate(alternative).links[0]
    for side in ("forward", "reverse"):
        d = getattr(result, side)
        assert d.base_dbm == pytest.approx(getattr(simulated_base, side).received_power_dbm, abs=1e-12)
        assert d.alternative_dbm == pytest.approx(getattr(simulated_alternative, side).received_power_dbm, abs=1e-12)
        assert sum(t.change_db for t in d.terms) == pytest.approx(d.change_db, abs=1e-9)
    assert result.limiting_change_db == pytest.approx(result.alternative_limiting_margin_db
                                                      - result.base_limiting_margin_db)


def test_moving_out_from_behind_a_wall_is_explained_by_distance_and_that_wall():
    result = difference(home(), home(sensor=Point(x=3, y=3, z=1)))
    terms = {t.term: t.change_db for t in result.forward.terms}
    assert terms["walls"] == pytest.approx(6 + 12 * 0.1) and terms["path_loss"] > 0
    assert all(terms[k] == 0 for k in ("tx_power", "system_gain", "extra_loss", "polarization"))
    assert [(w.wall_id, w.change) for w in result.forward.walls] == [("brick-wall", "no-longer-crossed")]
    assert result.forward.walls[0].change_db == pytest.approx(terms["walls"])


def test_a_radio_change_only_moves_its_own_term():
    result = difference(home(), home(ap_radio=radio(tx_power_dbm=14)))
    reverse = {t.term: t.change_db for t in result.reverse.terms}  # AP → sensor
    assert reverse["tx_power"] == pytest.approx(-6) and result.reverse.change_db == pytest.approx(-6)
    assert result.forward.change_db == 0 and result.forward.walls == []
    directional = difference(home(), home(sensor_radio=radio(antenna="directional", beamwidth_deg=60,
                                                              orientation_deg=180, tx_gain_dbi=5, rx_gain_dbi=5)))
    forward = {t.term: t.change_db for t in directional.forward.terms}
    assert forward["tx_antenna_gain"] != 0 and forward["path_loss"] == 0 and forward["walls"] == 0


def test_residual_risks_name_the_hypotheses_of_the_new_path():
    through_door = difference(home(), home(sensor=Point(x=2, y=8, z=1))).residual_risks
    assert any("puerta door" in r and "desconocido" in r for r in through_door)
    through_partition = difference(home(), home(sensor=Point(x=5, y=8, z=1))).residual_risks
    assert any("material de partition es incierto (1–8 dB" in r for r in through_partition)
    assert not any("brick-wall" in r or "puerta" in r for r in through_partition)
    assert difference(home(), home()).residual_risks == [], "the base path crosses only a known brick wall"


def test_missing_power_is_reported_not_filled():
    result = difference(home(), home(sensor_radio=radio(tx_power_dbm=None)))
    assert result.forward.terms == [] and result.forward.change_db is None
    assert "la alternativa" in result.forward.reason and result.limiting_change_db is None
    assert any("Sentido ida" in r for r in result.residual_risks)


def test_links_with_other_ends_are_not_compared():
    base, alternative = home(), home()
    alternative.links[0] = Link(id="l", source_device_id="ap", source_radio_id="r", target_device_id="s",
                                target_radio_id="r")
    alternative.links.append(Link(id="extra", source_device_id="s", source_radio_id="r", target_device_id="ap",
                                  target_radio_id="r"))
    result = compare(DifferenceRequest(base=base, alternative=alternative))
    assert result.links == [], "reversed ends are another link; extra exists in one version only"
    assert result.unmatched_link_ids == ["extra", "l"]
    with pytest.raises(ValidationError, match="share no link"):
        DifferenceRequest(base=base, alternative=home().model_copy(update={"links": []}))


def test_api_compares_and_refuses_other_engines():
    body = {"base": home().model_dump(mode="json"), "alternative": home(sensor=Point(x=3, y=3, z=1)).model_dump(mode="json")}
    response = client.post("/api/link-differences", json=body)
    assert response.status_code == 200 and response.json()["links"][0]["link_id"] == "l"
    assert client.post("/api/link-differences", json={**body, "engine": "sionna-rt"}).status_code == 501
