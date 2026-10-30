# Protocolo de medidas piloto — Wi-Fi 2.4 GHz (B-101)

Versión 1 · 2026-10-30. Estado: **propuesta, sin ejecutar**. No existe ninguna medida real
en el repositorio. Los valores numéricos de este documento son parámetros de diseño
revisables, no resultados ni objetivos de precisión. Formato: [MEASUREMENT_FORMAT](MEASUREMENT_FORMAT.md).

## Objetivo del piloto

1. Comprobar que el recorrido de medida es ejecutable y registra todo lo necesario.
2. Estimar la repetibilidad de la propia medida, que limita el error alcanzable por el modelo.
3. Obtener una primera distribución de error predicción−medida para **proponer** objetivos
   numéricos (error, falsos favorables, abstenciones) que se congelarán antes de evaluar.

El piloto **no valida** el producto: sus viviendas no pueden reutilizarse en validación.

## Partición de datos

| Conjunto (`split`) | Uso | Regla |
|---|---|---|
| `pilot` | Ensayar el protocolo y proponer objetivos | Sus viviendas quedan excluidas de `validation` |
| `calibration` | Ajustar materiales/parámetros del modelo | Puede compartir vivienda con `pilot` |
| `validation` | Evaluación independiente con objetivos y criterio congelados | Viviendas nunca vistas en `pilot` ni `calibration` |
| `format-example` | Plantillas y pruebas de software | Siempre `synthetic`; sin observaciones; nunca evidencia |

La unidad de partición es la **vivienda**, no el punto: los puntos de una misma vivienda
están correlacionados (mismos materiales, AP y entorno) y separarlos por punto sobrestimaría
la precisión. `partition_issues()` comprueba esta regla.

## Preparación

1. Dibujar la vivienda en la aplicación (paredes, materiales/espesores conocidos, alturas)
   y guardar el proyecto. Registrar su `input_hash`; no modificar el plano durante la campaña.
   Si hay que corregirlo, se guarda una versión nueva y la campaña se referencia a ella.
2. Router existente: modelo, firmware, posición y altura en el proyecto. Fijar canal y
   ancho de 20 MHz en 2.4 GHz; desactivar o anotar band steering, potencia automática y malla.
   La potencia declarada por la interfaz del router es `declared`, no `measured`.
3. Instrumentos: preferir el equipo candidato o uno del mismo modelo. Si se usa un móvil,
   declararlo `phone`; caracteriza el entorno, no la radio del candidato. Registrar
   herramienta y versión usadas para leer RSSI y si el valor se informa en dBm.
4. Sentido de retorno (`device-to-ap`): obtener el RSSI que ve el router del cliente (interfaz
   o registros del router) si está disponible. Si no, queda sin medir; no se deduce del otro sentido.

## Puntos y alturas (propuesta inicial)

- Cada ubicación prevista de un equipo domótico, a la altura real de instalación.
- Alturas de referencia en esas ubicaciones: 0.3 m (suelo/zócalo), 1.2 m (interruptor/mesa)
  y 2.2 m (techo/alto), como en la plantilla.
- Muestreo complementario por habitación para observar la variación espacial, con puntos
  a más de 0.5 m de paredes salvo que la ubicación prevista esté junto a ella.
- Repetir un subconjunto de puntos otro día y con otra persona colocando el equipo para
  estimar repetibilidad. Proponer un 10 % de los puntos; revisar tras el piloto.
- Posición medida con cinta o láser desde dos paredes de referencia; anotar la incertidumbre.
  Orientación del equipo respecto al eje X del plano.

## Procedimiento en cada punto

1. Colocar el equipo y esperar a que la conexión se estabilice; anotar la hora.
2. RSSI AP→equipo: muestras crudas durante un intervalo fijo (propuesta: 1 Hz, 60 s).
   RSSI equipo→AP si el router lo expone, en el mismo intervalo.
3. Prueba activa de entrega del perfil de bajo tráfico (propuesta: eco ICMP o sonda UDP de
   64 B cada 0.2 s, 100 paquetes en el sentido que define el criterio).
4. Registrar condiciones: puertas, personas, redes visibles en el mismo canal.
5. Marcar `excluded` con motivo si ocurre un incidente (reinicio del router, cambio de
   canal, interferencia evidente). Las reglas de exclusión se fijan **antes** de comparar
   con las predicciones; nunca se excluye un punto por discrepar del modelo.

## Criterio activo de fallo — decisión pendiente

El formato permite definir método, sentido, paquetes mínimos y proporción mínima de
entrega. **El umbral no está decidido** y no se fija en este documento: es una decisión de
producto para el perfil de sensor/actuador de bajo tráfico. Debe acordarse antes del
piloto, revisarse con sus resultados y congelarse (`frozen_on`) antes de recoger datos de
validación. Un RSSI favorable no sustituye este criterio.

## Qué se analizará después (P4, no implementado)

- Residuo predicción−medida por punto y sentido, con versión del motor y del proyecto.
- Mediana/dispersión por vivienda, material y altura; no solo un promedio global.
- Falsos favorables frente al criterio activo, abstenciones («sin datos») y su utilidad.
- Repetibilidad de la medida como cota inferior del error alcanzable.

## Seguridad y privacidad

Datos solo locales; `site_id` seudónimo; sin direcciones, nombres ni fotografías del interior
en archivos versionados. No se publican planos ni campañas reales sin decisión expresa del usuario.
