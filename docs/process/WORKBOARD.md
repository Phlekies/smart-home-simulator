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

Esto no significa que M2 esté completa, ni que existan mapas nuevos, motor avanzado o
validación en viviendas. Los checklists técnico y de producto siguen siendo la aceptación.

## Próximas tareas disjuntas

| ID | Rol | Estado inicial | Entrega y aceptación mínima | Dependencia |
|---|---|---|---|---|
| A-101 | A | ready | Recuperación local de un proyecto válido tras recargar, con restaurar/descartar; datos corruptos/versiones/cuota manejados y pruebas | Contrato actual; sin modificarlo |
| A-102 | A | ready | Propuesta y recorrido de imagen de plano con escala y cotas; persistencia acordada antes de cambiar formato exportado | Coordinar contrato con B si se necesita ampliarlo |
| A-103 | A | ready | Revisar teclado/foco/errores y completar recorrido de crear vivienda, editar y guardar; registrar fallos concretos y pruebas | Base actual |
| B-101 | B | review | Casos de espacio libre/pared/reflexión, protocolo piloto y formato/procedencia de medidas; separar calibración y validación. Entregado 2026-10-30 en `agent-b/b-101-reference-cases`, [PR #3](https://github.com/Phlekies/smart-home-simulator/pull/3) en borrador (107 Python, 16 editor; ver [registro B](AGENT_B.md)) | Sin merge; integrar en la rama de migración. Umbral del criterio activo de fallo pendiente de decisión |
| B-102 | B | review | Prueba técnica aislada de motor avanzado; versiones/hardware/interacciones y benchmark reproducible; error explícito si no ejecuta. Sionna RT 2.2.0 en WSL/CPU: 18/18 referencias; Windows nativo no ejecuta (ver [evaluación](../simulation/ADVANCED_ENGINE_EVALUATION.md)) | Rama local `agent-b/b-102-sionna-evaluation` apilada sobre B-101; sin push |
| B-103 | B | ready | Contrato y ejecución de mapas por perfil/altura, límites y cancelación; tipos generados y pruebas. Debe declarar métrica (coherente/banda ancha/directa), convergencia de profundidad y celdas sin calcular | Alcance de B-102 verificado en su rama; propuesta de contrato antes de implementar |
| B-104 | B | review | Contrato aditivo para persistir la referencia de plano (escala, origen, píxeles, huella) solicitado por A-102; imagen como recurso local, no incrustada. Ver [contrato](../simulation/PLAN_REFERENCE_CONTRACT.md) | Rama local `agent-b/b-104-plan-reference`; A integra el consumidor en A-102 |
| A-104 | A | blocked | Mostrar mapa, leyenda/resolución/perfil/altura, puntos sin calcular y obsolescencia de resultados | Contrato e implementación B-103 |
| I-001 | B integrador | done | Base publicada en `codex/migrate-web-python`, PR #2 en borrador; pruebas locales y CI de código 33f1df8 superadas | Sin merge ni force-push; AGENTS.md local; consultar el PR para revisiones posteriores |

`ready` indica que puede comenzar el trabajo independiente; los criterios de salida
siguen requiriendo sus dependencias. Tomar preferentemente A-101 y B-101; después elegir
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
