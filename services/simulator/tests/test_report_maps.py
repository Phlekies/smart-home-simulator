"""Coverage maps attached to the installation report (B-120): same numbers as the map API, no verdict."""

import statistics

import pytest
from fastapi.testclient import TestClient

from smart_environment.api import app
from smart_environment.coverage import MAX_WORK, compute
from smart_environment.models import CoverageMapRequest, Point, Radio, ReceiverProfile, Wall
from smart_environment.report import ReportRequest, build_report, to_markdown

from test_scenarios import project as scenario_project

client = TestClient(app)


def map_parameters(filler_walls=0, **changes):
    project = scenario_project(sensitivity=-77)
    # Walls far from the grid only add cost: the bound counts cells × walls.
    project.building.walls += [Wall(id=f"filler-{k}", start=Point(x=50 + k, y=50), end=Point(x=50 + k, y=51),
                                    material_id="wood") for k in range(filler_walls)]
    ap = project.devices[0]
    profile = ReceiverProfile(id="p", name="Sensor genérico",
                              radio=Radio(id="p", protocol="wifi", channel=ap.radios[0].channel,
                                          frequency_hz=ap.radios[0].frequency_hz, bandwidth_hz=ap.radios[0].bandwidth_hz,
                                          tx_power_dbm=10, sensitivity_dbm=-77))
    data = {"access_point_device_id": ap.id, "access_point_radio_id": ap.radios[0].id, "profile": profile,
            "grid": {"width_m": 12, "depth_m": 6, "resolution_m": 1, "height_m": 1},
            "points": [{"x": 2, "y": 2, "z": 1}, {"x": 11, "y": 5, "z": 1}], **changes}
    return project, data


def test_report_map_is_the_map_api_result_with_a_plain_summary():
    project, parameters = map_parameters()
    report = build_report(ReportRequest(project=project, maps=[parameters]))
    expected = compute(CoverageMapRequest(project=project, **parameters))
    item = report.maps[0]
    assert item.result.request_hash == expected.request_hash and item.result.cells == expected.cells
    assert item.result.points == expected.points
    margins = sorted(min(f, r) for f, r, s in zip(expected.cells.forward_margin_db, expected.cells.reverse_margin_db,
                                                  expected.cells.status) if s == "computed")
    assert item.summary.limiting_margin_db == [margins[0], statistics.median(margins), margins[-1]]
    assert item.summary.negative_limiting_cells == sum(m < 0 for m in margins)
    assert item.summary.cells == expected.columns * expected.rows
    assert item.title == "Sensor genérico · 1 m"


def test_worst_case_map_is_named_and_kept_apart():
    project, parameters = map_parameters()
    worst = {"id": "worst", "name": "Peor caso", "doors": {"door-1": "closed"}, "materials": {"partition": "high"}}
    report = build_report(ReportRequest(project=project, maps=[parameters, {**parameters, "scenario": worst}]))
    nominal, pessimistic = report.maps
    assert pessimistic.title.endswith("· Peor caso") and nominal.result.request_hash != pessimistic.result.request_hash
    assert pessimistic.summary.limiting_margin_db[0] <= nominal.summary.limiting_margin_db[0]


def test_markdown_lists_counts_points_and_no_percentage():
    project, parameters = map_parameters()
    text = to_markdown(build_report(ReportRequest(project=project, maps=[parameters])))
    assert "## Mapas de cobertura" in text and "### Sensor genérico · 1 m" in text
    maps_section = text.split("## Mapas de cobertura")[1].split("\n## ")[0]
    assert "no un porcentaje de cobertura" in maps_section and "%" not in maps_section
    assert "Celdas por clase: Favorable" in maps_section and "| Clase |" in maps_section
    assert "| (2, 2, 1) |" in text and "| (11, 5, 1) |" in text


def test_reports_without_maps_are_unchanged():
    project, _ = map_parameters()
    report = build_report(ReportRequest(project=project))
    assert report.maps == [] and "## Mapas de cobertura" not in to_markdown(report)


@pytest.mark.parametrize("change, message", [
    ({"access_point_device_id": "nope"}, "Unknown access point device"),
    ({"engine": "sionna-rt"}, "no fallback"),
    ({"filler_walls": 60, "grid": {"width_m": 199, "depth_m": 199, "resolution_m": 1, "height_m": 1}},
     "evaluaciones"),
])
def test_invalid_or_too_costly_maps_are_rejected(change, message):
    project, parameters = map_parameters(**change)
    response = client.post("/api/reports", json={"project": project.model_dump(mode="json"),
                                                 "maps": [{**parameters, "profile": parameters["profile"].model_dump()}]})
    assert response.status_code == 422 and message in response.text


def test_maps_share_one_cost_bound():
    project, parameters = map_parameters(filler_walls=37)  # 40 walls: one 40 000-cell map fits, two do not
    big = {**parameters, "points": [], "grid": {"width_m": 200, "depth_m": 200, "resolution_m": 1, "height_m": 1}}
    assert 40_000 * len(project.building.walls) <= MAX_WORK < 2 * 40_000 * len(project.building.walls)
    ReportRequest(project=project, maps=[big])
    with pytest.raises(ValueError, match="Los mapas del informe"):
        ReportRequest(project=project, maps=[big, big])


def test_api_report_with_a_map():
    project, parameters = map_parameters()
    body = {"project": project.model_dump(mode="json"), "maps": [{**parameters, "profile": parameters["profile"].model_dump()}]}
    response = client.post("/api/reports", json=body)
    assert response.status_code == 200 and len(response.json()["maps"]) == 1
    markdown = client.post("/api/reports/markdown", json=body)
    assert markdown.status_code == 200 and "## Mapas de cobertura" in markdown.text
