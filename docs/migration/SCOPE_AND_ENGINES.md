# Ámbito real y motores disponibles (B-125)

Actualizado: 2026-11-01. Mantenedor: B / integrador. Resume **qué hace hoy** la aplicación local
nueva, con qué motor y con qué evidencia. Remite a cada contrato y no sustituye a
[STATUS](STATUS.md) ni a los checklists, que siguen siendo la aceptación.

## Estado de integración

| Dónde | Qué contiene |
|---|---|
| `main` | Hasta #10 inclusive: base de migración, importación Java, estimador directo, editor (A-101…A-108), casos de referencia y evaluación de Sionna (B-101…B-104), búsqueda de ubicación y perfiles de cliente (B-105/B-106), escenarios (B-108) y mapas en la interfaz (A-104) |
| En revisión (PR en borrador) | #11 (documentos y matriz Java) → #13 (B-109…B-112) → #15 (B-113…B-116) → #16 (revisión I-005) → #17 (B-117…B-121) → #22 (B-122…B-125). Interfaz de A: #12 y #14 (A-102, A-109…A-113) |

Lo que solo está en revisión **no** está en `main` hasta que el usuario fusione esos PR.

## Qué responde la aplicación

Todo se ejecuta en local, con la API en loopback. Rutas en [arranque local](LOCAL_DEVELOPMENT.md).

| Pregunta | Función | Contrato |
|---|---|---|
| ¿Llega la señal entre dos equipos, en ambos sentidos? | `POST /api/simulations` | Presupuesto de enlace directo; paredes atravesadas; datos ausentes declarados |
| ¿Cómo queda cada punto del plano para un perfil y una altura? | Mapas de cobertura | [mapas](../simulation/COVERAGE_MAP_CONTRACT.md) |
| ¿Dónde pongo el router entre los sitios posibles? | Búsqueda de ubicación | [ubicación](../simulation/PLACEMENT_SEARCH_CONTRACT.md) |
| ¿Qué cambia si muevo un equipo, la altura o la radio? | `POST /api/link-differences` | [diferencias](../simulation/LINK_DIFFERENCE_CONTRACT.md) |
| ¿Y si la puerta está cerrada o el tabique es peor? | Escenarios de mejor y peor caso | [escenarios](../simulation/SCENARIOS_CONTRACT.md) |
| ¿Llegan a la red los datos de cada AP? | Conexión de datos | [conexión](../simulation/DATA_CONNECTION_CONTRACT.md) |
| ¿Qué guardo para instalar? | Informe JSON/Markdown con mapas | [informe](../simulation/REPORT_CONTRACT.md) |
| ¿Cuánto se separan mis medidas del modelo? | Comprobación de campañas y calibración mínima | [medidas](../simulation/MEASUREMENT_FORMAT.md), [calibración](../simulation/CALIBRATION.md) |

Perfiles disponibles: clientes y AP Wi-Fi 4 de 2.4 GHz en 20 MHz, con procedencia por valor
([perfiles](../simulation/RADIO_PROFILES.md)). La potencia de transmisión siempre se declara.

## Motores

| Motor | Estado | Evidencia | Límites principales |
|---|---|---|---|
| Estimación rápida (`quick-estimate` 0.1.0) | Implementado y disponible en todas las rutas | [Casos analíticos](../simulation/REFERENCE_CASES.md). Trayecto directo igual al de Java en 76 sondas de antena y polarización, con diferencia ≤ 0.0022 dB ([paridad](../simulation/JAVA_PARITY.md)) | Solo trayecto directo y paredes verticales. Sin forjados, reflexiones, difracción ni desvanecimiento. Materiales empíricos sin calibrar. Sin validación con medidas |
| Sionna RT 2.2.0 | Evaluado; **no integrado** | 18/18 casos de referencia en WSL2/CPU ([evaluación](../simulation/ADVANCED_ENGINE_EVALUATION.md)) | No se ejecuta en Windows nativo, no está en la API y rechaza antenas directivas. Las rutas responden 501 sin fallback |
| ns-3 | No implementado | — | Extensión futura para protocolos; no es necesario para la cobertura inicial |
| Motor multipath Java | Referencia conservada (aplicación de escritorio) | Contraste con el estimador: +0.3 a +3.6 dB en viviendas y oficinas, hasta +33 dB en el almacén ([paridad](../simulation/JAVA_PARITY.md)) | Modelo 2D sin validar; no se usa en la API |

`GET /api/engines` informa de lo mismo en tiempo de ejecución. Pedir un motor no implementado
devuelve 501 y **nunca** recurre en silencio a otro.

## Niveles de evidencia

| Nivel | Estado |
|---|---|
| Modelo analítico y unidades | Cubierto: pruebas de fórmulas, geometría, contratos y regresiones (más de 370 en Python) |
| Comprobación matemática frente a referencias | Cubierto: casos cerrados (B-101), paridad con Java (B-121) y Sionna en WSL (B-102) |
| Validación en viviendas | **Sin datos.** El formato, el protocolo piloto y la calibración están preparados, pero no hay medidas reales |

## Qué no dice la aplicación

- No clasifica la cobertura (favorable, marginal o insuficiente): faltan el umbral del criterio de
  fallo y la reserva de diseño, que decide el usuario.
- No da probabilidades, porcentajes de éxito, velocidad útil, latencia ni interferencias.
- Un margen positivo no garantiza el funcionamiento. Un equipo empotrado, en otra planta o con
  datos ausentes nunca obtiene un estado favorable (B-122).
- No recomienda comprar ningún modelo ni evalúa la compatibilidad funcional entre equipos.

## Fuera del ámbito actual

Automatizaciones, tiendas y precios, nube y multiusuario, compatibilidad funcional completa,
Zigbee, Thread, BLE y Z-Wave, 5 GHz como ámbito validado, varias plantas e interferencias de otras
redes. Ver [objetivo del producto](../PRODUCT_OBJECTIVE.md).
