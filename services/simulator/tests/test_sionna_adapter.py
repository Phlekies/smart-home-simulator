"""Translation rules of the Sionna RT adapter; they run without Sionna installed."""

import sys

import pytest

from smart_environment.models import Point, Radio, Wall
from smart_environment.references import reference_cases
from smart_environment.sionna_adapter import (
    LEGACY_ITU_TYPES, EngineUnavailable, SionnaRT, UnsupportedScene, obj_text, scene_spec,
    unsupported_radio_reasons, wall_surface,
)


def radio(**changes):
    return Radio(**{"id": "r", "protocol": "wifi", "channel": 1, "frequency_hz": 2.412e9, "bandwidth_hz": 20e6,
                    "tx_power_dbm": 20, **changes})


def test_wall_becomes_a_centre_plane_rectangle():
    wall = Wall(id="w", start=Point(x=1, y=2, z=0.5), end=Point(x=4, y=6, z=0.5), height_m=2,
                thickness_m=0.3, material_id="m")
    vertices, faces = wall_surface(wall)
    assert vertices == ((1, 2, 0.5), (4, 6, 0.5), (4, 6, 2.5), (1, 2, 2.5))
    assert faces == ((0, 1, 2), (0, 2, 3))
    text = obj_text(vertices, faces)
    assert text.count("\nv ") + text.startswith("v ") == 4 and text.endswith("f 1 3 4\n")


def test_reference_case_materials_are_given_and_legacy_ids_are_inferred():
    case = next(c for c in reference_cases() if c.id == "WALL-fit-series")
    spec = scene_spec(case.project, 2.412e9, case.itu_materials)
    assert [s.itu_type for s in spec.surfaces] == ["concrete", "plasterboard"]
    assert [s.thickness_m for s in spec.surfaces] == [0.20, 0.0125]
    assert all("given" in origin for origin in spec.material_provenance.values())
    legacy = next(c for c in reference_cases() if c.id == "WALL-drywall-12.5mm")
    spec = scene_spec(legacy.project, 2.412e9)
    assert spec.material_provenance == {"drywall": "plasterboard (inferred-from-legacy-id)"}
    assert set(LEGACY_ITU_TYPES) == {"concrete", "brick", "drywall", "glass", "wood", "metal-door"}


def test_unknown_material_is_rejected_instead_of_defaulted():
    case = next(c for c in reference_cases() if c.id == "WALL-fit-single")
    with pytest.raises(UnsupportedScene):
        scene_spec(case.project, 2.412e9)


@pytest.mark.parametrize("tx,rx,fragment", [
    (radio(antenna="directional", beamwidth_deg=90), radio(), "direccional"),
    (radio(polarization_deg=90), radio(), "Polarizaciones"),
    (radio(tx_power_dbm=None), radio(), "potencia"),
    (radio(), radio(frequency_hz=2.462e9, channel=11), "frecuencia"),
])
def test_untranslated_radio_features_are_reported(tx, rx, fragment):
    assert any(fragment in reason for reason in unsupported_radio_reasons(tx, rx))


def test_matching_omnidirectional_radios_are_supported():
    assert unsupported_radio_reasons(radio(), radio(tx_gain_dbi=2)) == []


def test_missing_sionna_raises_instead_of_falling_back(monkeypatch):
    monkeypatch.setitem(sys.modules, "sionna", None)
    monkeypatch.setitem(sys.modules, "sionna.rt", None)
    with pytest.raises(EngineUnavailable, match="Sionna RT no se puede cargar"):
        SionnaRT()


def test_coherent_sum_applies_the_carrier_phase_of_each_delay():
    import math

    from smart_environment.sionna_adapter import combine_paths

    f, c = 2.412e9, 299_792_458
    single = combine_paths([1e-3], [10 / c], f, 20e6)
    assert single == pytest.approx((1e-6, 1e-6, 1e-6))
    # Equal amplitudes, extra path of half a wavelength: cancel at the carrier frequency.
    half_wave = (c / f) / 2 / c
    coherent, incoherent, _ = combine_paths([1e-3, 1e-3], [10 / c, 10 / c + half_wave], f, 20e6)
    assert coherent == pytest.approx(0, abs=1e-15) and incoherent == pytest.approx(2e-6)
    # A long delay difference decorrelates across 20 MHz: the wideband mean tends to the power sum.
    long_delay = 965 / f + half_wave  # ≈ 8 cycles of phase slope across the 20 MHz channel
    coherent, incoherent, wideband = combine_paths([1e-3, 1e-3], [10 / c, 10 / c + long_delay], f, 20e6, 256)
    assert coherent == pytest.approx(0, abs=1e-12)
    assert wideband == pytest.approx(incoherent, rel=0.05)
    assert combine_paths([], [], f, 20e6) == (0.0, 0.0, 0.0)
    assert math.isclose(sum(combine_paths([2e-3], [0.0], f, 20e6)) / 3, 4e-6)
