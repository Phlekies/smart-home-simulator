# Checklist de aceptación del simulador

`[x]` requiere implementación y evidencia registrada en `STATUS.md`. `[ ]` significa
pendiente, incluso si existe un contrato, una maqueta o una dependencia detectable.
Revisar este archivo en cada entrega. No marcar una fase completa con trabajo obligatorio pendiente.
La evidencia de CI remota mencionada en M1 y M5 es compartida: no se requieren dos
ejecuciones idénticas para acreditar el mismo estado de los contratos.

## M0 — Preparación

- [x] Clonar el repositorio y registrar el commit de origen.
- [x] Mantener fuentes y configuración Java como referencia.
- [x] Auditar arquitectura, métricas y formato de proyectos.
- [x] Documentar arquitectura y tratamiento de cada área Java.
- [x] Definir fases y puertas de aceptación.
- [x] Separar precisión física de consistencia matemática.

## M1 — Primer recorrido local

- [x] Contrato versionado con unidades explícitas y coordenadas decimales/altura.
- [x] Varias radios y enlaces identificados sin frecuencia global.
- [x] Validación de IDs, referencias, números finitos y geometría degenerada.
- [x] JSON Schema y OpenAPI comprobados por CI remota de migración en PR #2 (commit 33f1df8, evidencia en STATUS).
- [x] Importar apartamento, oficina y almacén Java sin perder el original.
- [x] Rechazar versiones desconocidas y archivos inválidos.
- [x] Avisar sobre alturas, canales y parámetros inferidos.
- [x] Conservar antenas y ajustes Java aunque el motor rápido no los soporte.
- [x] API de ejemplos, importación, validación y estimación.
- [x] Presupuesto de enlace bidireccional con receptores asimétricos.
- [x] Pérdidas por cruces de paredes y distancia tridimensional.
- [x] Compatibilidad básica de radios; desconocidos no se declaran compatibles.
- [x] Resultados con hash de entrada, motor, versión, alcance y limitaciones.
- [x] Capacidad teórica separada de rendimiento real; métricas no calculadas ausentes.
- [x] Motores avanzados no implementados rechazan ejecución sin fallback silencioso.
- [x] Abrir ejemplo y archivo local desde la web.
- [x] Inspeccionar plano 2D y escena 3D.
- [x] Editar ubicación decimal y altura de dispositivos.
- [x] Editar potencia y parámetros de radio.
- [x] Añadir dispositivos y conexiones en el contrato.
- [x] Exportar y reimportar el nuevo formato.
- [x] Invalidar resultados tras cambios de entradas y descartar respuestas antiguas.
- [x] Mostrar carga, errores, advertencias y estado vacío accesibles.
- [x] Pruebas Python y compilación TypeScript superadas.
- [x] Recorrido web verificado en navegador.
- [x] Documentar arranque local reproducible.

## M2 — Editor y proyectos útiles

- [x] Cuadrícula en metros y dibujo/movimiento/rotación/borrado de paredes.
- [x] Espesor/material/altura configurables; alcance explícito de paredes verticales de una planta, sin forjados.
- [x] Imagen de referencia con escala y cotas (A-102 + B-104 en `main`: calibración por dos puntos y distancia, huella y reasociación; cotas: línea de dimensión con el ancho real de la imagen y longitud de la pared seleccionada o en dibujo, en metros).
- [x] Undo/redo con 50 acciones; cada arrastre es una acción; transformaciones y pérdidas de material recuperables.
- [x] Guardado/apertura manual de proyectos JSON (base M1, conservada).
- [x] Recuperación automática de trabajo tras cierre o recarga (A-101; validación, restaurar/descartar y límites documentados; I-002 integra la evidencia).
- [x] Accesibilidad y recorrido de creación de una vivienda (A-103 teclado; A-118: recorrido guiado de seis pasos, foco visible en el plano, revisión de nombres, etiquetas y avisos; [evidencia](../ui/CLOSING_UI_TASKS.md)).
- [x] Ámbito de una planta declarado hasta soportar y validar forjados.

## M3 — Sustitución del motor

- [x] Candidato avanzado ejecutado, versiones y entorno CPU/GPU documentados (Sionna RT 2.2.0 en WSL/CPU; Windows nativo y GPU documentados como no disponibles; B-102).
- [x] Conversión de unidades, ejes, geometría, radios y materiales probada (B-102: unidades, ejes, paredes y materiales ITU; B-121: antenas direccionales y polarizaciones iguales a Java en 76 sondas, ≤ 0.0022 dB).
- [x] Interacciones físicas y omisiones de la versión seleccionada documentadas (B-102).
- [x] Espacio libre, pared y reflexión contrastados con referencias (B-101 + B-102: 18/18).
- [x] Diferencias respecto a Java explicadas; errores antiguos no se conservan como requisito (tabla de materiales y fase de reflexión, B-101/B-102; esquinas contadas dos veces en Java y dependencia del dibujo corregidas, B-126; contraste multipath, B-121; decisión de motor, ADR-008).
- [x] Progreso, cancelación, caché y límites para cálculo pesado (B-103: progreso, cancelación y límites de mapas; B-105: búsqueda acotada; B-110: caché en memoria por hash de petición).
- [x] Benchmark inicial reproducible de tiempo y memoria (script y evidencia JSON de B-102; un equipo, una ejecución).

## M4 — Mapas y comparación básica

- [x] Muestreo de cobertura por altura con resolución declarada (B-103 + A-104 en `main`; evidencia en [COVERAGE_MAP](../ui/COVERAGE_MAP.md)).
- [x] Presupuesto de ambos sentidos para puntos individuales (punto exacto sin redondeo; B-103 + A-104 en `main`; evidencia en [COVERAGE_MAP](../ui/COVERAGE_MAP.md)).
- [x] AP/emisor y receptor/perfil identificados en cada resultado (B-103 + A-104 en `main`; evidencia en [COVERAGE_MAP](../ui/COVERAGE_MAP.md)).
- [x] Energía agregada no se presenta como señal de una conexión (un AP por mapa; B-103 + A-104 en `main`; evidencia en [COVERAGE_MAP](../ui/COVERAGE_MAP.md)).
- [x] Comparación de posiciones y optimización básica con restricciones (A-105, A-110, B-105, B-117/B-119 y orden bajo incertidumbre B-134, en `main`; comparación verificada en navegador sobre `main` en I-007).
- [x] Mapas guardables y resultados invalidados al editar (invalidación A-104; guardar y reabrir con vigencia según la huella, A-114 sobre B-132; mapas dentro del informe, B-120 y A-115).
- [x] Predicción técnica separada de recomendación de compra validada (API sin veredicto ni recomendación; revisión de textos y aviso explícito en la interfaz, A-119).

## M5 — Cierre técnico

- [x] JSON Schema/OpenAPI/TypeScript comprobados por CI remota (PR #2, commit 33f1df8).
- [x] Importación y recuperación de los tres ejemplos Java sin pérdida silenciosa (B-111: original Java íntegro, recuentos, exportar/reimportar idéntico; recuperación local A-101).
- [x] Pruebas de fórmulas/geometría y regresiones pertinentes (444 pruebas Python; 47 casos de geometría B-126; paridad Java B-121; regresiones de huella y ejemplos; CI de `main` 8734c9b en verde).
- [x] E2E de crear/importar, editar, calcular, comparar y guardar (API B-111; navegador B-127 sobre la combinación integrada; recorrido sobre `main` 8734c9b desde un clon nuevo en I-007; evidencia en [STATUS](STATUS.md)).
- [x] Instalación limpia y arranque local reproducibles (B-112: clon nuevo en Windows x64 siguiendo LOCAL_DEVELOPMENT; Linux en cada CI de migración desde el lock).
- [x] Matriz de funciones conservadas/sustituidas/excluidas y motivos ([FEATURE_MATRIX](FEATURE_MATRIX.md), B-107; revisar al cerrar cada fase).
- [x] Documentación del ámbito real y motores disponibles ([ámbito real y motores](SCOPE_AND_ENGINES.md), [ADR-008](ARCHITECTURE.md)).
- [x] Java preservado como referencia hasta superar las puertas de sustitución (intacto hasta `main` 23ace32, con CI Java en verde en los tres sistemas; después retirado de `main` y conservado en la etiqueta `java-desktop-final` y la release v1.0.0, ADR-009).

## Puertas separadas del producto

El producto de cobertura previa a la compra se define en [PRODUCT_OBJECTIVE.md](../PRODUCT_OBJECTIVE.md).
Su [plan](../product/DEVELOPMENT_PLAN.md) y [checklist](../product/ACCEPTANCE_CHECKLIST.md)
son independientes: terminar esta migración técnica no acredita precisión experimental.

Automatizaciones, compatibilidad funcional completa, ns-3 obligatorio, tienda/precios,
cuentas/nube y servidor multiusuario dejan de ser requisitos de la primera versión.
Varias plantas, otras bandas y mallas tendrán aceptación propia cuando se incorporen.
