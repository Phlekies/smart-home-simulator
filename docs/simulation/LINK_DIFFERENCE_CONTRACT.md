# Diferencia exacta entre dos versiones del proyecto (B-123)

Versión 1 · 2026-11-01. Modelos y cálculo: `differences.py`. Pruebas: `test_link_differences.py`.
Esquema: `contracts/link-difference.schema.json`. Tipos TS: `apps/web/src/generated/link-difference.ts`.

## Qué responde

«Si muevo este equipo, cambio su altura, giro la antena o cambio la radio, ¿cuánto cambia cada
sentido y por qué, según el modelo?». Corresponde a dos criterios de producto:
- mover un AP, un equipo o su altura ofrece la diferencia de señal y de margen limitante;
- la explicación identifica mejoras y riesgos residuales sin atribuciones causales falsas.

## Endpoint (aditivo)

`POST /api/link-differences` con `{ base, alternative, engine? }`, dos proyectos completos. La
respuesta es **200** `DifferenceResult`. Responde 422 si las versiones no comparten ningún enlace y
501 para un motor no implementado (sin fallback). Es síncrono: dos simulaciones de los enlaces
comunes.

## Semántica

- **Enlaces comparados:** los que tienen el mismo `id` y los mismos extremos (equipo y radio) en
  ambas versiones. Los demás aparecen en `unmatched_link_ids`.
- **Por sentido** (`forward` es origen→destino del enlace y `reverse` lo contrario): potencia y margen
  en la base y en la alternativa, y el cambio.
- **`terms`:** contribución de cada término del presupuesto a la potencia recibida, en dB, con las
  pérdidas en negativo. Los términos son:
  - `tx_power`;
  - `tx_antenna_gain` y `rx_antenna_gain`, con el diagrama hacia el otro equipo;
  - `system_gain`;
  - `path_loss`, que depende de la distancia;
  - `walls`;
  - `extra_loss` por metro;
  - `polarization`.

  **Los cambios suman exactamente el cambio de potencia.** Es la aritmética del propio modelo, no una
  causa medida.
- **`walls`:** paredes que dejan de atravesarse (`no-longer-crossed`), que pasan a atravesarse
  (`newly-crossed`) o cuya pérdida cambia (`loss-changed`), cada una con su efecto en dB.
- **Margen limitante** de la base y de la alternativa (el menor de los dos sentidos) y su cambio. Es
  `None` si falta algún sentido.
- **`residual_risks`:** en qué se apoya todavía la alternativa:
  - puertas de estado desconocido y materiales con rango incierto en su trayecto;
  - equipos fuera del modelo (B-122);
  - sentidos sin calcular, sensibilidades ausentes y margen negativo.

  No hay probabilidades.
- Si a una versión le falta la potencia de un sentido, ese sentido no tiene términos y `reason` dice
  en cuál falta. No se rellena.

## Trabajo del consumidor (A)

1. Añadir `link-difference.ts` al script `contracts`.
2. En la comparación manual (A-105) o tras aplicar una alternativa (A-110), mostrar el cambio por
   sentido, los términos principales, las paredes que entran o salen y los riesgos residuales. Usar
   lenguaje de modelo («según el modelo, la pared X deja de atravesarse: +7.2 dB»), no causas reales.

## Límites

- Trayecto directo del estimador. El multipath puede cambiar la diferencia; en el contraste con Java
  (B-121) añadió de +0.3 a +3.6 dB en viviendas y hasta +33 dB en un almacén.
- Compara versiones nominales: para puertas y materiales inciertos se usan los escenarios (B-108).
