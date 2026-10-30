"""Coverage maps by profile and height (B-103), computed as cancellable background jobs.

Every cell is a direct-path link budget between the selected AP radio and the candidate
profile placed at the cell centre, in both directions. No coverage class is assigned: the
design-reserve policy is still undecided, so only received power and margins are reported.
"""

from __future__ import annotations

import hashlib
import json
import math
import threading
import time
import uuid
from collections import OrderedDict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from .cache import ResultCache

from .engines import LIMITATIONS, direction, input_hash, radio_pair_check
from .models import (
    CoverageCells, CoverageMapJob, CoverageMapRequest, CoverageMapResult, CoverageSample, Device, Point, Project,
    Wall,
)

ENGINE_VERSION = "0.1.0"
MAX_WORK = 2_000_000  # cells × walls; bounds a quick-estimate job to a few seconds
MAP_LIMITATIONS = LIMITATIONS + [
    "Valor en el centro de cada celda, sin interpolación; los puntos exactos se evalúan aparte.",
    "Un solo AP seleccionado: la energía de otros AP no se suma a esta conexión.",
    "Sin clasificación favorable/marginal/insuficiente: la reserva de diseño está pendiente.",
]


class CoverageLimitError(ValueError):
    """The request exceeds the bounded cost accepted for synchronous-sized jobs."""


class Cancelled(Exception):
    pass


def request_hash(request: CoverageMapRequest) -> str:
    parameters = request.model_dump(mode="json", exclude={"project"})
    canonical = json.dumps({"project": input_hash(request.project), "parameters": parameters},
                           sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def preflight(request: CoverageMapRequest) -> None:
    """Reject before queueing: incompatible radios or a cost above the accepted bound."""
    ap = next(d for d in request.project.devices if d.id == request.access_point_device_id)
    ap_radio = next(r for r in ap.radios if r.id == request.access_point_radio_id)
    _, blocked, reasons = radio_pair_check(ap_radio, request.profile.radio)
    if blocked is not None:
        raise CoverageLimitError("El perfil no puede evaluarse con esta radio del AP: " + " ".join(reasons))
    samples = request.grid.columns * request.grid.rows + len(request.points)
    work = samples * max(1, len(request.project.building.walls))
    if work > MAX_WORK:
        raise CoverageLimitError(f"El mapa requiere {work} evaluaciones celda×pared (máximo {MAX_WORK}); "
                                 "aumenta la resolución, reduce el área o el número de paredes.")


def inside_wall(point: Point, wall: Wall) -> bool:
    """Point within half the wall thickness of its centre line and within its height."""
    if not wall.start.z <= point.z <= wall.start.z + wall.height_m:
        return False
    ax, ay, bx, by = wall.start.x, wall.start.y, wall.end.x, wall.end.y
    length_sq = (bx - ax) ** 2 + (by - ay) ** 2
    t = max(0.0, min(1.0, ((point.x - ax) * (bx - ax) + (point.y - ay) * (by - ay)) / length_sq))
    return math.hypot(point.x - (ax + t * (bx - ax)), point.y - (ay + t * (by - ay))) < wall.thickness_m / 2


def evaluate(project: Project, ap: Device, ap_radio, profile_radio, point: Point) -> CoverageSample:
    for wall in project.building.walls:
        if inside_wall(point, wall):
            return CoverageSample(forward_dbm=None, reverse_dbm=None, forward_margin_db=None,
                                  reverse_margin_db=None, status="not-computed", reason="inside-wall")
    if math.dist((ap.position.x, ap.position.y, ap.position.z), (point.x, point.y, point.z)) < 0.1:
        return CoverageSample(forward_dbm=None, reverse_dbm=None, forward_margin_db=None,
                              reverse_margin_db=None, status="not-computed", reason="too-close-to-access-point")
    candidate = Device.model_construct(id="__profile__", name="profile", role="endpoint", position=point,
                                       radios=[profile_radio], evidence="map sample")
    forward = direction(project, ap, ap_radio, candidate, profile_radio)
    reverse = direction(project, candidate, profile_radio, ap, ap_radio)
    values = (None if forward is None else forward.received_power_dbm,
              None if reverse is None else reverse.received_power_dbm,
              None if forward is None else forward.margin_db,
              None if reverse is None else reverse.margin_db)
    return CoverageSample(forward_dbm=values[0], reverse_dbm=values[1], forward_margin_db=values[2],
                          reverse_margin_db=values[3], status="computed" if None not in values else "partial")


def compute(request: CoverageMapRequest, progress: Callable[[float], None] = lambda _: None,
            cancelled: Callable[[], bool] = lambda: False) -> CoverageMapResult:
    """Quick-estimate map; raises Cancelled between rows when asked to stop."""
    started = time.perf_counter()
    project, grid = request.project, request.grid
    ap = next(d for d in project.devices if d.id == request.access_point_device_id)
    ap_radio = next(r for r in ap.radios if r.id == request.access_point_radio_id)
    profile_radio = request.profile.radio
    preflight(request)
    compatibility, _, reasons = radio_pair_check(ap_radio, profile_radio)
    if ap_radio.tx_power_dbm is None:
        reasons.append("Falta la potencia de transmisión del AP: sentido AP→equipo no calculado.")
    if profile_radio.tx_power_dbm is None:
        reasons.append("Falta la potencia de transmisión del perfil: sentido equipo→AP no calculado.")
    if profile_radio.sensitivity_dbm is None or ap_radio.sensitivity_dbm is None:
        reasons.append("Falta alguna sensibilidad: los márgenes de ese sentido no se calculan.")
    columns, rows = grid.columns, grid.rows
    total = rows + (1 if request.points else 0)
    samples: list[CoverageSample] = []
    for j in range(rows):
        if cancelled():
            raise Cancelled()
        y = grid.origin_y_m + (j * grid.resolution_m + min((j + 1) * grid.resolution_m, grid.depth_m)) / 2
        for i in range(columns):
            x = grid.origin_x_m + (i * grid.resolution_m + min((i + 1) * grid.resolution_m, grid.width_m)) / 2
            point = Point.model_construct(x=x, y=y, z=grid.height_m)
            samples.append(evaluate(project, ap, ap_radio, profile_radio, point))
        progress((j + 1) / total)
    if cancelled():
        raise Cancelled()
    exact = [evaluate(project, ap, ap_radio, profile_radio, point) for point in request.points]
    progress(1.0)
    counts = {status: sum(s.status == status for s in samples) for status in ("computed", "partial", "not-computed")}
    if counts["not-computed"]:
        reasons.append(f"{counts['not-computed']} celdas sin calcular (dentro de paredes o junto al AP).")
    return CoverageMapResult(
        engine="quick-estimate", engine_version=ENGINE_VERSION, input_hash=input_hash(project),
        request_hash=request_hash(request), parameters=request.model_dump(exclude={"project"}),
        metric="direct-path-received-power", frequency_hz=ap_radio.frequency_hz, compatibility=compatibility,
        columns=columns, rows=rows,
        cells=CoverageCells(forward_dbm=_rounded(s.forward_dbm for s in samples),
                            reverse_dbm=_rounded(s.reverse_dbm for s in samples),
                            forward_margin_db=_rounded(s.forward_margin_db for s in samples),
                            reverse_margin_db=_rounded(s.reverse_margin_db for s in samples),
                            status=[s.status for s in samples]),
        points=exact, computed_cells=counts["computed"], partial_cells=counts["partial"],
        not_computed_cells=counts["not-computed"], elapsed_ms=(time.perf_counter() - started) * 1000,
        scope=f"Mapa de trayecto directo a {grid.height_m:g} m para el perfil «{request.profile.name}»; "
              "compatibilidad funcional no evaluada",
        limitations=MAP_LIMITATIONS, reasons=reasons)


def _rounded(values) -> list[float | None]:
    # 0.001 dB keeps map payloads small; exact points keep full precision.
    return [None if v is None else round(v, 3) for v in values]


class _Job:
    def __init__(self, request: CoverageMapRequest) -> None:
        self.id = uuid.uuid4().hex
        self.request = request
        self.hash = request_hash(request)
        self.state = "queued"
        self.progress = 0.0
        self.result: CoverageMapResult | None = None
        self.error: str | None = None
        self.cached = False
        self.cancel = threading.Event()


class CoverageJobs:
    """In-process job queue: one worker, bounded history, cooperative cancellation."""

    def __init__(self, max_jobs: int = 16, cache_entries: int = 8) -> None:
        self._jobs: OrderedDict[str, _Job] = OrderedDict()
        self.cache: ResultCache[CoverageMapResult] = ResultCache(cache_entries)
        self._lock = threading.Lock()
        self._max_jobs = max_jobs
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="coverage-map")

    def _snapshot(self, job: _Job) -> CoverageMapJob:
        return CoverageMapJob(job_id=job.id, state=job.state, progress=job.progress, request_hash=job.hash,
                              result=job.result, error=job.error, cached=job.cached)

    def submit(self, request: CoverageMapRequest) -> CoverageMapJob:
        preflight(request)
        job = _Job(request)
        cached = self.cache.get(f"{ENGINE_VERSION}:{job.hash}")
        if cached is not None:
            job.result, job.state, job.progress, job.cached = cached, "done", 1.0, True
        with self._lock:
            finished = [k for k, v in self._jobs.items() if v.state in ("done", "cancelled", "failed")]
            while len(self._jobs) >= self._max_jobs and finished:
                del self._jobs[finished.pop(0)]
            if len(self._jobs) >= self._max_jobs:
                raise OverflowError("Demasiados mapas en curso; cancela alguno o espera a que terminen.")
            self._jobs[job.id] = job
        if not job.cached:
            self._executor.submit(self._run, job)
        return self._snapshot(job)

    def _run(self, job: _Job) -> None:
        with self._lock:
            if job.cancel.is_set():
                job.state = "cancelled"
                return
            job.state = "running"

        def report(value: float) -> None:
            job.progress = value

        try:
            result = compute(job.request, report, job.cancel.is_set)
        except Cancelled:
            with self._lock:
                job.state = "cancelled"
            return
        except Exception as error:  # surfaced to the client, never replaced by another engine
            with self._lock:
                job.state, job.error = "failed", f"{type(error).__name__}: {error}"
            return
        with self._lock:
            if job.cancel.is_set():
                job.state = "cancelled"
            else:
                job.result, job.state, job.progress = result, "done", 1.0
                self.cache.put(f"{ENGINE_VERSION}:{job.hash}", result)

    def get(self, job_id: str) -> CoverageMapJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return None if job is None else self._snapshot(job)

    def cancel(self, job_id: str) -> CoverageMapJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            job.cancel.set()
            if job.state == "queued":
                job.state = "cancelled"
            return self._snapshot(job)

    def shutdown(self) -> None:
        with self._lock:
            for job in self._jobs.values():
                job.cancel.set()
        self._executor.shutdown(wait=True, cancel_futures=True)
