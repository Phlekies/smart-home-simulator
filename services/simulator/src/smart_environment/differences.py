"""Exact difference between two versions of a project, link by link (B-123, P3).

For each link present in both versions and each direction, the change of received power is
split into the terms of the quick estimator's budget (transmit power, antenna gains, system
gain, path loss, walls, extra loss, polarization). The terms add up to the change exactly, so
the explanation is the model's own arithmetic, not a guess about real-world causes. Residual
risks list what the alternative still rests on: unknown doors and uncertain materials on its
path, missing data and positions outside the model.
"""

from __future__ import annotations

import time
from typing import Literal

from pydantic import Field, model_validator

from .engines import LIMITATIONS, Budget, budget, geometry_issue, input_hash, link_result
from .models import Link, Model, Project

ENGINE_VERSION = "0.1.0"
Term = Literal["tx_power", "tx_antenna_gain", "rx_antenna_gain", "system_gain", "path_loss", "walls",
               "extra_loss", "polarization"]


class DifferenceRequest(Model):
    base: Project
    alternative: Project
    engine: Literal["quick-estimate", "sionna-rt", "ns-3"] = "quick-estimate"

    @model_validator(mode="after")
    def comparable(self) -> DifferenceRequest:
        if not {link.id for link in self.base.links} & {link.id for link in self.alternative.links}:
            raise ValueError("The two versions share no link id: nothing to compare")
        return self


class BudgetTerm(Model):
    term: Term
    base_db: float = Field(description="Contribution to the received power in the base version (losses negative)")
    alternative_db: float
    change_db: float = Field(description="alternative − base; the terms add up to the change of received power")


class WallChange(Model):
    wall_id: str
    change: Literal["no-longer-crossed", "newly-crossed", "loss-changed"]
    change_db: float = Field(description="Effect on the received power (positive helps)")


class DirectionDifference(Model):
    direction: Literal["forward", "reverse"]
    base_dbm: float | None
    alternative_dbm: float | None
    change_db: float | None
    base_margin_db: float | None
    alternative_margin_db: float | None
    terms: list[BudgetTerm] = Field(description="Empty when either version lacks this direction")
    walls: list[WallChange]
    reason: str | None = None


class LinkDifference(Model):
    link_id: str
    base_status: str
    alternative_status: str
    forward: DirectionDifference
    reverse: DirectionDifference
    base_limiting_margin_db: float | None
    alternative_limiting_margin_db: float | None
    limiting_change_db: float | None
    residual_risks: list[str] = Field(description="What the alternative still rests on; no probabilities")


class DifferenceResult(Model):
    engine: str
    engine_version: str
    base_hash: str
    alternative_hash: str
    links: list[LinkDifference]
    unmatched_link_ids: list[str] = Field(description="Links missing in one version or with different ends")
    elapsed_ms: float
    scope: str
    limitations: list[str]


def _contributions(terms: Budget) -> dict[Term, float]:
    return {"tx_power": terms.tx_power_dbm, "tx_antenna_gain": terms.tx_gain_db, "rx_antenna_gain": terms.rx_gain_db,
            "system_gain": terms.system_gain_db, "path_loss": -terms.path_loss_db, "walls": -terms.wall_loss_db,
            "extra_loss": -terms.extra_loss_db, "polarization": -terms.polarization_loss_db}


def _ends(project: Project, link: Link, reverse: bool):
    devices = {d.id: d for d in project.devices}
    source, target = devices[link.source_device_id], devices[link.target_device_id]
    a = next(r for r in source.radios if r.id == link.source_radio_id)
    b = next(r for r in target.radios if r.id == link.target_radio_id)
    return (target, b, source, a) if reverse else (source, a, target, b)


def _direction(base: Project, alternative: Project, link: Link, reverse: bool) -> DirectionDifference:
    side = "reverse" if reverse else "forward"
    versions = []
    for project in (base, alternative):
        tx, tx_radio, rx, rx_radio = _ends(project, link, reverse)
        versions.append((budget(project, tx, tx_radio, rx, rx_radio), rx_radio.sensitivity_dbm))
    (old, old_sensitivity), (new, new_sensitivity) = versions
    margin = [None if terms is None or sensitivity is None else terms.received_dbm - sensitivity
              for terms, sensitivity in versions]
    if old is None or new is None:
        missing = " y ".join(name for name, terms in (("la base", old), ("la alternativa", new)) if terms is None)
        return DirectionDifference(
            direction=side, base_dbm=None if old is None else old.received_dbm,
            alternative_dbm=None if new is None else new.received_dbm, change_db=None, base_margin_db=margin[0],
            alternative_margin_db=margin[1], terms=[], walls=[],
            reason=f"Falta la potencia de transmisión de este sentido en {missing}.")
    before, after = _contributions(old), _contributions(new)
    terms = [BudgetTerm(term=name, base_db=before[name], alternative_db=after[name],
                        change_db=after[name] - before[name]) for name in before]
    old_walls, new_walls = dict(old.walls), dict(new.walls)
    walls = []
    for wall_id in list(dict.fromkeys([*new_walls, *old_walls])):
        if wall_id not in new_walls:
            walls.append(WallChange(wall_id=wall_id, change="no-longer-crossed", change_db=old_walls[wall_id]))
        elif wall_id not in old_walls:
            walls.append(WallChange(wall_id=wall_id, change="newly-crossed", change_db=-new_walls[wall_id]))
        elif new_walls[wall_id] != old_walls[wall_id]:
            walls.append(WallChange(wall_id=wall_id, change="loss-changed",
                                    change_db=old_walls[wall_id] - new_walls[wall_id]))
    return DirectionDifference(direction=side, base_dbm=old.received_dbm, alternative_dbm=new.received_dbm,
                               change_db=new.received_dbm - old.received_dbm, base_margin_db=margin[0],
                               alternative_margin_db=margin[1], terms=terms, walls=walls)


def _limiting(forward: float | None, reverse: float | None) -> float | None:
    return None if forward is None or reverse is None else min(forward, reverse)


def _risks(project: Project, link: Link, status: str, crossed: set[str], directions) -> list[str]:
    walls = {w.id: w for w in project.building.walls}
    materials = {m.id: m for m in project.building.materials}
    risks = []
    for wall_id in sorted(crossed):
        wall = walls[wall_id]
        if wall.door == "unknown":
            risks.append(f"La puerta {wall_id} del trayecto alternativo tiene estado desconocido.")
        if (uncertainty := materials[wall.material_id].uncertainty) is not None:
            risks.append(f"El material de {wall_id} es incierto ({uncertainty.loss_db_24ghz_low:g}–"
                         f"{uncertainty.loss_db_24ghz_high:g} dB a 2.4 GHz).")
    devices = {d.id: d for d in project.devices}
    for device_id in (link.source_device_id, link.target_device_id):
        if issue := geometry_issue(project, devices[device_id].position, devices[device_id].name):
            risks.append(issue)
    risks += [f"Sentido {'ida' if d.direction == 'forward' else 'vuelta'}: {d.reason}"
              for d in directions if d.reason]
    if any(d.alternative_dbm is not None and d.alternative_margin_db is None for d in directions):
        risks.append("Falta la sensibilidad de algún receptor en la alternativa: sin margen en ese sentido.")
    if status == "below-threshold":
        risks.append("La alternativa tiene margen negativo en algún sentido.")
    return risks


def compare(request: DifferenceRequest) -> DifferenceResult:
    started = time.perf_counter()
    base, alternative = request.base, request.alternative
    old_links = {link.id: link for link in base.links}
    new_links = {link.id: link for link in alternative.links}
    links, unmatched = [], sorted(set(old_links) ^ set(new_links))
    for link in alternative.links:
        previous = old_links.get(link.id)
        if previous is None:
            continue
        if previous.model_dump() != link.model_dump():
            unmatched.append(link.id)
            continue
        old_result, new_result = link_result(base, previous), link_result(alternative, link)
        directions = [_direction(base, alternative, link, reverse) for reverse in (False, True)]
        forward, reverse = directions
        crossed = {wall_id for d in (new_result.forward, new_result.reverse) if d is not None
                   for wall_id in d.crossed_wall_ids}
        before = _limiting(forward.base_margin_db, reverse.base_margin_db)
        after = _limiting(forward.alternative_margin_db, reverse.alternative_margin_db)
        links.append(LinkDifference(
            link_id=link.id, base_status=old_result.status, alternative_status=new_result.status,
            forward=forward, reverse=reverse, base_limiting_margin_db=before, alternative_limiting_margin_db=after,
            limiting_change_db=None if before is None or after is None else after - before,
            residual_risks=_risks(alternative, link, new_result.status, crossed, directions)))
    return DifferenceResult(
        engine="quick-estimate", engine_version=ENGINE_VERSION, base_hash=input_hash(base),
        alternative_hash=input_hash(alternative), links=links, unmatched_link_ids=sorted(set(unmatched)),
        elapsed_ms=(time.perf_counter() - started) * 1000,
        scope="Diferencia del presupuesto de trayecto directo entre dos versiones del proyecto; los términos "
              "son la aritmética del modelo, no causas medidas",
        limitations=LIMITATIONS + ["El multipath puede cambiar la diferencia: en el contraste con Java (B-121) "
                                   "añadió de +0.3 a +3.6 dB en viviendas y hasta +33 dB en un almacén."])
