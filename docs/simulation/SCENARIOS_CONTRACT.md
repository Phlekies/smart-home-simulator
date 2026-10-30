# Escenarios de puertas y materiales inciertos (B-108)

Versión 1 · 2026-10-30. Modelos: `MaterialUncertainty`, `Material.uncertainty`, `Wall.door`,
`ScenarioAssumptions`, `ScenarioRequest` y `ScenarioResult` en `models.py`. Cálculo: `scenarios.py`.
Esquema: `contracts/scenario-result.schema.json`. Tipos TS: `apps/web/src/generated/scenario-result.ts`
(los campos nuevos de pared y material están en `project.ts`).

## Qué responde (P2)

«¿Qué cambia si esa pared o esa puerta no se comportan como supongo?». Un material desconocido
se evalúa como un **rango razonado de escenarios**, no con una propiedad exacta inventada, y el
resultado indica cuándo la conclusión **depende de hipótesis no resueltas**. Los rangos no son
intervalos de probabilidad y no se publica ninguna probabilidad de éxito.

## Contrato (aditivo, v1)

- `Material.uncertainty` (opcional): pérdidas mínima y máxima por cruce para 2.4 y 5 GHz, más
  `source` con el motivo. La pérdida nominal debe quedar dentro del rango.
- `Wall.door` (opcional): `null` si la pared no es una puerta; `open`, `closed` o `unknown` si lo es.
- Ambos campos son opcionales en JSON Schema y en TypeScript (`door?`, `uncertainty?`). Sin ellos,
  **el hash del proyecto no cambia**, así que los resultados y las campañas de medida existentes
  siguen siendo válidos. Si se rellenan, entran en el hash porque cambian el cálculo.
- Cálculo nominal (simulaciones, mapas, búsqueda de ubicación): una puerta `open` no suma pérdida;
  `closed`, `unknown` o una pared normal cuentan como hasta ahora; los materiales usan su valor nominal.

## Endpoint

`POST /api/scenario-simulations` con `{ project, scenarios?, engine }` → **200** `ScenarioResult`.
Devuelve 422 si un escenario cita algo que no es una puerta, un material sin rango, o un id
reservado o repetido, y 501 si se pide otro motor (sin fallback).

Escenarios evaluados, siempre en este orden:

| id | Puertas `unknown` | Materiales con rango | Resto |
|---|---|---|---|
| `nominal` | cerradas | valor nominal | como en el proyecto |
| `best` | abiertas | mínimo | como en el proyecto |
| `worst` | cerradas | máximo | como en el proyecto |
| escenarios pedidos (hasta 16) | lo que fije cada escenario | `low`/`nominal`/`high` por material | como en el proyecto |

Las puertas declaradas `open` o `closed` son hechos del proyecto y no se varían en mejor ni peor
caso; un escenario con nombre sí puede fijarlas. Con el estimador directo, la potencia recibida
decrece con cada pérdida, así que `best` y `worst` son los extremos **exactos** de esas hipótesis.

## Resultado por enlace

- `outcomes`: resultado de cada sentido en cada escenario (el mismo `DirectionResult` que las simulaciones).
- `forward_range_dbm` / `reverse_range_dbm`: mínimo y máximo entre escenarios, o `null` si no se calcula.
- `hypotheses`: paredes cruzadas por el trayecto con puerta `unknown` o material con rango.
- `margin_sign`:
  - `consistent`: el margen limitante tiene el mismo signo en todos los escenarios.
  - `depends-on-hypotheses`: el signo cambia; la conclusión depende de lo no resuelto.
  - `incomplete`: falta potencia o sensibilidad.

  No es una clasificación de cobertura: la reserva de diseño sigue pendiente.

## Trabajo del consumidor (A)

1. Añadir `scenario-result.ts` al script `contracts` (junto a `placement-search.ts` y `radio-profile.ts`).
2. En el inspector de paredes, marcar una pared como puerta y su estado; en el de materiales,
   declarar el rango y su motivo. Ambos son cambios del proyecto: se deshacen e invalidan resultados.
3. Mostrar por enlace el rango de cada sentido, las hipótesis que lo afectan y `margin_sign`,
   sin convertirlo en un semáforo de cobertura.

## Límites

- Trayecto directo; con un motor multipath el peor caso no tiene por qué coincidir con todas las
  pérdidas máximas, y habría que evaluar las combinaciones (ver [B-102](ADVANCED_ENGINE_EVALUATION.md)).
- Una puerta abierta se modela como ausencia de la pared de la puerta; no se modela la difracción del hueco.
- Orientación del equipo, ruido e interferencia no se varían todavía.
