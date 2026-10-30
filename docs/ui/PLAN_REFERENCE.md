# Referencia de plano a escala — A-102

Entrega de interfaz del 2026-10-30 (Europe/Madrid). Escala, origen, huella y puntos de
calibración persistidos mediante `Project.plan_reference`, contrato B-104 ya integrado.
No cambia backend, tipos generados ni formato de proyecto. La imagen continúa en el
archivo local de la persona: no se incrusta ni se envía a la API.

## Uso

1. Abrir o crear un proyecto y desplegar «Plano de referencia».
2. Cargar PNG, JPEG o WebP local: hasta 8 MB, 16384 px por lado y 16 millones de píxeles.
3. Elegir A y B en la previsualización o introducir sus coordenadas en píxeles.
   Introducir la distancia real conocida en metros y pulsar «Aplicar escala al plano».
4. Ajustar origen X/Y (esquina superior izquierda) y aplicar de nuevo cuando sea necesario.
   Escala uniforme; se mantiene la proporción original. No se corrige perspectiva,
   distorsión de escáner, inclinación o errores de la medida conocida.
5. Ajustar opacidad o mostrar/ocultar el fondo. Dibujar paredes o crearlas por coordenadas.
   La anchura de la imagen y la longitud de la pared seleccionada se muestran en metros.
6. Guardar JSON o esperar la copia de recuperación. Al reabrir, se conservan los metadatos;
   la referencia muestra «imagen no disponible» hasta elegir «Reasociar imagen guardada».
7. Reasociar el archivo original. Se comprueban SHA-256 de sus bytes, dimensiones y tipo.
   Un nombre distinto es válido con los mismos bytes; el mismo nombre no acredita identidad.

La selección de referencia ocurre en un SVG distinto del editor: no crea ni mueve paredes.
No se redondean los puntos de calibración a la cuadrícula de 0,1 m. Se exige separación
mínima de 2 píxeles y una distancia conocida entre 0,01 y 20000 m; toda la imagen aplicada
debe caber en las coordenadas admitidas por el editor (±10000 m).

Al elegir solo A se impide aplicar una pareja incompleta. Escape recupera los puntos
previos. Introducir coordenadas numéricas permite completar el ajuste sin ratón. Ctrl+Z
dentro del panel no deshace la geometría de la vivienda. Aplicar/retirar la referencia
cancela el modo de dibujo de paredes para evitar mezclar herramientas.

Las paredes y dispositivos existentes conservan sus medidas al recalibrar la imagen.
La imagen es referencia visual: no se convierte automáticamente en obstáculos ni afecta
a la simulación. Solo la geometría del proyecto llega al cálculo.

## Datos locales, historial y recuperación

El JSON y la recuperación incluyen nombre, MIME, SHA-256, píxeles, metros por píxel,
origen, puntos exactos y distancia conocida, con procedencia de calibración del usuario.
No incluyen bytes de imagen, URL del navegador, opacidad ni visibilidad. Estas preferencias
vuelven a 55 % y visible al abrir otro proyecto. La huella se calcula localmente.

Una imagen ausente o distinta no bloquea la vivienda ni borra su referencia. Reasociar
rehidrata los puntos, escala y origen sin recalibrar ni cambiar los metadatos. También
se admiten referencias importadas sin puntos de calibración: se usa su escala guardada;
para recalibrarlas se debe indicar una distancia conocida.

«Elegir otra imagen» prepara un borrador. El fondo y los metadatos anteriores se mantienen
hasta aplicar la nueva escala; «Descartar imagen pendiente» conserva la referencia previa.
Los cambios pendientes de calibración se rotulan como no incluidos aún en el proyecto.

Aplicar, sustituir y retirar metadatos son acciones de historial. Deshacer puede recuperar
una referencia cuyo archivo ya no está en memoria: se indica y se permite reasociarla.
Al cambiar de proyecto se descarta el recurso de sesión para evitar mezclar viviendas.
Las URLs se revocan al descartar borradores, cambiar/retirar el recurso o cerrar el editor.
Las cargas obsoletas se descartan si cambia el proyecto o la referencia durante la lectura.

La referencia visual no es entrada del motor. Sus cambios y su undo/redo conservan los
resultados de radio, mapas y comparabilidad de posiciones. Los cambios físicos mantienen
la invalidación habitual. Guardar comprueba la revisión completa del proyecto, incluida
la referencia, para no exportar una respuesta de validación anterior.

Compatibilidad: los proyectos v1 sin referencia siguen abriendo. Un proyecto con este
campo puede ser rechazado por versiones anteriores a B-104; ver
[PLAN_REFERENCE_CONTRACT.md](../simulation/PLAN_REFERENCE_CONTRACT.md).

## Evidencia

- 11 pruebas iniciales del dominio: distancia horizontal/vertical/diagonal, coordenadas
  fraccionarias, puntos coincidentes/fuera de imagen, escalas, proporción, origen,
  límites físicos/de píxeles y límites de archivos/MIME.
- 10 pruebas adicionales de persistencia/comparación: vector SHA-256 conocido, identidad
  por bytes y dimensiones/MIME, recurso renombrado/ausente/distinto, coordenadas fraccionarias,
  metadatos sin URL/preferencias, recuperación e historial, datos originales conservados,
  referencias sin calibración y separación de entradas físicas/visuales.
- Navegador/API reales con [fixture sintético](reference-fixture.png), 800×600 px:
  A=(100.125,300.25), B=(700.375,300.25), distancia=12.005 m → escala 0.02 m/px,
  imagen de 16×12 m, origen (−2.125,3.75). Los campos muestran sus decimales completos.
- Descarga real `entorno.shsim (5).json`, validada por API y leída desde disco: todos los
  campos canónicos y los puntos exactos presentes; SHA-256 coincide con el archivo local
  `85c35c6236ca2aeb6026c1752a5342190bf646ece3cab73298fb1479c5f78422`.
- Recargar/restaurar conserva la calibración y muestra imagen ausente. Un PNG con el mismo
  nombre y dimensiones pero bytes distintos se rechaza; copia idéntica renombrada se acepta
  y recupera el fondo. Reabrir el JSON descargado conserva los mismos datos y vuelve a pedir
  reasociación, sin reutilizar el recurso de la vivienda anterior.
- Cambiar origen a −1.375 se aplica exactamente; Deshacer recupera −2.125. Una sustitución
  pendiente conserva la URL aplicada anterior y se descarta sin pérdida. Retirar referencia,
  deshacer y rehacer restaura/retira metadatos; imagen ausente explícita y reasociable.
- Un mapa calculado conserva identidad al aplicar/deshacer un origen de imagen. Mover el
  equipo de X=7 a X=7.125 retira el mapa al instante. Mostrar/ocultar fondo funciona.
- Consola final sin errores ni advertencias. [Captura de la recuperación](plan-reference-persistence.jpg).
  La [captura inicial](plan-reference.jpg) documenta la entrega histórica de sesión.
- `npm.cmd --prefix apps/web test`: **94 superadas**; TypeScript/Vite y `git diff --check`
  correctos. Persiste el aviso previo del chunk 3D de ~933 kB. Servicios temporales detenidos.

La escala depende de la distancia indicada y de la calidad de la imagen. No certifica
dimensiones del edificio ni valida el modelo de propagación. Esta entrega completa el
consumidor A-102; la aceptación global de M2 requiere el resto de su checklist.
