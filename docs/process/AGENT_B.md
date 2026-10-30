# Registro del agente B — simulación, contratos e integración

Este archivo lo mantiene exclusivamente B; A lo lee para conocer contratos/dependencias.
Proceso: [WORKFLOW](WORKFLOW.md). Prioridades: [WORKBOARD](WORKBOARD.md).

## Reserva actual

- Estado: **claimed** — cinco tareas pedidas por el usuario el 2026-10-30: **I-004** (revisar e integrar
  A-102, PR #12), **B-109** (medidas frente a predicciones y calibración), **B-110** (caché de
  resultados), **B-111** (E2E de la API con los ejemplos Java) y **B-112** (instalación limpia).
- En review: I-003/B-107 en [PR #11](https://github.com/Phlekies/smart-home-simulator/pull/11), pendiente de que el usuario lo fusione.
- Sesión/chat: sesión Claude Code (desktop), agente B; sin identificador adicional conocido.
- Rama/worktree: clon B, rama local `agent-b/b-109-112` apilada sobre #11. No escribe en el
  checkout ni en el worktree de A.
- Última actualización: 2026-10-30 (Europe/Madrid).
- Archivos reservados: `services/simulator/**` (nuevos `calibration.py`, `cache.py`, pruebas),
  `scripts/export_contracts.py`, `contracts/**`, `apps/web/src/generated/**` solo por generación,
  `docs/simulation/**`, documentos comunes de integración y este registro. No toca archivos de A.

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

### I-003 y B-107 — consolidación tras #7 y matriz de funciones Java (review)

```text
Tarea / estado: I-003 y B-107 / review. Rama local agent-b/i-003-b-107-docs sobre #9 (e6fb351).
Motivo: A declaró I-002 terminada y volvió a A-104; B retoma la integración.
Archivos: docs/process/WORKBOARD.md, docs/migration/STATUS.md, docs/migration/CHECKLIST.md,
  docs/product/ACCEPTANCE_CHECKLIST.md, docs/migration/LOCAL_DEVELOPMENT.md,
  docs/migration/FEATURE_MATRIX.md (nuevo) y este registro. Ningún archivo reservado por A.
Evidencia: CI de main (046ee82) en verde (migración y Java); cabezas de #3–#6 ancestros de main;
  PR #8 con base main y CI verde. En esta rama: pytest 199, export --check sin deriva,
  npm test 70/70, build correcto; enlaces de los documentos comprobados.
Marcado: B-101…B-104 e I-002 done; M5 «matriz de funciones» [x]; el resto solo con anotaciones
  de estado parcial (nada sin evidencia pasa a [x]).
Límites: la matriz se basa en el README y los paquetes Java de eff803c y en el código actual;
  conviene revisarla al cerrar cada fase.
Publicación: [PR #11](https://github.com/Phlekies/smart-home-simulator/pull/11) en borrador, apilado sobre #9, por autorización del usuario.
Fusiones autorizadas por el usuario en el orden propuesto: #8 → 6d7e69f, #9 → 760e3cd (base
  cambiada a `main`), #10 (A-104, cabeza verificada) → 6fb42e2; CI de `main` en verde. Conflictos de
  STATUS/WORKBOARD con #10 resueltos consolidando ambos textos; checklists M4/P1 marcados con la
  evidencia de A-104 y B-103.
  Incidencia: GitHub devolvió 500 en `git-receive-pack` en tres intentos; el cuarto entró, pero el
  PR #11 no se sincronizó con la rama, y un commit posterior forzó la sincronización y la CI.
```

### B-108 — escenarios de puertas y materiales inciertos (review)

```text
Tarea / estado: B-108 / review. Rama local agent-b/b-108-scenarios sobre agent-b/b-105-106-on-integration.
Archivos: models.py (MaterialUncertainty, Material.uncertainty, Wall.door, _optional_fields,
  ScenarioAssumptions/Request/Outcome, LinkScenarioResult, ScenarioResult), engines.py
  (material_loss_db, direction con escenario y puertas abiertas, input_hash estable),
  scenarios.py (nuevo), api.py (POST /api/scenario-simulations), export_contracts.py,
  contracts/project.schema.json, openapi.json, scenario-result.schema.json (nuevo),
  apps/web/src/generated/project.ts y scenario-result.ts (generados), tests/test_scenarios.py,
  docs/simulation/SCENARIOS_CONTRACT.md.
Criterio (P2): puertas y materiales inciertos admiten escenarios identificados; mejor/peor caso
  exactos para el trayecto directo; aviso cuando el signo del margen depende de hipótesis.
Contrato: aditivo. Wall/Material ganan propiedades opcionales (required sin cambios, comprobado);
  TS opcional; proyectos sin los campos conservan su hash (la prueba de la plantilla de medidas
  lo detectó y se corrigió antes de entregar).
Comandos: pytest → 199 passed; export --check sin deriva; npm run contracts sin más cambios;
  npm run build correcto; npm test 70/70 (incluye el código de A de main).
Límites: trayecto directo; puerta abierta = sin pared, sin difracción; sin clasificación.
Solicitud a A: script `contracts` con scenario-result.ts (y placement-search.ts, radio-profile.ts);
  inspectores para puerta/estado y rango de material; vista de rangos e hipótesis por enlace.
```

### Revisión de las correcciones de A en la integración (79e88f1) — aceptadas

- Celdas de borde recortadas: centro de la parte dentro del área pedida (antes podía caer fuera).
- Trabajo cancelado mientras terminaba: ahora queda `cancelled`, no `done` (carrera real).
- Gestor de trabajos creado por ciclo de vida de la app y extensión del mapa limitada a ±10000 m.
- Script `contracts` de la web ya genera `coverage-map.ts`. Falta añadir `placement-search.ts` y
  `radio-profile.ts` (B-105/B-106). Sobre esa base: pytest 187, contratos y generados sin deriva,
  npm test 70/70 y build correcto.

### B-106 — perfiles Wi-Fi genéricos con procedencia (review)

```text
Tarea / estado: B-106 / review. Rama local agent-b/b-106-radio-profiles sobre B-105.
Archivos: models.py (ProfileValue, GenericProfile.receiver_profile), profiles.py (catálogo nuevo),
  api.py (GET /api/profiles), scripts/export_contracts.py, contracts/radio-profile.schema.json
  (nuevo), openapi.json, apps/web/src/generated/radio-profile.ts (json2ts), tests/test_profiles.py,
  docs/simulation/RADIO_PROFILES.md.
Criterio: perfiles 2.4 GHz con parámetros trazables; desconocidos e inferidos diferenciados.
Valores: HT20 MCS0/MCS3/MCS7 = −82/−74/−64 dBm, mínimos de IEEE 802.11-2020 tabla 21-25
  (verificados en la reproducción de MathWorks); tabla HT de 2.4 GHz no cotejada (declarado en
  la fuente). Potencia TX desconocida; ganancia 0 dBi y NF 7 dB inferidas con motivo.
Contrato: aditivo (1 ruta, 1 esquema; ningún esquema existente cambia).
Comandos: pytest → 182 passed; export --check sin deriva; npm run build correcto; npm test 16/16.
Límites: no son datos de producto; sin 802.11b/g, 5 GHz, Zigbee ni Thread.
Solicitud a A: añadir radio-profile.ts al script `contracts`; ofrecer el catálogo al elegir perfil
  del mapa mostrando la procedencia de cada valor y pidiendo la potencia TX si se conoce.
```

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
