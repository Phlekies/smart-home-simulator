# Casos analíticos de referencia (B-101)

Versión 1 · 2026-10-30. Código: `services/simulator/src/smart_environment/references.py`.
Pruebas: `services/simulator/tests/test_references.py`.

Estos casos sirven para contrastar un motor con expresiones cerradas antes de usar
medidas. **No son medidas ni acreditan precisión en viviendas.** Distinguen tres evidencias
que el proyecto mantiene separadas:

| Tipo de caso | Qué comprueba | Qué no comprueba |
|---|---|---|
| `physical-reference` | Que el motor reproduce física idealizada (Friis, losa homogénea, reflexión de Fresnel) | Que una pared real se comporte como una losa homogénea infinita |
| `model-consistency` | Que el motor calcula correctamente su propio modelo cuando recibe el parámetro de referencia | Que el parámetro sea correcto para una vivienda |
| Validación con medidas | Error frente a la realidad (piloto/calibración/validación, ver [protocolo](PILOT_PROTOCOL.md)) | — no la cubren estos casos |

## Ejecutar

```powershell
.venv/Scripts/python.exe -m smart_environment.references          # tabla Markdown
.venv/Scripts/python.exe -m smart_environment.references --json   # resultados y componentes
```

`compare(cases, run, modelled)` acepta cualquier motor `Project → SimulationResult` y la
lista de interacciones que declara modelar. El estimador rápido publica la suya en
`/api/engines` (`interactions`: `free-space`, `log-distance`, `wall-penetration`).
B-102 debe conectar aquí el adaptador candidato, sin modificar las referencias.

## Expresiones y fuentes

- **Espacio libre:** `L = 20·log10(4πd/λ)` (Friis, ITU-R P.525), antenas isotrópicas.
  Solo campo lejano; los casos usan d ≥ 1 m (≈ 8 λ a 2.412 GHz).
- **Log-distance:** `PL = FSPL(1 m) + 10·n·log10(d)`. Es un modelo empírico de ajuste; el
  caso solo comprueba coherencia de implementación, no la validez de un exponente.
- **Materiales:** permitividad compleja `η = a·f^b − j·c·f^d / (2π f ε0)` con f en GHz en
  los coeficientes y ε0 de CODATA 2022. Coeficientes de la tabla 3 de ITU-R P.2040-3.
  Rango de frecuencias aplicado de forma estricta: fuera de rango se rechaza el cálculo.
- **Interfaz:** Fresnel TE `Γ = (cosθ − √(η − sin²θ)) / (cosθ + √(η − sin²θ))`; TM con la
  forma ponderada por η (Γ_TM = −Γ_TE en incidencia normal).
- **Losa homogénea:** `q = (2πd/λ)·√(η − sin²θ)`, `T = (1 − Γ²)e^{−jq} / (1 − Γ²e^{−2jq})`,
  `R = Γ(1 − e^{−2jq}) / (1 − Γ²e^{−2jq})`. Solo se usan |T| y |R|.
- **Reflexión especular:** método de imágenes sobre el plano vertical de la pared, con
  comprobación de que el punto especular cae dentro del segmento y de su altura.
  Referencia coherente `|e^{−jkd₁}/d₁ + R_TE·e^{−jkd₂}/d₂|²`, con R de la losa del espesor de
  la pared (0.20 m); también se publican la componente directa, la reflejada y la suma incoherente.
  (Revisado en B-102: la primera versión usaba Γ de una interfaz semiinfinita, 0.05 dB menor.)

Las fórmulas se comprueban con identidades que no reutilizan la implementación:
conservación de energía en losa sin pérdidas (TE/TM, varios ángulos y espesores), losa
de espesor nulo y de media onda transparentes, ángulo de Brewster, incidencia rasante,
pendiente de una losa gruesa igual a la atenuación del medio, forma clásica en MHz/km de
Friis y forma `17.98·σ/f` de ITU para la parte imaginaria.

### Procedencia de la tabla de materiales

| Material | a | b | c | d | Rango (GHz) |
|---|---:|---:|---:|---:|---|
| Hormigón | 5.24 | 0 | 0.0462 | 0.7822 | 1–100 |
| Ladrillo | 3.91 | 0 | 0.0238 | 0.16 | 1–10 |
| Placa de yeso | 2.73 | 0 | 0.0085 | 0.9395 | 1–100 |
| Madera | 1.99 | 0 | 0.0047 | 1.0718 | 0.001–100 |
| Vidrio | 6.31 | 0 | 0.0036 | 1.3394 | 0.1–100 |

El código incluye además placa de techo, aglomerado, contrachapado, mármol, tarima (solo
50–100 GHz, por tanto inutilizable a 2.4 GHz) y metal. Verificación del 2026-10-30: el PDF
de ITU-R P.2040-3 en itu.int devolvió 404; los valores se contrastaron con la reproducción
de esa tabla en la documentación de MathWorks `buildingMaterialPermittivity` (indica
P.2040-3, agosto de 2023). **Pendiente:** cotejar con el PDF oficial o con P.2040-4
(09/2025) antes de usarlos como parámetros de un motor validado.

## Resultado actual del estimador rápido

Salida real del comando anterior el 2026-10-30 (filas REFL regeneradas en `agent-b/b-102-sionna-evaluation`).
Frecuencia 2.412 GHz, 20 dBm, antenas de 0 dBi, enlace a 1.2 m de altura salvo `FS-3D`.

| Caso | Tipo | Referencia (dBm) | Motor (dBm) | Δ (dB) | Veredicto | Nota |
|---|---|---:|---:|---:|---|---|
| FS-1m | physical-reference | -20.095 | -20.095 | +0.000 | agrees |  |
| FS-5m | physical-reference | -34.075 | -34.075 | +0.000 | agrees |  |
| FS-10m | physical-reference | -40.095 | -40.095 | +0.000 | agrees |  |
| FS-30m | physical-reference | -49.638 | -49.638 | -0.000 | agrees |  |
| FS-ch11 | physical-reference | -40.274 | -40.274 | +0.000 | agrees |  |
| FS-3D | physical-reference | -36.206 | -36.206 | -0.000 | agrees |  |
| LD-n3 | model-consistency | -50.095 | -50.095 | +0.000 | agrees |  |
| WALL-concrete-100mm | physical-reference | -48.184 | -52.095 | -3.911 | deviates |  |
| WALL-concrete-200mm | physical-reference | -54.727 | -54.095 | +0.632 | deviates |  |
| WALL-brick-100mm | physical-reference | -43.175 | -47.095 | -3.920 | deviates |  |
| WALL-drywall-12.5mm | physical-reference | -41.172 | -43.095 | -1.923 | deviates |  |
| WALL-glass-6mm | physical-reference | -42.013 | -42.095 | -0.082 | deviates |  |
| WALL-wood-40mm | physical-reference | -40.708 | -43.295 | -2.587 | deviates |  |
| WALL-concrete-100mm-60deg | physical-reference | -51.963 | -52.095 | -0.132 | deviates |  |
| WALL-fit-single | model-consistency | -54.727 | -54.727 | +0.000 | agrees |  |
| WALL-fit-series | model-consistency | -55.804 | -55.804 | +0.000 | agrees |  |
| REFL-grazing | physical-reference | -35.316 | -40.095 | -4.779 | not-modelled | coincide con direct_only_dbm |
| REFL-steep | physical-reference | -26.393 | -26.116 | +0.277 | not-modelled | coincide con direct_only_dbm |
| REFL-miss | physical-reference | -40.095 | -40.095 | +0.000 | agrees | interacción no modelada: coincidencia trivial |

Tolerancia de coincidencia: 0.01 dB. Es una tolerancia numérica para el mismo modelo
(motores en float32), **no un objetivo de precisión**; los objetivos se fijan con el piloto.

### Interpretación

- Espacio libre, altura 3D y log-distance coinciden: la implementación del trayecto
  directo es coherente con sus fórmulas.
- Con la pérdida de losa como parámetro del material (`WALL-fit-*`) el cruce y la suma
  de paredes coinciden. Las desviaciones de `WALL-*` se deben a la tabla empírica heredada
  de Java (p. ej. ladrillo 10 cm: 7 dB frente a 3.08 dB de la losa ITU; madera 4 cm: 3.2
  frente a 0.61 dB). Ninguna de las dos cifras es una medida: indican cuánto depende el
  resultado de la hipótesis de material y por qué P2 debe tratarlo como incertidumbre.
- El estimador ignora el ángulo de incidencia (`60deg`: la losa ITU pasa de 8.09 a 11.87 dB).
- Reflexión: el estimador devuelve exactamente la componente directa. Junto a una pared
  la suma coherente cambia el resultado entre −4.8 y +0.3 dB en estos dos ejemplos y varía
  con desplazamientos de centímetros; un mapa futuro debe declarar si promedia ese efecto.
- Java modela la reflexión con pérdidas empíricas (`reflectionBiasDb`) y un desfase fijo de
  un cuarto de ciclo; Fresnel da Γ ≈ −0.39 (fase ≈ π) en incidencia normal sobre hormigón.
  Ese desfase no se conserva como requisito de la migración.
- Sionna RT 2.2.0 reproduce los 18 casos físicos y de coherencia con |Δ| < 0.001 dB: ver
  [evaluación del motor avanzado](ADVANCED_ENGINE_EVALUATION.md).

## Limitaciones y trabajo pendiente

- Solo polarización vertical frente a paredes verticales con rayo horizontal (TE pura).
  Sin forjados, suelo, techo, difracción en esquinas, dispersión difusa ni antenas reales.
- La losa es homogénea e infinita; tabiques con cámara de aire, montantes, armaduras,
  humedad, puertas metálicas con holguras y marcos no se representan (metal se rechaza).
- `Material` del contrato solo tiene pérdidas en dB. Un motor físico (Sionna RT) necesita
  permitividad/conductividad o un identificador ITU: `itu_materials` de cada caso hace esa
  correspondencia de forma provisional. Ampliar `Project` es una propuesta de contrato
  para B-102/B-103 que debe describirse y coordinarse con A antes de implementarla.
- Casos a 5 GHz, varias plantas y más rebotes requieren su propia aceptación.
