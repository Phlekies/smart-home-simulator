# Geometría de cruces de paredes (B-126)

Versión 1 · 2026-11-03. Código: `crossing_parameter` y `crossed_walls` en `engines.py`. Pruebas:
`services/simulator/tests/test_geometry_cases.py` (47 casos) y `test_geometry_scope.py` (B-122).

## Reglas

| Situación | Regla |
|---|---|
| Pared | Segmento central vertical entre `start` y `end`, desde su base `z` hasta `z + height_m`. El grosor solo cuenta en la pérdida por centímetro y al detectar equipos empotrados |
| Cruce normal | El trayecto corta el segmento central entre sus extremos. Cuenta una vez |
| Altura | Se comprueba la altura del trayecto **en el punto de cruce**: incluye el borde superior y deja fuera lo que pasa por encima o por debajo. Funciona igual con trayectos inclinados y con paredes cuya base no está en el suelo |
| Rasante | Un trayecto que corre a lo largo de una pared o paralelo a ella no la cruza |
| Extremo del trayecto sobre una pared | No es un cruce. El equipo queda «dentro de la pared» y su enlace nunca es favorable (B-122) |
| Paso exacto por extremos de pared | Las paredes que terminan en ese punto se reparten según el lado del trayecto en que quedan, y cuenta solo el lado con menos paredes, como si el trayecto se desplazase un poco hacia el lado más abierto. Si empatan, cuenta el lado con más pérdida y después el de la pared que va antes en el proyecto, así que ida y vuelta coinciden |

Consecuencias de la última regla:

| Caso | Paredes contadas |
|---|---|
| Salir por la esquina de una L | 1 |
| Rozar la esquina exterior de una L | 0 |
| Pared recta dibujada en dos tramos, cruzada por la unión | 1 |
| Cruce en X de cuatro paredes, en diagonal | 2 |
| Unión en T | 1 (la pared pasante) |
| Rozar el extremo libre de una pared | 0 |

## Error corregido

Hasta B-125, los extremos de pared seguían un convenio semiabierto: el inicio contaba y el final no.
Por eso el resultado dependía del **sentido en que se dibujó cada pared**, algo que la interfaz no
muestra. La misma esquina en L costaba 0, 10 o 20 dB (material de 10 dB), y el extremo libre de una
pared 0 o 10 dB. Las celdas de los mapas y los lugares de búsqueda en posiciones regulares pasan a
menudo por esos puntos. Con la regla nueva el resultado ya no depende del dibujo, y los tres ejemplos
Java no cambian: la regresión de paridad (B-121) sigue dentro de 1e-9 dB.

## Escalas y tolerancias

- Paralelismo: determinante absoluto < 1e-10 m². Extremos del trayecto: 1e-9 en parámetro.
  Extremos de pared: 1e-9 de su longitud. Agrupación de extremos: coordenadas redondeadas a 1 µm.
- Desplazar todo el plano hasta ±9990 m no cambia las paredes cruzadas, y la potencia varía menos
  de 1e-6 dB. Una pared de 1.4 cm se sigue detectando.
- Rendimiento: un mapa de 29 415 celdas del almacén, con 617 715 evaluaciones celda×pared, tarda
  0.83 s (unas 740 000 por segundo; Windows, Python 3.13.7).

## Lo que no modela

Forjados ni varias plantas (B-122 los declara fuera del modelo), paredes curvas o inclinadas, huecos
dentro de una pared salvo puertas modeladas como paredes propias, y la difracción en las esquinas.
Esta última aparece en el contraste multipath de [B-121](JAVA_PARITY.md).
