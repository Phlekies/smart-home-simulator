"""Local HTTP boundary. Heavy solvers will use separate job adapters."""

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .cache import ResultCache
from .coverage import CoverageJobs, CoverageLimitError
from .engines import engine_capabilities, simulate
from .legacy import import_project
from .placement import ENGINE_VERSION as PLACEMENT_VERSION, PlacementLimitError, search
from .placement import request_hash as placement_hash
from .profiles import CATALOG
from .scenarios import ENGINE_VERSION as SCENARIO_VERSION, evaluate as evaluate_scenarios
from .scenarios import request_hash as scenario_hash
from .models import (
    CoverageMapJob, CoverageMapRequest, GenericProfile, PlacementSearchRequest, PlacementSearchResult, Project,
    ScenarioRequest, ScenarioResult, SimulationRequest, SimulationResult,
)

ROOT = Path(__file__).resolve().parents[4]
EXAMPLES = {"apartment": "smart-apartment.shsim.json", "office": "office-floor.shsim.json",
            "warehouse": "warehouse.shsim.json"}
coverage_jobs = CoverageJobs()
# Deterministic results reused for identical requests; local, bounded, emptied on restart.
placement_cache: ResultCache[PlacementSearchResult] = ResultCache(16)
scenario_cache: ResultCache[ScenarioResult] = ResultCache(32)


@asynccontextmanager
async def lifespan(_: FastAPI):
    global coverage_jobs
    coverage_jobs.shutdown()
    jobs = coverage_jobs = CoverageJobs()
    try:
        yield
    finally:
        jobs.shutdown()  # cancel queued/running maps so the server stops promptly


app = FastAPI(title="Smart Environment Simulator", version="0.1.0", lifespan=lifespan,
              description="API local. Estimación analítica; sin garantía de precisión experimental.")


@app.middleware("http")
async def limit_body(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH"}:
        chunks, total = [], 0
        async for chunk in request.stream():
            total += len(chunk)
            if total > 2_000_000:
                return JSONResponse(status_code=413, content={"detail": "Project exceeds the 2 MB local API limit"})
            chunks.append(chunk)
        request._body = b"".join(chunks)
    return await call_next(request)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": "0.1.0", "mode": "local"}


@app.get("/api/engines")
def engines() -> list[dict]:
    return engine_capabilities()


@app.get("/api/examples")
def examples() -> list[dict]:
    return [{"id": key, "name": value} for key, value in EXAMPLES.items()]


@app.get("/api/examples/{example_id}", response_model=Project)
def example(example_id: str) -> Project:
    if example_id not in EXAMPLES:
        raise HTTPException(404, "Unknown example")
    return import_project(json.loads((ROOT / "examples" / EXAMPLES[example_id]).read_text(encoding="utf-8")))


@app.post("/api/projects/import", response_model=Project)
def project_import(data: dict[str, Any]) -> Project:
    try:
        json.dumps(data, allow_nan=False)
        return import_project(data)
    except ValidationError as error:
        raise HTTPException(422, error.errors(include_context=False, include_input=False)) from error
    except (ValueError, TypeError, KeyError, AttributeError) as error:
        raise HTTPException(422, f"Invalid project: {error}") from error


@app.post("/api/simulations", response_model=SimulationResult)
def simulation(request: SimulationRequest) -> SimulationResult:
    if request.engine != "quick-estimate":
        raise HTTPException(501, f"{request.engine}: adapter not implemented or verified; no fallback executed")
    return simulate(request.project)


@app.post("/api/coverage-maps", response_model=CoverageMapJob, status_code=202)
def coverage_map(request: CoverageMapRequest) -> CoverageMapJob:
    """Queue a map; poll it with GET and stop it with DELETE."""
    if request.engine != "quick-estimate":
        raise HTTPException(501, f"{request.engine}: map adapter not implemented or verified; no fallback executed")
    try:
        return coverage_jobs.submit(request)
    except CoverageLimitError as error:
        raise HTTPException(422, str(error)) from error
    except OverflowError as error:
        raise HTTPException(429, str(error)) from error


@app.get("/api/coverage-maps/{job_id}", response_model=CoverageMapJob)
def coverage_map_status(job_id: str) -> CoverageMapJob:
    if (job := coverage_jobs.get(job_id)) is None:
        raise HTTPException(404, "Unknown coverage map job")
    return job


@app.delete("/api/coverage-maps/{job_id}", response_model=CoverageMapJob)
def coverage_map_cancel(job_id: str) -> CoverageMapJob:
    if (job := coverage_jobs.cancel(job_id)) is None:
        raise HTTPException(404, "Unknown coverage map job")
    return job


@app.post("/api/placement-searches", response_model=PlacementSearchResult)
def placement_search(request: PlacementSearchRequest) -> PlacementSearchResult:
    """Bounded exhaustive comparison of allowed AP places; synchronous because it is capped."""
    if request.engine != "quick-estimate":
        raise HTTPException(501, f"{request.engine}: placement adapter not implemented or verified; no fallback executed")
    key = f"{PLACEMENT_VERSION}:{placement_hash(request)}"
    if (cached := placement_cache.get(key)) is not None:
        return cached
    try:
        result = search(request)
    except PlacementLimitError as error:
        raise HTTPException(422, str(error)) from error
    placement_cache.put(key, result)
    return result


@app.get("/api/profiles", response_model=list[GenericProfile])
def profiles() -> list[GenericProfile]:
    """Generic radio profiles with per-value provenance; approximations, not products."""
    return CATALOG


@app.post("/api/scenario-simulations", response_model=ScenarioResult)
def scenario_simulation(request: ScenarioRequest) -> ScenarioResult:
    """Nominal, best and worst cases of unresolved doors/materials, plus named scenarios."""
    if request.engine != "quick-estimate":
        raise HTTPException(501, f"{request.engine}: scenario adapter not implemented or verified; no fallback executed")
    key = f"{SCENARIO_VERSION}:{scenario_hash(request)}"
    if (cached := scenario_cache.get(key)) is None:
        cached = evaluate_scenarios(request)
        scenario_cache.put(key, cached)
    return cached
