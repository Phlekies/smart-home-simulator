"""Generate schemas from the source of truth; --check detects committed contract drift."""

import argparse
import json
from pathlib import Path

from smart_environment.api import app
from smart_environment.measurements import MeasurementCampaign
from smart_environment.models import (
    CoverageMapJob, GenericProfile, PlacementSearchResult, Project, SimulationResult,
)

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
contracts = {"project.schema.json": Project.model_json_schema(mode="serialization"),
             "simulation-result.schema.json": SimulationResult.model_json_schema(mode="serialization"),
             "measurement-campaign.schema.json": MeasurementCampaign.model_json_schema(mode="serialization"),
             "coverage-map.schema.json": CoverageMapJob.model_json_schema(mode="serialization"),
             "placement-search.schema.json": PlacementSearchResult.model_json_schema(mode="serialization"),
             "radio-profile.schema.json": GenericProfile.model_json_schema(mode="serialization"),
             "openapi.json": app.openapi()}
for name, schema in contracts.items():
    path = root / "contracts" / name
    text = json.dumps(schema, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            raise SystemExit(f"Contract drift: regenerate {path}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
print("Contracts checked" if args.check else "Contracts exported")
