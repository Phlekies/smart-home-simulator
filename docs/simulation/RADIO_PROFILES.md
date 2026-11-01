# Perfiles de radio genéricos con procedencia (B-106, B-118)

Versión 2 · 2026-11-01 (perfiles de AP en B-118). Catálogo: `services/simulator/src/smart_environment/profiles.py`.
Modelos: `ProfileValue`, `GenericProfile` y `ProfileRadioRequest` en `models.py`.
API: `GET /api/profiles?role=client|access-point` y `POST /api/profiles/{id}/radio`.
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

Perfiles de AP o router (`roles = ["access-point"]`, B-118), con los mismos modos y sensibilidades:

| Perfil | Sensibilidad | Potencia TX | Ganancia | Notas |
|---|---|---|---|---|
| `wifi4-ht20-ap-mcs0`, `-mcs3`, `-mcs7` | −82, −74 y −64 dBm, mínimo del estándar | desconocida, con el límite legal de la UE en la fuente | 0 dBi, inferida | Sin MIMO, diversidad ni conformación de haz; la sensibilidad del AP limita el sentido equipo→AP |

### Procedencia y verificación

- Sensibilidades: IEEE Std 802.11-2020, tabla 21-25 (receptor mínimo, 20 MHz, PER 10 % con PSDU
  de 4096 octetos), comprobadas el 2026-10-30 en la reproducción de MathWorks WLAN Toolbox
  («802.11ac Receiver Minimum Input Sensitivity Test»). Esa tabla es la de VHT (5 GHz). Se usa como
  mínimo de un receptor OFDM de 20 MHz; **la tabla HT de 2.4 GHz (cláusula 19) no se ha cotejado**
  directamente. El 2026-11-01 (B-118) se buscó una fuente primaria pública. Solo aparecieron
  reproducciones secundarias y borradores IEEE con los mismos valores para MCS0–7 (−82 … −64 dBm),
  así que la procedencia sigue siendo «mínimo del estándar» con esta salvedad en la fuente.
  Pendiente: verificarla en el texto de la norma antes de dar el perfil por validado.
- Potencia de transmisión: no hay valor de estándar; se deja desconocida. El máximo regulatorio
  (PIRE) es un techo legal, no una potencia típica, y no se usa como valor por defecto. Los perfiles
  de AP citan el de la UE (20 dBm PIRE, según resúmenes de ETSI EN 300 328 V2.2.2 no cotejados con
  la norma) solo como información.
- Ganancia de antena y figura de ruido: inferidas, porque el contrato exige un número; la figura de
  ruido solo afecta al ruido/SNR informado, no al margen respecto a la sensibilidad.
- 802.11b/g: no se incluyen; sus mínimos no se pudieron verificar en esta entrega.

## Cómo se usan

`GenericProfile.receiver_profile(radio_del_AP)` crea el `ReceiverProfile` de un mapa (B-103): un
cliente Wi-Fi sigue la frecuencia y el canal del AP. Rechaza un AP fuera de 2.4 GHz o con otro
ancho de banda. Sin potencia declarada, el sentido equipo→AP queda sin calcular y las celdas
salen `partial`, como exige el objetivo: no se inventa la vuelta.

`POST /api/profiles/{id}/radio` con `{ role, channel (1–13), radio_id? }` devuelve un `Radio` listo para
un equipo del proyecto en ese canal: frecuencia 2407 + 5·canal MHz, procedencia de cada valor y
potencia vacía si es desconocida. Responde 422 si el perfil no admite ese papel o el canal no es
OFDM de 2.4 GHz, y 404 si el perfil no existe. `GET /api/profiles` sin parámetro sigue devolviendo
solo clientes, así que los selectores de mapas existentes no muestran perfiles de AP.

## Lo que un perfil no dice

- La sensibilidad mínima corresponde a PER 10 % con paquetes de 4096 octetos; **no** es el criterio
  activo de fallo de un sensor, que sigue pendiente de decisión ([protocolo piloto](PILOT_PROTOCOL.md)).
- Un margen positivo frente a un mínimo del estándar no garantiza el funcionamiento ni clasifica
  la cobertura: la reserva de diseño (P2) no está fijada.
- No hay perfiles de Zigbee, Thread, 5 GHz ni de productos comerciales.
- Trabajo del consumidor (A, B-118): ofrecer «Aplicar perfil de AP» en el inspector de la radio de un
  router o AP, con el canal, y mostrar la procedencia y la potencia que falta por declarar.
