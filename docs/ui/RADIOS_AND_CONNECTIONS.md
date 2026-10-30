# Radios y conexiones explícitas — A-107/A-108

Entrega de interfaz, 2026-10-30 (Europe/Madrid). Usa Device/Radio/Link existentes;
no cambia contratos, backend ni soporte de tecnologías.

## Recorrido

- En un equipo, elegir «Interfaz de radio». El selector muestra ID, protocolo y frecuencia.
  La lista lateral resume todas las radios del equipo, en lugar de solo la primera.
- «Añadir radio» crea otra interfaz genérica con ID local libre (radio-1, radio-2...).
  Protocolo/canal/potencia/sensibilidad quedan desconocidos. Frecuencia 2412 MHz, ancho
  20 MHz, ganancias 0 dBi y demás valores genéricos son editables, sin datos de fabricante
  ni validación inferida. El formulario lo explica; no es un catálogo de productos.
- Se conserva el mínimo de una radio y el máximo de ocho del contrato. Al añadir,
  cambiar o retirar una radio, el foco se mantiene en el selector disponible.
- «Retirar radio y sus enlaces» muestra cuántos enlaces retirará. Solo afecta a la radio
  del equipo seleccionado, aunque otro equipo use el mismo ID de radio. Una sola acción
  de Deshacer recupera radio y enlaces. La última radio exige retirar el equipo completo.
- En Conexiones, elegir una radio de destino de otro equipo. Se muestran todas las
  interfaces agrupadas por equipo, con IDs/protocolo/frecuencia, y un botón para crear.
  Ya no se utiliza implícitamente la primera radio del equipo destino.
- Radios ya enlazadas se identifican y desactivan como opción; no se crean duplicados
  de la misma pareja ni su inversión, porque cada enlace evalúa ambos sentidos.
- Cada enlace del equipo puede quitarse sin eliminar dispositivos ni radios, y deshacerse.
  Se respeta el límite de 512 enlaces; al alcanzarlo aún se permite retirar existentes.
- Diagnóstico y comparación muestran IDs de radios junto al par de equipos para distinguir
  enlaces paralelos. No se suman sus señales ni se interpreta la pareja como una malla.

Todos los cambios pertenecen al proyecto canónico: invalidan resultados, se guardan en
JSON y entran en la recuperación existente. La comparación de posiciones se bloquea si
se cambia esta configuración, como en A-105. Original Java y notas no se sobrescriben.

## Evidencia

- 12 pruebas nuevas de conexiones: desconocidos genéricos, copias independientes,
  IDs locales, mínimo/máximo de radios, cascada por ambos extremos y alcance por equipo,
  undo/redo de cascada, elección exacta de radios, duplicados/inversión, referencias,
  límites de identificadores/enlaces y retirada individual.
- Una prueba nueva de comparación: dos enlaces del mismo par de equipos conservan
  radios, resultados y deltas independientes por sentido.
- Navegador con datos sintéticos: AP de prueba y Sensor de prueba, dos radios cada uno.
  Sensor/radio-2→AP/radio-2 y Sensor/radio-2→AP/radio-1 definidos explícitamente.
  La opción ya enlazada queda desactivada. Al enlazar todas las opciones se explica y
  desactiva Añadir enlace, sin impedir retirarlos.
- Calcular entre las segundas radios con TX desconocida devuelve «Sin datos» y «Sin
  verificar», sin potencia favorable inventada. El enlace hacia AP/radio-1 mantiene
  la estimación parcial real de la API en el sentido que tiene TX conocida.
- Retirar Sensor/radio-2 elimina los dos enlaces, conserva el sensor con radio-1 y las
  radios del AP. Un solo Deshacer recupera radio-2 y los dos enlaces. Retirar un enlace
  individual conserva ambas radios/equipos; otro Deshacer lo recupera.
- Descarga real `entorno.shsim (4).json`, validada por la API y leída: dos equipos,
  radios por equipo 2/2, dos enlaces con radios destino radio-2/radio-1 y TX de las
  radios nuevas nula. Recargar/restaurar conserva todas esas referencias.
- Foco en selector de radio después de cambios y en destino después de retirar enlace;
  consola de navegador sin errores. [Captura](radios-connections.jpg).
- Pruebas/build finales: [registro A](../process/AGENT_A.md). Los máximos de ocho radios
  y 512 enlaces se verificaron automáticamente; no se atribuyen a un recorrido visual.

La pareja de radios solo define un enlace a evaluar. No acredita conexión a Internet,
rutas de malla, capacidad de tráfico ni compatibilidad funcional. Zigbee/Thread y otras
tecnologías no pasan a estar soportadas por poder introducir sus nombres en una radio.
