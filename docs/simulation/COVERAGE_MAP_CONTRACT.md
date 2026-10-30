# Contrato de mapas de cobertura por perfil y altura (B-103)

Versión 1 · 2026-10-30. Modelos: `ReceiverProfile`, `MapGrid`, `CoverageMapParameters`,
`CoverageMapRequest`, `CoverageMapResult` y `CoverageMapJob` en `models.py`. Cálculo y trabajos:
`services/simulator/src/smart_environment/coverage.py`. Esquema: `contracts/coverage-map.schema.json`.
Tipos TS: `apps/web/src/generated/coverage-map.ts`.

## Qué responde

«¿Cómo sería el enlace de **este perfil de equipo**, a **esta altura**, en cada punto del plano,
con **este AP**?», en ambos sentidos. Es la base de P1 y del consumidor A-104. **No** clasifica
cobertura: sin política de reserva acordada (P2), solo se devuelven potencias y márgenes.

## Endpoints (aditivos)

| Método | Ruta | Respuesta |
|---|---|---|
| `POST` | `/api/coverage-maps` | **202** `CoverageMapJob` en cola. 422 datos inválidos, radios incompatibles o coste excesivo; 501 motor no implementado (sin fallback); 429 cola llena |
| `GET` | `/api/coverage-maps/{job_id}` | `CoverageMapJob` con `state` (`queued`, `running`, `done`, `cancelled`, `failed`), `progress` 0–1 y `result` al terminar; 404 desconocido |
| `DELETE` | `/api/coverage-maps/{job_id}` | Cancela: un trabajo en cola pasa a `cancelled` al momento; uno en curso se detiene en la siguiente fila |

Cuerpo de `POST`: `{ ...CoverageMapParameters, project }`. Los parámetros son
`access_point_device_id`/`access_point_radio_id` (radio del AP en el proyecto), `profile` (una
`Radio` completa del equipo candidato, con nombre y procedencia), `grid` (origen, ancho, fondo,
resolución 0.1–5 m y **altura obligatoria**), `points` (hasta 256 posiciones exactas) y `engine`.

## Semántica del resultado

- **Celdas:** la celda (i, j) se evalúa en su centro, `x = origen_x + (i + 0.5)·resolución`, a
  `height_m`. Las matrices están por filas: índice `j·columns + i`. Sin interpolación.
  En el borde, la celda se recorta al ancho/fondo solicitado y se evalúa en el centro
  de ese rectángulo recortado, incluso si el área es menor que una celda. El consumidor
  debe usar ese mismo recorte al dibujarla. Toda la extensión queda dentro de ±10000 m.
- **Ambos sentidos:** `forward` es AP→perfil y `reverse` es perfil→AP, cada uno con su potencia,
  su receptor y su sensibilidad. Un margen de retorno negativo es visible aunque la bajada sea buena.
- **Estados por celda:** `computed` (cuatro valores), `partial` (falta potencia o sensibilidad de
  algún lado) o `not-computed` (dentro de una pared o a menos de 0.1 m del AP). Nunca se rellenan.
- **Puntos exactos:** `points[]` se evalúan en su coordenada, sin redondear a la rejilla (P1).
- **Identificación:** el resultado repite `parameters` y lleva `metric`
  (`direct-path-received-power`), `frequency_hz`, `compatibility` (`radio-compatible`/`unverified`),
  `input_hash` (el mismo hash de proyecto que las simulaciones) y `request_hash` (proyecto y
  todos los parámetros). Un mapa con otro `request_hash` es de otro escenario.
- **Un solo AP:** no se suma la energía de otros AP como si fuese señal de esta conexión.
- Valores de celdas redondeados a 0.001 dB; los puntos exactos conservan toda la precisión.

## Límites y cancelación

- Hasta 40 000 celdas y 256 puntos; como máximo 2 000 000 evaluaciones celda×pared por trabajo.
- Medido el 2026-10-30 (Windows, Python 3.13.7): unas 600 000 evaluaciones por segundo. Apartamento
  a 0.25 m (21 525 celdas, 11 paredes) en 0.5 s y 0.87 MB de JSON; almacén a 0.25 m (29 415
  celdas, 21 paredes) en 1.0 s. El límite acota un trabajo a unos 3–4 s en este equipo.
- Un trabajador en segundo plano, cola e historial de 16 trabajos; al apagar la API se cancelan.
  Los resultados viven en memoria del proceso local: no hay caché persistente.

## Trabajo del consumidor (A-104)

1. Añadir al script `contracts` de `apps/web/package.json` la generación
   `json2ts -i ../../contracts/coverage-map.schema.json -o src/generated/coverage-map.ts`,
   para que la CI detecte deriva. B generó el archivo con ese mismo comando, sin tocar `package.json`.
2. Pedir el mapa con el perfil y la altura elegidos, consultar el progreso y ofrecer cancelar.
3. Mostrar AP, perfil, altura, resolución, métrica y celdas `partial`/`not-computed` con su
   propia leyenda; no convertirlos en «sin cobertura».
4. Descartar el mapa si el proyecto o los parámetros cambian (comparar `request_hash` o la
   revisión del editor), como ya se hace con las simulaciones.
5. No derivar «favorable/insuficiente» en la interfaz mientras la política de reserva no exista.

## Pendiente para un motor avanzado

Según [B-102](ADVANCED_ENGINE_EVALUATION.md), antes de admitir `engine = "sionna-rt"` en mapas:
proceso trabajador aislado (WSL/Linux; Windows nativo no ejecuta), métrica declarada (coherente,
banda ancha o incoherente), comprobación de convergencia frente a `max_depth`, tratamiento de
metales y aberturas, y celdas sin trayecto marcadas como «no convergido», no como señal nula.
Añadir valores a `metric` o a los estados de celda amplía uniones TypeScript: será un cambio de
contrato que se describirá a A antes de implementarlo, aunque la forma de los datos se mantenga.
