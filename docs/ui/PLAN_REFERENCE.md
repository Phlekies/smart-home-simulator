# Referencia de plano a escala — A-102

Entrega de interfaz del 2026-10-30 (Europe/Madrid). Recorrido de sesión implementado;
persistencia de imagen/transformación pendiente de acuerdo e implementación por B.
No se modifican contratos ni se crea otro formato de proyecto persistido.

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

## Datos locales y persistencia pendiente

La interfaz avisa de que la imagen es **de sesión**, no incluida en el JSON ni en la
recuperación. Cambiar de proyecto o recargar la elimina; las paredes trazadas se guardan
normalmente. Se utilizan URLs de objeto del navegador, revocadas al reemplazar/retirar
el recurso o desmontar el componente. No se envían imágenes a la API ni a terceros.

La solicitud a B está en [AGENT_A](../process/AGENT_A.md): decidir recursos locales,
transformación canónica, identificación por huella, compatibilidad v1 y límites del JSON.
No marcar completa toda A-102/M2 por esta entrega parcial sin persistencia acordada.

## Evidencia

- 11 pruebas de dominio nuevas: distancia horizontal/vertical/diagonal, coordenadas
  fraccionarias, puntos coincidentes/fuera de imagen, escalas, proporción, origen,
  límites físicos/de píxeles y límites de archivos/MIME.
- Navegador: [fixture sintético](reference-fixture.png), 800×600 px, A=(100,300),
  B=(700,300), distancia=12 m → imagen de 16×12 m. Origen (−2,−2) y fondo visibles.
- Dibujo sobre imagen: nueva pared de 4,00 m con inspector/cota. La pared sobrevivió
  a la recarga; la imagen no, de acuerdo con el aviso de sesión.
- Mostrar/ocultar imagen verificado. Elegir nuevo A bloquea aplicar; Escape devuelve
  A.x=100 y conserva B.x=700. Ctrl+Z en la previsualización no altera el enlace existente.
- Captura del editor: [plan-reference.jpg](plan-reference.jpg). Usa datos sintéticos.
- Guardar JSON con imagen aplicada descarga el contrato canónico sin nuevos campos.
  Resultados finales de pruebas/build registrados en [la entrega A](../process/AGENT_A.md).
