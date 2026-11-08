"""Generic 2.4 GHz Wi-Fi profiles (B-106 clients, B-118 access points). Every value states where it comes from.

Sensitivities are the minimum a compliant 20 MHz OFDM receiver must reach (10 % PER with a
4096-octet PSDU), so real devices are usually better; the profiles are conservative bounds,
not product data. Transmit power has no standard value and stays unknown until declared.
"""

from .models import GenericProfile, ProfileValue

STANDARD_SOURCE = ("IEEE Std 802.11-2020, tabla 21-25 (VHT, 20 MHz, PER 10 % con PSDU de 4096 octetos), "
                   "reproducida por MathWorks WLAN Toolbox. La tabla HT de 2.4 GHz (cláusula 19) no se ha "
                   "cotejado con el texto de la norma: el 2026-11-01 solo se hallaron reproducciones secundarias "
                   "con los mismos valores")
EU_POWER_LIMIT = ("En la UE la PIRE máxima en 2.4 GHz es 20 dBm (100 mW), según resúmenes de ETSI EN 300 328 "
                  "V2.2.2 no cotejados con el texto de la norma. Es un límite legal, no la potencia del equipo.")
_MINIMUMS = {0: -82, 3: -74, 7: -64}
_MODES = {0: "BPSK 1/2", 3: "16-QAM 1/2", 7: "64-QAM 5/6"}


def _sensitivity(mcs: int) -> ProfileValue:
    return ProfileValue(value=_MINIMUMS[mcs], provenance="standard-minimum", source=STANDARD_SOURCE)


def _noise_figure() -> ProfileValue:
    return ProfileValue(value=7, provenance="inferred",
                        source="Valor por defecto del contrato; solo afecta al ruido/SNR informado, "
                               "no al margen respecto a la sensibilidad.")


def _profile(mcs: int) -> GenericProfile:
    return GenericProfile(
        id=f"wifi4-ht20-mcs{mcs}",
        name=f"Wi-Fi 2.4 GHz genérico · HT20 MCS{mcs}",
        description=f"Cliente Wi-Fi 4 de una antena en 20 MHz, receptor que solo cumple el mínimo del estándar "
                    f"para MCS{mcs} ({_MODES[mcs]}). Aproximación conservadora; no representa un producto.",
        protocol="wifi", band="2.4GHz", mode=f"HT 20 MHz, 1 flujo, MCS{mcs} ({_MODES[mcs]}), GI 800 ns",
        bandwidth_hz=20e6, roles=["client"],
        sensitivity_dbm=_sensitivity(mcs),
        tx_power_dbm=ProfileValue(source="Sin valor de estándar; declarar la del equipo (ficha técnica o medida)."),
        antenna_gain_dbi=ProfileValue(value=0, provenance="inferred",
                                      source="Antena isotrópica supuesta: la ganancia real del equipo es desconocida."),
        noise_figure_db=_noise_figure(),
        notes=["La sensibilidad mínima está definida para PER 10 % con PSDU de 4096 octetos; no es el criterio "
               "de fallo del enlace de un sensor, que se fija aparte.",
               "Los equipos reales suelen ser más sensibles que el mínimo: el margen calculado es prudente.",
               "Sin potencia de transmisión declarada no se calcula el sentido equipo→AP."],
    )


def _access_point(mcs: int) -> GenericProfile:
    return GenericProfile(
        id=f"wifi4-ht20-ap-mcs{mcs}",
        name=f"AP/router Wi-Fi 2.4 GHz genérico · HT20 MCS{mcs}",
        description=f"Punto de acceso Wi-Fi 4 en 20 MHz cuyo receptor solo cumple el mínimo del estándar para "
                    f"MCS{mcs} ({_MODES[mcs]}), la tasa que usaría el cliente al responder. Aproximación "
                    "conservadora; no representa un producto.",
        protocol="wifi", band="2.4GHz", mode=f"HT 20 MHz, 1 flujo, MCS{mcs} ({_MODES[mcs]}), GI 800 ns",
        bandwidth_hz=20e6, roles=["access-point"],
        sensitivity_dbm=_sensitivity(mcs),
        tx_power_dbm=ProfileValue(source="Sin valor de estándar; declarar la del equipo (ficha técnica o medida). "
                                         + EU_POWER_LIMIT),
        antenna_gain_dbi=ProfileValue(value=0, provenance="inferred",
                                      source="Antena isotrópica supuesta: las antenas de un router suelen tener "
                                             "ganancia, pero su valor y su diagrama son desconocidos."),
        noise_figure_db=_noise_figure(),
        notes=["Sin potencia de transmisión declarada no se calcula el sentido AP→equipo.",
               EU_POWER_LIMIT,
               "Varias antenas (MIMO), diversidad y conformación de haz no se modelan: el AP se trata como una "
               "sola antena.",
               "La sensibilidad del AP limita el sentido equipo→AP, que suele ser el más débil con sensores "
               "de poca potencia."],
    )


CATALOG = [_profile(mcs) for mcs in sorted(_MINIMUMS)] + [_access_point(mcs) for mcs in sorted(_MINIMUMS)]
