# Conexión de datos de los puntos de acceso (B-117)

Versión 1 · 2026-11-01. Modelos: `DataConnection`, `BackhaulHop` y `AccessPointConnection` en
`models.py`. Cálculo: `backhaul.py`. Pruebas: `services/simulator/tests/test_backhaul.py`.
Esquemas: `project.schema.json` (`Device.data_connection`) y `simulation-result.schema.json`
(`access_points`). Tipos TS: `project.ts` y `simulation-result.ts`.

## Qué responde

«¿Cómo llegan a la red los datos de cada router, AP o repetidor?». Responde al criterio de producto
«añadir un AP exige definir su conexión de datos». Un AP con buena cobertura hacia los sensores no
sirve si su propio enlace con el router no funciona. Ese enlace se evalúa igual que cualquier otro:
en ambos sentidos, con el margen limitante.

## Contrato (aditivo y opcional)

`Device.data_connection` es opcional y vale `None` por defecto, que significa sin definir:

| `kind` | Significado | `link_id` |
|---|---|---|
| `gateway` | Es la salida de la red (p. ej. el router del operador) | — |
| `wired` | Cable declarado (Ethernet, PLC…); **no se evalúa** | — |
| `wireless` | Los datos viajan por un enlace del proyecto (malla, repetidor) | Obligatorio; el enlace debe llegar a este equipo |
| `unknown` | Se sabe que no está decidido | — |

`note` es texto libre de documentación. La validación rechaza:
- un `wireless` sin enlace;
- un enlace en un tipo que no es `wireless`;
- un enlace inexistente;
- un enlace que no toca al equipo.

El campo entra en `input_hash` solo si se define. Los proyectos anteriores conservan su huella.

## Resultado

`SimulationResult.access_points` contiene un elemento por cada equipo con rol `access-point`,
`router` o `bridge`, y por cada equipo con conexión definida:

- **`hops`:** enlaces inalámbricos desde el equipo hacia la pasarela, en orden. Cada salto lleva su
  estado y su margen limitante (el menor de los dos sentidos, o `None` si falta alguno).
- **`ends_at`:** dónde acaba la cadena: `gateway`, `wired`, `unknown`, `undefined` (un equipo sin
  conexión definida) o `loop` (vuelve a un equipo ya recorrido).
- **`weakest_margin_db`:** el menor margen de los saltos. Es `None` si no hay saltos o si falta
  alguno.
- **`reasons`:** sin definir, desconocida, cable no evaluado, salto sin margen, bucle.

No hay veredicto: no se dice que un AP «tenga red», solo qué se ha calculado y qué falta.

## Dónde se usa

- **Búsqueda de ubicación (B-105):** si el AP movido tiene una conexión `wireless`, su enlace de
  datos se mueve con él. Se evalúa siempre como un equipo prioritario más (`TargetEvaluation.backhaul`),
  aunque no esté en `target_device_ids` y aunque use otra radio del AP. Sin conexión definida, el
  resultado lo advierte.
- **Mapas (B-103):** si el AP del mapa no tiene un camino de datos completo, una nota del mapa lo dice.
  Por ejemplo, cuando la conexión no está definida o el salto más débil tiene margen negativo.
- **Informe (B-115):** sección «Conexión de datos de los AP», con la misma información.

## Límites

- Los cables y la pasarela se declaran, no se comprueban.
- No se evalúan el caudal, la latencia ni la capacidad del enlace de retorno compartido. Tampoco la
  banda dedicada de una malla, salvo que se modele como otra radio y otro enlace.
- La energía de varios AP no se suma: cada enlace es una conexión con un solo extremo de cada lado.

## Trabajo del consumidor (A)

1. Editor de la conexión de datos en el inspector de los equipos de red: tipo, enlace si es
   inalámbrica y nota.
2. Mostrar `access_points` en el panel de resultados y en el informe: cadena, margen más débil y avisos.
