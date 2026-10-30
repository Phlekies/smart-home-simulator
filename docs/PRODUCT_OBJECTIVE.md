# Objetivo del producto

Versión 1 · 2026-10-29. Prioridad confirmada por el usuario: **Wi-Fi primero**.
Este documento define el producto; no afirma que la migración o estas capacidades estén terminadas.

## Formulación propuesta

**Permitir que una persona, antes de comprar e instalar dispositivos domóticos, estime
si cada equipo dispondrá de cobertura de radio suficiente en su ubicación prevista,
detecte ubicaciones y configuraciones de riesgo y compare cambios de posición o de
infraestructura, con supuestos, limitaciones e incertidumbre explícitos.**

La decisión que resolvemos es: «¿Puedo colocar este equipo aquí con la infraestructura
que tengo? Si hay riesgo, ¿qué cambio concreto lo reduce antes de gastar dinero?».
El éxito es reducir decisiones de compra e instalación equivocadas por falta de cobertura.
No se promete certificar equipos ni garantizar el funcionamiento de una vivienda desconocida.

## Usuario y recorrido principal

Persona que prepara o amplía la domótica de su vivienda, sin conocimientos de radio.

1. Introducir un plano a escala o dibujar habitaciones y obstáculos relevantes.
2. Indicar materiales/espesores conocidos; conservar como hipótesis lo desconocido.
3. Situar el router/AP actual con altura, banda y configuración conocidas.
4. Elegir un equipo candidato o un perfil de radio y colocarlo donde se instalaría.
5. Consultar cobertura en el plano y diagnóstico individual de ambos sentidos del enlace.
6. Comparar la instalación original con cambios: mover el AP/equipo o añadir un AP.
7. Guardar un informe que explique riesgos, mejoras y datos todavía necesarios.

Las primeras medidas de calibración pueden tomarse con el router existente y equipos
disponibles. No se exige comprar toda la domótica para usar el modo predictivo.
Medir con un móvil no demuestra por sí solo que otro dispositivo tenga la misma radio.

## Qué significan los términos del objetivo

| Expresión | Definición operativa |
|---|---|
| «Cada punto» | Mapa muestreado a resolución declarada, por planta/altura y perfil de radio; además, evaluación de la coordenada exacta elegida, sin redondearla a la cuadrícula visual |
| «La señal» | Potencia recibida prevista y, cuando el modelo/datos lo permiten, ruido/SNR o interferencia; cada magnitud indica qué está modelado |
| «Buena cobertura» | Margen suficiente en ambos sentidos para un perfil/configuración concretos, considerando la reserva de diseño y los escenarios declarados |
| «Conexión fiable» | Entrega/estabilidad observada o modelada y validada bajo condiciones definidas; no se deduce solo de RSSI o de superar una sensibilidad nominal |
| «Este producto» | Modelo y versión con datos trazables; si faltan, perfil genérico identificado como aproximación, nunca equivalencia certificada |
| «Mejor ubicación» | Alternativa que mejora el criterio acordado dentro de lugares físicamente permitidos, con alimentación/cableado considerados |
| «Perfecto» | Recorrido completo, reproducible, explicable y validado dentro de un ámbito definido; no precisión absoluta |

La altura es importante incluso en una sola planta. El mapa es una predicción del entorno
y del receptor seleccionado, no una propiedad universal de la vivienda. Un mapa al que
le falta el perfil de cliente no acredita cobertura domótica bidireccional.

## Qué debe devolver el diagnóstico

- Potencia y margen de AP→dispositivo y dispositivo→AP; indicar el sentido limitante.
- Obstáculos atravesados y contribuciones del modelo; no afirmar causalidad única cuando
  hay interacciones multipath que no se pueden descomponer con esa certeza.
- Escenarios evaluados: materiales aproximados, puerta abierta/cerrada, posiciones,
  orientación y ruido/interferencia, si se dispone de datos/modelo para representarlos.
- Una conclusión de cobertura: **favorable bajo las condiciones evaluadas**, **marginal**,
  **insuficiente** o **sin datos suficientes**. Umbrales y reserva se documentan por perfil.
- Comprobación de compatibilidad de radio separada. La compatibilidad funcional con
  asistentes, aplicaciones y automatizaciones queda fuera de la primera versión.
- Alternativas comparadas y la diferencia respecto al escenario inicial.
- Evidencia de los parámetros: medido, declarado por fabricante, inferido o desconocido.
- Estado independiente de rendimiento: «tráfico y estabilidad no evaluados» cuando aplique.

No hay un umbral RSSI universal válido para cualquier sensor o cámara. Un margen positivo
respecto a una sensibilidad nominal tampoco equivale a «compra segura». La clasificación
favorable requiere un perfil válido y una política de reserva respaldada por evidencia.

## Incertidumbre y modos de uso

**Predictivo:** permite explorar antes de instalar con valores conocidos e hipótesis
visibles. Si faltan datos esenciales, produce estimaciones parciales o se abstiene.

**Calibrado:** incorpora mediciones con ubicación, altura, radio, configuración y condiciones;
ajusta el modelo y muestra el error observado. Siempre se distingue lo medido de lo predicho.

Si un material es desconocido, se evalúa un rango razonado de escenarios en lugar de
asignarle una propiedad exacta. Ese rango no es un intervalo probabilístico calibrado.
No se publican porcentajes de éxito sin validación estadística que los respalde.

El piloto debe fijar umbrales de precisión y falsos favorables antes de la evaluación
independiente. Un «falso favorable» ocurre cuando se aconseja una ubicación como favorable
pero falla el criterio de enlace establecido en la prueba real. Se mide también cuánto
se abstiene el producto: responder siempre «sin datos» no resuelve la decisión de compra.

## Alcance inicial y ampliaciones

### Primera versión útil: Wi-Fi doméstico de 2.4 GHz

- Interfaz local en navegador y cálculo local.
- Vivienda de una planta, con alturas y obstáculos configurables; perfil de cada equipo.
- AP existente y comparación de posiciones; varios AP cuando sus enlaces de alimentación
  de datos estén definidos. Una nueva caja en el plano no implica conectividad a Internet.
- Mapa por perfil/altura, enlace bidireccional y evaluación exacta de puntos elegidos.
- Escenarios de materiales/puertas y diagnóstico explicable.
- Perfiles genéricos declarados y catálogo pequeño con evidencia, no catálogo exhaustivo.
- Comparación antes/después e informe para planificar la instalación.
- Piloto experimental y validación independiente de las conclusiones de cobertura.

### Ampliaciones necesarias según el ámbito ofrecido

Wi-Fi 5/6 GHz con datos y validación propios; varias plantas y forjados; enlaces inalámbricos
entre AP; interferencias y carga con modelos/evidencia; Zigbee y Thread con sus propias
topologías, roles y rutas. El router Wi-Fi no es necesariamente el nodo al que se conecta
un dispositivo de otra tecnología. No se anuncia soporte por añadir un nombre al selector.

Si se ofrecen cámaras o recomendaciones sobre tráfico continuo, primero hay que evaluar
entrega y carga: la primera versión puede informar de su cobertura, pero no de la viabilidad
del vídeo ni de la capacidad de la red. El informe debe mantener esa distinción visible.

## Funciones que ayudan y funciones que pueden esperar

| Función | Decisión |
|---|---|
| Plano, escala, paredes/materiales, alturas, perfiles y parámetros por radio | Núcleo |
| Mapas, ambos sentidos del enlace y estados de datos insuficientes | Núcleo |
| Medidas, calibración, trazabilidad e incertidumbre | Núcleo desde el piloto |
| Comparación de posiciones y restricciones de enchufes/cableado | Núcleo |
| Guardado, undo/redo, informes y accesibilidad | Núcleo de uso |
| 3D | Inspección y comprensión; la precisión del cálculo no depende del realismo gráfico |
| Ver trayectos calculados/obstáculos | Conservar cuando explica una decisión |
| Animaciones decorativas de ondas/rayos, BER BPSK y capacidad Shannon en pantalla principal | No son requisito; retirar del recorrido principal, sin borrar evidencia o pruebas útiles |
| Simulación completa de paquetes con ns-3 | Extensión condicionada a preguntas de tráfico/interferencia; no puerta obligatoria de la versión de cobertura |
| Automatizaciones, compatibilidad funcional completa, cuentas/nube y latencias de servicios | Fuera del alcance inicial |
| Precios, tienda, ranking general de productos, multiusuario y servidor remoto | Fuera del alcance inicial |

No se elimina hoy código de referencia Java. Al sustituirlo se puede omitir una función
que no ayude al objetivo, documentando el motivo y preservando pruebas/datos necesarios.
Migrar no exige copiar cada control académico ni cada animación.

## Cómo sabremos que aporta valor

La persona puede identificar una ubicación problemática, entender qué limita el enlace,
comparar una solución físicamente realizable y obtener un informe con lo pendiente de
verificar. La calidad se evalúa con error de predicción, falsos favorables, abstenciones,
reproducibilidad y pruebas de uso; no por cantidad de algoritmos o detalle visual.

## Base técnica de las decisiones

- [Cisco: planificación y validación de cobertura](https://www.cisco.com/c/en/us/support/docs/wireless/5500-series-wireless-controllers/116057-site-survey-guidelines-wlan-00.html): distingue estudios predictivos, medición pasiva y pruebas activas bidireccionales.
- [ITU-R P.1238](https://www.itu.int/rec/R-REC-P.1238): referencia de métodos y datos para predicción de propagación interior.
- [OpenThread: roles de nodos](https://openthread.io/guides/thread-primer/node-roles-and-types): los equipos finales y los que encaminan tráfico tienen funciones distintas.

Las fases y sus criterios están en [el plan posterior a la migración](product/DEVELOPMENT_PLAN.md)
y [su checklist](product/ACCEPTANCE_CHECKLIST.md).
