# Informe de instalación por enlace (B-115, B-117, B-120)

Versión 2 · 2026-11-01. Modelos: `ReportRequest` e `InstallationReport` en `report.py`.
Esquema: `contracts/installation-report.schema.json`. Tipos TS: `apps/web/src/generated/installation-report.ts`.

## Qué es

El documento que una persona guarda para planificar la instalación (P5). Reúne lo que la API ya
calcula, sin física nueva:

- **Por enlace:** los dos equipos y sus radios, la compatibilidad de radio y el estado del cálculo.
- **Por sentido:** potencia, margen, procedencia de la sensibilidad del receptor y paredes
  atravesadas, con material y estado de puerta.
- **Sentido limitante** (solo si hay margen en ambos sentidos), rango de escenarios de
  [B-108](SCENARIOS_CONTRACT.md), `margin_sign`, hipótesis que le afectan y notas de datos ausentes.
- **Global:** recuentos, alcance, limitaciones del motor, lo que no se evalúa (tráfico, interferencia,
  compatibilidad funcional, multipath) y las decisiones pendientes.

**No emite veredicto de cobertura ni recomienda compras**: el criterio activo de fallo y la reserva de
diseño no están decididos, y el informe lo dice en «Decisiones pendientes».

## Endpoints (aditivos)

| Ruta | Respuesta |
|---|---|
| `POST /api/reports` con `{ project, scenarios?, title?, maps? }` | `InstallationReport` (JSON) |
| `POST /api/reports/markdown` con el mismo cuerpo | Documento `text/markdown` listo para descargar |

Los escenarios con nombre se validan igual que en `/api/scenario-simulations` (422 si son inválidos).
El informe lleva la huella del proyecto (`input_hash`) y la versión del motor para que sea reproducible.
En Markdown, los nombres se escapan para no romper las tablas, los estados se traducen al castellano y
cada sentido limitante va acompañado de «un margen positivo no garantiza el funcionamiento».

## Secciones aditivas (B-117, B-120)

- **`access_points`:** camino de datos de cada router o AP, igual que en la simulación
  ([conexión de datos](DATA_CONNECTION_CONTRACT.md)). En Markdown es la tabla «Conexión de datos de los AP».
- **`maps`:** hasta 4 mapas pedidos con los mismos parámetros que `/api/coverage-maps` (perfil,
  altura, rejilla, puntos exactos y escenario). Se calculan de forma síncrona y entre todos comparten
  el límite de un mapa: 2 000 000 evaluaciones celda×pared (422 si se supera, con motor no
  implementado o con datos inválidos). Cada `ReportMap` contiene:
  - el **resultado completo** (`CoverageMapResult`, con `input_hash` y `request_hash`), para que el
    archivo del informe conserve el mapa y la interfaz lo dibuje o detecte que está obsoleto;
  - un **resumen**: celdas calculadas, parciales y sin calcular; mínimo, mediana y máximo del margen
    limitante; y recuento de celdas con margen negativo.

  El resumen **no es un porcentaje de cobertura**: no hay criterio de fallo ni reserva de diseño.
  En Markdown, cada mapa lleva sus recuentos, sus notas y una tabla con los puntos exactos.

## Trabajo del consumidor (A)

1. Añadir `installation-report.ts` al script `contracts` de la web.
2. Ofrecer «Descargar informe» (Markdown) y, si se quiere, una vista del JSON en la interfaz.
   No añadir semáforos ni porcentajes que el informe no contiene.
3. Opcional (B-120): pedir los mapas visibles al generar el informe y dibujarlos a partir de
   `maps[].result` en la versión descargada.

## Nivel de evidencia (B-135)

`evidence_levels` separa tres cosas que no deben confundirse:
- **Consistencia matemática** (comprobada): casos analíticos, reglas de cruce y paridad con Java.
- **Calibración con medidas** (ninguna todavía).
- **Validación en viviendas** (ninguna todavía).

En Markdown es la tabla «Nivel de evidencia». Cuando haya medidas, estos estados cambiarán con su
evidencia; nunca se dan por supuestos.

## Informe guardado (B-132)

El JSON del informe lleva `input_hash` y `engine_version`, también en cada mapa. Al reabrirlo,
`POST /api/projects/fingerprint` dice si sigue describiendo el proyecto actual.

## Límites

- Trayecto directo del estimador rápido; cifras sin calibración experimental.
- Los mapas van como datos; la imagen la dibuja la interfaz. Las búsquedas de ubicación no se adjuntan.
- No es un PDF ni un HTML maquetado: el formato de presentación lo decide la interfaz.
