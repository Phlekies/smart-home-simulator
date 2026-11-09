"""Coverage classification (B-139): decisions U1 and U2 of 2026-11-09, delegated by the user to B.

A link, map cell or point gets one of four classes from its *limiting margin*: the lower of
the two directions, each being received power minus the sensitivity of that receiver at the
rate the profile needs. The design reserve covers what the direct-path estimator does not
model (furniture, people, fading, device spread) and its own unknown error. It is provisional
until the pilot measures that error, and it is frozen before independent validation.

The classes are a prudent reading of an uncalibrated prediction, never a guarantee. See
docs/simulation/COVERAGE_CLASSIFICATION.md for the rationale and the review plan.
"""

from __future__ import annotations

from typing import Literal

from .models import ClassificationPolicy, CoverageClass

DESIGN_RESERVE_DB = 10.0
POLICY_ID: Literal["coverage-class-v1"] = "coverage-class-v1"
FAILURE_CRITERION_TEXT = (
    "Prueba activa del perfil de bajo tráfico: eco ICMP de ida y vuelta desde un equipo cableado al router, "
    "≥ 300 paquetes de 64 B a 1 por segundo (5 min). Falla si se entrega menos del 95 % o si el equipo no se "
    "asocia. Provisional hasta el piloto; se congela antes de recoger datos de validación.")
RULE_TEXT = (
    f"Margen limitante = el menor de ambos sentidos. Favorable: ≥ {DESIGN_RESERVE_DB:g} dB en el proyecto y en el "
    f"peor caso de sus hipótesis. Marginal: entre 0 y {DESIGN_RESERVE_DB:g} dB, o favorable solo si se resuelven "
    "hipótesis. Insuficiente: algún sentido por debajo de 0 dB. Sin datos: falta potencia o sensibilidad, radios "
    "sin verificar o incompatibles, banda no soportada o posición fuera del modelo.")

POLICY = ClassificationPolicy(id=POLICY_ID, design_reserve_db=DESIGN_RESERVE_DB, rule=RULE_TEXT,
                              failure_criterion=FAILURE_CRITERION_TEXT, calibrated=False)


def classify_margin(limiting_margin_db: float | None) -> CoverageClass:
    """Class of one limiting margin that is otherwise classifiable (compatible radios, inside the model)."""
    if limiting_margin_db is None:
        return "no-data"
    if limiting_margin_db < 0:
        return "insufficient"
    return "marginal" if limiting_margin_db < DESIGN_RESERVE_DB else "favourable"


def classify_link(status: str, nominal_db: float | None, worst_case_db: float | None) -> CoverageClass:
    """Class of a project link from its status and its nominal and worst-case limiting margins.

    A negative margin in either direction is insufficient even if the other one is unknown. Any
    status other than above/below threshold (missing data, unverified or incompatible radios,
    unsupported band, position outside the model) gives no data. A favourable class needs the
    reserve both as drawn and with every unresolved door and material at its worst.
    """
    if status == "below-threshold":
        return "insufficient"
    if status != "above-threshold" or nominal_db is None:
        return "no-data"
    worst = nominal_db if worst_case_db is None else worst_case_db
    if nominal_db >= DESIGN_RESERVE_DB and worst >= DESIGN_RESERVE_DB:
        return "favourable"
    return "marginal"


def classify_outcome(link_status: str, margins: list[float | None]) -> CoverageClass:
    """Class of one scenario of a link, bounded by the link's own status.

    A negative direction is insufficient in that scenario; otherwise a link that cannot be
    classified as drawn (missing data, unverified radios, position outside the model) stays
    without data in every scenario.
    """
    if any(m is not None and m < 0 for m in margins):
        return "insufficient"
    if link_status not in ("above-threshold", "below-threshold"):
        return "no-data"
    return classify_margin(limiting(*margins))


def limiting(*margins: float | None) -> float | None:
    """Lower margin of both directions; None if either is missing."""
    return None if any(m is None for m in margins) or not margins else min(margins)  # type: ignore[type-var]
