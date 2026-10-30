# Registro del agente B — simulación, contratos e integración

Este archivo lo mantiene exclusivamente B; A lo lee para conocer contratos/dependencias.
Proceso: [WORKFLOW](WORKFLOW.md). Prioridades: [WORKBOARD](WORKBOARD.md).

## Reserva actual

- Estado: **claimed** — B-104 (contrato de la referencia de plano pedido por A-102), después B-103.
- Entregas en `review`: **B-101** ([PR #3](https://github.com/Phlekies/smart-home-simulator/pull/3), publicada) y **B-102** (commit local en
  `agent-b/b-102-sionna-evaluation`, apilada sobre B-101; sin push hasta autorización).
- Sesión/chat: sesión Claude Code (desktop), agente B; sin identificador adicional conocido.
- Rama/worktree: clon separado `C:/Users/ibane/Desktop/Programación/SmartHomeSimulator`; ramas
  apiladas `agent-b/b-101-…` → `agent-b/b-102-…` → siguientes. No usa el checkout compartido de A
  (`C:/Simulador_smart_homes3D/smart-home-simulator`); A no ve este registro hasta integrar.
- Última actualización: 2026-10-30 (Europe/Madrid).
- Archivos reservados: `services/simulator/src/smart_environment/models.py`, contratos generados
  (`contracts/*.json`, `apps/web/src/generated/**` solo por generación), `scripts/export_contracts.py`,
  `docs/simulation/**` y este registro.
- Integración pendiente de A: **A-101** en review, pero A mantiene reservados `App.tsx`/`styles.css`
  para A-102 y pide no integrarlos aún. No se integra hasta que A los libere.

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
