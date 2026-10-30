# Diagnóstico de obstáculos por sentido — A-106

Entrega de interfaz del 2026-10-30 (Europe/Madrid), con el estimador `quick-estimate`
actual. Consume `DirectionResult` existente, sin fórmulas físicas nuevas ni cambio de API.

«Ver diagnóstico» está disponible para cada enlace calculado, también cuando no hay
motivos de advertencia. Presenta ida y vuelta por separado:

- Nombres, radios, protocolo, frecuencia exacta en MHz, canal y sensibilidad del receptor.
- Distancia 3D, pérdida de propagación y pérdida acumulada de paredes recibidas del motor.
- Señal prevista, ruido modelado, SNR y margen con unidades explícitas.
- Lista de paredes que devuelve `crossed_wall_ids`, con material, espesor y procedencia.
  «Inspeccionar pared» la selecciona y enfoca el inspector, conservando el resultado.
- Un sentido no calculado se identifica sin deducir su señal a partir de la dirección
  opuesta. Los motivos del enlace se mantienen visibles en el diagnóstico.

Las pérdidas son un total del trayecto directo. No se inventan pérdidas individuales
por pared ni se presenta esta lista como explicación de todo el multipath real. Cero
cruces no significa ausencia de otros obstáculos/interferencias. Ruido térmico y figura
de ruido del receptor no representan una evaluación de interferencias/tráfico.

Cambiar una pared invalida los resultados y retira el diagnóstico anterior hasta volver
a estimar. No se dibujan trayectos supuestamente calculados por un motor avanzado.
Al integrar un motor distinto, B y A deberán revisar que esta presentación siga expresando
su ámbito; no anunciar este diagnóstico directo como ray tracing avanzado.

## Evidencia en navegador

- Apartamento original: Thermostat→Hub muestra 0 paredes cruzadas y advertencia de que
  eso no demuestra ausencia de otros obstáculos. La vuelta no se calcula por falta de
  potencia TX del Hub; no se muestra como una conexión funcional.
- Smoke detector→Hub: distancia 19.0 m, una pared (n.º 5, Drywall), espesor 8 cm,
  pérdida acumulada 3.0 dB y señal −69.9 dBm. Procedencia empírica heredada visible.
- Inspeccionar esa pared la selecciona y enfoca «Centro X». Cambiar a Concrete y
  recalcular: misma pared/19.0 m, pérdidas 11.6 dB y señal −78.5 dBm. La vuelta continúa
  sin calcular y el enlace «Sin verificar». [Captura](link-diagnostics.jpg).
- Consola del navegador sin errores durante el recorrido. Estos números son predicciones
  del estimador, no datos de una vivienda medida ni validación experimental.

No se añaden pruebas que repliquen un formateo de campos. Se verificó el recorrido real
con resultados de la API. Las pruebas/build de la entrega están en
[el registro de A](../process/AGENT_A.md). Backend/contratos/Java no se modificaron.
