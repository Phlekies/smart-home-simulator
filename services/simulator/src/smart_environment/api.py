"""Local HTTP boundary. Heavy solvers will use separate job adapters."""

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .engines import engine_capabilities, simulate
from .legacy import import_project
from .models import Project, SimulationRequest, SimulationResult

ROOT = Path(__file__).resolve().parents[4]
EXAMPLES = {"apartment": "smart-apartment.shsim.json", "office": "office-floor.shsim.json",
            "warehouse": "warehouse.shsim.json"}
app = FastAPI(title="Smart Environment Simulator", version="0.1.0",
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
