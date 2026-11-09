"""Build the synthetic demo project used for screenshots and the README (no real home data).

    python scripts/make_demo_project.py [--output docs/images/demo-apartment.shsim.json]

Starts from the Java apartment example and gives every radio Wi-Fi 2.4 GHz values, so both link
directions can be computed. One interior door has an unknown state and the drywall a declared
uncertainty range, so the scenario view has hypotheses to show; a low-power sensor fails only in one
direction and a camera's margin depends on those hypotheses. Every value is illustrative.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "simulator" / "src"))

from smart_environment.legacy import import_project  # noqa: E402
from smart_environment.models import DataConnection, MaterialUncertainty, Project, RadioValueSource  # noqa: E402

DEMO_NOTE = "Proyecto sintético de demostración: valores ilustrativos, no medidos ni de un producto real."


def demo() -> Project:
    data = json.loads((ROOT / "examples" / "smart-apartment.shsim.json").read_text(encoding="utf-8"))
    project = import_project(data)
    project.name = "Piso de demostración · Wi-Fi 2.4 GHz"
    project.legacy_source = None
    project.migration_notes = [DEMO_NOTE]
    declared = RadioValueSource(provenance="declared", source="Valor ilustrativo de la demostración")
    for device in project.devices:
        hub = device.role == "controller"
        if hub:
            device.name, device.role = "Router Wi-Fi", "access-point"
            device.data_connection = DataConnection(kind="gateway", note="Router del operador (ilustrativo)")
        for radio in device.radios:
            radio.protocol, radio.channel, radio.frequency_hz = "wifi", 6, 2.437e9
            radio.tx_power_dbm = 20.0 if hub else 10.0
            radio.sensitivity_dbm = -90.0 if hub else -82.0
            radio.provenance = {"tx_power_dbm": declared, "sensitivity_dbm": declared}
        if device.name == "Security camera":
            # Video needs a high rate: the HT20 MCS7 minimum leaves little margin, so hypotheses matter.
            device.radios[0].sensitivity_dbm = -64.0
            device.radios[0].provenance["sensitivity_dbm"] = RadioValueSource(
                provenance="standard-minimum", source="IEEE 802.11 HT20 MCS7 (ilustrativo)")
        if device.name == "Window sensor":
            # A low-power battery sensor: the router hears it worse than it hears the router.
            device.radios[0].tx_power_dbm = -20.0
    for material in project.building.materials:
        if material.id == "drywall":
            material.uncertainty = MaterialUncertainty(loss_db_24ghz_low=2, loss_db_24ghz_high=7, loss_db_5ghz_low=3,
                                                       loss_db_5ghz_high=10, source="Composición del tabique desconocida (ilustrativo)")
    doors = [wall for wall in project.building.walls if wall.material_id == "wood"]
    if doors:
        doors[0].door = "unknown"
    return Project.model_validate(project.model_dump())


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "images" / "demo-apartment.shsim.json")
    args = parser.parse_args(argv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(demo().model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Demo project: {args.output}")


if __name__ == "__main__":
    main()
