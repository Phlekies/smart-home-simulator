"""Canonical SI project contract. The scene is independent of every solver and renderer."""

from __future__ import annotations

import math
import json
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Finite = Annotated[float, Field(allow_inf_nan=False)]
Positive = Annotated[float, Field(gt=0, allow_inf_nan=False)]
Identifier = Annotated[str, Field(min_length=1, max_length=120)]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False,
                              json_schema_serialization_defaults_required=True)


class Point(Model):
    x: Finite = Field(ge=-10000, le=10000)
    y: Finite = Field(ge=-10000, le=10000)
    z: Finite = Field(default=0, ge=-1000, le=1000)


class Material(Model):
    id: Identifier
    name: str = Field(min_length=1, max_length=160)
    loss_db_24ghz: Finite = Field(ge=0, le=1000)
    loss_db_5ghz: Finite = Field(ge=0, le=1000)
    extra_loss_db_per_cm: Finite = Field(default=0, ge=0, le=100)
    evidence: str = "Hypothesis: legacy empirical values; not calibrated"


class Wall(Model):
    id: Identifier
    start: Point
    end: Point
    height_m: Positive = Field(default=2.6, le=100)
    thickness_m: Positive = Field(default=0.12, le=10)
    material_id: Identifier

    @model_validator(mode="after")
    def valid_segment(self) -> Wall:
        if math.hypot(self.end.x - self.start.x, self.end.y - self.start.y) < 1e-6:
            raise ValueError("Wall endpoints must be different")
        if self.start.z != self.end.z:
            raise ValueError("Wall bases must be horizontal")
        return self


class Building(Model):
    width_m: Positive = Field(default=20, le=1000)
    depth_m: Positive = Field(default=15, le=1000)
    walls: list[Wall] = Field(default_factory=list, max_length=2000)
    materials: list[Material] = Field(min_length=1, max_length=64)


class Radio(Model):
    id: Identifier
    protocol: Literal["wifi", "thread", "zigbee", "ble", "zwave", "unknown"] = "unknown"
    frequency_hz: Positive = Field(le=100e9)
    bandwidth_hz: Positive = Field(le=1e9)
    channel: int | None = Field(default=None, ge=0, le=1000)
    tx_power_dbm: Finite | None = Field(default=None, ge=-100, le=100)
    tx_gain_dbi: Finite = Field(default=0, ge=-100, le=100)
    rx_gain_dbi: Finite = Field(default=0, ge=-100, le=100)
    sensitivity_dbm: Finite | None = Field(default=None, ge=-200, le=0)
    noise_figure_db: Finite = Field(default=7, ge=0, le=60)
    antenna: Literal["omnidirectional", "directional"] = "omnidirectional"
    orientation_deg: Finite = Field(default=0, ge=-360, le=360)
    beamwidth_deg: Finite = Field(default=360, gt=0, le=360)
    pattern_sharpness: Finite = Field(default=1.8, ge=0.5, le=100)
    side_lobe_attenuation_db: Finite = Field(default=18, ge=0, le=100)
    polarization_deg: Finite = Field(default=0, ge=-360, le=360)


class Device(Model):
    id: Identifier
    name: str = Field(min_length=1, max_length=160)
    role: Literal["endpoint", "access-point", "controller", "router", "bridge", "unknown"] = "unknown"
    position: Point
    radios: list[Radio] = Field(min_length=1, max_length=8)
    evidence: str = "User-defined generic device; functional compatibility unverified"


class Link(Model):
    id: Identifier
    source_device_id: Identifier
    source_radio_id: Identifier
    target_device_id: Identifier
    target_radio_id: Identifier


class Settings(Model):
    path_loss_exponent: Finite = Field(default=2.1, ge=1, le=6)
    extra_loss_db_per_m: Finite = Field(default=0, ge=0, le=100)
    system_gain_db: Finite = Field(default=0, ge=-100, le=100)


class PixelPoint(Model):
    x: Finite = Field(ge=0, le=16384)
    y: Finite = Field(ge=0, le=16384)


class PlanReferenceCalibration(Model):
    """Two image points and the real distance between them, kept so the scale can be reviewed."""

    point_a_px: PixelPoint
    point_b_px: PixelPoint
    distance_m: Finite = Field(ge=0.01, le=20000)


class PlanReference(Model):
    """Background floor-plan image placed at scale; display aid only, never a solver input.

    The image stays a local file: only its fingerprint travels in the project. Pixel (u, v),
    u to the right and v downwards from the top-left corner, maps to
    x = origin_x_m + u·meters_per_pixel and y = origin_y_m + v·meters_per_pixel.
    """

    file_name: str = Field(min_length=1, max_length=255)
    media_type: Literal["image/png", "image/jpeg", "image/webp"]
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$", description="SHA-256 of the image file bytes")
    width_px: int = Field(ge=1, le=16384)
    height_px: int = Field(ge=1, le=16384)
    meters_per_pixel: Positive = Field(le=20000)
    origin_x_m: Finite = Field(ge=-10000, le=10000)
    origin_y_m: Finite = Field(ge=-10000, le=10000)
    calibration: PlanReferenceCalibration | None = None
    evidence: str = "User calibration from a known distance; not surveyed"

    @model_validator(mode="after")
    def consistent_placement(self) -> PlanReference:
        if self.width_px * self.height_px > 16_000_000:
            raise ValueError("Plan reference images are limited to 16 million pixels")
        width_m, height_m = self.width_px * self.meters_per_pixel, self.height_px * self.meters_per_pixel
        if min(width_m, height_m) < 0.01:
            raise ValueError("The placed image must span at least 0.01 m on each axis")
        if max(abs(self.origin_x_m + width_m), abs(self.origin_y_m + height_m)) > 10000:
            raise ValueError("The placed image must stay within ±10000 m")
        if self.calibration is not None:
            a, b = self.calibration.point_a_px, self.calibration.point_b_px
            if not all(p.x <= self.width_px and p.y <= self.height_px for p in (a, b)):
                raise ValueError("Calibration points must lie inside the image")
            pixels = math.hypot(b.x - a.x, b.y - a.y)
            if pixels < 2:
                raise ValueError("Calibration points must be at least 2 pixels apart")
            if not math.isclose(self.calibration.distance_m / pixels, self.meters_per_pixel, rel_tol=1e-9):
                raise ValueError("meters_per_pixel does not match the recorded calibration")
        return self


def _plan_reference_optional(schema: dict[str, Any]) -> None:
    # Additive v1 field: generated clients must not have to send it.
    schema["required"] = [name for name in schema.get("required", []) if name != "plan_reference"]


class Project(Model):
    model_config = ConfigDict(json_schema_extra=_plan_reference_optional)

    format: Literal["smart-environment-simulator"] = "smart-environment-simulator"
    version: Literal[1] = 1
    name: str = Field(default="Entorno inteligente", min_length=1, max_length=160)
    units: Literal["m"] = "m"
    building: Building
    devices: list[Device] = Field(default_factory=list, max_length=128)
    links: list[Link] = Field(default_factory=list, max_length=512)
    settings: Settings = Field(default_factory=Settings)
    migration_notes: list[str] = Field(default_factory=list, max_length=256)
    legacy_source: dict[str, Any] | None = None
    plan_reference: PlanReference | None = None

    @field_validator("version", mode="before")
    @classmethod
    def integer_version(cls, value):
        if type(value) is not int:
            raise ValueError("Project version must be an integer")
        return value

    @field_validator("legacy_source")
    @classmethod
    def finite_legacy_json(cls, value):
        if value is not None:
            json.dumps(value, allow_nan=False)
        return value

    @model_validator(mode="after")
    def validate_references(self) -> Project:
        def unique(ids: list[str], label: str) -> None:
            if len(ids) != len(set(ids)):
                raise ValueError(f"Duplicate {label} IDs")

        unique([m.id for m in self.building.materials], "material")
        unique([w.id for w in self.building.walls], "wall")
        unique([d.id for d in self.devices], "device")
        unique([link.id for link in self.links], "link")
        materials = {m.id for m in self.building.materials}
        for wall in self.building.walls:
            if wall.material_id not in materials:
                raise ValueError(f"Unknown material: {wall.material_id}")
        devices = {d.id: d for d in self.devices}
        for device in self.devices:
            unique([r.id for r in device.radios], f"radio in {device.id}")
        for link in self.links:
            if link.source_device_id == link.target_device_id:
                raise ValueError("Self-links are not supported")
            for device_id, radio_id in [(link.source_device_id, link.source_radio_id),
                                        (link.target_device_id, link.target_radio_id)]:
                if device_id not in devices:
                    raise ValueError(f"Unknown device: {device_id}")
                if radio_id not in {r.id for r in devices[device_id].radios}:
                    raise ValueError(f"Unknown radio: {device_id}/{radio_id}")
        return self


class DirectionResult(Model):
    tx_device_id: str
    rx_device_id: str
    distance_m: float
    path_loss_db: float
    wall_loss_db: float
    crossed_wall_ids: list[str]
    received_power_dbm: float
    noise_dbm: float
    snr_db: float
    margin_db: float | None


class LinkResult(Model):
    id: str
    compatibility: Literal["radio-compatible", "incompatible", "unverified"]
    status: Literal["above-threshold", "below-threshold", "incompatible", "unverified", "unsupported"]
    forward: DirectionResult | None = None
    reverse: DirectionResult | None = None
    reasons: list[str] = Field(default_factory=list)


class SimulationResult(Model):
    engine: str
    engine_version: str
    input_hash: str
    elapsed_ms: float
    scope: str
    limitations: list[str]
    links: list[LinkResult]


class SimulationRequest(Model):
    project: Project
    engine: Literal["quick-estimate", "sionna-rt", "ns-3"] = "quick-estimate"


# --- Coverage maps (B-103) -------------------------------------------------------------

MAX_MAP_CELLS = 40_000
MAX_MAP_POINTS = 256


class ReceiverProfile(Model):
    """Radio of the candidate device as it would be installed; drives both link directions."""

    id: Identifier
    name: str = Field(min_length=1, max_length=160)
    radio: Radio
    evidence: str = "Generic profile; not a certified product"


class MapGrid(Model):
    """Horizontal sampling plane. Cell (i, j) is evaluated at its centre:
    x = origin_x_m + (i + 0.5)·resolution_m, y = origin_y_m + (j + 0.5)·resolution_m, z = height_m.
    Edge cells narrower than resolution_m use the centre of their clipped extent."""

    origin_x_m: Finite = Field(default=0, ge=-10000, le=10000)
    origin_y_m: Finite = Field(default=0, ge=-10000, le=10000)
    width_m: Positive = Field(le=2000)
    depth_m: Positive = Field(le=2000)
    resolution_m: Finite = Field(default=0.5, ge=0.1, le=5)
    height_m: Finite = Field(ge=-1000, le=1000)

    @property
    def columns(self) -> int:
        return max(1, math.ceil(self.width_m / self.resolution_m - 1e-9))

    @property
    def rows(self) -> int:
        return max(1, math.ceil(self.depth_m / self.resolution_m - 1e-9))

    @model_validator(mode="after")
    def bounded(self) -> MapGrid:
        if self.columns * self.rows > MAX_MAP_CELLS:
            raise ValueError(f"Grid exceeds {MAX_MAP_CELLS} cells; increase resolution_m or reduce the area")
        if self.origin_x_m + self.width_m > 10000 or self.origin_y_m + self.depth_m > 10000:
            raise ValueError("The entire map extent must stay within ±10000 m")
        return self


class CoverageMapParameters(Model):
    """Everything that defines a map except the project; echoed in the result for staleness checks."""

    access_point_device_id: Identifier
    access_point_radio_id: Identifier
    profile: ReceiverProfile
    grid: MapGrid
    points: list[Point] = Field(default_factory=list, max_length=MAX_MAP_POINTS,
                                description="Exact positions evaluated without snapping to the grid")
    engine: Literal["quick-estimate", "sionna-rt", "ns-3"] = "quick-estimate"


class CoverageMapRequest(CoverageMapParameters):
    project: Project

    @model_validator(mode="after")
    def known_access_point(self) -> CoverageMapRequest:
        device = next((d for d in self.project.devices if d.id == self.access_point_device_id), None)
        if device is None:
            raise ValueError(f"Unknown access point device: {self.access_point_device_id}")
        if self.access_point_radio_id not in {r.id for r in device.radios}:
            raise ValueError(f"Unknown access point radio: {self.access_point_radio_id}")
        return self


CellStatus = Literal["computed", "partial", "not-computed"]


class CoverageSample(Model):
    """One evaluated position. Forward is AP→profile, reverse is profile→AP; no classification."""

    forward_dbm: float | None
    reverse_dbm: float | None
    forward_margin_db: float | None
    reverse_margin_db: float | None
    status: CellStatus
    reason: str | None = None


class CoverageCells(Model):
    """Row-major arrays (index = j·columns + i), one entry per cell, same meaning as CoverageSample."""

    forward_dbm: list[float | None]
    reverse_dbm: list[float | None]
    forward_margin_db: list[float | None]
    reverse_margin_db: list[float | None]
    status: list[CellStatus]


class CoverageMapResult(Model):
    engine: str
    engine_version: str
    input_hash: str = Field(description="Hash of the project (same as simulation results)")
    request_hash: str = Field(description="Hash of the project and every map parameter")
    parameters: CoverageMapParameters
    metric: Literal["direct-path-received-power"]
    frequency_hz: float
    compatibility: Literal["radio-compatible", "unverified"]
    columns: int
    rows: int
    cells: CoverageCells
    points: list[CoverageSample]
    computed_cells: int
    partial_cells: int
    not_computed_cells: int
    elapsed_ms: float
    scope: str
    limitations: list[str]
    reasons: list[str] = Field(description="Map-level notes: missing data, unverified compatibility, etc.")


class CoverageMapJob(Model):
    job_id: str
    state: Literal["queued", "running", "done", "cancelled", "failed"]
    progress: float = Field(ge=0, le=1)
    request_hash: str
    result: CoverageMapResult | None = None
    error: str | None = None
