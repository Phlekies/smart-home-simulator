"""The references are checked with identities that do not reuse their own formulas."""

import cmath
import json
import math

import pytest

from smart_environment.engines import MODELLED_INTERACTIONS, engine_capabilities, input_hash, simulate
from smart_environment.models import Point, Project, Wall
from smart_environment.references import (
    ITU_P2040_3, LEGACY_24GHZ, ItuMaterial, compare, free_space_loss_db, fresnel_zone_radius_m,
    interface_reflection, log_distance_loss_db, main, reference_cases, slab_coefficients, slab_loss_db,
    specular_reflection, two_ray_received_dbm, wavelength_m,
)

F = 2.412e9
LOSSLESS = ItuMaterial("lossless", "Lossless dielectric", 4.0, 0, 0, 0, 0.001, 100)


@pytest.fixture(scope="module")
def results():
    return {r.case_id: r for r in compare(reference_cases(), simulate, MODELLED_INTERACTIONS)}


def test_friis_matches_the_classic_db_form():
    # 32.45 dB is the rounded constant of the MHz/km expression (exact value 32.4478 dB).
    classic = 32.45 + 20 * math.log10(F / 1e6) + 20 * math.log10(10 / 1000)
    assert free_space_loss_db(10, F) == pytest.approx(classic, abs=0.01)
    assert free_space_loss_db(wavelength_m(F) / (4 * math.pi), F) == pytest.approx(0, abs=1e-12)
    assert free_space_loss_db(20, F) - free_space_loss_db(10, F) == pytest.approx(20 * math.log10(2))
    with pytest.raises(ValueError):
        free_space_loss_db(0, F)


def test_log_distance_reduces_to_friis_with_exponent_two():
    assert log_distance_loss_db(17, F, 2.0) == pytest.approx(free_space_loss_db(17, F))
    assert log_distance_loss_db(10, F, 3.0) - free_space_loss_db(1, F) == pytest.approx(30)


def test_fresnel_zone_radius_at_midpoint():
    assert fresnel_zone_radius_m(5, 5, F) == pytest.approx(math.sqrt(wavelength_m(F) * 2.5))


def test_itu_permittivity_matches_the_17_98_shortcut():
    eta = ITU_P2040_3["concrete"].relative_permittivity(F)
    sigma = 0.0462 * 2.412 ** 0.7822
    assert eta.real == pytest.approx(5.24)
    assert -eta.imag == pytest.approx(17.98 * sigma / 2.412, rel=1e-3)


@pytest.mark.parametrize("material,frequency", [("floorboard", F), ("brick", 12e9), ("plywood", 45e9)])
def test_tabulated_frequency_range_is_enforced(material, frequency):
    with pytest.raises(ValueError):
        ITU_P2040_3[material].relative_permittivity(frequency)


def test_fresnel_normal_incidence_and_tm_convention():
    eta = ITU_P2040_3["glass"].relative_permittivity(F)
    expected = (1 - cmath.sqrt(eta)) / (1 + cmath.sqrt(eta))
    assert interface_reflection(eta, 0, "TE") == pytest.approx(expected)
    assert interface_reflection(eta, 0, "TM") == pytest.approx(-expected)


def test_brewster_angle_cancels_tm_reflection_of_a_lossless_dielectric():
    eta = LOSSLESS.relative_permittivity(F)
    brewster = math.degrees(math.atan(math.sqrt(4.0)))
    assert abs(interface_reflection(eta, brewster, "TM")) < 1e-12
    assert abs(interface_reflection(eta, brewster, "TE")) > 0.5


def test_grazing_incidence_reflects_almost_everything():
    eta = ITU_P2040_3["concrete"].relative_permittivity(F)
    assert abs(interface_reflection(eta, 89.99, "TE")) > 0.999
    with pytest.raises(ValueError):
        interface_reflection(eta, 90, "TE")


@pytest.mark.parametrize("thickness", [0.003, 0.05, 0.137])
@pytest.mark.parametrize("angle", [0, 35, 70])
@pytest.mark.parametrize("polarization", ["TE", "TM"])
def test_lossless_slab_conserves_energy(thickness, angle, polarization):
    r, t = slab_coefficients(LOSSLESS, thickness, F, angle, polarization)
    assert abs(r) ** 2 + abs(t) ** 2 == pytest.approx(1)


def test_lossy_slab_absorbs_energy():
    r, t = slab_coefficients(ITU_P2040_3["concrete"], 0.1, F)
    assert abs(r) ** 2 + abs(t) ** 2 < 0.9


def test_zero_thickness_and_half_wave_slabs_are_transparent():
    r, t = slab_coefficients(ITU_P2040_3["concrete"], 0, F)
    assert r == pytest.approx(0) and t == pytest.approx(1)
    half_wave = wavelength_m(F) / (2 * math.sqrt(4.0))
    assert slab_loss_db(LOSSLESS, half_wave, F) == pytest.approx(0, abs=1e-9)


def test_thick_slab_slope_equals_bulk_attenuation():
    concrete = ITU_P2040_3["concrete"]
    alpha = 2 * math.pi / wavelength_m(F) * abs(cmath.sqrt(concrete.relative_permittivity(F)).imag)
    slope = slab_loss_db(concrete, 0.40, F) - slab_loss_db(concrete, 0.30, F)
    assert slope == pytest.approx(20 * math.log10(math.e) * alpha * 0.10, abs=0.1)


def test_metal_slab_is_reported_as_opaque_not_as_a_number():
    with pytest.raises(ValueError):
        slab_loss_db(ITU_P2040_3["metal"], 0.001, F)


def test_image_method_geometry():
    wall = Wall(id="w", start=Point(x=-20, y=0), end=Point(x=30, y=0), material_id="m")
    bounce = specular_reflection(Point(x=0, y=1, z=1.2), Point(x=10, y=1, z=1.2), wall)
    assert bounce.point == pytest.approx((5, 0, 1.2))
    assert bounce.path_length_m == pytest.approx(math.hypot(10, 2))
    assert bounce.incidence_deg == pytest.approx(math.degrees(math.atan(5)))
    short = Wall(id="w", start=Point(x=-1, y=0), end=Point(x=2, y=0), material_id="m")
    assert specular_reflection(Point(x=0, y=1, z=1.2), Point(x=10, y=1, z=1.2), short) is None
    assert specular_reflection(Point(x=0, y=1, z=1.2), Point(x=10, y=-1, z=1.2), wall) is None
    low = Wall(id="w", start=Point(x=-20, y=0), end=Point(x=30, y=0), height_m=1, material_id="m")
    assert specular_reflection(Point(x=0, y=1, z=1.2), Point(x=10, y=1, z=1.2), low) is None


def test_two_ray_limits():
    lam = wavelength_m(F)
    assert two_ray_received_dbm(20, F, 10, 12, 0) == pytest.approx(20 - free_space_loss_db(10, F))
    # Γ = −1 and half a wavelength of extra path: the two rays add in phase.
    constructive = two_ray_received_dbm(20, F, 10, 10 + lam / 2, -1)
    amplitude = lam / (4 * math.pi) * (1 / 10 + 1 / (10 + lam / 2))
    assert constructive == pytest.approx(20 + 20 * math.log10(amplitude))
    coherent = two_ray_received_dbm(20, F, 10, 10.3, 0.6j)
    incoherent = two_ray_received_dbm(20, F, 10, 10.3, 0.6j, coherent=False)
    assert incoherent > 20 - free_space_loss_db(10, F)
    bounds = [20 + 20 * math.log10(lam / (4 * math.pi) * abs(1 / 10 + s * 0.6 / 10.3)) for s in (-1, 1)]
    assert bounds[0] <= coherent <= bounds[1]


def test_cases_are_valid_reproducible_synthetic_projects():
    cases = reference_cases()
    assert len({c.id for c in cases}) == len(cases)
    for case in cases:
        assert Project.model_validate_json(case.project.model_dump_json()) == case.project
        assert any("sintético" in note for note in case.project.migration_notes)
        assert case.tolerance_db > 0 and case.formula and case.source
        for material_id, itu_id in case.itu_materials.items():
            assert material_id in {m.id for m in case.project.building.materials} and itu_id in ITU_P2040_3
    assert [c.expected_dbm for c in cases] == [c.expected_dbm for c in reference_cases()]


def test_quick_estimate_agrees_with_free_space_and_its_own_model(results):
    for case in reference_cases():
        if case.interaction == "free-space" or case.kind == "model-consistency":
            assert results[case.id].verdict == "agrees"
            assert abs(results[case.id].delta_db) < 1e-9


def test_quick_estimate_wall_deviation_is_legacy_minus_slab(results):
    walls = [c for c in reference_cases() if c.interaction == "wall-penetration" and c.kind == "physical-reference"]
    assert walls
    for case in walls:
        material = case.project.building.materials[0]
        name, base, per_cm = LEGACY_24GHZ[material.id]
        assert (material.name, material.loss_db_24ghz, material.extra_loss_db_per_cm) == (name, base, per_cm)
        assert results[case.id].verdict == "deviates"
        assert results[case.id].delta_db == pytest.approx(case.components["slab_loss_db"]
                                                          - case.components["legacy_loss_db"])


def test_reflection_is_reported_as_not_modelled(results):
    for case_id in ("REFL-grazing", "REFL-steep"):
        assert results[case_id].verdict == "not-modelled"
        assert "direct_only_dbm" in results[case_id].note
    assert results["REFL-miss"].verdict == "agrees" and "trivial" in results["REFL-miss"].note


def test_engine_modelling_an_interaction_badly_is_flagged():
    def biased(project):
        result = simulate(project)
        if result.links[0].forward:
            result.links[0].forward.received_power_dbm += 0.5
        return result

    outcome = compare(reference_cases()[:1], biased, ["free-space"])[0]
    assert outcome.verdict == "deviates" and outcome.delta_db == pytest.approx(0.5)


def test_missing_direction_is_no_result():
    case = reference_cases()[0]
    case.project.devices[0].radios[0].tx_power_dbm = None
    assert compare([case], simulate, MODELLED_INTERACTIONS)[0].verdict == "no-result"


def test_capabilities_declare_interactions_and_hash_is_shared():
    quick = next(e for e in engine_capabilities() if e["id"] == "quick-estimate")
    assert quick["interactions"] == list(MODELLED_INTERACTIONS)
    project = reference_cases()[0].project
    assert simulate(project).input_hash == input_hash(project)


def test_cli_outputs_table_and_json(capsys):
    main([])
    assert "| FS-1m |" in capsys.readouterr().out
    main(["--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["engine"] == "quick-estimate" and len(data["results"]) == len(reference_cases())
