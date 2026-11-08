"""Directional antennas and polarization against the Java engine (B-121); no JDK needed.

The Java values were produced by ``benchmarks/java_parity.py`` and stored as evidence; these
tests recompute the Python side, so any drift of the estimator or of the import shows up here.
"""

import json
import sys
from pathlib import Path

import pytest

from smart_environment.legacy import import_project

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = json.loads((ROOT / "docs" / "simulation" / "evidence" / "java-parity.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(ROOT / "services" / "simulator" / "benchmarks"))
import java_parity  # noqa: E402

CASES = {case["id"]: case for case in EVIDENCE["parity_cases"]}
PROBES = [(row["case"], row["probe"], row["java_dbm"]) for row in EVIDENCE["parity"]]


@pytest.mark.parametrize("case_id, probe_id, java_dbm", PROBES)
def test_direct_path_matches_java(case_id, probe_id, java_dbm):
    case = CASES[case_id]
    probe = next(p for p in case["probes"] if p["id"] == probe_id)
    assert java_parity.python_dbm(case, probe) == pytest.approx(java_dbm, abs=EVIDENCE["tolerance_db"])


def test_evidence_covers_beams_side_lobes_polarization_walls_and_5ghz():
    ids = set(CASES)
    assert {f"pattern-{k}" for k in range(4)} <= ids and "walls-5200MHz" in ids
    assert {c["receiver_polarization_deg"] for c in CASES.values() if c["id"].startswith("polarization")} == {0, 90}
    # Inside and outside the beam, so both the cos^n lobe and the side-lobe floor are exercised.
    spread = [r["java_dbm"] for r in EVIDENCE["parity"] if r["case"] == "pattern-0"]
    assert max(spread) - min(spread) > 18
    assert EVIDENCE["parity_summary"]["max_abs_difference_db"] <= EVIDENCE["tolerance_db"]


@pytest.mark.parametrize("name", java_parity.EXAMPLES)
def test_imported_examples_still_give_the_recorded_direct_power(name):
    recorded = {r["sensor_id"]: r["python_imported_dbm"] for r in EVIDENCE["contrast"] if r["example"] == name}
    assert java_parity.imported_forward_dbm(name) == pytest.approx(recorded, abs=1e-9)
    for row in (r for r in EVIDENCE["contrast"] if r["example"] == name and not r["java_direct_at_floor"]):
        assert row["python_same_height_dbm"] == pytest.approx(row["java_direct_dbm"], abs=EVIDENCE["tolerance_db"])


def test_import_keeps_every_antenna_and_polarization_field():
    data = json.loads((ROOT / "examples" / "smart-apartment.shsim.json").read_text(encoding="utf-8"))
    devices = {d.id: d for d in import_project(data).devices}
    directional = [s for s in data["sensors"] if s["antenna"] == "DIRECTIONAL"]
    assert directional, "the apartment example has a directional sensor"
    for sensor in data["sensors"]:
        radio = devices[sensor["id"]].radios[0]
        assert (radio.antenna, radio.orientation_deg, radio.beamwidth_deg, radio.pattern_sharpness,
                radio.side_lobe_attenuation_db, radio.polarization_deg, radio.tx_gain_dbi) == (
            sensor["antenna"].lower(), sensor["orientationDeg"], sensor["beamwidthDeg"], sensor["patternSharpness"],
            sensor["sideLobeAttenuationDb"], sensor["polarizationDeg"], sensor["txGainDb"])
    hub = devices[data["hub"]["id"]].radios[0]
    assert (hub.polarization_deg, hub.rx_gain_dbi) == (data["hub"]["polarizationDeg"], data["hub"]["receiverGainDb"])


def test_contrast_never_states_a_difference_for_culled_links():
    for row in EVIDENCE["contrast"]:
        for mode in ("rays", "waves"):
            if row[f"java_{mode}_paths"] == 0 or row["java_direct_at_floor"]:
                assert row[f"{mode}_minus_direct_db"] is None
