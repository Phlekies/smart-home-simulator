# Registro del agente A — interfaz y edición

Este archivo lo mantiene exclusivamente A; B lo lee para integrar.
Proceso: [WORKFLOW](WORKFLOW.md). Prioridades: [WORKBOARD](WORKBOARD.md).

## Reserva actual

- Estado: **claimed**, integración I-002 por instrucción explícita del usuario.
- Cambio de rol secuencial: A asume temporalmente integración/Git y documentos comunes
  para revisar ramas B, verificar la combinación y actualizar main. Esta instrucción
  del usuario prevalece sobre el reparto ordinario; después vuelve al ámbito A.
- Ramas B verificadas remotamente: pila B-101→B-102→B-104→B-103, cabeza a5e6ff8;
  registro B remoto en review, clon separado y sin tarea nueva activa declarada.
- Reserva I-002: integración de las entregas A/B, package.json (generación de cobertura),
  documentos compartidos de estado/checklist/tablero y Git. No descartar cambios locales.
- Trabajo activo I-002 aislado en `smart-home-simulator/.local/integration-review`, rama
  `codex/integrate-agents`, porque otra sesión creó `agent-a/a-101-a108-ui` y guardó
  las entregas A en 1b5b596 mientras se iniciaba la revisión. No cambiar la rama del
  checkout compartido; todas las operaciones siguientes se hacen en este worktree.
- Tareas: **A-107**, gestión de interfaces de radio, y **A-108**, gestión de enlaces por
  radio. Usuario pide seguir completando tareas del rol A; contratos vigentes.
- Sesión/chat: conversación actual, agente A; sin identificador adicional conocido.
- Rama/worktree: checkout compartido `codex/migrate-web-python`; A no cambia ramas ni prepara commits.
- Última actualización: 2026-10-30 (Europe/Madrid).
- Archivos de esta entrega, liberados para integración: `apps/web/src/App.tsx`, `apps/web/src/styles.css`, nuevos
  `apps/web/src/ConnectionEditor.tsx`, `apps/web/src/editor/connections.ts`,
  `apps/web/src/editor/connections.test.ts`, `docs/ui/RADIOS_AND_CONNECTIONS.md`,
  `apps/web/src/PositionComparison.tsx`, `apps/web/src/editor/comparison.ts`,
  `apps/web/src/editor/comparison.test.ts`,
  `docs/ui/radios-connections.jpg` y este registro.
- Archivos de la entrega anterior:
  `apps/web/src/PositionComparison.tsx`, `apps/web/src/editor/comparison.ts`,
  `apps/web/src/editor/comparison.test.ts`, `docs/ui/POSITION_COMPARISON.md`,
  `docs/ui/position-comparison.jpg`, nuevo `apps/web/src/LinkDiagnostics.tsx`,
  `docs/ui/LINK_DIAGNOSTICS.md`, `docs/ui/link-diagnostics.jpg` y este registro.
  B puede revisar e integrar estos archivos junto a la base A previa.
- Archivos de entregas anteriores: `apps/web/src/App.tsx`, `apps/web/src/Plan.tsx`,
  `apps/web/src/styles.css`, nuevo `apps/web/src/PlanReference.tsx`,
  `apps/web/src/editor/reference.ts`, `apps/web/src/editor/reference.test.ts`,
  nuevo `apps/web/src/WallCreator.tsx`, `apps/web/src/editor/wallCreation.ts`,
  `apps/web/src/editor/wallCreation.test.ts`, `apps/web/src/WallInspector.tsx`,
  nuevo `apps/web/src/NumberField.tsx`,
  `docs/ui/PLAN_REFERENCE.md`, `docs/ui/plan-reference.jpg`, `docs/ui/reference-fixture.png`
  y `docs/ui/KEYBOARD_WORKFLOW.md`, además de este registro.
  Las entregas previas siguen locales, también entregables; conjunto acumulado: 34 archivos.
- Alcance A-105: fijar una base calculada, mover equipos, recalcular y comparar cada
  sentido. Rechazar deltas si cambian radios, paredes, enlaces, condiciones o motor/versión.
  Base de sesión; no nuevo formato persistido, endpoint o cálculo físico de interfaz.
  Es un adelanto independiente de comparación, no aceptación de M4/P3 ni motor avanzado.
- Alcance A-106: presentar distancia, pérdidas y paredes atravesadas ya devueltas por
  el motor, con selección de pared y datos de radio. Sin atribuciones físicas nuevas.
- Alcance nuevo: añadir radios genéricas con desconocidos explícitos, respetar mínimo 1
  y máximo 8 radios, retirar radio/enlaces asociados como acción reversible, elegir radio
  de destino y quitar enlaces sin borrar equipos; impedir duplicados y máximo 512 enlaces.
  No catálogo comercial, protocolos nuevos, compatibilidad inventada ni cambios de API.
- Siguiente paso: B revisa/integra las entregas con evidencia. Persistencia A-102 y
  mapas A-104 siguen esperando acuerdos/productor de B, sin inventar sus contratos.

## Solicitud a B — persistencia de A-102

- Pregunta: conservar la referencia calibrada al guardar/reabrir una vivienda.
- El contrato actual carece de imagen/transformación. Propuesta: acordar si la imagen
  queda como recurso local y la transformación (metros por píxel, origen en m, dimensiones
  en píxeles y huella del recurso) pasa al proyecto exportable mediante cambio aditivo.
- No se añade una estructura persistida paralela ni campos manuales. B decide contrato,
  compatibilidad con proyectos v1, límite de importación de 2 MB y transporte de recursos;
  A integra los tipos generados cuando estén disponibles.
- Mientras tanto, A implementa referencia solo de sesión, rotulada como no incluida en
  JSON/recuperación y eliminada al cambiar de proyecto. Las paredes trazadas sí pertenecen
  al proyecto actual y conservan su guardado/historial normales.
- Archivos futuros afectados: modelos/contratos/tipos generados (B); consumidor y pruebas
  de exportación/recuperación (A). Mantener A-102 parcial hasta acordar y verificar persistencia.

## Plantilla de entrega — completar al trabajar

```text
Tarea / estado (claimed, review, blocked):
Sesión, rama/worktree, fecha/hora y zona:
Archivos previstos / realmente modificados:
Criterio de aceptación resuelto:
Comandos y resultados reales:
Recorrido de navegador / evidencia:
Limitaciones o dependencias:
Solicitud a B (si cambia contrato/integración):
Siguiente paso:
```

## Historial

### A-101 — recuperación local, 2026-10-30 (Europe/Madrid)

- Usuario asigna explícitamente rol A y autoriza empezar. Base limpia verificada en
  `codex/migrate-web-python`; B aparecía sin tarea activa al reservar.
- Copia local versionada tras 500 ms de inactividad y validación por API existente.
  Al volver se elige restaurar/descargar/descartar antes de abrir el ejemplo.
- Guardas por formato/versión/tamaño, cuota/permisos y errores de validación. Se mantiene
  la copia previa si falla una actualización. Respuestas obsoletas no escriben; se detectan
  cambios observados desde otra pestaña. No se promete un bloqueo atómico entre pestañas.
- Restaurar conserva proyecto/notas/original Java, reinicia historial y no reutiliza resultados.
- Archivos realmente modificados/creados: los ocho correspondientes a esta entrega
  (`App.tsx`, `styles.css`, `recovery.ts`, `recovery.test.ts`, `useProjectRecovery.ts`,
  `PROJECT_RECOVERY.md`, `recovery.jpg`, este registro).
- `npm.cmd --prefix apps/web test`: **28 pruebas superadas** (16 previas + 12 recuperación).
- `npm.cmd --prefix apps/web run build`: **correcto**, TypeScript y Vite. Permanece aviso
  previo del chunk 3D de ~933 kB, ajeno a esta entrega.
- `git diff --check`: correcto, sin errores de whitespace (avisos de conversión LF/CRLF).
- Navegador real: editar nombre/X `7.125`, simular, esperar copia, recargar/restaurar;
  datos conservados, historial y resultados vacíos. JSON descargado; nombre vacío muestra
  error y corregirlo reanuda la copia. Descartar tras respaldar JSON abre el apartamento
  original (X `7`); nueva recarga ofrece la nueva copia. Detalle y captura en
  [PROJECT_RECOVERY.md](../ui/PROJECT_RECOVERY.md).
- Cuota, formatos dañados/versiones, permisos y concurrencia se verifican por pruebas
  inyectables; no se atribuyen a un recorrido real que no se ejecutó.
- Servicios de prueba iniciados por A en loopback y detenidos; comprobación final sin
  listeners en 5174/8000. Primer arranque en sandbox no respondió; se detuvo y se verificó
  con arranque autorizado fuera del sandbox.
- Límites: una copia por origen/navegador, API necesaria para validar/restaurar; un cierre
  abrupto puede perder cambios aún pendientes. Guardado JSON manual conservado.
- No se modificaron backend, contratos/tipos generados, Java ni archivos comunes de B.
  No hay commits/push ni CI nueva de esta entrega preparados por A.
- **Solicitud a B:** revisar el diff y esta evidencia; integrar estos ocho archivos,
  actualizar WORKBOARD (A-101), STATUS y checklist M2 de recuperación. Revisar también el
  párrafo de LOCAL_DEVELOPMENT que todavía declara autosave pendiente. Esta entrega no
  completa M2, la accesibilidad integral, el motor avanzado ni toda la migración.

### A-102 — imagen a escala de sesión, 2026-10-30 (Europe/Madrid)

- Estado: **review parcial**, recorrido de sesión listo; persistencia pendiente del
  acuerdo solicitado arriba. No se marca completa A-102/M2.
- `PlanReference.tsx`, `editor/reference.ts` y pruebas; integración en App/Plan/styles.
  PNG/JPEG/WebP locales, límites de bytes/píxeles, escala uniforme por dos puntos exactos,
  origen/opacidad/visibilidad, cotas y limpieza de URLs. No altera geometría existente.
- Implementación y 11 pruebas del dominio por subagente A; raíz A inspeccionó módulo,
  integró consumidor y ejecutó pruebas/build completos. No intervino ningún agente B.
- Navegador: fixture 800×600, 600 px = 12 m → 16×12 m; origen (−2,−2); trazar pared
  de 4 m. Restaurar tras recarga conserva pared y elimina referencia de sesión.
  Selección A incompleta bloquea aplicar; Escape recupera los puntos previos.
  Mostrar/ocultar y exclusión de Ctrl+Z verificadas.
- Documentación/fixture/captura: [PLAN_REFERENCE.md](../ui/PLAN_REFERENCE.md).
- JSON descargado con referencia aplicada conserva únicamente las claves canónicas;
  la imagen no se envía a la API ni se introduce en un formato persistido alternativo.
- Limitación: no rotación/corrección de perspectiva ni persistencia de imagen. Se avisa
  en la propia interfaz; la escala aplicada exige una distancia conocida real del usuario.

### A-103 — teclado, foco y errores, 2026-10-30 (Europe/Madrid)

- Estado: **review**, recorrido implementado/verificado; no certificación de accesibilidad.
- Nuevo `WallCreator.tsx`, `editor/wallCreation.ts` y pruebas: coordenadas exactas, Enter,
  límites/min longitud y mensajes accesibles. Nuevo `NumberField.tsx` compartido por App
  y WallInspector: borrador inválido visible, error/aria-invalid, último valor válido
  preservado y canal entero. Objetos/radios cambian de inspector sin heredar borradores.
- Foco al nombre al abrir/restaurar/nuevo/eliminar, al equipo al añadir y al campo
  inválido al guardar/calcular; abrir detalles cerrados que contengan ese campo.
  Borradores de paredes aún no creadas no bloquean el guardado del proyecto válido.
- Edición suspendida durante cargas mediante inert/guardas/controles. Revisado en código;
  no se simuló una API lenta ni se hizo evaluación con lector de pantalla.
- Navegador: pared (1.125,2.375)→(5.125,2.375) con Enter; undo/redo; centro fuera de
  rango rechazado y enfocado al guardar; corregir y eliminar devuelve foco al nombre.
  Equipo nuevo enfoca nombre; X=1.125 y canal 1.5 rechazado, luego 1 válido.
  Dos equipos/un enlace calculados, sensibilidad desconocida sigue «sin verificar».
  Pérdida −1 en detalles cerrados se revela/enfoca al guardar.
- Descarga real `entorno.shsim (3).json`, leída: cinco paredes, dos equipos, un enlace,
  X=1.125 y diez claves canónicas; sin campos de referencia nuevos.
- Corrección detectada en revisión visual: claves React distintas para los dos paneles
  al reiniciar proyecto. Recarga limpia final sin duplicación ni nuevos errores de consola.
- Evidencia ampliada: [KEYBOARD_WORKFLOW.md](../ui/KEYBOARD_WORKFLOW.md).

### Verificación conjunta y traspaso — A-101/102/103

- `npm.cmd --prefix apps/web test`: **46 pruebas superadas** (16 base + 12 recuperación
  + 11 referencia + 7 creación de paredes). Ejecución final por raíz A.
- `npm.cmd --prefix apps/web run build`: **correcto**, TypeScript y Vite. Aviso previo
  de chunk 3D ~933 kB permanece. `git diff --check` sin errores de whitespace.
- Servicios temporales de esta sesión detenidos; sin listeners finales en 5174/8000.
- No se cambiaron backend/contratos/generados/Java/archivos comunes ni Git/commits/push.
  No se atribuye CI remota a estos cambios locales.
- **B/integrador:** revisar los 21 archivos acumulados de A, integrar y actualizar
  WORKBOARD/STATUS/checklists/LOCAL_DEVELOPMENT con evidencia real. Registrar A-102 parcial
  y decidir el contrato/recurso persistente antes de implementarlo. M2 y la evaluación
  completa de accesibilidad siguen pendientes; A-104 espera el productor B-103.

### A-105 — comparación manual de posiciones, 2026-10-30 (Europe/Madrid)

- Estado **review**. Trabajo independiente del objetivo de comparar alternativas con
  los contratos vigentes; no se marca M4/P3 como terminado ni se altera el ámbito del motor.
- Archivos: PositionComparison.tsx, editor/comparison.ts y comparison.test.ts; App/styles;
  [documentación](../ui/POSITION_COMPARISON.md) y position-comparison.jpg.
- Base independiente de proyecto/resultado con fecha/motor/versión/hash. Alternativa
  exige cálculo vigente; editar/undo/restaurar retira deltas obsoletos. Se comparan por
  separado ambos sentidos, conservando nulos y evaluaciones sin verificar.
- Cambios de radios, paredes, materiales, enlaces, condiciones o motor/versión bloquean
  la comparación de posiciones. Se verifican identidades de enlaces/sentidos y hash
  distinto tras desplazar equipos. Sin promedios, probabilidades o compra recomendada.
- Restaurar posiciones es una acción de historial; conserva parámetros, invalida cálculo
  y devuelve foco al nombre. Base de sesión explícita; se limpia al abrir otro proyecto.
- Navegador: X=1.125→3 del Router de prueba, resto idéntico: antes de recalcular no hay
  deltas; después −54.5→−50.1 dBm, +4.4 dB por sentido, margen sin datos y sin verificar.
  TX=20 dBm bloquea la tabla; deshacer la recupera. Restaurar devuelve X=1.125;
  undo devuelve X=3. Abrir apartamento elimina la base anterior.
- 11 pruebas nuevas: snapshots, comparabilidad, orden, datos ausentes/cero, signos
  asimétricos, motores, identidades y obsolescencia. Vectores sintéticos de aritmética.
- Límites: base no persistida, sin optimización ni restricciones de instalación; no
  sustituye los contratos de escenarios/mapas ni la futura validación de producto.

### A-106 — explicar obstáculos y datos de cada sentido, 2026-10-30 (Europe/Madrid)

- Estado **review**. Nuevo LinkDiagnostics.tsx, integración App/styles,
  [documentación](../ui/LINK_DIAGNOSTICS.md) y link-diagnostics.jpg.
- Expone campos ya calculados de DirectionResult: distancia, pérdidas, paredes cruzadas,
  señal, ruido/SNR y margen. Radios con frecuencia/canal/sensibilidad identificadas.
- Paredes inspeccionables con material/espesor/procedencia; la selección enfoca inspector
  sin invalidar el resultado. Editar sí lo retira hasta recalcular. Sin pérdidas por
  pared inventadas ni interpretación multipath de un cálculo directo.
- Navegador: termostato con cero cruces y aviso de alcance; retorno no calculado explícito.
  Smoke detector: 19.0 m y pared 5 Drywall (8 cm), pérdidas 3.0 dB / señal −69.9 dBm.
  Inspeccionar pared enfoca Centro X. Concrete: pérdidas 11.6 dB / señal −78.5 dBm;
  vuelta ausente por TX del Hub desconocida y evaluación sin verificar conservadas.
- Presentación verificada contra API real; no nuevas pruebas que copien el formateo.
  Consola de navegador sin errores. Números del estimador, no medidas experimentales.

### Verificación y traspaso A-105/A-106

- `npm.cmd --prefix apps/web test`: **57 pruebas superadas**, 46 previas + 11 comparación.
- `npm.cmd --prefix apps/web run build`: TypeScript/Vite correctos; aviso anterior de
  chunk 3D ~933 kB conservado. `git diff --check` sin errores de whitespace.
- Servicios temporales detenidos y puertos 5174/8000 sin listeners finales.
- Sin cambios en backend, contratos/generados, Java o documentación compartida de B.
  Sin commits/push/CI remota de estas entregas; 29 archivos locales acumulados de A.
- **Solicitud B:** integrar A-101/102/103/105/106 con evidencia y límites, registrar estas
  dos entregas independientes en WORKBOARD y actualizar STATUS/checklists sin dar por
  completada migración, M4/P3 o validación física. A-102 persistencia y A-104 mapas siguen
  esperando el acuerdo/productor de B. No ejecutar sus fases en la UI por aproximación.

### A-107/A-108 — radios y enlaces editables, 2026-10-30 (Europe/Madrid)

- Estado **review**, UI implementada con contratos actuales. No se añadieron protocolos,
  perfiles comerciales ni funciones de cálculo/compatibilidad en la interfaz.
- Archivos: ConnectionEditor.tsx, editor/connections.ts y connections.test.ts; App/styles;
  PositionComparison.tsx, editor/comparison.ts y comparison.test.ts para identificar radios;
  [RADIOS_AND_CONNECTIONS.md](../ui/RADIOS_AND_CONNECTIONS.md) y radios-connections.jpg.
- Radios de 1 a 8, IDs únicos dentro del equipo, alta genérica con TX/sensibilidad/canal/
  protocolo desconocidos. Lista lateral muestra todas las radios/protocolos, no solo radio-1.
- Elegir cualquier radio destino en otro equipo, añadir explícitamente y quitar enlaces
  individualmente. Guardas de referencias, duplicados/inversión y máximo 512 enlaces;
  las opciones ya enlazadas se identifican, sin sumar emisores ni afirmar malla/Internet.
- Retirar radio limpia solo sus enlaces en ambos extremos, con alcance por equipo incluso
  si los IDs de radio coinciden entre equipos. Acción completa recuperable con un Undo.
- Cambios invalidan cálculos y usan el guardado/recuperación canónicos. Resultados y
  comparación muestran radios para distinguir conexiones paralelas del mismo par de equipos.
- 12 pruebas nuevas de radios/enlaces y una de comparación entre interfaces paralelas.
  Se conservan entradas originales, metadatos y objetos de otras creaciones.
- Navegador: dos radios en AP/Sensor; enlaces Sensor/radio-2→AP/radio-2 y →AP/radio-1.
  TX desconocida no produce señal ficticia; resultado parcial solo donde hay datos.
  Retirar radio elimina dos enlaces; un Undo recupera radio y ambos. Quitar uno conserva
  dispositivos/radios y se puede deshacer; foco de los selectores comprobado.
- Archivo descargado `entorno.shsim (4).json` validado por API y leído: dos equipos,
  radios 2/2, destinos radio-2/radio-1 y TX nueva nula. Recarga/restauración conserva todo.
  Consola sin errores. Los máximos se verificaron con pruebas, no mediante datos visuales.
- `npm.cmd --prefix apps/web test`: **70 pruebas superadas** (57 previas + 13 nuevas).
- `npm.cmd --prefix apps/web run build`: correcto, TypeScript/Vite; aviso previo 3D ~933 kB.
  `git diff --check` correcto; servicios temporales detenidos, sin listeners en 5174/8000.
- Sin cambios de backend/contratos/generados/Java ni archivos compartidos del integrador.
  Sin commits/push/CI nueva; conjunto acumulado de A: 34 archivos locales.
- **Solicitud B:** integrar A-107/A-108 junto a entregas anteriores y consolidar tablero/
  estado/evidencia sin atribuir soporte físico nuevo. Mantener A-102/A-104 pendientes de
  sus contratos/productores; la migración y las puertas de producto siguen incompletas.
