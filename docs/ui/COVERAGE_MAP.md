# Mapas por perfil, altura y dirección — A-104

Entrega de interfaz del 2026-10-30 (Europe/Madrid), sobre la API B-103 integrada en
[PR #7](https://github.com/Phlekies/smart-home-simulator/pull/7). No cambia modelos físicos,
contratos ni Java. Usa el estimador de trayecto directo disponible; Sionna/ns-3 siguen
pendientes de integración en la API.

## Uso

1. Elegir equipo/radio emisor y equipo/radio que representa el cliente. El perfil copia
   sus parámetros y procedencia actuales; no completa potencia o sensibilidad desconocidas.
2. Indicar origen, área, altura y resolución, con unidades en metros. Opcionalmente añadir
   un punto exacto XYZ, evaluado por la API sin ajustarlo a la rejilla.
3. Calcular. La interfaz muestra cola/progreso y permite cancelar. Editar parámetros,
   instalación, radios o paredes retira el mapa y descarta respuestas anteriores.
4. Elegir señal o margen, AP→perfil o perfil→AP. Cambiar de métrica usa los datos ya
   recibidos. La capa se muestra en el plano 2D, con AP/perfil/frecuencia/altura/resolución.
5. Consultar el punto exacto, metadatos y supuestos. Compatibilidad de radio sin verificar
   conserva esa indicación aunque existan valores numéricos para ambos sentidos.

El área admite los límites del contrato: hasta 40 000 celdas y coste acotado por paredes;
se explican los errores de entrada y de la API. Durante una carga de proyecto el formulario
queda desactivado. Las respuestas deben corresponder al trabajo, huella y parámetros
solicitados; se rechazan dimensiones, arrays o puntos incompletos.

## Interpretación visual

- Escala fija púrpura→turquesa: señal de −100 a −30 dBm, margen de −30 a +40 dB.
  Los extremos saturan; no es una clasificación de fiabilidad ni una probabilidad.
- Rayado: valor disponible en una celda con información parcial.
- Gris: no hay valor de la métrica seleccionada. Gris oscuro: celda sin calcular.
- Cada celda representa una muestra de la API. No hay interpolación de resultados.
  Las celdas del borde se recortan al área pedida sin estirar el resto de la rejilla.
- Los colores no suman energía de varios AP y no acreditan rendimiento, interferencias,
  estabilidad, rutas de malla o compatibilidad funcional. No hay calibración experimental.

## Evidencia

- `npm.cmd --prefix apps/web test`: **84 superadas** (70 previas y 14 de mapas).
  Incluyen coordenadas/bordes, rejillas alargadas, escalas y desconocidos/cero, huellas/parámetros y arrays,
  progreso, cancelación con POST pendiente, edición durante polling, fallos HTTP,
  cancelación no confirmada, desmontaje y entradas independientes.
- `npm.cmd --prefix apps/web run build`: TypeScript/Vite correctos. Permanece el aviso
  previo de tamaño del chunk 3D (~933 kB).
- Navegador y API reales: apartamento 43.6×30.6 m, resolución 0.5 m, altura 1.4 m,
  Hub/radio-1 como AP y Thermostat/radio-1 como perfil; 88×62 celdas.
- Con datos originales incompletos: 0 completas, 5322 parciales y 134 sin calcular.
  AP→perfil sin valor por TX del Hub desconocida; el sentido de retorno conserva su
  valor disponible con rayado. Cambiar de métrica no vuelve a ejecutar el trabajo.
- Punto exacto (7.125, 3.3, 0.4): en ese caso, retorno −48.1 dBm y margen 43.9 dB;
  ida y su margen sin datos. Coordenadas fraccionarias conservadas.
- Caso sintético de asimetría: TX Hub 20 dBm; TX Thermostat −60 dBm y sensibilidad
  −90 dBm. Mismo punto: ida −28.1 dBm / margen 61.9 dB; retorno −108.1 dBm /
  margen −16.1 dB. Son entradas de prueba y predicciones del estimador, no datos de
  fabricante ni mediciones. Compatibilidad sin verificar conservada.
- Cambiar X del AP de 5 a 5.125 retira capa/metadatos al instante; recalcular restaura
  únicamente datos actuales. Un mapa 190×190 m, resolución 1 m, se cancela desde la UI:
  resultado descartado y capa retirada. Respuestas tardías cubiertas por pruebas.
- Consola sin errores ni advertencias en el recorrido final.
  [Captura del caso sintético](coverage-map.jpg).

## Límites y siguiente paso

Mapas/resultados y parámetros del formulario son de sesión: no se guardan con el proyecto
ni hay caché/exportación persistente de mapas. Solo un punto exacto en este primer
consumidor, aunque la API admite más. La capa es 2D, con altura declarada; no añade forjados
ni aceptación de varias plantas. Esta entrega no completa M4 ni la validación de producto.
El siguiente consumidor A es la persistencia del plano de referencia mediante B-104.
