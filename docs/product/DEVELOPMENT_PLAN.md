# Desarrollo del producto después de la migración técnica

Versión 1 · 2026-10-29. Objetivo rector: [PRODUCT_OBJECTIVE.md](../PRODUCT_OBJECTIVE.md).
Prioridad confirmada: Wi-Fi primero, comenzando por 2.4 GHz.

La migración actual aún no está completa. Sus puertas están en
[migration/ROADMAP.md](../migration/ROADMAP.md). No confundir fin de migración con producto
validado. Se pueden preparar datos/mediciones antes; no se espera a terminar la interfaz
para iniciar la validación científica.

## Criterio para ordenar el trabajo

Cada entrega debe acercar al recorrido: **vivienda → equipo candidato → ubicación → riesgo
de cobertura → alternativa → informe**. La comparación de algoritmos se decide por su
error y coste de cálculo en este recorrido. Sionna RT es candidato, no un fin del producto.
No se obliga a integrar ns-3 antes de entregar una herramienta de cobertura útil.
Las funciones ya satisfechas en M2–M4 se reutilizan: las fases P1/P3 completan su
aceptación de uso, incertidumbre y validación; no exigen reimplementar mapas u optimización.

## P0 — Fijar el experimento y la decisión de compra

**Entradas:** contrato/base técnica suficiente y ejemplos de vivienda; puede iniciarse
durante la migración. Ningún dato experimental inventado.

Entregables:

- Especificación de perfiles iniciales de equipos Wi-Fi 2.4 GHz y modos de comunicación.
- Parámetros de AP y cliente en ambos sentidos, fuentes, configuración y desconocidos.
- Requisitos y escenarios concretos de enlaces de sensores/actuadores de bajo tráfico.
- Protocolo de medidas piloto: puntos, alturas, orientaciones, AP/configuración, radio
  utilizada, condiciones, RSSI/ruido y pruebas activas de entrega del perfil definido.
- Partición de viviendas/datos de calibración y evaluación independiente.
- Política de clasificación de cobertura y criterio de fallo de la prueba real.

**Salida:** se puede ejecutar el piloto y evaluar la calidad del diagnóstico. Los objetivos
numéricos se fijan con el piloto y se congelan antes del conjunto independiente.
El origen de los datos de catálogo y materiales es revisable.

## P1 — Mapa orientado al dispositivo y puntos elegidos

**Pregunta:** «¿Cómo sería el enlace de este equipo en cada ubicación?».

- Muestreo configurable de plano, altura y perfil; coordenadas exactas para cada equipo.
- Capas separadas: potencia AP→cliente, cliente→AP y margen limitante.
- Identificación del AP/ruta seleccionados, banda y configuración del cálculo.
- Resolución espacial, interpolación y huecos sin calcular visibles; límite de recursos.
- Leyenda que distingue cobertura, compatibilidad de radio y rendimiento no evaluado.
- Revisión/caché de entrada: editar cualquier dato invalida los resultados relevantes.

**Salida:** un equipo de menor potencia puede resultar limitado en retorno aunque vea
buena señal del AP. Un mapa agregado por varios AP no mezcla señal útil y energía total.

## P2 — Escenarios e incertidumbre útil

**Pregunta:** «¿Qué cambia si esa pared o puerta no se comporta como supongo?».

- Puertas abiertas/cerradas, rangos de materiales/espesores y orientación del equipo.
- Geometría y parámetros medidos, declarados e inferidos diferenciados.
- Sensibilidad del resultado a las hipótesis y detección de escenarios no soportados.
- Reserva de diseño documentada; clasificación favorable/marginal/insuficiente/sin datos.
- Ruido/interferencias no medidos se declaran; pruebas de robustez si existe modelo válido.

**Salida:** una conclusión cambia a marginal o sin datos cuando depende de hipótesis
no resueltas. Variar supuestos no se presenta como una probabilidad estadística de éxito.

## P3 — Comparación y mejora de la instalación

**Pregunta:** «¿Qué puedo cambiar antes de comprar?».

- Escenario base y alternativas con idénticos perfiles y condiciones comparables.
- Mover AP/equipo, cambiar altura/orientación o añadir un AP y su enlace de datos.
- Lugares permitidos, alimentación, cableado y posiciones fijas de equipos.
- Mejorar el peor margen entre ubicaciones importantes, además del área cubierta.
- Recomendaciones explicadas con diferencias cuantificadas y advertencias residuales.
- Búsqueda exhaustiva pequeña como referencia antes de adoptar heurísticas complejas.

**Salida:** la recomendación es realizable; no consiste en situar un router en una pared
sin enchufe ni en añadir un repetidor sin verificar su enlace con la red.
No se recomiendan compras concretas cuya compatibilidad de radio sea desconocida.

## P4 — Calibración y puerta de validación independiente

La campaña piloto empieza en P0 y acompaña P1–P3; esta fase cierra la evidencia para
publicar conclusiones de cobertura en el ámbito definido.

- Importación de medidas con procedencia, equipo, configuración, posición y condiciones.
- Ajuste de materiales/modelo y trazabilidad de cambios respecto a la predicción inicial.
- Comparación entre baseline rápido y motor avanzado sobre los mismos datos independientes.
- MAE/RMSE/sesgo de señal y distribución espacial del error; no solo promedio global.
- Falsos favorables y falsos desfavorables frente al criterio de enlace definido, tamaño
  de muestra, dependencia entre puntos e incertidumbre estadística apropiada.
- Tasa de «sin datos», cobertura de perfiles y pérdida de utilidad por abstención.
- Evaluación por tipos de vivienda/material/perfil, sin esconder casos difíciles.
- Objetivos congelados antes de evaluar; si fallan, revisar y reevaluar con datos nuevos.

**Salida:** informe reproducible de lo que se predice bien y de lo que no se puede afirmar.
No se publica «funcionará» por pasar tests de fórmulas ni por no observar fallos en pocos puntos.

## P5 — Entrega local utilizable sin conocimientos de RF

- Asistente para plano, equipos, datos conocidos/desconocidos y ubicaciones.
- Informe por equipo: decisión, sentidos del enlace, hipótesis, mejoras y pendientes.
- Guardado, recuperación, accesibilidad, ayuda y errores orientados a la tarea.
- Arranque y distribución locales comprobados; preflight CPU/GPU con mensajes claros.
- Pruebas con usuarios nuevos sobre el recorrido de compra/colocación.
- Comprobaciones automáticas de contratos, escenarios e instalación reproducible.

**Salida:** una persona puede completar el recorrido sin editar código ni conocer dBm.
El modo predictivo no obliga a comprar o instalar todos los equipos para obtener utilidad.

## Extensiones posteriores, con puertas propias

| Extensión | Cuándo se justifica | Evidencia necesaria |
|---|---|---|
| Varias plantas/forjados | Se ofrece evaluación entre plantas | Geometría y campaña de validación vertical |
| Wi-Fi 5/6 GHz | Se ofrecen equipos de esas bandas | Materiales, antenas y validación por banda |
| Interconexión inalámbrica de AP/repetidores | Se recomienda ampliar red sin cable | Ambos enlaces y, si se habla de rendimiento, carga compartida |
| Zigbee/Thread | Se amplía la domótica más allá de Wi-Fi | Roles, hubs/border routers, rutas y perfiles de radio propios |
| Rendimiento de cámaras o saturación | Se promete viabilidad de tráfico | Entrega, carga y pruebas activas; ns-3 u otro modelo validado cuando aporte valor |
| Ecosistemas/automatizaciones | Se quiere evaluar funciones de aplicación | Requisitos nuevos; no requisito del producto de cobertura |

## Dependencias y orden

Migración técnica → P0 → P1 → P2 → P3 → cierre P4 → P5.
P0/piloto y preparación de P5 pueden avanzar mientras se completa la base técnica.
La validación no se difiere hasta el último momento. Ninguna ampliación reemplaza estas puertas.

## Métricas de producto y de cómputo

- **Decisión:** falsos favorables, abstenciones y cambios que efectivamente mejoran el enlace.
- **Modelo:** error de señal y estabilidad de conclusiones en escenarios independientes.
- **Uso:** completar plano→diagnóstico→alternativa; comprensión de pendientes y límites.
- **Cálculo:** tiempo al primer resultado, total, memoria y cancelación, con tamaño de
  vivienda, resolución, perfiles, hardware y versiones registrados.

Los objetivos se fijan antes de la evaluación correspondiente. «Más rayos», «más GPU» o
«más fotorealismo» no son métricas de éxito del producto.
