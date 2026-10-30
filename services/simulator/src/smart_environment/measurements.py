"""Local measurement-campaign contract for the pilot, kept apart from the exportable project.

A campaign records what was observed, with which radio and under which conditions. It never
stores predictions or derived pass/fail flags, and a missing value means "not measured",
never zero. Files stay on the local machine; ``site_id`` is a pseudonym, not an address.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from collections.abc import Iterable
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .engines import input_hash
from .models import Finite, Identifier, Model, Point, Positive, Project

Provenance = Literal["measured", "declared", "inferred", "unknown"]
Split = Literal["format-example", "pilot", "calibration", "validation"]
Direction = Literal["ap-to-device", "device-to-ap"]
DeliveryDirection = Literal["ap-to-device", "device-to-ap", "round-trip"]
DeliveryMethod = Literal["icmp-echo", "udp-probe", "application-report", "other"]
Note = Annotated[str, Field(max_length=500)]


class ParameterValue(Model):
    """A radio parameter with its origin; ``unknown`` and an absent value always go together."""

    value: Finite | None = None
    provenance: Provenance = "unknown"
    source: Note | None = None

    @model_validator(mode="after")
    def value_matches_provenance(self) -> ParameterValue:
        if (self.value is None) != (self.provenance == "unknown"):
            raise ValueError("A value needs a known provenance, and 'unknown' cannot carry a value")
        return self


class RadioCharacterization(Model):
    tx_power_dbm: ParameterValue = Field(default_factory=ParameterValue)
    antenna_gain_dbi: ParameterValue = Field(default_factory=ParameterValue)
    noise_figure_db: ParameterValue = Field(default_factory=ParameterValue)
    sensitivity_dbm: ParameterValue = Field(default_factory=ParameterValue)


class Instrument(Model):
    """Device that reports a reading. A phone is not the candidate device's radio."""

    id: Identifier
    kind: Literal["candidate-device", "same-model-as-candidate", "phone", "laptop", "usb-adapter",
                  "access-point", "other"]
    model: Note | None = None
    radio_chipset: Note | None = None
    firmware: Note | None = None
    software: str | None = Field(default=None, max_length=500,
                                 description="App/tool and version used to read the values")
    rssi_reporting: Literal["dbm", "vendor-scale", "unknown"] = "unknown"
    radio: RadioCharacterization = Field(default_factory=RadioCharacterization)
    notes: Note | None = None


class AccessPointSetup(Model):
    id: Identifier
    project_device_id: Identifier
    project_radio_id: Identifier
    instrument_id: Identifier
    frequency_hz: Positive = Field(le=100e9)
    channel: int | None = Field(default=None, ge=0, le=1000)
    bandwidth_hz: Positive = Field(le=1e9)
    tx_power_dbm: ParameterValue = Field(default_factory=ParameterValue)
    antenna_gain_dbi: ParameterValue = Field(default_factory=ParameterValue)
    settings_note: str | None = Field(default=None, max_length=500,
                                      description="Fixed channel, band steering, power mode, etc.")


class Conditions(Model):
    id: Identifier
    doors: dict[Identifier, Literal["open", "closed", "unknown"]] = Field(
        default_factory=dict, description="Project wall ids representing doors and their state")
    people_present: int | None = Field(default=None, ge=0, le=1000)
    visible_networks_same_channel: int | None = Field(default=None, ge=0, le=10000)
    notes: Note | None = None


class FailureCriterion(Model):
    """Active link test decided before looking at predictions; frozen before validation."""

    id: Identifier
    description: str = Field(min_length=1, max_length=500)
    method: DeliveryMethod
    direction: DeliveryDirection
    min_packets: int = Field(ge=1, le=1_000_000)
    min_delivery_ratio: float = Field(gt=0, le=1)
    frozen_on: date | None = None


class RssiObservation(Model):
    direction: Direction
    receiver_instrument_id: Identifier
    samples_dbm: list[Finite] = Field(min_length=1, max_length=100_000)
    noise_dbm: Finite | None = Field(default=None, ge=-200, le=0)
    duration_s: Positive | None = None

    @model_validator(mode="after")
    def plausible_samples(self) -> RssiObservation:
        if any(not -150 <= sample <= 0 for sample in self.samples_dbm):
            raise ValueError("RSSI samples must be reported in dBm within [-150, 0]")
        return self


class DeliveryTest(Model):
    """Raw counts only; the outcome is derived against its criterion, never stored."""

    criterion_id: Identifier
    method: DeliveryMethod
    direction: DeliveryDirection
    payload_bytes: int = Field(ge=0, le=65_535)
    interval_s: Positive
    sent: int = Field(ge=1, le=1_000_000)
    received: int = Field(ge=0, le=1_000_000)
    retries_reported: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def received_not_above_sent(self) -> DeliveryTest:
        if self.received > self.sent:
            raise ValueError("A delivery test cannot receive more packets than it sent")
        return self


class MeasurementPoint(Model):
    id: Identifier
    status: Literal["planned", "measured", "excluded"]
    position: Point
    position_uncertainty_m: Positive | None = Field(default=None, le=100)
    orientation_deg: Finite | None = Field(default=None, ge=-360, le=360)
    device_instrument_id: Identifier
    access_point_id: Identifier
    conditions_id: Identifier
    measured_at: datetime | None = None
    rssi: list[RssiObservation] = Field(default_factory=list, max_length=64)
    delivery: list[DeliveryTest] = Field(default_factory=list, max_length=64)
    exclusion_reason: Note | None = None

    @model_validator(mode="after")
    def consistent_status(self) -> MeasurementPoint:
        observed = bool(self.rssi or self.delivery)
        if self.status == "planned" and (observed or self.measured_at is not None):
            raise ValueError(f"Planned point {self.id} cannot contain observations")
        if self.status == "measured" and not (observed and self.measured_at is not None):
            raise ValueError(f"Measured point {self.id} needs observations and a timestamp")
        if self.status == "excluded" and not self.exclusion_reason:
            raise ValueError(f"Excluded point {self.id} needs an exclusion reason")
        return self


class ProjectReference(Model):
    name: str = Field(min_length=1, max_length=160)
    input_hash: str = Field(pattern=r"^[0-9a-f]{64}$", description="SHA-256 of the canonical project JSON")


class MeasurementCampaign(Model):
    format: Literal["smart-environment-measurements"] = "smart-environment-measurements"
    version: Literal[1] = 1
    id: Identifier
    site_id: Identifier = Field(description="Pseudonymous home identifier; never an address")
    split: Split
    synthetic: bool = Field(description="True only for format examples; synthetic data is never evidence")
    purpose: str = Field(min_length=1, max_length=1000)
    project: ProjectReference
    collected_from: date | None = None
    collected_to: date | None = None
    operator_role: str | None = Field(default=None, max_length=160, description="Role, not a personal name")
    instruments: list[Instrument] = Field(min_length=1, max_length=64)
    access_points: list[AccessPointSetup] = Field(min_length=1, max_length=32)
    conditions: list[Conditions] = Field(min_length=1, max_length=64)
    criteria: list[FailureCriterion] = Field(default_factory=list, max_length=32)
    points: list[MeasurementPoint] = Field(default_factory=list, max_length=10_000)
    notes: list[str] = Field(default_factory=list, max_length=256)

    @model_validator(mode="after")
    def validate_campaign(self) -> MeasurementCampaign:
        def index(items, label):
            ids = [item.id for item in items]
            if len(ids) != len(set(ids)):
                raise ValueError(f"Duplicate {label} IDs")
            return {item.id: item for item in items}

        instruments = index(self.instruments, "instrument")
        access_points = index(self.access_points, "access point")
        conditions = index(self.conditions, "conditions")
        criteria = index(self.criteria, "criterion")
        index(self.points, "point")
        if self.synthetic != (self.split == "format-example"):
            raise ValueError("Only 'format-example' campaigns may be synthetic, and they must be")
        if self.synthetic and any(p.status != "planned" for p in self.points):
            raise ValueError("A synthetic format example cannot contain observations")
        if self.collected_from and self.collected_to and self.collected_to < self.collected_from:
            raise ValueError("collected_to precedes collected_from")
        for ap in self.access_points:
            if ap.instrument_id not in instruments:
                raise ValueError(f"Unknown instrument: {ap.instrument_id}")
        for point in self.points:
            for ref, known, label in [(point.device_instrument_id, instruments, "instrument"),
                                      (point.access_point_id, access_points, "access point"),
                                      (point.conditions_id, conditions, "conditions")]:
                if ref not in known:
                    raise ValueError(f"Unknown {label}: {ref}")
            for observation in point.rssi:
                if observation.receiver_instrument_id not in instruments:
                    raise ValueError(f"Unknown instrument: {observation.receiver_instrument_id}")
            for test in point.delivery:
                if test.criterion_id not in criteria:
                    raise ValueError(f"Unknown criterion: {test.criterion_id}")
            if point.measured_at is not None:
                if not (self.collected_from and self.collected_to):
                    raise ValueError("Measured points need the campaign collection dates")
                if not self.collected_from <= point.measured_at.date() <= self.collected_to:
                    raise ValueError(f"Point {point.id} measured outside the collection dates")
        if self.split == "validation":
            for criterion in self.criteria:
                if criterion.frozen_on is None or (self.collected_from and criterion.frozen_on > self.collected_from):
                    raise ValueError(f"Validation criterion {criterion.id} must be frozen before collection starts")
        return self


def delivery_outcome(test: DeliveryTest, criterion: FailureCriterion) -> Literal["pass", "fail", "inconclusive"]:
    """Apply a criterion to raw counts; a test that does not match its criterion proves nothing."""
    if (test.method, test.direction) != (criterion.method, criterion.direction) or test.sent < criterion.min_packets:
        return "inconclusive"
    return "pass" if test.received / test.sent >= criterion.min_delivery_ratio else "fail"


def summarize(campaign: MeasurementCampaign) -> list[dict]:
    """Per-point descriptive statistics of what was measured; no interpretation added."""
    criteria = {c.id: c for c in campaign.criteria}
    rows = []
    for point in campaign.points:
        if point.status != "measured":
            continue
        by_direction: dict[str, list[float]] = defaultdict(list)
        for observation in point.rssi:
            by_direction[observation.direction].extend(observation.samples_dbm)
        rows.append({
            "point_id": point.id, "position": point.position.model_dump(),
            "rssi": {direction: {"samples": len(values), "median_dbm": statistics.median(values),
                                 "min_dbm": min(values), "max_dbm": max(values)}
                     for direction, values in sorted(by_direction.items())},
            "delivery": [{"criterion_id": t.criterion_id, "direction": t.direction, "sent": t.sent,
                          "received": t.received, "outcome": delivery_outcome(t, criteria[t.criterion_id])}
                         for t in point.delivery],
        })
    return rows


def project_issues(campaign: MeasurementCampaign, project: Project) -> list[str]:
    """Problems that prevent comparing this campaign with predictions for ``project``."""
    issues = []
    if campaign.project.input_hash != input_hash(project):
        issues.append("El hash del proyecto no coincide: las posiciones pueden referirse a otra versión del plano.")
    devices = {d.id: d for d in project.devices}
    for ap in campaign.access_points:
        device = devices.get(ap.project_device_id)
        if device is None:
            issues.append(f"AP {ap.id}: el dispositivo {ap.project_device_id} no existe en el proyecto.")
        elif ap.project_radio_id not in {r.id for r in device.radios}:
            issues.append(f"AP {ap.id}: la radio {ap.project_radio_id} no existe en {device.id}.")
    walls = {w.id for w in project.building.walls}
    for conditions in campaign.conditions:
        for wall_id in conditions.doors:
            if wall_id not in walls:
                issues.append(f"Condiciones {conditions.id}: la puerta {wall_id} no es una pared del proyecto.")
    return issues


def partition_issues(campaigns: Iterable[MeasurementCampaign]) -> list[str]:
    """Leakage between calibration and validation is checked per home, not per point."""
    campaigns = list(campaigns)
    issues = []
    ids = [c.id for c in campaigns]
    if len(ids) != len(set(ids)):
        issues.append("Hay campañas con el mismo id.")
    splits: dict[str, set[str]] = defaultdict(set)
    for campaign in campaigns:
        splits[campaign.site_id].add(campaign.split)
    for site, used in sorted(splits.items()):
        if {"calibration", "validation"} <= used:
            issues.append(f"La vivienda {site} aparece en calibración y validación: no es una evaluación independiente.")
        if {"pilot", "validation"} <= used:
            issues.append(f"La vivienda {site} se usó en el piloto y en validación: los objetivos se fijaron con ella.")
    return issues
