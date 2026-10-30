"""Result cache (B-110): identical requests reuse results; anything else recomputes."""

import time

import pytest
from fastapi.testclient import TestClient

from smart_environment import api, coverage
from smart_environment.cache import ResultCache
from smart_environment.coverage import CoverageJobs
from smart_environment.models import CoverageMapJob, CoverageMapRequest
from test_coverage import request_data
from test_placement import request as placement_request
from test_scenarios import project as scenario_project


def wait(jobs, job_id, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = jobs.get(job_id)
        if job.state in ("done", "cancelled", "failed"):
            return job
        time.sleep(0.02)
    raise AssertionError("job did not finish")


def test_lru_bounds_and_counts():
    cache = ResultCache[int](2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1  # 'a' becomes the most recent
    cache.put("c", 3)
    assert cache.get("b") is None and cache.get("a") == 1 and cache.get("c") == 3
    assert (cache.hits, cache.misses, len(cache)) == (3, 1, 2)
    with pytest.raises(ValueError):
        ResultCache(0)


def test_identical_map_is_served_from_cache_without_recomputing(monkeypatch):
    calls = []
    real = coverage.compute
    monkeypatch.setattr(coverage, "compute", lambda *a, **k: calls.append(1) or real(*a, **k))
    jobs = CoverageJobs()
    try:
        first = wait(jobs, jobs.submit(CoverageMapRequest.model_validate(request_data())).job_id)
        second = jobs.submit(CoverageMapRequest.model_validate(request_data()))
        assert first.state == "done" and not first.cached
        assert second.state == "done" and second.cached and second.job_id != first.job_id
        assert second.result == first.result and len(calls) == 1
        other = request_data()
        other["grid"]["height_m"] = 2.0
        third = wait(jobs, jobs.submit(CoverageMapRequest.model_validate(other)).job_id)
        assert not third.cached and len(calls) == 2
    finally:
        jobs.shutdown()


def test_cancelled_and_failed_maps_are_not_cached(monkeypatch):
    def cancelled(*_args, **_kwargs):
        raise coverage.Cancelled()

    def failed(*_args, **_kwargs):
        raise RuntimeError("boom")

    for broken, state in ((cancelled, "cancelled"), (failed, "failed")):
        monkeypatch.setattr(coverage, "compute", broken)
        jobs = CoverageJobs()
        try:
            job = wait(jobs, jobs.submit(CoverageMapRequest.model_validate(request_data())).job_id)
            assert job.state == state and len(jobs.cache) == 0
        finally:
            jobs.shutdown()


def test_cached_flag_is_optional_in_the_contract():
    schema = CoverageMapJob.model_json_schema(mode="serialization")
    assert "cached" in schema["properties"] and "cached" not in schema["required"]


def test_placement_and_scenarios_reuse_results(monkeypatch):
    client = TestClient(api.app)
    calls = []
    real_search, real_scenarios = api.search, api.evaluate_scenarios
    monkeypatch.setattr(api, "search", lambda r: calls.append("p") or real_search(r))
    monkeypatch.setattr(api, "evaluate_scenarios", lambda r: calls.append("s") or real_scenarios(r))
    body = placement_request(target_device_ids=["b"]).model_dump(mode="json")
    first = client.post("/api/placement-searches", json=body).json()
    again = client.post("/api/placement-searches", json=body).json()
    assert first == again and calls.count("p") == 1
    edited = {**body, "candidates": body["candidates"][:1]}
    client.post("/api/placement-searches", json=edited)
    assert calls.count("p") == 2
    scenario_body = {"project": scenario_project(sensitivity=-77).model_dump(mode="json")}
    first = client.post("/api/scenario-simulations", json=scenario_body).json()
    again = client.post("/api/scenario-simulations", json=scenario_body).json()
    assert first == again and calls.count("s") == 1
    scenario_body["project"]["devices"][0]["position"]["x"] = 0.5
    client.post("/api/scenario-simulations", json=scenario_body)
    assert calls.count("s") == 2
