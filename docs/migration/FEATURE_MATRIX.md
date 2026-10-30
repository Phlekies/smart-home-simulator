# Matriz de funciones Java: conservadas, sustituidas y excluidas (B-107)

Versión 1 · 2026-10-30. Base Java: `eff803c` (v1.0.0; README, paquetes `ui`, `app`, `simulation`,
`model`, `physics`). Estado de la nueva aplicación: `main` en `046ee82` más PR #8 (B-105/B-106) y
PR #9 (B-108) en revisión. Criterio: [ROADMAP](ROADMAP.md) («Criterio para omitir o retirar
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
| Antena omnidireccional o direccional `cos^k`, polarización | Conservada | Campos en `Radio`; los usa el estimador rápido; el adaptador Sionna rechaza direccionales | Falta traducir antenas al motor avanzado (M3) |
| Sensibilidad global del hub | Sustituida | Sensibilidad y potencia por radio; desconocidas se quedan desconocidas | Ambos sentidos con su receptor |
| — | Nueva | Perfiles Wi-Fi genéricos con procedencia por valor (B-106, PR #8) | Explorar sin producto concreto |

## Cálculo

| Función Java | Estado | Nueva aplicación / evidencia | Motivo |
|---|---|---|---|
| Motor multipath (directo, reflexión, difracción, difusa; rayos/ondas) | Sustituida (en curso) | Estimador directo bidireccional en la API; Sionna RT evaluado en WSL/CPU con 18/18 referencias (B-102), sin integrar | El estimador no equivale a Java multipath; Java queda como referencia |
| Tabla empírica de materiales | Conservada como hipótesis | Importada con procedencia; contrastada con losa ITU (B-101); rangos y escenarios (B-108, PR #9) | Diferencias documentadas, no se conservan como verdad |
| Fase fija de reflexión (cuarto de ciclo) | Excluida | Fresnel/losa en referencias y Sionna | Error físico documentado en B-101/B-102 |
| Fading Rayleigh/Rician | Excluida | Se tratan desvanecimiento e incertidumbre con media de banda ancha (B-102) y escenarios (B-108) | Estadístico sin validación; no apoya una decisión de compra |
| Heatmap en vivo con leyenda | Sustituida (en curso) | Mapas por perfil, altura y AP, ambos sentidos, celdas sin calcular explícitas (B-103 API); interfaz A-104 en curso | Un mapa debe identificar perfil, altura y configuración |
| Sonda de celda (`CellProbe`) | Sustituida | `points` exactos en los mapas, sin redondeo a la celda (B-103) | P1: coordenada elegida exacta |
| Estadísticas de cobertura (% de área) | Excluida por ahora | — | P3 prioriza ubicaciones importantes frente al área cubierta |
| Métrica SINR (resto de sensores como interferencia) | Excluida | — | Modelo de interferencia no validado y suma energía de emisores independientes |
| BER BPSK y capacidad Shannon en pantalla | Excluida | Fórmulas conservadas en Java | PRODUCT_OBJECTIVE: no son requisito y no relacionan con el uso real |
| Enlaces verde/rojo y tabla potencia/SNR/margen | Sustituida | Ida y vuelta con margen por sentido, «sin verificar» si faltan datos, diagnóstico de paredes (A-106) | Sin semáforo: la reserva de diseño (P2) no está decidida |
| Optimizador del hub (cada metro, máx-mín) | Sustituida | Búsqueda exhaustiva entre lugares permitidos y márgenes bidireccionales (B-105, PR #8); comparación manual (A-105) | Recomendaciones realizables (P3) |
| Cálculo cancelable en segundo plano | Conservada | Trabajos de mapa con progreso y cancelación (B-103); búsqueda acotada síncrona (B-105) | Sin caché todavía |
| Animación de rayos y ondas | Excluida | El diagnóstico muestra paredes atravesadas; trayectos de Sionna disponibles para una vista futura | Ilustrativa, no evidencia numérica |
| Ventana de validación de fórmulas | Sustituida | Casos analíticos independientes y pruebas (B-101), evidencia en STATUS | Verificar contra referencias, no contra la misma implementación |
| — | Nueva | Escenarios de puertas y materiales inciertos (B-108, PR #9) | P2 |
| — | Nueva | Formato de campañas de medida y protocolo piloto (B-101) | Calibración y validación (P0/P4) |

## Informe, distribución y pruebas

| Función Java | Estado | Nueva aplicación / evidencia | Motivo |
|---|---|---|---|
| Informe HTML de cobertura | Pendiente | — | P5: informe por equipo con decisión, sentidos, hipótesis y pendientes |
| Paquetes nativos (jpackage) y releases | Conservada en Java; pendiente en la nueva | Arranque local con `scripts/dev.py` | M5/P5: distribución local sin herramientas de desarrollo |
| 192 pruebas Java en CI | Conservada | CI Java sigue en Linux/Windows/macOS | Referencia mientras no se superen las puertas |
| — | Nueva | Pruebas Python (199 en la pila de PR) y web (70) con contratos sin deriva en CI | Sustitución verificable |

## Pendiente para cerrar M5 sobre esta matriz

- Integrar y verificar el motor avanzado o declarar el alcance del estimador directo como definitivo.
- Informe (P5), exportación de imagen, zoom/pan y, si aporta, plantillas adicionales.
- Revisar la matriz al cerrar cada fase: un estado «Pendiente» no se convierte en «Excluida» sin motivo.
