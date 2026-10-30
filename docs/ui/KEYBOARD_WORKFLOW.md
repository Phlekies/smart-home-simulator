# Recorrido de teclado y errores — A-103

Entrega del 2026-10-30 (Europe/Madrid), pendiente de revisión/integración por B.

## Cambios

- «Crear pared por coordenadas»: formulario accesible de inicio/fin X/Y en metros,
  envío con Enter, extremos decimales exactos, mensajes de éxito y errores con foco.
  No requiere pulsar dos puntos en el plano. Longitud mínima práctica: 0,1 m.
- El SVG del editor expone un grupo con botones para objetos. Enter/Espacio seleccionan;
  flechas desplazan, Shift amplía el paso. Se conserva dibujo con ratón y undo/redo.
- Abrir/nuevo/restaurar devuelve foco al nombre del proyecto. Añadir dispositivo lo
  coloca en el nombre del equipo. Eliminar anuncia qué se elimina y devuelve foco
  al nombre del proyecto; la eliminación se puede deshacer.
- Los campos numéricos conservan el borrador inválido visible, muestran el motivo y
  `aria-invalid`/descripción; el modelo mantiene el último valor válido. Se permite
  precisión decimal independiente de la cuadrícula. El canal exige un entero.
- Guardar/calcular con un campo del proyecto sin aplicar lleva el foco al problema y
  revela los detalles que lo contienen. Errores del formulario de una pared aún no
  creada no bloquean guardar el proyecto existente. Cambiar objeto/radio reinicia los
  borradores de su inspector; no los confunde con los valores del nuevo objeto.
- Durante importación/apertura se bloquea la edición con `inert`, controles desactivados
  y guarda de cambios. El atajo global de historial se suspende durante esas cargas
  y cuando se trabaja dentro del panel de referencia de imagen.

## Evidencia de recorrido

- Crear por coordenadas con Enter: (1.125,2.375)→(5.125,2.375), longitud 4 m; inspector
  muestra centro (3.125,2.375). Undo/redo recupera la creación.
- Intentar centro X=10000 con pared de 4 m: extremos fuera de rango rechazados,
  borrador visible. Guardar enfoca el campo, sin descargar un proyecto distinto del
  que aparece editándose. Corregir a 3.125 elimina el error.
- Eliminar pared devuelve foco al nombre del proyecto y anuncia posibilidad de deshacer.
- Añadir dispositivo enfoca su nombre. Coordenada X=1.125 conservada; canal=1.5 muestra
  error y Guardar lo enfoca. Corregir a canal=1 permite continuar.
- Dos equipos de prueba con Wi-Fi y un enlace: cálculo recibido con «sin verificar»
  para sensibilidades desconocidas. No se convierten esos valores en datos favorables.
- JSON descargado realmente; mantiene cinco paredes, dos equipos, un enlace y X=1.125.
- Borrador de pared degenerada muestra error; al cerrar el formulario Guardar JSON
  continúa funcionando para el proyecto válido.
- Pérdida de material = −1: error visible. Cerrar detalles y guardar vuelve a abrirlos
  y enfoca ese campo. El modelo conserva la pérdida anterior.
- Siete pruebas nuevas de extremos/creación: precisión decimal, longitudes, degenerados,
  tolerancia numérica al mínimo, límites y no mutación de otras creaciones.

La protección contra edición durante cargas se implementó y revisó en código; no se
simuló una API lenta. El recorrido se verificó en el navegador disponible, no con un
lector de pantalla ni una matriz de tecnologías de asistencia. Sigue pendiente una
evaluación completa de accesibilidad; esta entrega no certifica conformidad WCAG.

No cambian API, modelos físicos, contratos o tipos generados. Los casos de dominio se
ejecutan con las pruebas web existentes. Evidencia de comandos en
[AGENT_A](../process/AGENT_A.md); documentación común/checklists corresponden a B.
