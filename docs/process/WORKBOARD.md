# Tablero de trabajo

Inicializado: 2026-10-29. Mantenedor: **B / integrador**. Actualizar al integrar cada
entrega. Consultar también [A](AGENT_A.md) y [B](AGENT_B.md): sus reservas activas mandan
sobre la disponibilidad mostrada aquí hasta consolidar el traspaso.

Estados: `ready` (se puede tomar), `claimed` (sesión identificada trabajando), `blocked`
(dependencia concreta), `review` (implementado pendiente de integración), `done` (evidencia
consolidada). Una tarea que espera su turno no implica que el proyecto entero esté bloqueado.

## Base completada: no reconstruir

- Repositorio clonado y código Java original conservado.
- Objetivo, ruta y checklists; Wi-Fi primero, inicialmente 2.4 GHz.
- Base React/TypeScript y API Python; contratos y tipos generados.
- Importación de tres ejemplos Java con original preservado; JSON manual.
- Estimador analítico directo bidireccional con obstáculos y datos desconocidos explícitos.
- Editor de paredes: dibujo, selección, arrastre, giro, material/espesor/altura, 2D/3D.
- Historial de 50 acciones y agrupación de arrastres.
- Evidencia local previa: 16 pruebas de editor, 31 Python, build web; 192 Java en la entrega
  de base. Detalles y fechas en [STATUS](../migration/STATUS.md). CI de migración y Java
  superadas remotamente para 33f1df8 en PR #2.
- `PROCESS-001`: instrucciones, reparto, tablero y registros creados en esta entrega.
- `main` (046ee82): base de migración, entregas A-101…A-108 y B-101…B-104 fusionadas por #7.

Esto no significa que M2 esté completa, ni que existan mapas nuevos, motor avanzado o
validación en viviendas. Los checklists técnico y de producto siguen siendo la aceptación.

## Próximas tareas disjuntas

| ID | Rol | Estado inicial | Entrega y aceptación mínima | Dependencia |
|---|---|---|---|---|
| A-101 | A | done | Recuperación local validada, restaurar/descartar, errores/cuota y pruebas; evidencia en AGENT_A y docs/ui/PROJECT_RECOVERY.md | Integrada en I-002; copia por origen/navegador |
| A-102 | A | ready | Imagen de sesión a escala implementada; completar persistencia, huella y reasociación con contrato B-104 | Contrato integrado en I-002; conservar imagen local y avisar si no está disponible |
| A-103 | A | done | Paredes por teclado, foco, errores y recorrido crear/editar/guardar verificados | No certifica accesibilidad completa; evidencia en docs/ui/KEYBOARD_WORKFLOW.md |
| B-101 | B | done | Casos analíticos (espacio libre, pared, reflexión), formato de medidas con procedencia y protocolo piloto | fusionada en `main` por #7 (046ee82; CI de migración y Java en verde para ese commit); PR #3 cerrado sin fusionar. Umbral del criterio de fallo pendiente de decisión |
| B-102 | B | done | Sionna RT evaluado en WSL/CPU (18/18 referencias); Windows nativo no ejecuta; benchmark reproducible ([evaluación](../simulation/ADVANCED_ENGINE_EVALUATION.md)) | fusionada en `main` por #7 (046ee82; CI de migración y Java en verde para ese commit); PR #4 cerrado. No integrado en la API |
| B-103 | B | done | Mapas por perfil/altura como trabajos cancelables, ambos sentidos, puntos exactos ([contrato](../simulation/COVERAGE_MAP_CONTRACT.md)) | fusionada en `main` por #7 (046ee82; CI de migración y Java en verde para ese commit), con correcciones de A (bordes, cancelación, ciclo de vida); PR #6 cerrado |
| B-104 | B | done | Contrato aditivo `plan_reference` (imagen local, huella y escala) ([contrato](../simulation/PLAN_REFERENCE_CONTRACT.md)) | fusionada en `main` por #7 (046ee82; CI de migración y Java en verde para ese commit); PR #5 cerrado; consumidor en A-102 |
| A-104 | A | claimed | Mostrar mapa, leyenda/resolución/perfil/altura, puntos sin calcular y obsolescencia de resultados | A trabaja en su worktree (`codex/coverage-map-ui`); ver registro A |
| A-105 | A | done | Comparación manual de posiciones con los mismos perfiles/condiciones; ambos sentidos y datos ausentes | Base de sesión; no optimización ni persistencia de variantes |
| A-106 | A | done | Diagnóstico del trayecto directo y paredes inspeccionables, datos de ambos sentidos | Consume resultados existentes; no multipath nuevo |
| A-107/A-108 | A | done | Radios 1–8 y enlaces por interfaz; límites, cascada, undo y recuperación verificados | Sin nuevos protocolos ni compatibilidad funcional |
| I-002 | A (integración por instrucción del usuario) | done | Entregas A-101…A-108 y B-101…B-104 combinadas y publicadas | PR #7 fusionado en `main` (046ee82); CI verde en el PR y en `main`; A volvió a su rol |
| B-105 | B | review | Búsqueda exhaustiva de ubicación del AP entre lugares permitidos, máx-mín del margen bidireccional ([contrato](../simulation/PLACEMENT_SEARCH_CONTRACT.md)) | [PR #8](https://github.com/Phlekies/smart-home-simulator/pull/8) en borrador, base `main`, CI verde; A consume después |
| B-106 | B | review | Perfiles Wi-Fi 2.4 GHz genéricos con procedencia por valor ([perfiles](../simulation/RADIO_PROFILES.md)) | PR #8; tabla HT de 2.4 GHz no cotejada (declarado) |
| B-108 | B | review | Escenarios de puertas desconocidas y materiales con rango; mejor/peor caso y dependencia de hipótesis ([contrato](../simulation/SCENARIOS_CONTRACT.md)) | [PR #9](https://github.com/Phlekies/smart-home-simulator/pull/9) en borrador, apilado sobre #8 |
| B-107 | B integrador | review | [Matriz de funciones Java](../migration/FEATURE_MATRIX.md) conservadas/sustituidas/excluidas con motivos (M5) | Rama `agent-b/i-003-b-107-docs` |
| I-003 | B integrador | review | Consolidar tablero, STATUS y checklists tras #7; registrar PR #8/#9 y cierre de #3–#6 | Rama `agent-b/i-003-b-107-docs`, apilada sobre #9 |
| I-001 | B integrador | done | Base publicada en `codex/migrate-web-python`, PR #2 en borrador; pruebas locales y CI de código 33f1df8 superadas | Sin merge ni force-push; AGENTS.md local; consultar el PR para revisiones posteriores |

`ready` indica que puede comenzar el trabajo independiente; los criterios de salida
siguen requiriendo sus dependencias. Ahora: A en A-104 y después A-102 (persistencia) y los consumidores de
B-105/B-106/B-108; B revisa e integra. Después elegir
según avance y registros. No ejecutar todas las filas como un único cambio gigante.

## Trabajo posterior

Comparación/optimización de ubicaciones con restricciones; perfiles de radio con evidencia;
incertidumbre de materiales; campaña piloto y evaluación independiente; distribución local
usable sin herramientas de desarrollo. Seguir las fases P0–P5, reutilizando lo ya migrado.

## Fuera del alcance inicial

Automatizaciones completas, compatibilidad con asistentes/nube, tiendas/precios,
multiusuario/servidor remoto, ns-3 obligatorio y soporte anunciado de toda tecnología.
Varias plantas, otras bandas y mallas necesitan aceptación propia; no añadir solo sus
nombres a un selector y darlas por soportadas.

## Reservas y entregas

Los registros A/B se inicializan sin tarea activa. Al recibir instrucciones futuras,
cada agente debe consultar el estado actual y escribir su reserva ANTES de editar.
El integrador consolida ID/estado/evidencia en esta tabla, sin reescribir el registro ajeno.
