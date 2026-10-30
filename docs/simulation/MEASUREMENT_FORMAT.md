# Formato de campañas de medida (B-101)

Versión 1 · 2026-10-30. Modelo canónico: `services/simulator/src/smart_environment/measurements.py`.
Esquema generado: `contracts/measurement-campaign.schema.json`. Plantilla:
`services/simulator/examples/measurement-campaign.template.json`.

## Decisión de persistencia

Una campaña es un **archivo local separado** del proyecto exportable. No se incrusta en
`Project`, no cambia `project.schema.json`, `simulation-result.schema.json` ni OpenAPI, y la
interfaz (A) no necesita cambios. La campaña referencia el proyecto por nombre y por el
hash SHA-256 del JSON canónico (`input_hash`, el mismo que devuelven las simulaciones). Si
el plano cambia, el hash deja de coincidir y `project_issues()` lo informa: las posiciones
pueden referirse a otra versión.

No hay endpoint HTTP para campañas en esta entrega. Si la interfaz necesita importarlas,
B propondrá un endpoint aditivo y A implementará el consumidor.

## Privacidad

`site_id` es un seudónimo, nunca una dirección. `operator_role` describe un rol, no un nombre.
Los archivos no se envían a terceros. Las notas libres no deben incluir datos personales.

## Estructura

| Bloque | Contenido | Reglas |
|---|---|---|
| Cabecera | `id`, `site_id`, `split`, `synthetic`, `purpose`, `project`, fechas | `synthetic` solo y siempre con `split = format-example` |
| `instruments` | Router, equipo candidato o del mismo modelo, móvil, portátil… con modelo, chipset, firmware, herramienta y forma de informar RSSI | Un móvil (`phone`) no representa la radio del candidato |
| `radio` / `ParameterValue` | Potencia, ganancia, figura de ruido, sensibilidad: `value` + `provenance` (`measured`, `declared`, `inferred`, `unknown`) + `source` | Valor ausente ⇔ `unknown`; nunca un número por defecto |
| `access_points` | Dispositivo y radio del proyecto, frecuencia, canal, ancho, potencia y ganancia con procedencia, ajustes fijados | Referencias comprobadas contra el proyecto |
| `conditions` | Estado de puertas (ids de paredes del proyecto), personas, redes visibles en el canal, notas | Puertas desconocidas se declaran `unknown` |
| `criteria` | Criterio activo de fallo: método, sentido, paquetes mínimos, proporción mínima de entrega, `frozen_on` | En `validation`, `frozen_on` es obligatorio y no posterior al inicio |
| `points` | Posición en metros del proyecto, incertidumbre, orientación, instrumento, AP, condiciones | `planned` sin observaciones; `measured` con observaciones y hora; `excluded` con motivo |
| `rssi` | Sentido (`ap-to-device` / `device-to-ap`), instrumento receptor, muestras en dBm crudas, ruido si se informa, duración | Muestras en [−150, 0] dBm; sin promedios precalculados |
| `delivery` | Método, sentido, carga, intervalo, enviados, recibidos, reintentos | Solo recuentos crudos; el resultado se deriva |

## Funciones

- `delivery_outcome(test, criterion)`: `pass`/`fail`, o `inconclusive` si el método o el
  sentido no coinciden con el criterio o hay menos paquetes de los exigidos.
- `summarize(campaign)`: mediana, mínimo, máximo y número de muestras por sentido, y los
  resultados de entrega. Solo describe lo medido; no compara con predicciones.
- `project_issues(campaign, project)`: hash distinto, AP/radio inexistentes, puertas que no
  son paredes del proyecto.
- `partition_issues(campaigns)`: una vivienda en calibración y validación, o en piloto y
  validación, invalida la independencia; ids de campaña duplicados.

## Lo que el formato no hace todavía

- No calcula residuos predicción−medida ni ajusta materiales (P4). La comparación exigirá
  mapear el instrumento a un perfil de radio y registrar la versión del motor.
- No representa varias plantas, 5 GHz ni medidas de espectro/interferencia detalladas.
- No acredita equivalencia entre instrumentos: esa diferencia se declara en `instruments`.
