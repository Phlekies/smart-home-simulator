# Checklist del producto de cobertura previa a la compra

Fecha: 2026-10-29. Reconciliado con el código el 2026-11-09 (B-141: `main` 80e0f2d más B-139/B-140).
Marcar requiere implementación y evidencia; no basta esta especificación. La migración tiene
[su checklist propio](../migration/CHECKLIST.md). Las tareas pendientes por agente están en el
[tablero](../process/WORKBOARD.md).

## P0 — Requisitos y evidencia

- [ ] Perfiles iniciales Wi-Fi 2.4 GHz con parámetros de AP/cliente y procedencia (cliente B-106 y AP B-118 en `main`). Falta: la fuente primaria de la tabla HT (B-142) y elegir perfiles de AP en la interfaz (A4).
- [x] Configuración/modo de radio y requisitos por perfil documentados (modo B-106; requisito por perfil B-140: MCS0 bajo tráfico, MCS3 datos continuos, MCS7 solo cobertura; [perfiles](../simulation/RADIO_PROFILES.md)).
- [x] Desconocidos y valores inferidos diferenciados de datos medidos (contrato de medidas B-101, perfiles B-106, procedencia por parámetro B-113; se ve y edita en la interfaz desde #27).
- [x] Protocolo de medida piloto y criterio activo de fallo del enlace (protocolo B-101; criterio `low-traffic-v1` B-140, provisional: ≥ 300 ecos, falla con menos del 95 %; [clasificación](../simulation/COVERAGE_CLASSIFICATION.md)).
- [ ] Conjuntos de calibración y evaluación independientes separados (regla por vivienda en B-101; sin datos todavía).
- [ ] Objetivos numéricos congelados tras piloto y antes de evaluación independiente.
- [x] Clasificación de cobertura y reserva de diseño documentadas (B-139: reserva provisional de 10 dB, cuatro clases, plan de revisión; ADR-010).

## P1 — Cobertura espacial

- [x] Plano a escala, paredes/espesores/materiales y alturas editables (referencia calibrada B-104/A-102 con cota A–B en #27; inspector de paredes con material, espesor y altura; altura de cada equipo).
- [x] Mapa por perfil/banda/altura, con resolución y puntos no calculados identificados (B-103 + A-104 en `main`; [evidencia](../ui/COVERAGE_MAP.md)).
- [x] Coordenada elegida se evalúa sin redondeo a la celda visual (punto exacto; B-103 + A-104 en `main`; [evidencia](../ui/COVERAGE_MAP.md)).
- [x] Potencia y margen de ida y vuelta visibles (mapas y enlaces; B-103 + A-104 en `main`; [evidencia](../ui/COVERAGE_MAP.md)).
- [x] Un retorno insuficiente impide concluir cobertura favorable aunque la bajada sea buena (estado `below-threshold` y clase `insufficient`; prueba `test_weak_return_of_a_low_power_sensor_is_insufficient`, B-139).
- [x] Selección de AP explícita; energía de distintos AP no se suma como señal de una conexión (B-103 + A-104 en `main`; [evidencia](../ui/COVERAGE_MAP.md)).
- [x] Sensibilidad/configuración desconocida produce conclusión parcial o sin datos (estado `unverified`, celdas `partial`, clase `no-data`; pruebas de B-103, B-122 y B-139).
- [x] Cambiar paredes, AP o radios invalida resultados obsoletos (huella `input_hash` y B-132; la interfaz descarta resultado y mapa en cada cambio físico y las respuestas de revisiones antiguas).

## P2 — Riesgo y supuestos

- [x] Puertas y materiales inciertos admiten escenarios identificados (API B-108, mapas con escenario B-114, interfaz A-111…A-113; en `main`).
- [ ] Clasificación distingue favorable, marginal, insuficiente y sin datos (API B-139 en enlaces, escenarios, celdas, búsqueda e informe). Falta mostrarla en la interfaz (A1/A2).
- [x] Sin umbral RSSI universal ni porcentajes de éxito inventados (la clase usa el margen frente a la sensibilidad de cada receptor; sin probabilidades; los mapas del informe no dan porcentajes, con prueba).
- [x] Ruido/interferencia no evaluados se declaran independientemente de la cobertura (limitaciones del motor, «No evaluado» del informe y leyenda del mapa).
- [x] Fuera de banda, perfil o geometría soportados: sin recomendación favorable (banda `unsupported`, geometría fuera del modelo B-122; clase `no-data`, B-139).
- [x] Cobertura, compatibilidad de radio y funcionamiento de aplicación se presentan separados (campo `compatibility` aparte; «compatibilidad funcional no evaluada» en cada resultado y en el informe).

## P3 — Alternativas realizables

- [x] Comparación base/alternativa conserva perfiles y condiciones equivalentes (A-105: solo compara si todo salvo nombres y posiciones es idéntico, `editor/comparison.ts` con pruebas; B-123 compara por enlace).
- [x] Mover AP/equipo/altura ofrece diferencia de señal y margen limitante (A-105; diferencia exacta por términos B-123, mostrada en la interfaz desde #27).
- [x] Añadir AP exige definir su conexión de datos (API B-117; editor de conexión y diagnóstico del camino de datos en #27).
- [ ] Lugares permitidos, enchufes y cableado limitan la búsqueda (lugares B-105 con interfaz; enchufes y tomas B-119 solo en la API). Falta marcarlos en el plano (A3).
- [x] Se evalúan ubicaciones prioritarias, no solo el porcentaje de suelo cubierto (B-105: máximo del peor margen de los equipos elegidos).
- [x] La explicación identifica mejoras y riesgos residuales sin atribuciones causales falsas (B-123; explicación por términos en la interfaz desde #27).
- [x] Sin recomendar compra de modelo con datos/compatibilidad de radio sin verificar (no hay catálogo de productos; el informe y la interfaz dicen que no recomiendan compras, con prueba).

## P4 — Validación

- [ ] Medidas importables con posición, radio, configuración y condiciones (formato B-101 y comprobación por API B-116). Falta la importación en la interfaz (A6).
- [ ] Calibración reproducible y diferencias antes/después registradas.
- [ ] Baseline y motor avanzado comparados sobre datos independientes.
- [ ] Error de señal, sesgo y casos difíciles publicados.
- [ ] Falsos favorables frente a pruebas activas medidos, con tamaño de muestra.
- [ ] Abstenciones medidas; «sin datos» no oculta falta de utilidad.
- [ ] Incertidumbre estadística y dependencia entre puntos tratadas adecuadamente.
- [ ] Se cumplen objetivos congelados o se limita el ámbito ofrecido.

## P5 — Uso y entrega

- [ ] Persona nueva completa vivienda→equipo→ubicación→diagnóstico→alternativa→informe (prueba con usuarios pendiente, U3).
- [x] Puede explorar sin haber comprado toda la domótica (perfiles genéricos B-106/B-118, recorrido guiado A-118 y proyecto de demostración).
- [ ] Si usa móvil como medida, se explica su diferencia respecto al equipo candidato (B-124 en la API). Falta la importación de medidas en la interfaz (A6).
- [x] Informe conserva versiones, escenario, perfil, supuestos y datos pendientes (B-115, mapas B-120, niveles de evidencia B-135; descarga Markdown/JSON en la interfaz, A-115 y #27).
- [ ] Guardado/recuperación, accesibilidad e instalación local comprobados (guardado JSON, copia de recuperación, teclado A-118, `scripts/start.py` y zip 2.0.0 comprobados). Falta probar con un lector de pantalla real (U4).
- [x] Se distingue predicción de medidas reales y rendimiento no evaluado (niveles de evidencia B-135, `calibrated: false` en la clasificación, «No evaluado» del informe).
- [x] Las extensiones sin validar no se anuncian como soportadas (Sionna RT y ns-3 «Pendiente» en la interfaz y 501 en la API; límites en el README).

## Casos de aceptación representativos

| Caso | Resultado esperado |
|---|---|
| AP potente y sensor de baja potencia | Detectar el retorno limitante; no verde por buena recepción del sensor |
| Pared con mayores pérdidas en el trayecto dominante directo | Reflejar su efecto según el modelo y explicar las hipótesis; no exigir una regla monotónica falsa para cualquier multipath |
| Material desconocido | Rango de escenarios y conclusión prudente, no propiedad exacta inventada |
| Falta sensibilidad del candidato | Presupuesto parcial y «sin datos suficientes» para la clasificación |
| Se mueve el router a un lugar permitido | Recalcular y comparar con el mismo perfil y configuración |
| Se añade AP sin enlace de datos | No presentarlo como solución completa de conectividad |
| Cámara con señal favorable | Informar cobertura; vídeo/caudal/estabilidad pendientes si no se modelaron |
| Equipo Thread en versión solo Wi-Fi | Fuera del soporte de esta entrega; no evaluar contra el router Wi-Fi como enlace directo equivalente |
| Escena editada durante el cálculo | Descartar resultado obsoleto |
| Modelo con error en vivienda independiente | Registrar fallo; no ajustar y reutilizar ese mismo conjunto como validación independiente |

Casos con prueba automática de la clasificación (B-139, `test_classification.py`): AP potente y
sensor de baja potencia → insuficiente; material desconocido → marginal si pierde la reserva en el
peor caso; falta sensibilidad → sin datos; cámara del proyecto de demostración → marginal por el
retorno, con el vídeo como no evaluado.
