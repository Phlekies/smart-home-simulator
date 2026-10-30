# Checklist del producto de cobertura previa a la compra

Fecha: 2026-10-29. Estado inicial: pendiente. Marcar requiere implementación y evidencia,
no basta esta especificación. La migración tiene [su checklist propio](../migration/CHECKLIST.md).

## P0 — Requisitos y evidencia

- [ ] Perfiles iniciales Wi-Fi 2.4 GHz con parámetros de AP/cliente y procedencia.
- [ ] Configuración/modo de radio y requisitos por perfil documentados.
- [ ] Desconocidos y valores inferidos diferenciados de datos medidos.
- [ ] Protocolo de medida piloto y criterio activo de fallo del enlace.
- [ ] Conjuntos de calibración y evaluación independientes separados.
- [ ] Objetivos numéricos congelados tras piloto y antes de evaluación independiente.
- [ ] Clasificación de cobertura y reserva de diseño documentadas.

## P1 — Cobertura espacial

- [ ] Plano a escala, paredes/espesores/materiales y alturas editables.
- [ ] Mapa por perfil/banda/altura, con resolución y puntos no calculados identificados.
- [ ] Coordenada elegida se evalúa sin redondeo a la celda visual.
- [ ] Potencia y margen de ida y vuelta visibles.
- [ ] Un retorno insuficiente impide concluir cobertura favorable aunque la bajada sea buena.
- [ ] Selección de AP explícita; energía de distintos AP no se suma como señal de una conexión.
- [ ] Sensibilidad/configuración desconocida produce conclusión parcial o sin datos.
- [ ] Cambiar paredes, AP o radios invalida resultados obsoletos.

## P2 — Riesgo y supuestos

- [ ] Puertas y materiales inciertos admiten escenarios identificados.
- [ ] Clasificación distingue favorable, marginal, insuficiente y sin datos.
- [ ] Sin umbral RSSI universal ni porcentajes de éxito inventados.
- [ ] Ruido/interferencia no evaluados se declaran independientemente de la cobertura.
- [ ] Fuera de banda, perfil o geometría soportados: sin recomendación favorable.
- [ ] Cobertura, compatibilidad de radio y funcionamiento de aplicación se presentan separados.

## P3 — Alternativas realizables

- [ ] Comparación base/alternativa conserva perfiles y condiciones equivalentes.
- [ ] Mover AP/equipo/altura ofrece diferencia de señal y margen limitante.
- [ ] Añadir AP exige definir su conexión de datos.
- [ ] Lugares permitidos, enchufes y cableado limitan la búsqueda.
- [ ] Se evalúan ubicaciones prioritarias, no solo el porcentaje de suelo cubierto.
- [ ] La explicación identifica mejoras y riesgos residuales sin atribuciones causales falsas.
- [ ] Sin recomendar compra de modelo con datos/compatibilidad de radio sin verificar.

## P4 — Validación

- [ ] Medidas importables con posición, radio, configuración y condiciones.
- [ ] Calibración reproducible y diferencias antes/después registradas.
- [ ] Baseline y motor avanzado comparados sobre datos independientes.
- [ ] Error de señal, sesgo y casos difíciles publicados.
- [ ] Falsos favorables frente a pruebas activas medidos, con tamaño de muestra.
- [ ] Abstenciones medidas; «sin datos» no oculta falta de utilidad.
- [ ] Incertidumbre estadística y dependencia entre puntos tratadas adecuadamente.
- [ ] Se cumplen objetivos congelados o se limita el ámbito ofrecido.

## P5 — Uso y entrega

- [ ] Persona nueva completa vivienda→equipo→ubicación→diagnóstico→alternativa→informe.
- [ ] Puede explorar sin haber comprado toda la domótica.
- [ ] Si usa móvil como medida, se explica su diferencia respecto al equipo candidato.
- [ ] Informe conserva versiones, escenario, perfil, supuestos y datos pendientes.
- [ ] Guardado/recuperación, accesibilidad e instalación local comprobados.
- [ ] Se distingue predicción de medidas reales y rendimiento no evaluado.
- [ ] Las extensiones sin validar no se anuncian como soportadas.

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
