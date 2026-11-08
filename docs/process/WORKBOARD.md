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

Esto no significa que M2 esté completa ni que exista un motor avanzado integrado o
validación en viviendas. Los checklists técnico y de producto siguen siendo la aceptación.

## Próximas tareas disjuntas

| ID | Rol | Estado inicial | Entrega y aceptación mínima | Dependencia |
|---|---|---|---|---|
| A-101 | A | done | Recuperación local validada, restaurar/descartar, errores/cuota y pruebas; evidencia en AGENT_A y docs/ui/PROJECT_RECOVERY.md | Integrada en I-002; copia por origen/navegador |
| A-102 | A | review | Persistencia de la imagen de plano con `plan_reference` (B-104): huella SHA-256, reasociación y aviso si falta ([PR #12](https://github.com/Phlekies/smart-home-simulator/pull/12)) | Revisada por B (I-004): solo archivos de A; `main`+#12 con 199 Python, 94 web, build y contratos sin deriva. Falta cambiar su base a `main` y fusionar (usuario) |
| A-103 | A | done | Paredes por teclado, foco, errores y recorrido crear/editar/guardar verificados | No certifica accesibilidad completa; evidencia en docs/ui/KEYBOARD_WORKFLOW.md |
| B-101 | B | done | Casos analíticos (espacio libre, pared, reflexión), formato de medidas con procedencia y protocolo piloto; calibración y validación separadas. Ver [registro B](AGENT_B.md) | En `main` por #7 (046ee82); PR #3 cerrado sin fusionar. No son medidas reales; umbral del criterio de fallo pendiente de decisión |
| B-102 | B | done | Sionna RT 2.2.0 evaluado en WSL/CPU: 18/18 referencias; Windows nativo no ejecuta; benchmark reproducible ([evaluación](../simulation/ADVANCED_ENGINE_EVALUATION.md)) | En `main` por #7; PR #4 cerrado. La API sigue con 501 para Sionna; sin validación experimental |
| B-103 | B | done | `/api/coverage-maps`: trabajos cancelables por perfil/altura, ambos sentidos y puntos exactos ([contrato](../simulation/COVERAGE_MAP_CONTRACT.md)) | En `main` por #7, con las correcciones de A en I-002 (bordes, reinicio, cancelación); PR #6 cerrado |
| B-104 | B | done | Contrato aditivo `plan_reference`, imagen local sin incrustar ([contrato](../simulation/PLAN_REFERENCE_CONTRACT.md)) | En `main` por #7; PR #5 cerrado; consumidor A-102 pendiente |
| A-104 | A | done | Capa 2D por métrica/sentido, perfil/frecuencia/altura/resolución, datos parciales y punto exacto; progreso/cancelación e invalidación ([evidencia](../ui/COVERAGE_MAP.md)) | En `main` por [#10](https://github.com/Phlekies/smart-home-simulator/pull/10) (6fb42e2), CI del PR en verde; B verificó la combinación con #8/#9 (199 Python, 84 web, build). Mapas de sesión, sin motor físico nuevo |
| A-105 | A | done | Comparación manual de posiciones con los mismos perfiles/condiciones; ambos sentidos y datos ausentes | Base de sesión; no optimización ni persistencia de variantes |
| A-106 | A | done | Diagnóstico del trayecto directo y paredes inspeccionables, datos de ambos sentidos | Consume resultados existentes; no multipath nuevo |
| A-107/A-108 | A | done | Radios 1–8 y enlaces por interfaz; límites, cascada, undo y recuperación verificados | Sin nuevos protocolos ni compatibilidad funcional |
| B-105 | B | done | Búsqueda exhaustiva de ubicación del AP entre lugares permitidos, máx-mín del margen bidireccional ([contrato](../simulation/PLACEMENT_SEARCH_CONTRACT.md)) | En `main` por [#8](https://github.com/Phlekies/smart-home-simulator/pull/8) (6d7e69f), CI en verde; consumidor de interfaz pendiente |
| B-106 | B | done | Perfiles Wi-Fi 2.4 GHz genéricos con procedencia por valor ([perfiles](../simulation/RADIO_PROFILES.md)) | En `main` por #8; tabla HT de 2.4 GHz no cotejada (declarado); consumidor pendiente |
| B-108 | B | done | Escenarios de puertas desconocidas y materiales con rango; mejor/peor caso y dependencia de hipótesis ([contrato](../simulation/SCENARIOS_CONTRACT.md)) | En `main` por [#9](https://github.com/Phlekies/smart-home-simulator/pull/9) (760e3cd), CI en verde; consumidor pendiente |
| B-107 | B integrador | review | [Matriz de funciones Java](../migration/FEATURE_MATRIX.md) conservadas/sustituidas/excluidas con motivos (M5) | [PR #11](https://github.com/Phlekies/smart-home-simulator/pull/11) |
| I-003 | B integrador | review | Consolidar documentos comunes tras #7, #8, #9 y #10; cierre de #3–#6 | [PR #11](https://github.com/Phlekies/smart-home-simulator/pull/11) |
| I-004 | B integrador | review | Revisión e integración de A-102 (#12) | Rama local `agent-b/b-109-112` (sobre #11); cambio de base del #12 denegado por permisos: lo hace el usuario |
| B-109 | B | review | Medidas frente a predicciones y calibración de un desplazamiento solo con datos de calibración ([documento](../simulation/CALIBRATION.md)) | Rama local `agent-b/b-109-112` (sobre #11); sin medidas reales |
| B-110 | B | review | Caché en memoria por hash de petición para mapas, búsqueda y escenarios | Rama local `agent-b/b-109-112` (sobre #11); contrato aditivo (`cached?`) |
| B-111 | B | review | E2E de la API con los tres ejemplos Java y un proyecto nuevo; corrige el ciclo de vida del gestor de mapas | Rama local `agent-b/b-109-112` (sobre #11) |
| B-112 | B | review | Instalación limpia y arranque reproducibles; `dev.py` muestra por qué falla un servicio | Rama local `agent-b/b-109-112` (sobre #11) |
| I-002 | A (integración por instrucción del usuario) | done | Entregas A-101…A-108 y B-101…B-104 en `main` (046ee82) por [PR #7](https://github.com/Phlekies/smart-home-simulator/pull/7); 162 Python/70 web/build/contratos; CI de migración y Java verde antes y después | AGENTS.md excluido; Java conservado. No volver a fusionar la pila B como entregas nuevas |
| I-001 | B integrador | done | Base publicada en PR #2 e incluida en `main` por I-002; evidencia histórica en STATUS | Sin force-push; AGENTS.md local |

`ready` indica que puede comenzar el trabajo independiente; los criterios de salida
siguen requiriendo sus dependencias. Siguientes para A: A-102 (persistencia de la imagen) y los
consumidores de B-105/B-106/B-108 (lugares permitidos, perfiles, escenarios). B revisa e integra y
retoma su ámbito. Consultar las reservas antes de editar. No ejecutar todas las filas como un único cambio gigante.

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
