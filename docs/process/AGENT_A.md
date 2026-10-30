# Registro del agente A — interfaz y edición

Este archivo lo mantiene exclusivamente A; B lo lee para integrar.
Proceso: [WORKFLOW](WORKFLOW.md). Prioridades: [WORKBOARD](WORKBOARD.md).

## Reserva actual

- Estado: **review**, A-102 persistencia implementada y verificada; archivos liberados.
- Sesión: conversación actual, agente A; 2026-10-30, Europe/Madrid.
- Worktree aislado `smart-home-simulator/.local/integration-review`, rama
  `codex/persist-plan-reference` sobre `codex/coverage-map-ui` (PR #10, d5e64d3).
  No cambiar el checkout compartido ni fusionar por inferencia.
- Archivos reales A-102: App.tsx, CoveragePanel.tsx, PlanReference.tsx, styles.css,
  editor/referencePersistence.ts y referencePersistence.test.ts, editor/comparison.ts y
  comparison.test.ts, docs/ui/PLAN_REFERENCE.md, plan-reference-persistence.jpg y este registro.
- Contrato B-104 consumido sin cambios: metadatos canónicos en JSON/recuperación, archivo
  local identificado por SHA-256/dimensiones/tipo. Imagen ausente/distinta explícita.
- 94 pruebas web/editor, build y diff --check correctos; recorrido real de guardar,
  restaurar/reabrir, rechazar/reasociar, sustituir e historial completado. Servicios detenidos.
- A-104 en review publicada en [PR #10](https://github.com/Phlekies/smart-home-simulator/pull/10),
  con CI remota correcta. Esta rama es una entrega apilada, no incorpora aún PR #8/#9.
- I-002 en main 046ee827 por PR #7. Las entregas antiguas A/B están integradas allí;
  el historial de cada sesión conserva su estado de publicación en aquel momento.
- AGENTS.md sigue local/excluido. No backend, contratos/generados, Java ni documentos comunes modificados.

## Siguiente paso y dependencias

- Integrador: revisar esta entrega y A-104, consolidar WORKBOARD/STATUS y criterios
  acreditados de M2. La persistencia A-102 ya no espera contrato ni implementación de B.
- A puede continuar el recorrido completo por teclado y revisión de accesibilidad de M2;
  no declarar toda la fase completa por estas funciones.
- Consumidores de búsqueda/perfiles (PR #8) y escenarios (PR #9) requieren integrar sus
  contratos y revisar su evidencia. No inventar tipos ni tratar perfiles preliminares
  como datos de modelos comerciales. No tocar archivos de B durante esa revisión.
- Quedan motor avanzado en API, informes, mediciones y validación independiente de producto;
  esta entrega es persistencia visual y no acredita precisión radioeléctrica.

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


### A-104 — mapa por perfil, altura y sentido, 2026-10-30 (Europe/Madrid)

- Estado **review**. Rama `codex/coverage-map-ui`, worktree aislado basado en main
  046ee827. Archivos previstos y reales enumerados en la reserva actual.
- API B-103 consumida con trabajos, progreso/cancelación y descarte de respuestas tardías.
  Comprueba identidad/huella/parámetros/dimensiones/arrays y conserva desconocidos/cero.
- Capa 2D raster por celda, recorte exacto del borde, límites de raster para rejillas
  alargadas; señal/margen en ambos sentidos. AP/perfil/frecuencia/altura/resolución y
  leyenda fija; gris/rayado/sin calcular diferenciados, sin clasificación favorable.
- Punto exacto fraccionario conserva coordenadas y devuelve sus cuatro valores de la API.
  Editar proyecto/parámetros/undo retira el mapa. Cambiar métrica no vuelve a calcular.
- Navegador: caso original parcial, caso sintético asimétrico, punto exacto y cancelación.
  Mover X del AP retira la capa inmediatamente. Consola final sin errores/advertencias.
  Cifras y captura en [COVERAGE_MAP.md](../ui/COVERAGE_MAP.md).
- Pruebas finales: **84 web/editor**, TypeScript/Vite y diff --check correctos.
  Aviso previo de chunk 3D ~933 kB conservado. Python no se repite para este consumidor:
  backend/contratos intactos; I-002 ya verificó 162 pruebas y CI remota.
- Servicios de prueba propios detenidos; comprobación final sin listeners 5174/8000.
- Integración documental de cierre I-002: WORKBOARD/STATUS reflejan main publicado y su
  CI, y A-104 en review. Cambio secuencial de rol por instrucción del usuario; se vuelve a A.
- Límites: parámetros/resultados del mapa de sesión, sin caché ni exportación persistente,
  un punto exacto en UI, solo estimador directo. No completa M4 ni validación experimental.
- Publicación: código 9868ae8 en `codex/coverage-map-ui`, PR #10 abierto contra main.
  CI remota de esta entrega consultable en el PR; no se ha fusionado este consumidor.
- **Solicitud al integrador:** revisar esta entrega separada en PR #10; mantener el mapa
  avanzado, incertidumbre y medidas reales pendientes. AGENTS.md permanece excluido.
- Siguiente tarea A: persistir/reasociar referencia calibrada mediante contrato B-104.


### A-102 — persistencia y reasociación de referencia, 2026-10-30 (Europe/Madrid)

- Estado **review**, rama `codex/persist-plan-reference` sobre PR #10; archivos reales
  enumerados arriba, sin ampliar contrato o modificar código de B.
- SHA-256 local sobre bytes; nombre/MIME/dimensiones, escala/origen y calibración exacta
  en Project.plan_reference. Sin URLs, bytes ni preferencias visuales en el JSON.
- Al abrir/recuperar, imagen ausente explícita y reasociación por identidad. Una copia
  renombrada válida conserva los metadatos guardados; otra con igual nombre/píxeles y
  bytes distintos se rechaza. No bloquea la vivienda ni borra su referencia.
- Reemplazo preparado como borrador: fondo guardado conservado hasta aplicar. Descartar
  no altera proyecto. Retirar, undo/redo y restablecer calibración integrados en historial.
- URLs de recurso/borrador con dueño y limpieza; cargas tardías descartadas. Opacidad y
  visibilidad de sesión. Proyectos anteriores sin referencia siguen abriendo.
- Metadatos de fondo separados de revisiones físicas: preservan mapas/resultados y la
  comparación. Undo/redo de geometría/radio sí invalida. Exportar comprueba el snapshot
  completo para descartar validaciones anteriores aunque solo cambie la referencia.
- **94 pruebas superadas**: 84 anteriores + 9 de persistencia y 1 de comparabilidad.
  TypeScript/Vite y diff --check correctos; aviso previo del chunk 3D ~933 kB.
- Navegador/API: fixture 800×600, A=(100.125,300.25), B=(700.375,300.25), distancia12.005 m,
  escala0.02m/px y origen(-2.125,3.75). JSON descargado y leído; SHA contrastado con disco.
  Recargar/restaurar y reabrir JSON conservan puntos/escala; reasociación correcta,
  rechazo de bytes distintos, borrador descartable y undo/redo verificados.
- Un mapa mantiene identidad al aplicar/deshacer origen visual; X física7→7.125 lo retira.
  Consola sin errores/advertencias. Evidencia y límites en [PLAN_REFERENCE.md](../ui/PLAN_REFERENCE.md).
- Servicios propios detenidos, sin listeners finales en5174/8000. Backend no se repite:
  contrato intacto y consumidor validado contra API real; CI de la rama verificará conjunto.
- **Solicitud al integrador:** aceptar consumidor A-102 y consolidar evidencia; M2 y
  producto siguen parciales. Siguiente trabajo A: recorrido de accesibilidad o consumidores
  de #8/#9 cuando sus contratos estén integrados y revisados.
