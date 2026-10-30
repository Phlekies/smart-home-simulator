# Evaluación técnica del motor avanzado: Sionna RT (B-102)

Versión 1 · 2026-10-30. Adaptador: `services/simulator/src/smart_environment/sionna_adapter.py`.
Evaluador: `services/simulator/benchmarks/sionna_evaluation.py`. Evidencia bruta:
[`evidence/sionna-rt-2.2.0-wsl-cpu.json`](evidence/sionna-rt-2.2.0-wsl-cpu.json).

**Conclusión:** Sionna RT 2.2.0 se ejecuta en CPU dentro de WSL2 y reproduce los 18 casos
analíticos físicos y de coherencia de [B-101](REFERENCE_CASES.md) con |Δ| < 0.001 dB. En
Windows nativo no se ejecuta en este equipo. Es un candidato técnicamente viable para B-103,
pero **no está integrado en la API ni validado con medidas**: la API sigue respondiendo 501
a `engine = "sionna-rt"`, sin fallback.

## Entornos probados

| | Windows 11 nativo | WSL2 Ubuntu 24.04.4 |
|---|---|---|
| CPU / RAM | AMD Ryzen 9 7900X (12 núcleos, 24 hilos, `znver4`), 31.2 GB | Mismo equipo; 24 hilos, 15.2 GB asignados a la VM |
| GPU | AMD Radeon RX 6600: sin backend Dr.Jit (solo CUDA/NVIDIA, Metal y LLVM/CPU) | — |
| Python | 3.13.7, venv aislado `.local/sionna-venv` | 3.12.3, venv aislado `~/.cache/smart-home-simulator/sionna-venv` |
| Paquetes | sionna-rt 2.2.0, mitsuba 3.9.1, drjit 1.5.0 | Mismas versiones; pydantic fijado al lock del proyecto |
| LLVM | 18.1.8 oficial (`LLVM-C.dll` extraído del tarball de GitHub; tamaño publicado verificado; SHA-256 del archivo 22c5907d…82e8) | 20.1.2 de la distribución (`libLLVM-20.so`, instalado con Mesa) |
| Otros | — | `libatomic1` 14.2.0-4ubuntu2~24.04.1 desempaquetado sin sudo |
| Resultado | **No ejecuta.** Sin LLVM: `ImportError … "LLVM-C.dll" could not be found`. Con LLVM 18.1.8: incluso `x * 1.2 + 10` aborta con `JIT session error: Failed to materialize symbols: { (main, { __real@3f99999a, … }) }`. También con objetivo forzado `haswell`/AVX2, así que no depende de AVX-512 | **Ejecuta** con la variante `llvm_ad_mono_polarized` |

El fallo de Windows es del enlazado JIT de LLVM con objetos COFF (constantes `__real@`,
`__ymm@`), no de Sionna. No se probaron otras versiones de LLVM para Windows ni el instalador
oficial: cada intento es una descarga de ~1 GB que requiere autorización.

Reproducir en WSL (desde la raíz del repositorio en Windows):

```powershell
.venv/Scripts/python.exe -m pip download --no-deps --dest .local/wheels-pip pip==25.2
wsl -d Ubuntu -- bash services/simulator/benchmarks/wsl/setup.sh
wsl -d Ubuntu -- bash services/simulator/benchmarks/wsl/run.sh services/simulator/benchmarks/sionna_evaluation.py --output docs/simulation/evidence/sionna-rt-2.2.0-wsl-cpu.json
```

Ningún paso usa `sudo` ni modifica el sistema. Borrar `~/.cache/smart-home-simulator` en WSL
y `.local/` en Windows elimina todo lo instalado para esta evaluación.

## Traducción del proyecto

- Cada pared es **una sola superficie** vertical en su plano medio; el espesor pasa al material
  ITU como losa. Es el modelo que documenta Sionna (`RadioMaterial`: «objects like walls are
  modeled as single flat surfaces»). Modelarla como caja contaría la losa dos veces.
- Materiales: los casos dan su tipo ITU. Para proyectos importados se infiere desde el id Java
  (`drywall`→`plasterboard`, `metal-door`→`metal`, …) y se informa como inferencia. Un material
  sin correspondencia es un error; no hay material por defecto.
- Antenas isotrópicas con polarización vertical; las ganancias en dBi se suman. Patrones
  direccionales, polarizaciones distintas o radios sin potencia se rechazan con motivo.
- Sionna incluye su tabla ITU-R P.2040 con los mismos coeficientes que B-101 (ladrillo con
  rango 1–40 GHz frente a 1–10 GHz en la reproducción de MathWorks; irrelevante a 2.4 GHz).

### Convención de fase verificada

`paths.a` **no incluye** la fase de la portadora debida a la longitud del trayecto; se aplica con
`tau`: `H(f) = Σ aᵢ·e^{−j2πfτᵢ}`. Verificado en `REFL-grazing`: arg(a) del directo = 0; arg y
módulo del reflejado = fase (3.1171 rad) y |R_TE| (0.833) de la losa de referencia. Una primera
versión del adaptador sumaba `a` sin esa fase y daba 19 dB de error en ese caso.

El adaptador publica tres potencias: coherente a la portadora, media de banda ancha en los
20 MHz del canal (64 frecuencias; lo que promedia un receptor OFDM) e incoherente (suma de
potencias). La comparación con las referencias usa la coherente.

## Resultados frente a las referencias

| Grupo | Casos | Resultado |
|---|---|---|
| Espacio libre (1–30 m, canal 11, 3D) | 6 | Coinciden, |Δ| < 0.001 dB |
| Pared ITU (6 materiales, normal y 60°) | 7 | Coinciden: Sionna aplica la misma losa de P.2040 |
| Coherencia (pérdida de losa como parámetro, dos paredes) | 2 | Coinciden |
| Reflexión especular (rasante, casi normal, fuera de pared) | 3 | Coinciden, incluida la fase coherente |
| Log-distance n = 3 | 1 | `not-modelled`: Sionna no usa un exponente empírico |

Cobertura de interacciones: trayecto directo, refracción por losa y reflexión especular
verificadas con referencias. Difracción en aristas y reflexión difusa existen en Sionna pero
**no tienen caso de referencia**: sus resultados abajo son indicativos.

## Ejemplos Java y coste

Ejecución única del 2026-10-30 08:31 UTC, caché de núcleos de Dr.Jit ya caliente, `max_depth = 3`.
No son estadísticas de rendimiento: sirven para dimensionar B-103.

| Medida | Resultado |
|---|---|
| Importar Sionna | 1.12 s |
| Caso de referencia (escena nueva) | mediana 24 ms, máximo 78 ms |
| Enlace de un ejemplo (11–21 paredes) | mediana 35–48 ms; con difracción 68–85 ms |
| Rejilla de 5307 receptores a 0.5 m, 1.2 m de altura (apartamento) | 11.7 s; 550 puntos sin trayecto (ver profundidad); ejecución previa con caché fría: 21.8 s |
| Mapa planar `RadioMapSolver`, celdas de 0.25 m (21 525 celdas) | 0.02 s / 0.05 s / 0.41 s con 10⁶ / 10⁷ / 10⁸ rayos; celdas sin rayos: 81 % / 49 % / 18 % |
| Pico de memoria del proceso | 703 MB |

Potencia recibida de los ejemplos, dBm (materiales inferidos, sin calibrar):

| Ejemplo | Enlace | Rápido | Coherente | Banda ancha | Incoherente | Banda ancha con difracción | Trayectos |
|---|---|---:|---:|---:|---:|---:|---|
| apartamento | S1 | -59.3 | -55.5 | -56.7 | -57.5 | -56.8 | 23 / 132 |
| apartamento | S2 | -69.9 | -70.4 | -68.9 | -65.0 | -67.6 | 12 / 101 |
| apartamento | S3 | -78.8 | -88.2 | -85.9 | -70.0 | -81.4 | 5 / 55 |
| apartamento | S4 | -71.3 | -72.3 | -73.6 | -65.9 | -74.7 | 14 / 105 |
| apartamento | S5 | -72.7 | -63.0 | -63.3 | -66.7 | -66.9 | 9 / 88 |
| apartamento | S6 | -70.9 | — | — | — | — | antena direccional: rechazada |
| oficina | S1 | -62.8 | -65.5 | -62.8 | -60.8 | -62.8 | 23 / 161 |
| oficina | S2 | -61.2 | -63.0 | -59.6 | -59.4 | -59.4 | 23 / 173 |
| oficina | S3 | -73.0 | -73.3 | -70.9 | -69.9 | -70.0 | 5 / 55 |
| oficina | S4 | -71.1 | -65.1 | -66.4 | -67.7 | -66.9 | 3 / 42 |
| oficina | S5 | -72.7 | -75.6 | -72.7 | -70.0 | -71.2 | 4 / 50 |
| oficina | S6 | -62.3 | -62.8 | -60.1 | -58.2 | -60.5 | 14 / 133 |
| oficina | S7 | -68.4 | -61.6 | -61.8 | -65.0 | -62.2 | 20 / 142 |
| almacén | S1 | -82.8 | -70.9 | -70.9 | -73.4 | -70.1 | 2 / 51 |
| almacén | S2 | -113.4 | — | — | — | -95.8 | 0 / 3 |
| almacén | S3 | -132.0 | — | — | — | -105.0 | 0 / 3 |
| almacén | S4 | -152.8 | — | — | — | -141.1 | 0 / 1 |
| almacén | S5 | -103.8 | -71.4 | -72.5 | -70.2 | -69.9 | 4 / 40 |

«Trayectos» = sin / con difracción. Estas cifras comparan modelos entre sí; ninguna es una medida.

## Hallazgos que condicionan B-103

1. **Desvanecimiento.** El valor coherente en un punto puede caer más de 15 dB respecto a la
   suma incoherente (apartamento S3: −88.2 frente a −70.0 dBm). La media de banda ancha reduce
   parte de ese efecto (−85.9). Un mapa debe declarar qué métrica muestra; un punto exacto no
   debe clasificarse con un único valor de portadora sin indicar esa sensibilidad.
2. **Profundidad.** Cada pared atravesada consume una interacción de `max_depth`. En el almacén,
   S2 (4 paredes) no tiene trayecto con 3, da −107.3 dBm con 5 y −80.5 dBm con 8. S3 aparece con
   8 (−82.0) y S4 sigue sin trayecto. Por tanto, «sin trayectos» no es «sin señal», y un resultado
   solo se presenta si es estable al aumentar la profundidad o queda marcado como no convergido.
3. **Metal.** `metal-door` como metal ITU es opaco. Las cifras Java (18 dB) representan holguras y
   marcos que una losa no modela. Hace falta una decisión de modelado (abertura, losa equivalente
   calibrada o «sin datos»), no un valor inventado.
4. **Mapa planar.** Sin suelo ni techo, solo los rayos que cruzan el plano lo alimentan: muchas
   celdas quedan vacías y el resultado depende del número de rayos. La rejilla de receptores
   puntuales calcula trayectos por punto, pero tardó 11.7 s con 5307 puntos frente a 0.41 s del
   mapa de 21 525 celdas con 10⁸ rayos.
5. **Rendimiento.** Una vivienda pequeña cabe en segundos en CPU; mapas finos o barridos de
   profundidad necesitan trabajo asíncrono, progreso, cancelación y límites antes de llegar a la UI.
6. **Contrato.** `Material` solo tiene dB. Un motor físico necesita tipo ITU o (ε′, σ) por material,
   y `DirectionResult` exige `wall_loss_db`/`crossed_wall_ids`, que un trazador no descompone.

## Lo que esta evaluación no demuestra

- Precisión en viviendas: no hay medidas. Coincidir con referencias idealizadas solo verifica
  la implementación de esas interacciones.
- Difracción, dispersión difusa, suelo/techo, antenas reales y 5 GHz no se han verificado.
- Ejecución en Windows nativo o en GPU: no disponible en este equipo.
- Determinismo: el muestreo de rayos depende de la semilla; la rejilla dio 550 y 560 puntos sin
  trayecto en dos ejecuciones.
