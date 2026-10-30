# Perfiles de radio genéricos con procedencia (B-106)

Versión 1 · 2026-10-30. Catálogo: `services/simulator/src/smart_environment/profiles.py`.
Modelos: `ProfileValue` y `GenericProfile` en `models.py`. API: `GET /api/profiles`.
Esquema: `contracts/radio-profile.schema.json`. Tipos TS: `apps/web/src/generated/radio-profile.ts`.

## Para qué sirven

Permiten explorar un mapa o una ubicación **antes de elegir un producto concreto** (P0/P5),
con valores trazables. Son aproximaciones conservadoras, **no** datos de ningún equipo. Cuando
la persona conoce su equipo, sustituye los valores por los declarados (`declared`) o medidos
(`measured`) y la procedencia cambia en consecuencia.

## Catálogo inicial (Wi-Fi 2.4 GHz)

| Perfil | Modo | Sensibilidad | Potencia TX | Ganancia | Figura de ruido |
|---|---|---|---|---|---|
| `wifi4-ht20-mcs0` | HT 20 MHz, 1 flujo, MCS0 (BPSK 1/2) | −82 dBm, mínimo del estándar | desconocida | 0 dBi, inferida | 7 dB, inferida |
| `wifi4-ht20-mcs3` | HT 20 MHz, 1 flujo, MCS3 (16-QAM 1/2) | −74 dBm, mínimo del estándar | desconocida | 0 dBi, inferida | 7 dB, inferida |
| `wifi4-ht20-mcs7` | HT 20 MHz, 1 flujo, MCS7 (64-QAM 5/6) | −64 dBm, mínimo del estándar | desconocida | 0 dBi, inferida | 7 dB, inferida |

### Procedencia y verificación

- Sensibilidades: IEEE Std 802.11-2020, tabla 21-25 (receptor mínimo, 20 MHz, PER 10 % con PSDU
  de 4096 octetos), comprobadas el 2026-10-30 en la reproducción de MathWorks WLAN Toolbox
  («802.11ac Receiver Minimum Input Sensitivity Test»). Esa tabla es la de VHT (5 GHz). Se usa como
  mínimo de un receptor OFDM de 20 MHz; **la tabla HT de 2.4 GHz (cláusula 19) no se ha cotejado**
  directamente. Pendiente: verificarla en la norma antes de dar el perfil por validado.
- Potencia de transmisión: no hay valor de estándar; se deja desconocida. El máximo regulatorio
  (PIRE) es un techo legal, no una potencia típica, y no se usa como valor por defecto.
- Ganancia de antena y figura de ruido: inferidas, porque el contrato exige un número; la figura de
  ruido solo afecta al ruido/SNR informado, no al margen respecto a la sensibilidad.
- 802.11b/g: no se incluyen; sus mínimos no se pudieron verificar en esta entrega.

## Cómo se usan

`GenericProfile.receiver_profile(radio_del_AP)` crea el `ReceiverProfile` de un mapa (B-103): un
cliente Wi-Fi sigue la frecuencia y el canal del AP. Rechaza un AP fuera de 2.4 GHz o con otro
ancho de banda. Sin potencia declarada, el sentido equipo→AP queda sin calcular y las celdas
salen `partial`, como exige el objetivo: no se inventa la vuelta.

## Lo que un perfil no dice

- La sensibilidad mínima corresponde a PER 10 % con paquetes de 4096 octetos; **no** es el criterio
  activo de fallo de un sensor, que sigue pendiente de decisión ([protocolo piloto](PILOT_PROTOCOL.md)).
- Un margen positivo frente a un mínimo del estándar no garantiza el funcionamiento ni clasifica
  la cobertura: la reserva de diseño (P2) no está fijada.
- No hay perfiles de Zigbee, Thread, 5 GHz ni de productos comerciales.
