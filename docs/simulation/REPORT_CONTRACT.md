# Informe de instalación por enlace (B-115)

Versión 1 · 2026-10-30. Modelos: `ReportRequest` e `InstallationReport` en `report.py`.
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
| `POST /api/reports` con `{ project, scenarios?, title? }` | `InstallationReport` (JSON) |
| `POST /api/reports/markdown` con el mismo cuerpo | Documento `text/markdown` listo para descargar |

Los escenarios con nombre se validan igual que en `/api/scenario-simulations` (422 si son inválidos).
El informe lleva la huella del proyecto (`input_hash`) y la versión del motor para que sea reproducible.
En Markdown, los nombres se escapan para no romper las tablas, los estados se traducen al castellano y
cada sentido limitante va acompañado de «un margen positivo no garantiza el funcionamiento».

## Trabajo del consumidor (A)

1. Añadir `installation-report.ts` al script `contracts` de la web.
2. Ofrecer «Descargar informe» (Markdown) y, si se quiere, una vista del JSON en la interfaz.
   No añadir semáforos ni porcentajes que el informe no contiene.

## Límites

- Trayecto directo del estimador rápido; cifras sin calibración experimental.
- No incluye mapas ni búsquedas de ubicación: se pueden adjuntar más adelante como secciones aditivas.
- No es un PDF ni un HTML maquetado: el formato de presentación lo decide la interfaz.
