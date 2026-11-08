# Matriz de funciones Java: conservadas, sustituidas y excluidas (B-107)

Versión 2 · 2026-11-03 (B-129). Base Java: `eff803c` (v1.0.0; README, paquetes `ui`, `app`, `simulation`,
`model`, `physics`). Estado de la nueva aplicación: `main` hasta #10 (incluye B-105/B-106, B-108 y A-104).
En revisión: #11, #13, #15, #16, #17, #22 y B-126…B-129 (pila B) y #12/#14 (A). Lo que solo está en
revisión se indica así. Criterio: [ROADMAP](ROADMAP.md) («Criterio para omitir o retirar
funciones») y [objetivo del producto](../PRODUCT_OBJECTIVE.md). La aplicación Java sigue completa
como referencia; nada de esta matriz autoriza borrarla.

Estados: **Conservada** (equivalente útil), **Sustituida** (otra forma que responde mejor a la
decisión de cobertura), **Parcial**, **Pendiente** (útil, aún no hecha), **Excluida** (no se migra, con
motivo), **Nueva** (no existía en Java).

## Plano y proyecto

| Función Java | Estado | Nueva aplicación / evidencia | Motivo |
|---|---|---|---|
| Dibujar, mover, girar y borrar paredes; 6 materiales y espesor | Conservada | Editor web (M2): dibujo por clic y por coordenadas (A-103), inspector con altura y base | Núcleo del recorrido |
| Herramienta de habitaciones | Pendiente | Se compone con paredes sueltas | Útil para acelerar el plano; no bloquea |
| Undo/redo | Conservada | 50 acciones, gestos agrupados, atajos (M2) | Núcleo de uso |
| 12 plantillas de edificio | Parcial | Se importan los 3 ejemplos Java (apartamento, oficina, almacén) conservando el original | ROADMAP: no hace falta copiar las doce antes del recorrido; el PR #1 (Java) propone otras plantillas |
| Abrir/guardar proyecto JSON | Sustituida | Formato v1 versionado con unidades explícitas; importador Java v1 que conserva `legacy_source` | Contrato independiente del motor |
| — | Nueva | Recuperación local tras recarga (A-101) | Evita pérdida silenciosa |
| — | Nueva | Imagen de plano a escala: sesión (A-102) y contrato persistente (B-104) | Introducir la vivienda real |
| Exportar el plano como PNG | Pendiente | — | Útil para el informe P5 |
| Zoom y desplazamiento del plano | Pendiente | El plano se ajusta solo a la vista | Usabilidad P5 en viviendas grandes |
| Temas claro/oscuro (AtlantaFX) | Excluida | — | No ayuda a la decisión; se puede reconsiderar por accesibilidad |
| Atajos de teclado | Parcial | Undo/redo, Escape, flechas y Enter (A-103) | Sin atajos de mapa ni de exportación |
| — | Nueva | Vista 3D de inspección | Comprobar alturas y paredes |

## Dispositivos y radio

| Función Java | Estado | Nueva aplicación / evidencia | Motivo |
|---|---|---|---|
| Sensores y un hub, frecuencia global | Sustituida | Dispositivos con rol, 1–8 radios con frecuencia/canal propios y enlaces explícitos (A-107/A-108) | Varias radios y AP; sin frecuencia global |
| Antena omnidireccional o direccional `cos^k`, polarización | Conservada | Campos en `Radio`; los usa el estimador rápido, igual que Java en 76 sondas (diferencia ≤ 0.0022 dB, [B-121](../simulation/JAVA_PARITY.md)); el adaptador Sionna rechaza direccionales | Falta traducir antenas al motor avanzado (M3) |
| Sensibilidad global del hub | Sustituida | Sensibilidad y potencia por radio; desconocidas se quedan desconocidas | Ambos sentidos con su receptor |
| — | Nueva | Perfiles Wi-Fi genéricos con procedencia por valor: clientes (B-106, `main`) y AP (B-118, en revisión) | Explorar sin producto concreto |
| — | Nueva | Conexión de datos de cada AP y camino hasta la pasarela (B-117, en revisión) | Un AP sin camino de datos no sirve |

## Cálculo

| Función Java | Estado | Nueva aplicación / evidencia | Motivo |
|---|---|---|---|
| Motor multipath (directo, reflexión, difracción, difusa; rayos/ondas) | Sustituida (decisión del 2026-11-08, [ADR-008](ARCHITECTURE.md)) | Estimador directo bidireccional en la API; Sionna RT evaluado en WSL/CPU con 18/18 referencias (B-102), sin integrar | El estimador no equivale a Java multipath: contraste en [B-121](../simulation/JAVA_PARITY.md) (+0.3 a +3.6 dB en viviendas y oficinas en modo rayos, hasta +33 dB en el almacén); Java queda como referencia |
| Tabla empírica de materiales | Conservada como hipótesis | Importada con procedencia; contrastada con losa ITU (B-101); rangos y escenarios (B-108, `main`) | Diferencias documentadas, no se conservan como verdad |
| Fase fija de reflexión (cuarto de ciclo) | Excluida | Fresnel/losa en referencias y Sionna | Error físico documentado en B-101/B-102 |
| Fading Rayleigh/Rician | Excluida | Se tratan desvanecimiento e incertidumbre con media de banda ancha (B-102) y escenarios (B-108) | Estadístico sin validación; no apoya una decisión de compra |
| Heatmap en vivo con leyenda | Sustituida | Mapas por perfil, altura y AP, ambos sentidos, celdas sin calcular explícitas (B-103 + A-104, `main`); peor y mejor caso (B-114, en revisión) | Un mapa debe identificar perfil, altura y configuración |
| Sonda de celda (`CellProbe`) | Sustituida | `points` exactos en los mapas, sin redondeo a la celda (B-103) | P1: coordenada elegida exacta |
| Estadísticas de cobertura (% de área) | Excluida por ahora | — | P3 prioriza ubicaciones importantes frente al área cubierta |
| Métrica SINR (resto de sensores como interferencia) | Excluida | — | Modelo de interferencia no validado y suma energía de emisores independientes |
| BER BPSK y capacidad Shannon en pantalla | Excluida | Fórmulas conservadas en Java | PRODUCT_OBJECTIVE: no son requisito y no relacionan con el uso real |
| Enlaces verde/rojo y tabla potencia/SNR/margen | Sustituida | Ida y vuelta con margen por sentido, «sin verificar» si faltan datos, diagnóstico de paredes (A-106) | Sin semáforo: la reserva de diseño (P2) no está decidida |
| Optimizador del hub (cada metro, máx-mín) | Sustituida | Búsqueda exhaustiva entre lugares permitidos y márgenes bidireccionales (B-105, `main`); comparación manual (A-105); interfaz de búsqueda (A-110), enlace de datos del AP y enchufes y tomas (B-117/B-119) y diferencias exactas (B-123), en revisión | Recomendaciones realizables (P3) |
| Cálculo cancelable en segundo plano | Conservada | Trabajos de mapa con progreso y cancelación (B-103); búsqueda acotada síncrona (B-105); caché por hash de petición (B-110) | Caché solo en memoria, se vacía al reiniciar |
| Animación de rayos y ondas | Excluida | El diagnóstico muestra paredes atravesadas; trayectos de Sionna disponibles para una vista futura | Ilustrativa, no evidencia numérica |
| Ventana de validación de fórmulas | Sustituida | Casos analíticos independientes y pruebas (B-101), evidencia en STATUS | Verificar contra referencias, no contra la misma implementación |
| — | Nueva | Escenarios de puertas y materiales inciertos (B-108, `main`) | P2 |
| Cruces de paredes (`Geometry.segmentsIntersect`, extremos cerrados) | Sustituida | Cruces que no dependen del sentido de dibujo; esquinas, uniones y roces definidos (B-126, en revisión; [geometría](../simulation/GEOMETRY.md)) | Java cuenta dos veces las esquinas; la versión anterior de Python dependía del sentido de dibujo |
| — | Nueva | Formato de campañas de medida y protocolo piloto (B-101) | Calibración y validación (P0/P4) |

## Informe, distribución y pruebas

| Función Java | Estado | Nueva aplicación / evidencia | Motivo |
|---|---|---|---|
| Informe HTML de cobertura | Sustituida en la API (en revisión) | Informe JSON/Markdown por enlace con escenarios, conexión de datos y mapas (B-115, B-117, B-120); falta la descarga en la interfaz (A) | P5: informe por equipo con sentidos, hipótesis y pendientes, sin veredicto |
| Paquetes nativos (jpackage) y releases | Conservada en Java; sustituida en la nueva por una instalación con Python (decisión del 2026-11-08) | `python scripts/start.py` lo prepara y arranca todo; zip con la web compilada (`scripts/package_local.py`) adjunto a las releases (B-128/B-131, en revisión) | M5/P5: distribución local sin herramientas de desarrollo |
| 192 pruebas Java en CI | Conservada | CI Java sigue en Linux/Windows/macOS | Referencia mientras no se superen las puertas |
| — | Nueva | Pruebas Python (438 en la pila B), web (84 en `main`, 120 con #14), contratos sin deriva en CI, paridad con Java (B-121), recorrido E2E en navegador (B-127) y ensayo de integración completo (I-006) | Sustitución verificable |

## Pendiente para cerrar M5 sobre esta matriz

- Motor: decidido el 2026-11-08 ([ADR-008](ARCHITECTURE.md)). La migración se cierra con el estimador
  directo y Sionna RT queda evaluado, no integrado.
- Interfaz (A): descarga del informe con mapas, exportación de imagen, zoom/pan, accesibilidad completa y,
  si aporta, plantillas adicionales; mostrar procedencia, conexión de datos y diferencias.
- Distribución: decidido el 2026-11-08 que basta con Python. `scripts/start.py` lo prepara todo y
  `scripts/package_local.py` incluye la web compilada (B-131). No se hará instalador nativo en la migración.
- Revisar la matriz al cerrar cada fase: un estado «Pendiente» no se convierte en «Excluida» sin motivo.
