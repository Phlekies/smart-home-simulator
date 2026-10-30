# Contrato de la referencia de plano (B-104, respuesta a A-102)

Versión 1 · 2026-10-30. Modelo canónico: `PlanReference` en
`services/simulator/src/smart_environment/models.py`. Tipos generados en
`apps/web/src/generated/project.ts` (`PlanReference`, `PlanReferenceCalibration`, `PixelPoint`).

## Decisión

| Pregunta de A-102 | Decisión |
|---|---|
| ¿Dónde vive la imagen? | Archivo local del usuario. **No** se incrusta en el JSON: el límite de importación es 2 MB y la imagen no es una entrada de cálculo |
| ¿Qué viaja en el proyecto? | `Project.plan_reference`: nombre, tipo MIME, SHA-256 de los bytes, píxeles, metros por píxel, origen y la calibración opcional |
| ¿Compatibilidad v1? | Campo **opcional y aditivo**, versión 1 sin cambios. Los proyectos existentes validan igual y el tipo TS es `plan_reference?: PlanReference \| null` |
| ¿Afecta al cálculo o al hash? | No. `input_hash` excluye `plan_reference`: añadir o mover la imagen no cambia el hash ni invalida resultados físicos |
| ¿Opacidad y visibilidad? | Preferencias de vista, fuera del contrato; A puede conservarlas en la sesión o en almacenamiento local |

Transformación: el píxel (u, v), con u hacia la derecha y v hacia abajo desde la esquina superior
izquierda, va a `x = origin_x_m + u·meters_per_pixel` e `y = origin_y_m + v·meters_per_pixel`, la
misma convención que `referenceBounds()` del editor (eje Y del plano hacia abajo). Sin rotación en v1.

## Validaciones del productor

- `sha256` en hexadecimal en minúsculas (64 caracteres); `media_type` PNG, JPEG o WebP.
- 1–16 384 px por lado y como máximo 16 millones de píxeles, como en el editor.
- La imagen colocada mide al menos 0.01 m por eje y queda dentro de ±10 000 m.
- Si hay `calibration`: puntos dentro de la imagen y separados al menos 2 px, distancia de
  0.01–20 000 m, y `meters_per_pixel` igual a `distance_m / hypot(b − a)` (tolerancia relativa 1e-9).
- Campos desconocidos (p. ej. `opacity` o bytes de la imagen) se rechazan, como en todo el contrato.

## Trabajo del consumidor (A)

1. Al calibrar, calcular el SHA-256 localmente (`crypto.subtle.digest`) y rellenar `plan_reference`.
   La imagen nunca se envía a la API ni a terceros.
2. Exportar y recuperar `plan_reference` con el proyecto (A-101/A-102).
3. Al abrir un proyecto con referencia, pedir al usuario el archivo de imagen y comparar su huella.
   Si falta o no coincide, mostrar la referencia como «imagen no disponible», sin bloquear la vivienda.
4. Al cambiar de proyecto, la referencia es la del proyecto nuevo (o ninguna).
5. Integrar después de que estos tipos lleguen a la rama de trabajo de A. No editar los tipos generados.

Compatibilidad comprobada el 2026-10-30: una copia del código en curso de A (checkout compartido,
sin modificarlo) compila con `tsc --noEmit` usando estos tipos y sus 57 pruebas del editor pasan.

## Limitaciones

- Un archivo exportado con `plan_reference` no se abre en versiones anteriores a este contrato,
  porque el contrato rechaza campos desconocidos. Los archivos sin el campo siguen siendo legibles.
- La escala es una calibración del usuario, no un levantamiento topográfico: `evidence` lo declara.
- Varias plantas o imágenes rotadas necesitarán ampliar el contrato.
