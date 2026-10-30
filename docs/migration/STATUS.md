# Estado y evidencia

Inicio: 2026-10-29. La migración completa está en curso, no terminada.

## Resumen vigente para retomar trabajo

Última actualización documental: 2026-10-30, I-002 publicada y entrega A-104 en revisión. Leer también el archivo local `AGENTS.md`,
[proceso A/B](../process/WORKFLOW.md) y [tablero](../process/WORKBOARD.md).

- M0/base M1 implementados; CI remota de migración superada en PR #2 para 33f1df8.
- M2 parcial: paredes/undo, recuperación local, radios/enlaces y recorrido de teclado
  implementados. Referencia de imagen de sesión disponible; persistencia del consumidor
  A-102 y evaluación completa de accesibilidad pendientes.
- API de mapas B-103 y tipos en main; visualización A-104 implementada en rama de revisión
  `codex/coverage-map-ui`, con [evidencia UI](../ui/COVERAGE_MAP.md). Sionna RT no está integrado en la API.
  B-102: Sionna RT evaluado en WSL/CPU contra referencias (18/18); Windows nativo no ejecuta.
- Sin validación experimental en viviendas; el producto completo continúa pendiente.
- Última evidencia conjunta local: **162 pruebas Python, 70 web/editor, build y contratos
  correctos**. Se integran las entregas A-101/102/103/105–108 y B-101/102/103/104.
  Java no se modifica. A-104 posterior: **84 web/editor y build correctos**; no cambia
  backend/contratos. Es una entrega independiente, pendiente de integración.
- I-002 terminada por autorización del usuario: [PR #7](https://github.com/Phlekies/smart-home-simulator/pull/7)
  fusionado en main `046ee827ded4f97aebf58e251234fb5175a37dc1`. CI de migración y
  Java Linux/Windows/macOS verde antes y después. Trabajo posterior en worktree aislado
  para evitar cambios de rama concurrentes en el checkout compartido.
- `AGENTS.md` continúa local/excluido. Las secciones inferiores son evidencia histórica;
  las frases de publicación de aquellas entregas no describen revisiones posteriores.

Las secciones siguientes conservan evidencia histórica. Sus límites se refieren a cada
entrega; este resumen y el checklist reflejan lo pendiente actual.

## Base

- Clon local: `C:/Simulador_smart_homes3D/smart-home-simulator`.
- Origen: https://github.com/Phlekies/smart-home-simulator.git
- SHA: `eff803c7825ce2ad71e6c0b1b1934f9f8bb26515`.
- Fuentes Java conservadas; prototipo de la carpeta padre conservado.
- M0: documentos ROADMAP, CHECKLIST y decisiones preparados.

## I-002 — revisión conjunta del 2026-10-30

Por instrucción explícita del usuario, A asume temporalmente integración y publicación,
antes de volver al desarrollo de consumidores de interfaz. Se inspecciona la pila de B
hasta a5e6ff8 y se combina con las entregas A guardadas en 1b5b596. La CI previa de B
en PR #6 estaba verde; no acredita por sí sola la combinación nueva.

Revisión y correcciones antes de publicar:

- Se reproducía POST de mapas 500 al segundo ciclo de vida de la misma aplicación:
  la cola cerrada se reutilizaba. Se crea una cola por arranque y se cierra al salir.
- Una rejilla de 0.2×0.2 m con resolución de 1 m evaluaba (0.5,0.5), fuera del área.
  Ahora las celdas de borde usan el centro de su extensión recortada. Se valida toda
  la extensión de mapa dentro de ±10000 m y se actualiza la descripción del contrato.
- Una cancelación entre acabar el cálculo y publicar el resultado ya no publica `done`.
- Se incluye coverage-map.ts en el script de generación para que la CI detecte deriva.

Evidencia de la combinación: 162 pruebas Python (157 de B + 5 casos de regresión),
70 web/editor, build TypeScript/Vite y comprobación de contratos correctos. Regeneración
exclusivamente por sus herramientas canónicas. Java/Gradle/ejemplos originales intactos.
No se reinstala Sionna ni se atribuye una nueva ejecución a su evidencia WSL de B-102.
Se mantiene 501 para Sionna/ns-3 en la API y el estimador directo como único motor web.

Las pruebas con TestClient se ejecutan fuera del sandbox tras detener una ejecución
restringida bloqueada por los hilos; el resto de herramientas funciona normalmente.
`AGENTS.md`, node_modules, entornos y worktree temporal quedan fuera de los commits.
Publicación verificada: PR #7 fusionado el 2026-10-30, main 046ee827. CI previa en 79e88f1:
[migración](https://github.com/Phlekies/smart-home-simulator/actions/runs/41030716959) y
[Java](https://github.com/Phlekies/smart-home-simulator/actions/runs/41030717021) correctas.
CI posterior en main:
[migración](https://github.com/Phlekies/smart-home-simulator/actions/runs/41030985186) y
[Java](https://github.com/Phlekies/smart-home-simulator/actions/runs/41030985366) correctas.
La pila B de PR #3–#6 está incluida por este merge; no debe fusionarse otra vez como trabajo nuevo.

## Entrega actual — primera base funcional

M0 preparado y recorrido local M1 implementado. Queda pendiente su ejecución en CI
remota: el workflow está añadido, pero no se ha publicado ni ejecutado desde esta sesión.
No se ha completado la migración completa ni la paridad con Java.

Implementado:

- Contrato Pydantic con metros/Hz/dBm/dBi, alturas, materiales, múltiples radios y enlaces.
- IDs y referencias validados, números finitos y acotados, rechazo de geometría degenerada
  y versiones desconocidas; límite de entrada HTTP de 2 MB.
- Importador de los tres ejemplos Java; original íntegro conservado en `legacy_source`.
- API FastAPI para ejemplos, importación/validación, capacidades y estimación directa.
- Cálculo bidireccional, pérdidas de paredes verticales, distancia 3D, antena aproximada,
  ruido, margen y motivos de datos insuficientes. Sin métricas ficticias de tráfico.
- React/TypeScript: abrir/importar, nuevo proyecto, añadir/borrar dispositivos, crear
  enlaces, editar posición/altura/radio, plano arrastrable, vista 3D y exportaciones.
- Resultados invalidados tras editar; revisión de entrada para descartar respuestas antiguas.
- JSON Schema, OpenAPI y tipos TypeScript generados; workflow CI y dependencias fijadas.
- Lanzador conjunto local y documentación de instalación.

### Evidencia del 2026-10-29

| Verificación | Resultado |
|---|---|
| `git rev-parse HEAD` al clonar | SHA de origen registrado arriba |
| `gradlew.bat test --no-daemon` | BUILD SUCCESSFUL; 192 pruebas, 0 fallos, 0 errores, 0 omitidas (XML Gradle) |
| `.venv/Scripts/python.exe -m pytest services/simulator/tests -q` | 31 pruebas superadas |
| `scripts/export_contracts.py --check` | Contratos sin deriva |
| `npm --prefix apps/web run build` | TypeScript y Vite correctos |
| `pip check` | Sin dependencias incompatibles |
| Instalación editable documentada, sin dependencias ni aislamiento de build | Correcta con setuptools fijado |
| `git diff -- src build.gradle.kts settings.gradle.kts examples` | Sin cambios en las fuentes/configuración/ejemplos Java |
| Navegador: abrir apartamento y ejecutar | Seis enlaces y razones de «sin verificar» visibles |
| Navegador: X = 7.125 | Coordenada conservada; resultados anteriores retirados |
| Navegador: vista 3D | Escena visible; sin errores de consola |
| Navegador: abrir archivo `warehouse.shsim.json` | Seis dispositivos importados y aviso de archivo abierto |
| Navegador: guardar JSON | Descarga real completada; archivo leído y reimportado por Python, 7 dispositivos/6 enlaces/original conservado |
| Navegador: nuevo → dos dispositivos → enlace → simular | Presupuesto de ida y vuelta visible, sin inventar sensibilidades |
| `scripts/dev.py` | Interfaz HTTP 200 y `/api/health` = ok; ambos servicios en loopback |
| Captura | `preview.jpg` muestra la interfaz con diagnóstico |

### Límites de la primera entrega (histórico; ver entrega M2 más abajo)

- Sionna RT y ns-3 no están instalados/integrados ni validados. Sus endpoints rechazan
  ejecución (501) sin fallback silencioso.
- El estimador rápido no reemplaza el multipath Java: solo trayecto directo, materiales
  heredados empíricos y antenas aproximadas. No hay calibración experimental.
- Sin dibujo completo de paredes, forjados, mapas de cobertura nuevos, importación de
  planos a escala, undo/redo, autosave ni catálogo comercial: corresponden a fases siguientes.
- No hay Mbps útiles, latencia, comportamiento de malla, automatizaciones ni pruebas de
  compatibilidad funcional. Protocolo desconocido permanece sin verificar.
- CI preparado pero no ejecutado remotamente; no se ha hecho push. No se ha comprobado
  aún una instalación completamente limpia en otro ordenador ni distribución de escritorio.
- Build avisa de un chunk 3D de ~933 kB, cargado bajo demanda. Optimización de entrega
  pendiente de benchmark. Three/Fiber emite un aviso de deprecación de `THREE.Clock`.
- Las pruebas de TestClient emiten un aviso de deprecación httpx/Starlette; no afecta a
  las pruebas superadas, pero se debe revisar al actualizar ese adaptador de pruebas.
- Pruebas con hilos, Java y servidores se ejecutaron fuera del sandbox, porque algunas
  ejecuciones restringidas quedaron atascadas; procesos de prueba atascados cerrados.

Próxima puerta: M2 (edición/proyectos útiles) y prueba técnica M3 de motor y hardware.
El checklist conserva sin marcar CI remoto y todas las capacidades posteriores.

## Revisión de objetivo — 2026-10-29

El usuario concreta la decisión de producto: anticipar problemas de cobertura en la
ubicación prevista antes de comprar/instalar equipos domóticos. Confirma **Wi-Fi primero**;
la propuesta inicial se centra en 2.4 GHz.

- `docs/PRODUCT_OBJECTIVE.md` define usuario, decisión, entradas, mapas por perfil/altura,
  ambos sentidos, incertidumbre, clasificación prudente y alcance/exclusiones.
- `docs/product/DEVELOPMENT_PLAN.md` define las fases P0–P5 posteriores a la migración
  técnica, con piloto temprano y puerta de validación independiente.
- `docs/product/ACCEPTANCE_CHECKLIST.md` conserva esas capacidades como pendientes.
- ROADMAP/CHECKLIST de migración reordenados en M0–M5 para recuperar funciones útiles,
  sin exigir copiar animaciones ni completar automatizaciones, nube o ns-3.
- README y ADR-007 actualizados para mantener una única prioridad de producto.

Esta revisión cambia documentación y criterios; no añade capacidades ejecutables ni
elimina fuentes Java. Los resultados de pruebas anteriores siguen registrados como
evidencia de aquella entrega; no se repiten suites de código por estos cambios de texto.
Las puertas de migración y de precisión del producto permanecen separadas.
Los límites de automatizaciones, rendimiento de tráfico y compatibilidad funcional
registrados arriba no son pendientes bloqueantes del producto inicial de cobertura.

## Entrega de edición de paredes — 2026-10-29

M2 avanza sin darse por completada. Implementado:

- Selección de paredes en plano/lista/vista 3D; dibujo con dos puntos, vista previa,
  longitud y ajuste de creación a 0.1 m; Escape cancela el dibujo.
- Arrastre de paredes/dispositivos con encuadre congelado durante el gesto; flechas
  para desplazar el objeto enfocado (0.1 m, o 1 m con Shift).
- Inspector de centro, longitud, ángulo, altura, espesor, base y material. Los cambios
  llegan al mismo proyecto utilizado por la API y la vista 3D.
- Pérdidas del material editables en apartado avanzado, con efecto sobre todas las
  paredes de ese material y procedencia de hipótesis del usuario.
- Historial inmutable limitado a 50 acciones; un arrastre completo forma una entrada.
  Undo/redo con botones y atajos; importación/nuevo reinician historial. Navegar historial
  invalida resultados cuando cambia el proyecto; un atajo sin historial no los borra.
- Segmentos importados menores de 0.1 m conservan su longitud al mover/girar, respetando
  el mínimo del contrato. El mínimo práctico de dibujo no altera archivos importados.
- CI preparada para ejecutar las pruebas del dominio del editor, sin ejecución remota aún.

Evidencia actual:

| Comprobación | Resultado |
|---|---|
| `npm --prefix apps/web test` | 16 pruebas superadas: snapshots, ramas, gestos, límite y geometría |
| `npm --prefix apps/web run build` | TypeScript y Vite correctos |
| `pytest services/simulator/tests -q` | 31 pruebas superadas; aviso httpx/Starlette ya registrado |
| `scripts/export_contracts.py --check` | Sin deriva; contrato de proyecto sin cambios |
| Navegador: cambiar pared 5 del apartamento de Drywall a Concrete | Smoke detector pasó de -69.9 a -78.5 dBm; deshacer recuperó -69.9 dBm y el hash original |
| Navegador: Ctrl+Z sin historial disponible | Se conservó la tabla de resultados |
| Navegador: nuevo → dibujo horizontal de dos puntos | 5 paredes; nueva pared 5.9 m, ángulo 0° |
| Navegador: editar longitud/giro/altura/espesor/material | 6 m, 45°, 3 m, 20 cm y Brick, reflejados en el plano/inspector |
| Navegador: mover con flecha | Centro X 5.75→5.85; longitud y ángulo conservados |
| Navegador: arrastrar y deshacer una vez | Centro (5.85,2.8)→(7.05,3.7)→(5.85,2.8) |
| Navegador: borrar, deshacer y rehacer pared | Recuento 5→4→5→4; recuperada nuevamente para continuar el recorrido |
| Navegador: vivienda editada + dos dispositivos + enlace → API | Estimación recibida; datos desconocidos permanecen sin verificar |
| Navegador: vista 3D del proyecto editado | Pared seleccionada a 45°, altura 3 m y espesor 20 cm representados; sin errores de consola |
| Captura de esta entrega | `editor-walls.jpg` |

Los valores de señal son resultados del estimador analítico actual, no mediciones ni
evidencia de precisión experimental. Siguen pendientes imagen de referencia calibrada,
recuperación automática y evaluación completa de accesibilidad. No se han añadido
forjados, mapas de cobertura nuevos, Sionna RT ni simulación de tráfico.

## Entrega B-101 — referencias analíticas y medidas — 2026-10-30

Rama `agent-b/b-101-reference-cases` desde `ec62675`, clon separado del checkout de A.
Commit 263650c publicado y [PR #3](https://github.com/Phlekies/smart-home-simulator/pull/3) abierto en borrador contra `codex/migrate-web-python`;
sin merge. CI remota: consultar el PR. Documentación técnica en `docs/simulation/`.

- `references.py`: 19 casos (espacio libre, log-distance, pared ITU-R P.2040-3, reflexión
  especular por imágenes) independientes del motor y arnés `compare()` para cualquier motor.
- `measurements.py` y `contracts/measurement-campaign.schema.json`: campañas locales separadas
  del proyecto, procedencia de parámetros, puntos planificados/medidos/excluidos, recuentos
  crudos de entrega, criterio congelado y partición por vivienda. Plantilla sintética sin medidas.
- `PILOT_PROTOCOL.md`: protocolo propuesto, sin ejecutar; umbral de fallo pendiente de decisión.

| Comprobación | Resultado |
|---|---|
| `pytest services/simulator/tests -q` | 107 superadas (31 previas + 76 nuevas); aviso httpx/Starlette ya registrado |
| `scripts/export_contracts.py --check` | Sin deriva; contratos previos idénticos, nuevo esquema de campañas |
| `npm ci`, `npm run contracts`, `git diff --exit-code src/generated` | Tipos TypeScript sin deriva |
| `npm run build` / `npm test` | Correcto / 16 superadas |
| `python -m smart_environment.references` | Estimador = Friis y su propio modelo (Δ < 1e-9 dB); paredes con tabla Java se desvían de la losa ITU entre −3.9 y +0.6 dB; reflexión no modelada (−4.8 / +0.3 dB) |

CI remota de [PR #3](https://github.com/Phlekies/smart-home-simulator/pull/3) superada para `fc9f062`:
[migración](https://github.com/Phlekies/smart-home-simulator/actions/runs/41023810988) (python-web) y
[Java](https://github.com/Phlekies/smart-home-simulator/actions/runs/41023810990) en Linux, Windows y macOS.

Límites: referencias idealizadas, no medidas; tabla ITU contrastada con la reproducción de
MathWorks (PDF ITU con 404), pendiente de cotejo oficial. Ningún checklist se marca con esta
entrega: el criterio activo de fallo, los conjuntos reales y el motor avanzado siguen pendientes.

## Entrega B-102 — evaluación aislada de Sionna RT — 2026-10-30

Rama `agent-b/b-102-sionna-evaluation`, [PR #4](https://github.com/Phlekies/smart-home-simulator/pull/4) en borrador apilado sobre #3; sin merge. Informe completo en
[ADVANCED_ENGINE_EVALUATION](../simulation/ADVANCED_ENGINE_EVALUATION.md) y evidencia JSON en
`docs/simulation/evidence/`.

| Comprobación | Resultado |
|---|---|
| Windows 11, Python 3.13.7, sionna-rt 2.2.0 sin LLVM | `ImportError`: no encuentra `LLVM-C.dll` |
| Ídem con LLVM 18.1.8 portable (`DRJIT_LIBLLVM_PATH`) | Dr.Jit aborta en un cálculo trivial: `Failed to materialize symbols` (también con objetivo AVX2) |
| WSL2 Ubuntu 24.04, Python 3.12.3, LLVM 20.1.2, sionna-rt 2.2.0 / mitsuba 3.9.1 / drjit 1.5.0 | Ejecuta en `llvm_ad_mono_polarized` |
| `sionna_evaluation.py` en WSL | 18/18 casos físicos y de coherencia con |Δ| < 0.001 dB; LD-n3 no modelado; pico 703 MB |
| Ejemplos Java, `max_depth` 3 | 35–48 ms por enlace; con difracción 68–85 ms; almacén: 3 enlaces sin trayecto (profundidad/metal) |
| Rejilla de 5307 receptores / mapa planar de 21 525 celdas | 11.7 s / 0.02–0.41 s según rayos (81 %–18 % de celdas vacías) |
| `pytest services/simulator/tests -q` (venv de la aplicación) | 117 superadas; el adaptador no requiere Sionna para sus pruebas |
| `scripts/export_contracts.py --check` | Sin deriva; ningún contrato cambia |

Límites: concordancia con física idealizada, no con medidas. Difracción y difusa sin caso de
referencia. Sin GPU compatible. La API mantiene 501 para `sionna-rt`, sin fallback.

## Entrega B-104 — contrato de la referencia de plano — 2026-10-30

Respuesta a la solicitud de A-102. `Project.plan_reference` opcional (v1 aditivo): nombre,
tipo, SHA-256, píxeles, metros por píxel, origen y calibración; la imagen no viaja en el JSON
y el hash de cálculo la excluye. Detalle en [PLAN_REFERENCE_CONTRACT](../simulation/PLAN_REFERENCE_CONTRACT.md).

| Comprobación | Resultado |
|---|---|
| `pytest services/simulator/tests -q` | 137 superadas (20 nuevas del contrato) |
| `export_contracts.py` / `--check` | Esquemas y OpenAPI regenerados; sin deriva |
| `npm run contracts`, `build`, `test` | Solo `project.ts` cambia (campo opcional); build correcto; 16/16 |
| Copia del código en curso de A con los tipos nuevos | `tsc --noEmit` correcto; 57/57 pruebas |

M2 «Imagen de referencia con escala y cotas» sigue pendiente: falta el consumidor de A.

## Entrega B-103 — mapas por perfil y altura — 2026-10-30

[PR #6](https://github.com/Phlekies/smart-home-simulator/pull/6) en borrador, apilado sobre [PR #5](https://github.com/Phlekies/smart-home-simulator/pull/5) (B-104). `/api/coverage-maps` (POST/GET/DELETE) calcula, como trabajo cancelable, el presupuesto directo
AP↔perfil en una rejilla a altura declarada y en puntos exactos. Sin clasificación de cobertura.
Detalle en [COVERAGE_MAP_CONTRACT](../simulation/COVERAGE_MAP_CONTRACT.md).

| Comprobación | Resultado |
|---|---|
| `pytest services/simulator/tests -q` | 157 superadas (20 nuevas de mapas) |
| Contratos | `coverage-map.schema.json` nuevo; OpenAPI con 2 rutas y 10 esquemas añadidos, ninguno existente modificado |
| `npm run build` / `npm test` | Correcto / 16/16; `coverage-map.ts` generado con json2ts |
| Servidor real en 127.0.0.1:8765 | 202 → done en 534 ms (apartamento, 0.25 m); cancelación en cola y en curso; 501 para sionna-rt; 422 por frecuencia distinta |
| Coste medido | ~600 000 evaluaciones celda×pared/s; límite 2 M por trabajo |

Pendiente: visualización (A-104), clasificación con reserva (P2), caché y motor avanzado en mapas.

## Reglas de evidencia

Registrar comando, fecha, resultado y limitaciones de cada verificación. Detectar una
dependencia no acredita que el motor funcione. Un modelo analítico no acredita precisión
en viviendas. No marcar el recorrido del navegador si solo pasó la compilación.

## Proceso para agentes — 2026-10-29

Añadidos AGENTS.md, proceso común, tablero y registros separados de A/B. A posee
interfaz/editor; B posee simulación/contratos y consolida integración/documentación
común. Se documentan reservas, traspasos, aceptación, dependencias y límites Git.
Se añade una entrada en la carpeta padre para evitar trabajar sobre el prototipo antiguo.
Los registros se inicializan sin tarea activa; no se han iniciado dos sesiones nuevas.
Esta entrega es documental y no añade funciones de simulación ni ejecuta push/CI remota.

### Visibilidad de instrucciones locales

Por petición posterior del usuario, `AGENTS.md` queda fuera de Git mediante
`.git/info/exclude`. No estaba versionado y no se ha publicado. Se conservan sus
instrucciones en este equipo; un clon nuevo no lo incluye. Se han retirado los enlaces
Markdown al archivo local de la documentación versionable. Los documentos `docs/process/`
siguen siendo versionables; esta exclusión afecta a los archivos llamados `AGENTS.md`.

## Preparación de primera publicación — 2026-10-29

El usuario solicita actualizar GitHub con todos los cambios realizados, conservando
AGENTS.md local. Se crea `codex/migrate-web-python` desde el SHA de base, sin cambios
nuevos en `origin/main`. No se modifica ni elimina la referencia Java.

Verificación previa: 16 pruebas del editor y 31 Python superadas; build web correcto;
JSON Schema/OpenAPI sin deriva; regeneración TypeScript idéntica; Gradle test correcto
con tareas ya actualizadas. Dependencias, entornos, builds y AGENTS.md excluidos.
El commit de preparación no acredita por sí mismo push, PR ni CI remota: registrar
estos resultados solo después de verificarlos.

### Publicación verificada

- Commit inicial de la entrega: `33f1df8b81955070972873f6a89cff65e5e50d9e`, 48 archivos.
- Push verificado: `origin/codex/migrate-web-python` coincide con el commit local.
- [PR #2](https://github.com/Phlekies/smart-home-simulator/pull/2), abierto en borrador
  contra `main`; no se ha hecho merge ni force-push.
- [CI de migración](https://github.com/Phlekies/smart-home-simulator/actions/runs/40959814307)
  superada para 33f1df8: instalación limpia de dependencias, 31 pruebas Python, esquemas,
  regeneración de tipos sin deriva, build web y 16 pruebas del editor.
- [CI Java](https://github.com/Phlekies/smart-home-simulator/actions/runs/40959814298)
  superada para 33f1df8 en Linux, Windows y macOS, incluyendo build, pruebas y Javadoc.
- Esta evidencia corresponde al SHA indicado. Para revisiones posteriores de documentación
  o código, comprobar el último estado en el PR; no heredar conclusiones sin verificarlas.
- `git ls-tree` confirma que AGENTS.md no forma parte del commit. Tampoco se incluyen
  entornos, dependencias instaladas, builds ni archivos temporales locales.
- El plugin GitHub devolvió 403 al crear el PR; se creó correctamente con la sesión
  autorizada de GitHub CLI y se verificó después su URL, rama y estado de borrador.
