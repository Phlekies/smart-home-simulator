# Registro del agente B — simulación, contratos e integración

Este archivo lo mantiene exclusivamente B; A lo lee para conocer contratos/dependencias.
Proceso: [WORKFLOW](WORKFLOW.md). Prioridades: [WORKBOARD](WORKBOARD.md).

## Reserva actual

- Estado: **claimed** — B-106 (perfiles Wi-Fi genéricos con procedencia). B-105 en review.
- Integración: **I-002 la ejecuta A** por instrucción del usuario (registro A, 2026-10-30 09:54):
  A asume temporalmente Git, documentos comunes y `package.json`. B no integra ni edita
  WORKBOARD/STATUS/CHECKLIST/LOCAL_DEVELOPMENT mientras dure, y solo entrega ramas propias.
- Pila B publicada (borradores, sin merge): [PR #3](https://github.com/Phlekies/smart-home-simulator/pull/3) B-101 →
  [PR #4](https://github.com/Phlekies/smart-home-simulator/pull/4) B-102 → [PR #5](https://github.com/Phlekies/smart-home-simulator/pull/5) B-104 →
  [PR #6](https://github.com/Phlekies/smart-home-simulator/pull/6) B-103. Nuevas ramas locales encima: `agent-b/b-105-placement-search`, …
- Sesión/chat: sesión Claude Code (desktop), agente B; sin identificador adicional conocido.
- Rama/worktree: clon B `C:/Users/ibane/Desktop/Programación/SmartHomeSimulator`; no escribe en el
  checkout compartido de A.
- Última actualización: 2026-10-30 (Europe/Madrid).
- Archivos reservados: `services/simulator/**` (código y pruebas de B), contratos generados,
  `scripts/export_contracts.py`, `docs/simulation/**` y este registro.

## Plantilla de entrega — completar al trabajar

```text
Tarea / estado (claimed, review, blocked):
Sesión, rama/worktree, fecha/hora y zona:
Archivos previstos / realmente modificados:
Criterio de aceptación resuelto:
Cambios de contrato y compatibilidad:
Comandos, hardware/versiones y resultados reales:
Límites científicos y medidas pendientes:
Solicitud a A / tarea consumidora:
Integración: qué se revisó, evidencia y documentos consolidados:
Siguiente paso:
```

## Historial

### B-105 — búsqueda de ubicación del AP entre lugares permitidos (review)

```text
Tarea / estado: B-105 / review. Rama local agent-b/b-105-placement-search sobre B-103 (a5e6ff8).
Archivos: models.py (PlacementCandidate, PlacementZone, PlacementSearchParameters/Request/Result,
  TargetEvaluation, CandidateEvaluation, ExcludedCandidate), placement.py (nuevo), api.py
  (POST /api/placement-searches), scripts/export_contracts.py, contracts/placement-search.schema.json
  (nuevo), openapi.json, apps/web/src/generated/placement-search.ts (json2ts), tests/test_placement.py,
  docs/simulation/PLACEMENT_SEARCH_CONTRACT.md.
Criterio: comparar lugares permitidos (puntos/zonas) del AP con búsqueda exhaustiva acotada;
  máx-mín del margen limitante bidireccional de equipos prioritarios; línea base y deltas;
  datos ausentes declarados y sin orden; lugares dentro de paredes excluidos.
Contrato: aditivo (1 ruta, esquemas nuevos; ningún esquema existente cambia, comprobado).
Comandos: pytest → 174 passed; export --check sin deriva; npm run build correcto; npm test 16/16
  (rama B sin las entregas de A). Ejemplos: 1262–1491 lugares en 0.14–0.26 s.
Límites: un AP, trayecto directo, sin clasificación ni enlace de datos para AP nuevos.
Solicitud a A: añadir placement-search.ts y coverage-map.ts al script `contracts`; consumidor
  de lugares permitidos y comparación por equipo/sentido (detalle en el contrato).
```

### Incidente de integración concurrente — 2026-10-30 09:54

B hizo commit de las 34 entregas de A en `agent-a/a-101-a108-ui` (`1b5b596`) en el checkout
compartido, sin tocar el árbol. 17 s después, A (con instrucción del usuario para integrar)
añadió `347691e` y fusionó la pila B publicada (`90ff7ba`). B detectó las dos escrituras, no
cambió de rama ese checkout, retiró la referencia `integration/i-002` que había traído y dejó
su integración local sin publicar. I-002 queda a cargo de A; B no repite esa integración.

### B-103 — mapas por perfil y altura como trabajos cancelables (review)

```text
Tarea / estado: B-103 / review.
Sesión, rama/worktree, fecha/hora y zona: Claude Code agente B; agent-b/b-103-coverage-maps sobre
  agent-b/b-104-plan-reference; 2026-10-30, Europe/Madrid.
Archivos modificados: models.py (ReceiverProfile, MapGrid, CoverageMapParameters/Request/Result,
  CoverageCells, CoverageSample, CoverageMapJob), coverage.py (nuevo), engines.py
  (radio_pair_check extraído de simulate sin cambiar comportamiento), api.py (POST/GET/DELETE
  /api/coverage-maps, lifespan que cancela trabajos), scripts/export_contracts.py,
  contracts/coverage-map.schema.json (nuevo) y openapi.json, apps/web/src/generated/coverage-map.ts
  (generado con json2ts), tests/test_coverage.py (nuevo), docs/simulation/COVERAGE_MAP_CONTRACT.md.
Criterio: mapa por perfil/altura/resolución declarados, ambos sentidos, puntos exactos sin
  redondeo, AP y perfil identificados, celdas sin calcular explícitas, límites, progreso y
  cancelación; tipos generados y pruebas.
Contrato: aditivo (2 rutas, 10 esquemas nuevos; ningún esquema existente cambia, comprobado).
Comandos: pytest → 157 passed; export --check sin deriva; npm run build correcto; npm test 16/16;
  servidor uvicorn real en 127.0.0.1:8765: 202 → progreso → done en 534 ms (175×123 celdas),
  DELETE en cola y en curso → cancelled, sionna-rt → 501, perfil a otra frecuencia → 422.
  Servidor detenido; sin listener en 8765.
Límites: trayecto directo del estimador rápido; sin clasificación (reserva pendiente), sin caché
  persistente, un trabajador local. Sionna en mapas requiere proceso aislado y criterios de B-102.
Solicitud a A (A-104): añadir coverage-map.ts al script `contracts`, consumir los trabajos con
  progreso/cancelación, leyenda de celdas parciales/sin calcular y descarte por request_hash.
Siguiente paso: publicar la pila si el usuario lo autoriza; integrar A-101/A-102 cuando A libere.
```

### B-104 — contrato de la referencia de plano para A-102 (review)

```text
Tarea / estado: B-104 / review. Responde a la «Solicitud a B — persistencia de A-102».
Sesión, rama/worktree, fecha/hora y zona: Claude Code agente B; agent-b/b-104-plan-reference
  sobre agent-b/b-102-sionna-evaluation; 2026-10-30, Europe/Madrid.
Archivos modificados: models.py (PlanReference, PlanReferenceCalibration, PixelPoint,
  Project.plan_reference opcional), engines.py (input_hash excluye plan_reference),
  contracts/project.schema.json y openapi.json (regenerados), apps/web/src/generated/project.ts
  (solo por `npm run contracts`), tests/test_plan_reference.py (nuevo),
  docs/simulation/PLAN_REFERENCE_CONTRACT.md (nuevo).
Criterio: transformación metros/píxel + origen + dimensiones + huella persistibles; imagen local.
Contrato: aditivo y opcional en v1, también en TS (`plan_reference?:`). Hash de cálculo intacto.
  Archivos con el campo no se abren en versiones anteriores (extra=forbid), documentado.
Comandos: pytest → 137 passed; export_contracts.py → regenerado y --check sin deriva;
  npm run contracts → solo project.ts cambia; npm run build correcto; npm test 16/16.
  Copia del código en curso de A con los tipos nuevos: tsc --noEmit correcto, 57/57 pruebas.
Solicitud a A (A-102): rellenar plan_reference con SHA-256 local, exportar/recuperar el campo,
  re-asociar la imagen por huella al abrir y mostrar «imagen no disponible» si no coincide.
  Detalle en docs/simulation/PLAN_REFERENCE_CONTRACT.md. Opacidad/visibilidad fuera del contrato.
Siguiente paso: integrar la pila de ramas de B y avisar a A (vía usuario) de que los tipos existen.
```

### B-102 — evaluación aislada de Sionna RT (review)

```text
Tarea / estado: B-102 / review.
Sesión, rama/worktree, fecha/hora y zona: Claude Code agente B; rama agent-b/b-102-sionna-evaluation
  sobre agent-b/b-101-reference-cases; 2026-10-30, Europe/Madrid.
Archivos modificados: services/simulator/src/smart_environment/sionna_adapter.py (nuevo),
  references.py (compare_predictions; reflexión con R de losa), engines.py (descripción de
  sionna-rt), services/simulator/benchmarks/{sionna_evaluation.py, wsl/setup.sh, wsl/run.sh}
  (nuevos), tests/test_sionna_adapter.py (nuevo), docs/simulation/ADVANCED_ENGINE_EVALUATION.md
  y evidence/sionna-rt-2.2.0-wsl-cpu.json (nuevos), REFERENCE_CASES.md; como integrador
  WORKBOARD, STATUS y CHECKLIST.
Criterio de aceptación: motor ejecutado en entorno aislado con versiones/hardware registrados;
  interacciones verificadas con B-101; benchmark reproducible; error explícito donde no ejecuta.
Cambios de contrato: ninguno. La API sigue con 501 para sionna-rt; el adaptador no se importa
  al arrancar y no hay fallback (EngineUnavailable).
Comandos y resultados: Windows nativo (Python 3.13.7, LLVM 18.1.8 portable) → Dr.Jit aborta con
  "JIT session error: Failed to materialize symbols". WSL2 Ubuntu 24.04 (Python 3.12.3, LLVM
  20.1.2, sionna-rt 2.2.0, mitsuba 3.9.1, drjit 1.5.0) → 18/18 casos físicos y de coherencia con
  |Δ| < 0.001 dB; LD-n3 not-modelled. Pico 703 MB. pytest → 117 passed; export --check sin deriva.
Descargas autorizadas por el usuario: LLVM 18.1.8 (981 666 720 B, archivo borrado tras extraer
  LLVM-C.dll en .local/) y libatomic1 14.2.0-4ubuntu2~24.04.1 (10.5 kB, sin sudo).
Límites: sin medidas; difracción/difusa sin referencia; Windows nativo y GPU no disponibles.
Hallazgos para B-103: desvanecimiento coherente, max_depth limita cruces de pared, metal opaco,
  mapa planar ruidoso sin suelo/techo, Material sin ε/σ y DirectionResult no apto para trazadores.
Solicitud a A: ninguna en esta entrega.
Siguiente paso: B-104 (contrato pedido por A-102), luego B-103 con propuesta de contrato previa.
```

### B-101 — referencias analíticas, formato de medidas y protocolo piloto (review)

```text
Tarea / estado: B-101 / review.
Sesión, rama/worktree, fecha/hora y zona: Claude Code agente B; clon separado en
  C:/Users/ibane/Desktop/Programación/SmartHomeSimulator, rama agent-b/b-101-reference-cases
  desde ec62675; 2026-10-30, Europe/Madrid.
Archivos modificados: services/simulator/src/smart_environment/{references,measurements}.py (nuevos),
  engines.py (MODELLED_INTERACTIONS, input_hash() extraído, "interactions" en capacidades),
  services/simulator/tests/test_{references,measurements}.py (nuevos),
  services/simulator/examples/measurement-campaign.template.json (nuevo, sintético),
  scripts/export_contracts.py, contracts/measurement-campaign.schema.json (nuevo),
  docs/simulation/{REFERENCE_CASES,MEASUREMENT_FORMAT,PILOT_PROTOCOL}.md (nuevos),
  y como integrador docs/process/WORKBOARD.md y docs/migration/STATUS.md.
Criterio de aceptación: 19 casos de espacio libre (incl. 3D y canal 11), log-distance,
  pared (6 materiales normales + 60°, 2 de coherencia) y reflexión (rasante, casi normal,
  fuera de pared); arnés compare() para cualquier motor; formato de medida con procedencia,
  partición por vivienda y criterio congelado; protocolo piloto. Calibración y validación
  separadas por vivienda; ninguna medida inventada.
Cambios de contrato: aditivo. Nuevo measurement-campaign.schema.json; Project,
  SimulationResult y OpenAPI sin cambios (export --check sin deriva). /api/engines añade el
  campo "interactions" (respuesta sin tipar en OpenAPI; la UI lo ignora).
Comandos y resultados (Windows x64, Python 3.13.7, Node 22.20.0):
  pytest services/simulator/tests -q → 107 passed (31 previas + 76 nuevas), aviso httpx ya conocido.
  scripts/export_contracts.py --check → Contracts checked.
  npm ci + npm run contracts → git diff --exit-code src/generated sin deriva.
  npm run build → correcto (aviso de tamaño de chunk ya registrado). npm test → 16/16.
  python -m smart_environment.references → tabla publicada en docs/simulation/REFERENCE_CASES.md.
  git diff --check → sin errores.
Límites científicos: referencias idealizadas (losa homogénea infinita, TE, un rebote); la
  tabla ITU-R P.2040-3 se contrastó con la reproducción de MathWorks porque el PDF de la ITU
  devolvió 404 — pendiente de cotejo oficial. Sin medidas reales; umbral del criterio activo
  de fallo pendiente de decisión del usuario.
Solicitud a A: ninguna en esta entrega. Futuro (B-102/B-103): Material del Project solo tiene
  dB; un motor físico necesita permitividad/conductividad o id ITU. Se propondrá como
  cambio aditivo con la plantilla de WORKFLOW antes de implementarlo.
Integración: commit 263650c; push verificado (rama remota = local) y PR #3 en borrador
  contra codex/migrate-web-python, autorizados por el usuario el 2026-10-30. Sin merge.
  La CI remota no se registra aquí hasta verificarla en el PR.
Siguiente paso: revisión y merge del PR #3 cuando el usuario lo decida; después B-102.
```

### I-001 — entrega publicada

- Usuario autoriza publicar todos los cambios acumulados; `AGENTS.md` permanece local.
- Remoto `origin/main` verificado en el SHA de base; rama de entrega creada.
- Integración de base web/API, editor, contratos, documentación y proceso A/B existentes.
- 16 pruebas del editor y 31 Python pasan; build web y contratos correctos. Gradle test
  termina correctamente con tareas ya actualizadas. Regenerar tipos no produce deriva.
- Exclusiones revisadas: AGENTS.md, entornos, dependencias y builds no se publican.
- Push de rama verificado; PR https://github.com/Phlekies/smart-home-simulator/pull/2 en borrador.
- CI de migración 40959814307 y Java 40959814298 superadas para 33f1df8.
- El último estado de commits posteriores de documentación se consulta en el PR.
- No hay Sionna integrado ni medidas de viviendas; la publicación no completa la migración.
