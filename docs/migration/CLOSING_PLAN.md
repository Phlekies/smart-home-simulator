# Plan de cierre de la migración (B-133)

Preparado el 2026-11-08 por B (integrador). **Pasos 1–3 ejecutados el mismo día (I-007)**: los merges los
hizo B con autorización del usuario, `main` = 8734c9b y las casillas están marcadas. El paso 4 está en curso:
B asume el papel de A (A-114…A-119).
Ningún paso se marca antes: `[x]` en el [checklist](CHECKLIST.md) exige trabajo en `main` y evidencia en
[STATUS](STATUS.md).

## Decisiones ya tomadas por el usuario (2026-11-08)

- **Motor:** la migración se cierra con el estimador directo ([ADR-008](ARCHITECTURE.md)).
- **Instalación:** basta con Python. `python scripts/start.py` lo prepara todo; el zip de
  `scripts/package_local.py` incluye la web compilada (B-131).

## 1. Merges (usuario)

Orden: #11 → #13 → #15 → #16 → #17 → #22 → #23 → #24 → #25. Antes de fusionar cada PR
apilado, cambiar su base a `main`. El #14 de A (incluye el #12) puede ir antes o después.

El ensayo I-006 del 2026-11-08 fusionó todo sobre `main` (6fb42e2) en un worktree temporal **sin
conflictos**. En el árbol resultante:
- 438 pruebas Python y contratos sin deriva;
- el script `contracts` de A sin deriva en sus 6 tipos;
- build (`tsc` + vite) y 120 pruebas web;
- paquete local generado y arranque del servidor único correcto.

Repetido el mismo día con B-134/B-135: 444 pruebas Python, contratos y tipos de A sin deriva,
build y 120 pruebas web, sin conflictos.

## 2. Verificación en `main` (B, al terminar los merges)

1. CI de `main` en verde: migración y Java (Linux, Windows y macOS).
2. En local, sobre `main`:
   - `pytest`, `export_contracts.py --check` y `git diff --check`;
   - `npm test` y `npm run build`;
   - `python scripts/start.py --prepare-only` en un clon nuevo.
3. Recorrido corto en el navegador: importar, editar, calcular, comparar, guardar y recuperar.

## 3. Casillas que se marcan con esa verificación

| Fase | Punto | Evidencia ya registrada |
|---|---|---|
| M3 | Conversión de unidades, ejes, geometría, radios y materiales | B-102 + B-121 (76 sondas ≤ 0.0022 dB) |
| M3 | Diferencias respecto a Java explicadas | B-101/B-102 + contraste multipath B-121 + [ADR-008](ARCHITECTURE.md) |
| M4 | Comparación de posiciones y optimización con restricciones | A-105, A-110 (#14), B-105, B-119 y evaluación bajo incertidumbre B-134 |
| M5 | Pruebas de fórmulas/geometría y regresiones | B-126 (47 casos) + paridad B-121 |
| M5 | E2E crear/importar, editar, calcular, comparar y guardar | B-111 (API) + B-127 (navegador) + paso 2.3 |
| M5 | Documentación del ámbito real y motores | B-125 [SCOPE_AND_ENGINES](SCOPE_AND_ENGINES.md) + ADR-008 |
| M2 | Imagen de referencia con escala | A-102 (#12/#14) + B-104. Las **cotas** se comprueban en la interfaz; si faltan, es tarea de A |

## 4. Lo que seguirá abierto: interfaz (A)

| Punto | Qué falta | Apoyo de B ya disponible |
|---|---|---|
| M2 · Accesibilidad y recorrido de creación | Revisión completa y recorrido guiado | — |
| M4 · Mapas guardables | Guardar el mapa como archivo local, reabrirlo y marcarlo obsoleto | `POST /api/projects/fingerprint` (B-132): un mapa guardado vale si coinciden `input_hash` y `engine_version` |
| M4 · Predicción separada de recomendación de compra | Revisar los textos de la interfaz | La API nunca recomienda comprar |
| Matriz · Informe | Botón de descarga con mapas | `POST /api/reports` y `/api/reports/markdown` con `maps` (B-115/B-120) |
| Matriz · Plano | Zoom y desplazamiento; exportar imagen | — |

## 5. Declaración de cierre (B, con el usuario)

Cuando M0–M5 estén marcadas:
1. Actualizar [ROADMAP](ROADMAP.md) («Puerta de finalización»), [FEATURE_MATRIX](FEATURE_MATRIX.md) y STATUS.
2. Proponer al usuario qué hacer con Java: conservarlo como referencia, que es lo que hacen hoy
   ADR-001 y la ruta, o retirarlo en una tarea propia con su motivo y pruebas. Nada se borra sin
   esa decisión.
3. Recordar que cerrar la migración **no** valida la precisión: P0–P4 (criterio de fallo, medidas,
   calibración y evaluación independiente) siguen en el [plan del producto](../product/DEVELOPMENT_PLAN.md).
