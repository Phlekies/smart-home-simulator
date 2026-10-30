# Ruta de migración y desarrollo

Fecha de inicio: 2026-10-29. Base Java: `eff803c7825ce2ad71e6c0b1b1934f9f8bb26515`.

## Objetivo y límites

Ayudar a decidir, antes de comprar e instalar domótica, si cada equipo tendrá cobertura
de radio suficiente en la ubicación prevista y qué cambios reducen el riesgo de mala
conectividad. Prioridad confirmada: Wi-Fi primero, comenzando por 2.4 GHz. El objetivo
rector está en [PRODUCT_OBJECTIVE.md](../PRODUCT_OBJECTIVE.md). La compatibilidad funcional
completa, las automatizaciones y el rendimiento de tráfico no son requisitos iniciales.
Una simulación no garantiza perfección: cada resultado debe indicar modelo, versión,
supuestos, datos, ámbito de validez y evidencia experimental. Ningún porcentaje de confianza
ni margen de error se inventa. «Sin verificar» es un resultado válido.

No se migra borrando Java. Sus fuentes, Gradle, ejemplos, instaladores y pruebas permanecen
operativos como referencia hasta superar los criterios de sustitución. El prototipo 3D de
la carpeta padre tampoco se modifica. La nueva aplicación vive en este repositorio clonado.

## Arquitectura de destino

- `apps/web`: TypeScript, React y Three.js; plano 2D para edición, vista 3D para inspección.
- `services/simulator`: Python, FastAPI y Pydantic; contratos, importación, orquestación,
  diagnóstico y análisis. Sin dependencias gráficas en el dominio.
- `contracts`: JSON Schema del proyecto versionado y contrato HTTP OpenAPI generados.
- Motores intercambiables: estimador rápido explícitamente limitado; Sionna RT para
  propagación avanzada; ns-3 es una extensión opcional para preguntas de tráfico que
  requieran modelos comprobados, no una integración obligatoria de la versión de cobertura.
- Procesos de cálculo separados de la interfaz. En tareas pesadas: trabajos cancelables,
  límites, progreso y ejecución local o remota mediante el mismo contrato.
- Más adelante: almacenamiento de proyectos, mediciones, escenarios y resultados por hash;
  catálogo con procedencia; ejecutores CPU/GPU. No introducir C++ propio sin una carencia
  y un benchmark que lo justifiquen.

El contrato usa metros, Hz, dBm, dBi y grados explícitos. Frecuencia y canal pertenecen
a cada radio, no al entorno global. Dispositivos, interfaces, redes y conexiones tienen
identificadores estables; la geometría usa coordenadas decimales y altura.

## Inventario y tratamiento del código actual

| Área Java | Tratamiento | Condición para sustituirla |
|---|---|---|
| `physics/RadioMath` | Reimplementar fórmulas documentadas; conservar vectores analíticos | Unidades y casos límite comprobados; BER no confunde SINR con Eb/N0 |
| `physics/Geometry` | Geometría 2D/3D independiente del render | Cruces, esquinas, tangencias, sólidos y escalas probados |
| `model/Device`, `Sensor`, `Hub` | Nuevo dispositivo con radios y roles explícitos | Varias radios, redes, receptores y enlaces asimétricos |
| `model/Environment` | Separar edificio, materiales, ruido y configuración de radios | Sin frecuencia global obligatoria |
| `model/material` | Importar valores como hipótesis empíricas con procedencia | Datos medidos y ámbito de frecuencia/espesor; rangos de incertidumbre |
| `model/template` | Conservar ejemplos y portar plantillas de forma incremental | Igualdad geométrica y pruebas de importación |
| `simulation/PropagationEngine` | Referencia de comportamiento; sustituir mediante adaptadores | Concordancia en casos analíticos y evaluación experimental independiente |
| `simulation/HubPlacementOptimizer` | Recuperar función objetivo, añadir restricciones | Comparación con búsqueda exhaustiva pequeña y evaluación bajo incertidumbre |
| `simulation/LinkValidator` | Mantener comprobaciones internas separadas de validación física | Informes distinguen consistencia, calibración y validación |
| `simulation/raytrace` | Recuperar explicación visual; vincular trayectos al motor real | No usar animación ilustrativa como evidencia numérica |
| `app/ProjectFiles` | Importador Java v1 y nuevo esquema versionado | Todos los ejemplos importan; datos no representables se conservan y se avisan |
| `app/SimulatorModel` | Estado del editor, historial, snapshots y revisiones en web | Undo/redo, selección, autosave y resultados invalidados tras editar |
| `app/CoverageReport` | Nuevo informe exportable y reproducible | Incluye escenario, motor, unidades, límites y procedencia |
| `ui/*` | Reescritura React; edición 2D y representación 3D | Paridad de funciones útiles al objetivo y pruebas de recorridos completos |
| `src/test/*` | Portar intención y datos, no copiar acríticamente expectativas | Casos independientes detectan errores del modelo anterior |
| Gradle / releases | Mantener Java; añadir CI de Python y web | Nueva distribución reproducible y ejecutable desde entorno limpio |

## Fases, entregables y puertas de aceptación

### M0 — Base y auditoría

Clonar, registrar SHA, inventariar funciones y fuentes, mantener Java sin reestructuración.
Definir arquitectura, checklist, decisiones y registro de evidencia.
Salida: documentos revisables y alcance de cada fase explícito.

### M1 — Primer recorrido completo local

1. Proyecto versionado con edificio, alturas, materiales, dispositivos, radios y enlaces.
2. Importar los tres JSON Java v1; conservar el original y avisar de campos inferidos.
3. API de validación/importación, ejemplos, capacidades de motores y simulación rápida.
4. Estimación determinista de presupuesto de enlace directo en ambos sentidos, obstáculos
   y ruido, con compatibilidad básica de radios. Sin Mbps reales, latencia ni garantías.
5. Web con plano y vista 3D, edición de dispositivos, importación/exportación y diagnóstico.
6. Pruebas de API, importación, unidades, geometría y enlaces asimétricos; compilación web.

Salida: abrir ejemplo → editar → simular → exportar → reimportar. Los resultados no se
presentan como equivalentes al motor multipath Java. Motores avanzados no disponibles se
rechazan explícitamente; no se sustituyen silenciosamente por el estimador.

### M2 — Recuperar el editor y los proyectos útiles

Plano a escala, dibujo/movimiento/rotación de paredes, espesor/material, altura y obstáculos
representables por el motor. Importación de imagen como referencia a escala; undo/redo,
guardado/recuperación y accesibilidad. Se puede comenzar por una planta. Varias plantas
requieren forjados y validación propios; no aparentar soporte si solo se dibujan niveles.

Salida: recrear una vivienda sencilla, modificarla y recuperar el proyecto sin pérdida
silenciosa. Las plantillas sirven de ejemplos; no es obligatorio copiar las doce antes
de que el recorrido principal funcione.

### M3 — Motor y evidencia técnica de la sustitución

Evaluar Sionna RT frente a la referencia y al baseline con casos de espacio libre, pared
y reflexión. Probar entorno Python/SO/LLVM/GPU y fijar versiones; verificar interacciones
realmente soportadas. El modelo puede mejorar o corregir Java: no se exige conservar
resultados incorrectos ni fórmulas académicas ajenas a la decisión de cobertura.

Separar escena física de render; conservar unidades, radios, geometría y procedencia.
Cálculos pesados fuera de la interfaz, con progreso, cancelación, caché y límites.
Salida: adaptador ejecutable y reproducible, alcance documentado y benchmark inicial.
Instalar una dependencia o mostrar una escena no completa esta fase.

### M4 — Recuperar mapas y comparación básica

API y web para muestrear señal por plano/altura con resolución declarada, además de
presupuesto individual bidireccional. Seleccionar emisor y receptor/perfil; no sumar la
energía de AP independientes como si fuera señal de una única conexión. Comparar posiciones
del AP y recuperar la búsqueda básica de ubicación con restricciones simples.

Salida: equivalentes útiles de mapa, enlaces y optimización del Java, con límites claros.
No confundir esta recuperación técnica con una clasificación de compra validada: los
mapas por perfil y la clasificación robusta se cierran en las fases de producto P0–P4.

### M5 — Cierre técnico de migración

Contratos y tipos sin deriva, importación de todos los archivos de ejemplo, pruebas
analíticas/de regresión pertinentes, recorrido E2E y CI ejecutada. Verificar instalación
del entorno local y arranque de interfaz/API en un entorno limpio. Registrar matriz de
funciones conservadas, sustituidas y excluidas con motivos.

Salida: nuevo stack sustituye las funciones relevantes de la aplicación Java en el ámbito
anunciado. Java queda como referencia recuperable. No es requisito migrar animaciones
ilustrativas, BER BPSK o capacidad Shannon a la interfaz principal.

## Puerta de finalización de la migración

M0–M5 han de tener evidencia. Hoy solo la base M0/M1 tiene la evidencia descrita en
STATUS.md, con CI remota todavía pendiente. El estimador rápido actual no equivale al
motor multipath Java. Por tanto, la migración completa sigue en curso.

Completar migración no significa «producto con precisión validada». El objetivo rector
es [PRODUCT_OBJECTIVE.md](../PRODUCT_OBJECTIVE.md) y el desarrollo posterior se ejecuta
según [product/DEVELOPMENT_PLAN.md](../product/DEVELOPMENT_PLAN.md), con su checklist propio.

## Prioridades revisadas según el objetivo confirmado

- Núcleo: cobertura por ubicación/perfil, obstáculos, ambos sentidos, datos trazables,
  incertidumbre, comparación de alternativas y validación con medidas.
- Piloto/calibración: preparación temprana; no esperar a automatizaciones o simulación
  completa de paquetes para comenzar a recoger evidencia.
- ns-3 y tráfico: extensiones cuando se quiera evaluar rendimiento/interferencia y exista
  modelo adecuado. No bloquean por defecto el producto inicial de cobertura Wi-Fi.
- Compatibilidad funcional completa, automatizaciones, nube, precios, tiendas, cuentas y
  ejecución remota: fuera del alcance inicial; no requisitos de finalización.
- Zigbee/Thread, otras bandas y varias plantas: ampliaciones con puertas específicas;
  Wi-Fi primero no equivale a soporte de toda la domótica.

## Criterio para omitir o retirar funciones

Conservar una función si ayuda a introducir la vivienda, calcular/entender cobertura,
comparar soluciones o validar/guardar el resultado. Omitir del nuevo recorrido lo que
no ayude a esas decisiones. Retirar implementaciones sustituidas solo después de
comprobar importación, referencias y pruebas necesarias; documentar el motivo.
No se elimina código Java en esta revisión del objetivo.

## Validación y rendimiento de cálculo

Usar escenarios analíticos y viviendas piloto con hardware, tamaño de escena, radios,
resolución, materiales, versiones, memoria y tiempos registrados. Comparar algoritmos
sobre los mismos datos. Una salida físicamente más detallada no se considera mejor sin
reducir error o mejorar una decisión con un coste aceptable.

La evaluación posterior medirá también falsos favorables y abstenciones, no solo error
medio de RSSI. Los objetivos se fijan con el piloto antes de evaluar datos independientes.
No se inventan probabilidades, márgenes experimentales o garantías de conexión.

## Referencias

- [Objetivo del producto](../PRODUCT_OBJECTIVE.md)
- [Plan posterior a la migración](../product/DEVELOPMENT_PLAN.md)
- [Checklist del producto](../product/ACCEPTANCE_CHECKLIST.md)
- https://nvlabs.github.io/sionna/rt/index.html
- https://nvlabs.github.io/sionna/installation.html
- https://www.itu.int/rec/R-REC-P.1238
- https://www.cisco.com/c/en/us/support/docs/wireless/5500-series-wireless-controllers/116057-site-survey-guidelines-wlan-00.html
