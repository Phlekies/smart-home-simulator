"""Data path of access points (B-117): which wireless links carry each AP's data to the gateway.

Only wireless hops are evaluated, with the same link budget as any other link and in both
directions. Cables are declared, not checked. Nothing here classifies coverage: each hop keeps
its status and limiting margin, and missing or unknown connections are reported as such.
"""

from __future__ import annotations

from collections.abc import Callable

from .models import NETWORK_ROLES, AccessPointConnection, BackhaulHop, Device, LinkResult, Project


def limiting_margin(result: LinkResult) -> float | None:
    """Lower margin of both directions, or None when either is missing."""
    margins = [d.margin_db for d in (result.forward, result.reverse) if d is not None and d.margin_db is not None]
    return min(margins) if len(margins) == 2 else None


def is_network_device(device: Device) -> bool:
    return device.role in NETWORK_ROLES or device.data_connection is not None


def connection(project: Project, device: Device,
               link_result: Callable[[str], LinkResult]) -> AccessPointConnection:
    """Follow wireless data links from ``device`` until a gateway, a cable, a gap or a loop."""
    devices = {d.id: d for d in project.devices}
    links = {link.id: link for link in project.links}
    hops: list[BackhaulHop] = []
    reasons: list[str] = []
    seen = {device.id}
    current = device
    while True:
        data = current.data_connection
        if data is None:
            ends_at = "undefined"
            reasons.append(f"{current.name}: conexión de datos sin definir; no se sabe cómo llega a la red.")
            break
        if data.kind != "wireless":
            ends_at = data.kind
            if data.kind == "wired":
                reasons.append(f"{current.name}: conexión por cable declarada, no evaluada.")
            elif data.kind == "unknown":
                reasons.append(f"{current.name}: conexión de datos desconocida; no se puede comprobar el camino.")
            break
        link = links[data.link_id]
        upstream = link.target_device_id if link.source_device_id == current.id else link.source_device_id
        result = link_result(link.id)
        margin = limiting_margin(result)
        hops.append(BackhaulHop(link_id=link.id, from_device_id=current.id, to_device_id=upstream,
                                status=result.status, limiting_margin_db=margin))
        if margin is None:
            reasons.append(f"Enlace de datos {link.id}: sin margen en ambos sentidos ({result.status}).")
        if upstream in seen:
            ends_at = "loop"
            reasons.append(f"El camino de datos vuelve a {devices[upstream].name}: no llega a una pasarela.")
            current = devices[upstream]
            break
        seen.add(upstream)
        current = devices[upstream]
    margins = [hop.limiting_margin_db for hop in hops]
    weakest = min(margins) if hops and None not in margins else None
    kind = "undefined" if device.data_connection is None else device.data_connection.kind
    return AccessPointConnection(device_id=device.id, kind=kind, hops=hops, ends_at=ends_at,
                                 end_device_id=current.id, weakest_margin_db=weakest, reasons=reasons)


def path_note(path: AccessPointConnection) -> str | None:
    """One sentence for results that only make sense if this AP reaches the network."""
    notes = list(path.reasons)
    if path.weakest_margin_db is not None and path.weakest_margin_db < 0:
        notes.append(f"Su enlace de datos más débil tiene margen negativo ({path.weakest_margin_db:.1f} dB).")
    return "Camino de datos del AP: " + " ".join(notes) if notes else None


def access_point_connections(project: Project,
                             link_result: Callable[[str], LinkResult]) -> list[AccessPointConnection]:
    return [connection(project, device, link_result) for device in project.devices if is_network_device(device)]
