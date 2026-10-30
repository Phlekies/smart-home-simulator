# Registro del agente B — simulación, contratos e integración

Este archivo lo mantiene exclusivamente B; A lo lee para conocer contratos/dependencias.
Proceso: [WORKFLOW](WORKFLOW.md). Prioridades: [WORKBOARD](WORKBOARD.md).

## Reserva actual

- Estado: **review** — B-101 implementada y verificada localmente; publicada por autorización
  del usuario en `agent-b/b-101-reference-cases` y [PR #3](https://github.com/Phlekies/smart-home-simulator/pull/3) en borrador contra
  `codex/migrate-web-python`. Sin merge; CI remota a consultar en el PR.
- Tarea: **B-101**, referencias analíticas, protocolo piloto y formato/procedencia de medidas;
  asignación explícita del usuario («trabaja como agente B»).
- Sesión/chat: sesión Claude Code (desktop), agente B; sin identificador adicional conocido.
- Rama/worktree: clon separado `C:/Users/ibane/Desktop/Programación/SmartHomeSimulator`,
  rama local `agent-b/b-101-reference-cases` desde `ec62675`. No usa el checkout compartido
  de A (`C:/Simulador_smart_homes3D/smart-home-simulator`, donde A tiene A-101 en curso);
  A no ve esta reserva en su checkout hasta que se integre la rama.
- Última actualización: 2026-10-30 (Europe/Madrid).
- Archivos reservados hasta integrar: los listados en la entrega B-101 del historial.
- Siguiente tarea recomendada: **B-102**, prueba aislada del motor avanzado con el arnés de B-101.

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
