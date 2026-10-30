# Medidas frente a predicciones y calibración mínima (B-109)

Versión 1 · 2026-10-30. Código: `services/simulator/src/smart_environment/calibration.py`.
Pruebas: `services/simulator/tests/test_calibration.py`. Prepara P4; **no hay medidas reales**
en el repositorio y ningún resultado de este documento procede de una vivienda.

## Uso

```powershell
.venv/Scripts/python.exe -m smart_environment.calibration campaña-a.json=proyecto-a.json campaña-b.json=proyecto-b.json
```

Cada campaña ([formato](MEASUREMENT_FORMAT.md)) va emparejada con el proyecto que referencia.
La salida es un `CalibrationReport` en JSON. El ajuste entre viviendas sigue siendo offline. Para una
sola campaña, `POST /api/measurements/check` (B-116) devuelve sus residuos sin ajustar nada.

## Qué calcula

- **Predicción por punto y sentido** con el estimador rápido:
  - AP→equipo con la potencia del AP declarada en la campaña o, si falta, la del proyecto;
  - equipo→AP solo si se conoce la potencia del instrumento;
  - el estado de las puertas registrado en las condiciones de ese punto, como escenario de [B-108](SCENARIOS_CONTRACT.md).
- **Residuo** = mediana de las muestras medidas − predicción, en dB. Las ganancias de antena
  desconocidas se toman como 0 dBi y figuran en `assumptions` de cada residuo: el residuo las incluye.
- **Estadísticas por grupo** (AP→equipo, equipo→AP y todos): número de puntos, sesgo (media), mediana,
  MAE, RMSE, mínimo y máximo. No se calculan probabilidades ni intervalos de confianza.
- **Calibración `single-offset`**: un desplazamiento igual a la media de los residuos de las campañas
  `calibration`. Se aplica a las campañas `validation` y se publican sus estadísticas antes y después.
  Absorbe potencias y ganancias desconocidas; no corrige materiales ni geometría.

## Qué rechaza

| Situación | Resultado |
|---|---|
| La misma vivienda en calibración y validación, o en piloto y validación | `CalibrationError` (fuga entre conjuntos) |
| La campaña referencia otro hash de proyecto | `CalibrationError`: las posiciones podrían ser de otro plano |
| Campaña sintética (`format-example`) | `CalibrationError`: no es evidencia |
| Instrumento que no informa en dBm | Observación omitida con motivo |
| Falta la potencia del sentido medido | Observación omitida con motivo |
| Puntos planificados o excluidos | Se ignoran; las exclusiones se justifican en la campaña |

Las campañas `pilot` aparecen en los residuos, pero no entran ni en el ajuste ni en la evaluación.

## Lo que falta para cerrar P4

- Datos reales del piloto y de viviendas independientes, con objetivos congelados antes de evaluar.
- Falsos favorables frente a las pruebas activas: necesitan el umbral del criterio de fallo y la
  reserva de diseño, ambos pendientes de decisión.
- Dependencia espacial entre puntos e incertidumbre estadística; ajustes por material solo si
  reducen el error en datos independientes.
- Comparación con el motor avanzado sobre los mismos datos (ver [B-102](ADVANCED_ENGINE_EVALUATION.md)).
