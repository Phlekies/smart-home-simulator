"""Loss-aware import of the original Java JSON format."""

from copy import deepcopy
from typing import Any

from .models import Building, Device, Link, Material, Point, Project, Radio, Settings, Wall

# Preserve the actual Java empirical table; these values are not measured guarantees.
MATERIALS = [
    Material(id=key, name=name, loss_db_24ghz=a, loss_db_5ghz=b, extra_loss_db_per_cm=c)
    for key, name, a, b, c in [
        ("drywall", "Drywall", 3, 5, 0), ("brick", "Brick", 6, 9, .1),
        ("concrete", "Concrete", 10, 15, .2), ("glass", "Glass", 2, 3, 0),
        ("wood", "Wood", 3, 5, .05), ("metal-door", "Metal door", 18, 25, 0),
    ]
]


def import_project(data: dict[str, Any]) -> Project:
    if data.get("format") == "smart-environment-simulator":
        return Project.model_validate(data)
    if data.get("format") != "smart-home-simulator" or type(data.get("version")) is not int or data["version"] != 1:
        raise ValueError("Unsupported project format/version; expected Java v1 or native v1")
    env, settings = data["environment"], data["settings"]
    material_ids = {m.name.lower(): m.id for m in MATERIALS}
    walls = []
    for index, wall in enumerate(data["walls"]):
        name = wall["material"].lower()
        if name not in material_ids:
            raise ValueError(f"Unknown Java material: {wall['material']}")
        walls.append(Wall(id=f"wall-{index + 1}", start=Point(x=wall["x1"], y=wall["y1"]),
                          end=Point(x=wall["x2"], y=wall["y2"]), material_id=material_ids[name],
                          thickness_m=wall["thicknessCm"] / 100))
    if len(data["sensors"]) > 128:
        raise ValueError("Too many legacy sensors")
    devices: list[Device] = []
    for sensor in data["sensors"]:
        if sensor["antenna"] not in ("OMNIDIRECTIONAL", "DIRECTIONAL"):
            raise ValueError("Unknown legacy antenna")
        devices.append(Device(
            id=sensor["id"], name=sensor["name"], role="endpoint",
            position=Point(x=sensor["x"], y=sensor["y"], z=1.4),
            radios=[Radio(id="radio-1", frequency_hz=env["frequencyMHz"] * 1e6,
                          bandwidth_hz=env["bandwidthHz"], tx_power_dbm=sensor["txPowerDbm"],
                          tx_gain_dbi=sensor["txGainDb"], rx_gain_dbi=sensor["txGainDb"],
                          sensitivity_dbm=None, noise_figure_db=env["noiseFigureDb"],
                          antenna=sensor["antenna"].lower(), orientation_deg=sensor["orientationDeg"],
                          beamwidth_deg=sensor["beamwidthDeg"], pattern_sharpness=sensor["patternSharpness"],
                          side_lobe_attenuation_db=sensor["sideLobeAttenuationDb"],
                          polarization_deg=sensor["polarizationDeg"])],
        ))
    links = []
    if hub := data.get("hub"):
        for device in devices:
            links.append(Link(id=f"link-{device.id}", source_device_id=device.id, source_radio_id="radio-1",
                              target_device_id=hub["id"], target_radio_id="radio-1"))
        devices.append(Device(id=hub["id"], name=hub["name"], role="controller",
                              position=Point(x=hub["x"], y=hub["y"], z=1.3),
                              radios=[Radio(id="radio-1", frequency_hz=env["frequencyMHz"] * 1e6,
                                            bandwidth_hz=env["bandwidthHz"], tx_power_dbm=None,
                                            rx_gain_dbi=hub["receiverGainDb"],
                                            sensitivity_dbm=settings["receiverSensitivityDbm"],
                                            noise_figure_db=env["noiseFigureDb"],
                                            polarization_deg=hub["polarizationDeg"])]))
    xs = [p for w in walls for p in (w.start.x, w.end.x)] + [d.position.x for d in devices]
    ys = [p for w in walls for p in (w.start.y, w.end.y)] + [d.position.y for d in devices]
    return Project(
        name=f"Java · {data.get('template') or 'Proyecto importado'}",
        building=Building(width_m=max([20, *xs]) + 2, depth_m=max([15, *ys]) + 2,
                          walls=walls, materials=[m.model_copy() for m in MATERIALS]),
        devices=devices, links=links,
        settings=Settings(path_loss_exponent=settings["pathLossExponent"],
                          extra_loss_db_per_m=env["extraLossDbPerMeter"], system_gain_db=env["systemGainDb"]),
        legacy_source=deepcopy(data),
        migration_notes=[
            "El JSON Java original se conserva íntegro en legacy_source.",
            "Alturas inferidas: paredes 2.6 m, sensores 1.4 m y hub 1.3 m; revisar en la vivienda real.",
            "Protocolo y canal desconocidos: la compatibilidad permanece sin verificar.",
            "Java no define potencia TX del hub ni sensibilidad de los sensores: faltan datos bidireccionales.",
            "Ganancia RX de sensores y figura de ruido se han inferido de los valores Java; revisar.",
            "Materiales empíricos heredados sin calibración. Banda de materiales limitada a 2.4/5 GHz.",
            "Antenas se conservan. Multipath, fading, difracción y dispersión quedan guardados en legacy_source; "
            "el estimador rápido solo calcula el trayecto directo.",
        ],
    )
