"""Measured vs predicted signal and a minimal, auditable calibration (B-109, P4 preparation).

For every measured point the quick estimator predicts the received power in each measured
direction with the AP power declared in the campaign and the door states recorded at that
moment. Residual = measured median − prediction (dB). Unknown antenna gains are taken as 0 dBi
and listed as assumptions, so the residual still contains them.

Calibration fits one offset on ``calibration`` campaigns only and reports its effect on
``validation`` campaigns only, before and after. No probabilities, coverage classes or false
favourables are computed: those need the failure criterion and design reserve still pending.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Literal

from pydantic import Field

from .engines import direction
from .measurements import MeasurementCampaign, partition_issues, project_issues, summarize
from .models import Device, Model, Point, Project, Radio, ScenarioAssumptions

Direction = Literal["ap-to-device", "device-to-ap"]


class CalibrationError(ValueError):
    """The inputs cannot support an honest comparison (leakage, wrong project, synthetic data)."""


class PointResidual(Model):
    campaign_id: str
    site_id: str
    split: str
    point_id: str
    direction: Direction
    samples: int
    measured_median_dbm: float
    predicted_dbm: float
    residual_db: float = Field(description="measured − predicted")
    assumptions: list[str]


class SkippedObservation(Model):
    campaign_id: str
    point_id: str
    direction: Direction | None
    reason: str


class ResidualStats(Model):
    group: str
    count: int
    bias_db: float | None = Field(description="Mean residual (measured − predicted)")
    median_db: float | None
    mae_db: float | None
    rmse_db: float | None
    min_db: float | None
    max_db: float | None


class CalibrationReport(Model):
    engine: str = "quick-estimate"
    method: Literal["single-offset"] = "single-offset"
    offset_db: float | None = Field(description="Added to predictions; fitted on calibration campaigns only")
    calibration_points: int
    validation_before: list[ResidualStats]
    validation_after: list[ResidualStats]
    residuals: list[PointResidual]
    skipped: list[SkippedObservation]
    notes: list[str]


def _stats(group: str, values: list[float]) -> ResidualStats:
    if not values:
        return ResidualStats(group=group, count=0, bias_db=None, median_db=None, mae_db=None, rmse_db=None,
                             min_db=None, max_db=None)
    return ResidualStats(group=group, count=len(values), bias_db=statistics.fmean(values),
                         median_db=statistics.median(values), mae_db=statistics.fmean(abs(v) for v in values),
                         rmse_db=math.sqrt(statistics.fmean(v * v for v in values)), min_db=min(values),
                         max_db=max(values))


def residuals(campaign: MeasurementCampaign, project: Project) -> tuple[list[PointResidual], list[SkippedObservation]]:
    """Residuals of one campaign against the project it references; refuses a mismatched project."""
    if campaign.synthetic:
        raise CalibrationError(f"{campaign.id}: los datos sintéticos no son evidencia")
    if issues := project_issues(campaign, project):
        raise CalibrationError(f"{campaign.id}: " + " ".join(issues))
    instruments = {i.id: i for i in campaign.instruments}
    aps = {a.id: a for a in campaign.access_points}
    conditions = {c.id: c for c in campaign.conditions}
    devices = {d.id: d for d in project.devices}
    out, skipped = [], []
    for point in campaign.points:
        if point.status != "measured":
            continue
        setup = aps[point.access_point_id]
        ap_device = devices[setup.project_device_id]
        project_radio = next(r for r in ap_device.radios if r.id == setup.project_radio_id)
        device_instrument = instruments[point.device_instrument_id]
        ap_power = setup.tx_power_dbm.value if setup.tx_power_dbm.value is not None else project_radio.tx_power_dbm
        ap_gain = setup.antenna_gain_dbi.value
        dev_gain = device_instrument.radio.antenna_gain_dbi.value
        assumptions = []
        if ap_gain is None:
            assumptions.append("ganancia de antena del AP desconocida: 0 dBi")
        if dev_gain is None:
            assumptions.append("ganancia de antena del instrumento desconocida: 0 dBi")
        ap_radio = Radio(id="ap", protocol="wifi", frequency_hz=setup.frequency_hz, channel=setup.channel,
                         bandwidth_hz=setup.bandwidth_hz, tx_power_dbm=ap_power,
                         tx_gain_dbi=ap_gain or 0, rx_gain_dbi=ap_gain or 0)
        dev_radio = Radio(id="dev", protocol="wifi", frequency_hz=setup.frequency_hz, channel=setup.channel,
                          bandwidth_hz=setup.bandwidth_hz, tx_power_dbm=device_instrument.radio.tx_power_dbm.value,
                          tx_gain_dbi=dev_gain or 0, rx_gain_dbi=dev_gain or 0)
        ap = ap_device.model_copy(update={"radios": [ap_radio]})
        dev = Device.model_construct(id="__instrument__", name="instrument", role="endpoint", position=point.position,
                                     radios=[dev_radio], evidence="measurement point")
        doors = {wall: state for wall, state in conditions[point.conditions_id].doors.items() if state != "unknown"}
        scenario = ScenarioAssumptions(id="measured-conditions", name="Condiciones registradas", doors=doors)
        for observation in point.rssi:
            receiver = instruments[observation.receiver_instrument_id]
            if receiver.rssi_reporting != "dbm":
                skipped.append(SkippedObservation(campaign_id=campaign.id, point_id=point.id,
                                                  direction=observation.direction,
                                                  reason="el instrumento no informa en dBm"))
                continue
            if observation.direction == "ap-to-device":
                predicted = direction(project, ap, ap_radio, dev, dev_radio, scenario)
            else:
                predicted = direction(project, dev, dev_radio, ap, ap_radio, scenario)
            if predicted is None:
                skipped.append(SkippedObservation(campaign_id=campaign.id, point_id=point.id,
                                                  direction=observation.direction,
                                                  reason="falta la potencia de transmisión de ese sentido"))
                continue
            measured = statistics.median(observation.samples_dbm)
            out.append(PointResidual(campaign_id=campaign.id, site_id=campaign.site_id, split=campaign.split,
                                     point_id=point.id, direction=observation.direction,
                                     samples=len(observation.samples_dbm), measured_median_dbm=measured,
                                     predicted_dbm=predicted.received_power_dbm,
                                     residual_db=measured - predicted.received_power_dbm,
                                     assumptions=assumptions))
    return out, skipped


def calibrate(pairs: list[tuple[MeasurementCampaign, Project]]) -> CalibrationReport:
    """Fit one offset on calibration campaigns; evaluate it on validation campaigns only."""
    campaigns = [campaign for campaign, _ in pairs]
    if leaks := partition_issues(campaigns):
        raise CalibrationError(" ".join(leaks))
    all_residuals, skipped = [], []
    for campaign, project in pairs:
        found, missed = residuals(campaign, project)
        all_residuals += found
        skipped += missed
    fit = [r.residual_db for r in all_residuals if r.split == "calibration"]
    offset = statistics.fmean(fit) if fit else None
    notes = ["El desplazamiento absorbe ganancias y potencias desconocidas; no corrige materiales ni geometría.",
             "Las métricas de validación usan solo viviendas que no intervienen en el ajuste."]
    if offset is None:
        notes.append("Sin puntos de calibración: no se ajusta nada.")
    before, after = [], []
    for name in ("ap-to-device", "device-to-ap", "all"):
        values = [r.residual_db for r in all_residuals
                  if r.split == "validation" and (name == "all" or r.direction == name)]
        before.append(_stats(name, values))
        after.append(_stats(name, [v - offset for v in values] if offset is not None else []))
    return CalibrationReport(offset_db=offset, calibration_points=len(fit), validation_before=before,
                             validation_after=after, residuals=all_residuals, skipped=skipped, notes=notes)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare measurement campaigns with the quick estimator")
    parser.add_argument("pairs", nargs="+", metavar="CAMPAIGN=PROJECT",
                        help="campaign JSON and the project JSON it references, joined by '='")
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    pairs = []
    for item in args.pairs:
        campaign_path, _, project_path = item.partition("=")
        if not project_path:
            parser.error(f"expected CAMPAIGN=PROJECT, got {item}")
        pairs.append((MeasurementCampaign.model_validate_json(Path(campaign_path).read_text(encoding="utf-8")),
                      Project.model_validate_json(Path(project_path).read_text(encoding="utf-8"))))
    try:
        report = calibrate(pairs)
    except CalibrationError as error:
        print(f"No se puede comparar: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# --- Single-campaign check for the API (B-116) ------------------------------------------

class RssiSummary(Model):
    samples: int
    median_dbm: float
    min_dbm: float
    max_dbm: float


class DeliverySummary(Model):
    criterion_id: str
    direction: str
    sent: int
    received: int
    outcome: Literal["pass", "fail", "inconclusive"]


class PointSummary(Model):
    point_id: str
    position: Point
    rssi: dict[str, RssiSummary]
    delivery: list[DeliverySummary]


class MeasurementCheckRequest(Model):
    campaign: MeasurementCampaign
    project: Project | None = None


class MeasurementCheckResult(Model):
    campaign_id: str
    site_id: str
    split: str
    synthetic: bool
    points: dict[str, int] = Field(description="Count of planned, measured and excluded points")
    summary: list[PointSummary]
    project_issues: list[str] | None = Field(description="None when no project was sent")
    residuals: list[PointResidual] | None
    skipped: list[SkippedObservation]
    notes: list[str]


def check(request: MeasurementCheckRequest) -> MeasurementCheckResult:
    """Validate one campaign, describe what it measured and, with its project, compare predictions."""
    campaign, project = request.campaign, request.project
    counts = {status: sum(p.status == status for p in campaign.points) for status in ("planned", "measured", "excluded")}
    notes, issues, found, skipped = [], None, None, []
    if project is None:
        notes.append("Sin proyecto: no se comprueba el encaje ni se calculan residuos.")
    else:
        issues = project_issues(campaign, project)
        if campaign.synthetic:
            notes.append("Campaña sintética de formato: no es evidencia y no se calculan residuos.")
        elif issues:
            notes.append("El proyecto no encaja con la campaña: no se calculan residuos.")
        else:
            found, skipped = residuals(campaign, project)
            notes.append("Residuos = medido − predicho por el estimador rápido; no son una validación.")
    return MeasurementCheckResult(
        campaign_id=campaign.id, site_id=campaign.site_id, split=campaign.split, synthetic=campaign.synthetic,
        points=counts, summary=[PointSummary.model_validate(row) for row in summarize(campaign)],
        project_issues=issues, residuals=found, skipped=skipped, notes=notes)
