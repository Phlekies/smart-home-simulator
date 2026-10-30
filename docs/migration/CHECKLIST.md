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
- [ ] Imagen de referencia con escala y cotas.
- [x] Undo/redo con 50 acciones; cada arrastre es una acción; transformaciones y pérdidas de material recuperables.
- [x] Guardado/apertura manual de proyectos JSON (base M1, conservada).
- [x] Recuperación automática de trabajo tras cierre o recarga (A-101; validación, restaurar/descartar y límites documentados; I-002 integra la evidencia).
- [ ] Accesibilidad y recorrido de creación de una vivienda.
- [x] Ámbito de una planta declarado hasta soportar y validar forjados.

## M3 — Sustitución del motor

- [x] Candidato avanzado ejecutado, versiones y entorno CPU/GPU documentados (Sionna RT 2.2.0 en WSL/CPU; Windows nativo y GPU documentados como no disponibles; B-102).
- [ ] Conversión de unidades, ejes, geometría, radios y materiales probada (parcial B-102: unidades, ejes, paredes y materiales ITU; antenas direccionales y polarizaciones distintas pendientes).
- [x] Interacciones físicas y omisiones de la versión seleccionada documentadas (B-102).
- [x] Espacio libre, pared y reflexión contrastados con referencias (B-101 + B-102: 18/18).
- [ ] Diferencias respecto a Java explicadas; errores antiguos no se conservan como requisito (parcial: tabla de materiales y fase de reflexión documentadas; motor multipath Java no contrastado).
- [ ] Progreso, cancelación, caché y límites para cálculo pesado (parcial B-103: progreso, cancelación y límites de mapas; sin caché).
- [x] Benchmark inicial reproducible de tiempo y memoria (script y evidencia JSON de B-102; un equipo, una ejecución).

## M4 — Mapas y comparación básica

- [x] Muestreo de cobertura por altura con resolución declarada (B-103 + A-104 en `main`; evidencia en [COVERAGE_MAP](../ui/COVERAGE_MAP.md)).
- [x] Presupuesto de ambos sentidos para puntos individuales (punto exacto sin redondeo; B-103 + A-104 en `main`; evidencia en [COVERAGE_MAP](../ui/COVERAGE_MAP.md)).
- [x] AP/emisor y receptor/perfil identificados en cada resultado (B-103 + A-104 en `main`; evidencia en [COVERAGE_MAP](../ui/COVERAGE_MAP.md)).
- [x] Energía agregada no se presenta como señal de una conexión (un AP por mapa; B-103 + A-104 en `main`; evidencia en [COVERAGE_MAP](../ui/COVERAGE_MAP.md)).
- [ ] Comparación de posiciones y optimización básica con restricciones (comparación manual A-105 y API de lugares permitidos B-105 en `main`; falta su interfaz).
- [ ] Mapas guardables y resultados invalidados al editar (invalidación verificada en A-104; los mapas son de sesión y no se guardan).
- [ ] Predicción técnica separada de recomendación de compra validada.

## M5 — Cierre técnico

- [x] JSON Schema/OpenAPI/TypeScript comprobados por CI remota (PR #2, commit 33f1df8).
- [ ] Importación y recuperación de los tres ejemplos Java sin pérdida silenciosa.
- [ ] Pruebas de fórmulas/geometría y regresiones pertinentes.
- [ ] E2E de crear/importar, editar, calcular, comparar y guardar.
- [ ] Instalación limpia y arranque local reproducibles.
- [x] Matriz de funciones conservadas/sustituidas/excluidas y motivos ([FEATURE_MATRIX](FEATURE_MATRIX.md), B-107; revisar al cerrar cada fase).
- [ ] Documentación del ámbito real y motores disponibles.
- [ ] Java preservado como referencia hasta superar las puertas de sustitución.

## Puertas separadas del producto

El producto de cobertura previa a la compra se define en [PRODUCT_OBJECTIVE.md](../PRODUCT_OBJECTIVE.md).
Su [plan](../product/DEVELOPMENT_PLAN.md) y [checklist](../product/ACCEPTANCE_CHECKLIST.md)
son independientes: terminar esta migración técnica no acredita precisión experimental.

Automatizaciones, compatibilidad funcional completa, ns-3 obligatorio, tienda/precios,
cuentas/nube y servidor multiusuario dejan de ser requisitos de la primera versión.
Varias plantas, otras bandas y mallas tendrán aceptación propia cuando se incorporen.
