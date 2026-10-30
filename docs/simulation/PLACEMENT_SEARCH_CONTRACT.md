# Búsqueda de ubicación del AP entre lugares permitidos (B-105)

Versión 1 · 2026-10-30. Modelos: `PlacementCandidate`, `PlacementZone`, `PlacementSearchParameters`,
`PlacementSearchRequest` y `PlacementSearchResult` en `models.py`. Cálculo: `placement.py`.
Esquema: `contracts/placement-search.schema.json`. Tipos TS: `apps/web/src/generated/placement-search.ts`.

## Qué responde

«¿Dónde, entre los sitios donde **puedo** poner el router, mejora más el enlace del equipo que
peor está?». Corresponde a M4 («optimización básica con restricciones») y a la búsqueda
exhaustiva pequeña de P3, que sirve de referencia antes de cualquier heurística. No recomienda
compras ni clasifica cobertura.

## Diferencias con el optimizador Java

| Java (`HubPlacementOptimizer`) | B-105 |
|---|---|
| Cada metro entero del área es candidato | Solo lugares declarados por la persona (puntos con etiqueta o zonas muestreadas) |
| Solo sensor → hub | Ambos sentidos con la radio de cada equipo; cuenta el **margen limitante** |
| Sensibilidad global del hub | Sensibilidad y potencia de cada radio; sin datos, no hay margen |
| Orden: inalcanzables, peor margen, media | Orden: equipos con márgenes completos, peor margen limitante (máx-mín), media |

## Endpoint (aditivo)

`POST /api/placement-searches` con `{ ...PlacementSearchParameters, project }` → **200**
`PlacementSearchResult`. Responde 422 si los datos no son válidos, no hay ningún enlace evaluable
o el coste es excesivo, y 501 si el motor no está implementado (sin fallback). Es síncrono porque
está acotado: como máximo 2000 lugares y 2 000 000 evaluaciones lugar×equipo×pared. Medido:
1262–1491 lugares de los ejemplos en 0.14–0.26 s.

Parámetros:
- `access_point_device_id` y `access_point_radio_id`: el AP que se movería.
- `target_device_ids`: equipos prioritarios; vacío significa todos los enlazados con esa radio.
- `candidates`: puntos con `id`, etiqueta y posición con altura.
- `zones`: rectángulos con altura y paso de 0.25–10 m.
- `engine`.

## Semántica

- **Línea base:** la posición actual (`candidate_id = "current"`), evaluada igual que los demás.
- **Por equipo:** margen AP→equipo (`forward`), equipo→AP (`reverse`), margen limitante y su
  sentido, y estado `complete`, `incomplete` (falta potencia o sensibilidad) o `not-computed`
  (radio incompatible o a menos de 0.1 m).
- **Por lugar:** equipos completos, peor margen y su equipo, media, y `delta_worst_margin_db`
  frente a la línea base (solo si ambos tienen los mismos equipos completos).
- `ranked = false` si ningún lugar tiene márgenes completos: los candidatos se devuelven sin ordenar.
- Los lugares dentro del grosor de una pared se excluyen con su motivo. Se devuelven los 50 mejores.
- El resultado repite `parameters`, `input_hash` y `request_hash` para detectar obsolescencia.

## Trabajo del consumidor (A)

1. Añadir `placement-search.ts` al script `contracts` de `apps/web/package.json`.
2. Permitir marcar lugares permitidos (puntos o zonas con altura) y equipos prioritarios.
3. Mostrar la línea base y las alternativas por equipo y sentido, explicando el equipo limitante.
4. Aplicar una alternativa solo como acción explícita y deshacible, y descartar los resultados
   al editar el proyecto. La comparación manual A-105 puede reutilizarse tras aplicar.

## Límites

- Mueve un único AP. Añadir un AP exige definir su enlace de datos (P3) y no se evalúa.
- Trayecto directo del estimador rápido. Con Sionna, el orden podría cambiar por multipath:
  hay que aplicar las condiciones de [B-102](ADVANCED_ENGINE_EVALUATION.md).
- Alimentación, cableado y montaje los garantiza la persona al declarar los lugares.
