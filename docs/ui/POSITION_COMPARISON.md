# Comparación manual de ubicaciones — A-105

Entrega de interfaz, 2026-10-30 (Europe/Madrid). Reutiliza el endpoint y contratos actuales.
Adelanta un recorrido independiente del objetivo de comparar alternativas; no completa
M4/P3, mapas, optimización ni validación física.

## Recorrido

1. Ejecutar una estimación con enlaces definidos.
2. Pulsar «Fijar instalación base»: conserva una copia independiente del proyecto y del
   resultado, fecha y escenario/motor. Una edición posterior no modifica esa copia.
3. Mover uno o varios equipos o cambiar sus alturas; recalcular la alternativa.
4. Revisar señal base/alternativa, cambio en dB, margen y estado de cada sentido. La lista
   de posiciones conserva las coordenadas exactas; los valores de la tabla se presentan
   con una cifra decimal, sin atribuir esa precisión a mediciones reales.
5. «Restaurar posiciones base» recupera solo posiciones como una acción de historial,
   invalida el cálculo y permite deshacer. No sustituye radios/materiales por debajo.
6. Reemplazar la base o quitar la comparación explícitamente cuando sea necesario.

La base es de sesión y no se incluye en JSON/recuperación. Cambiar de proyecto la elimina.
La interfaz lo indica. No se introduce otro formato persistido ni endpoint de escenarios.

## Comparabilidad

Solo se admiten diferencias de posición/altura y nombres de proyecto/equipos. Se conserva
la configuración completa restante: radios, sensibilidad, frecuencia, orientación,
materiales, paredes, edificio, enlaces, parámetros y datos del proyecto. Un orden distinto
de entidades o de claves JSON no inventa una diferencia de configuración.

Si cambian esas condiciones, el motor/versión o las identidades de los enlaces/sentidos,
se bloquea la tabla con explicación. La comparación no interpreta una potencia TX mayor
como ventaja causada por mover un equipo. Si hay desplazamiento pero el hash devuelto
es el de la base, también se rechaza como resultado obsoleto.

El estado/revisión de App mantiene cada resultado asociado a su proyecto: editar,
deshacer o restaurar posiciones lo invalida; una respuesta antigua no se adopta. El
comparador no calcula por su cuenta el hash canónico Python ni sustituye esa guarda.

Datos ausentes/no finitos se conservan como «Sin datos», nunca cero. Las diferencias
son alternativa menos base de cada sentido por separado; no se promedian ni se suman
emisores. El estado «sin verificar» se conserva aunque suba la señal. No hay porcentajes,
garantías de estabilidad ni recomendaciones de compra.

## Evidencia

- 11 pruebas nuevas: snapshots independientes, posición/altura/nombres/orden,
  bloqueo por condiciones, resultados pendientes, signos asimétricos, margen cero,
  datos ausentes/no finitos, motores/versiones, identidades y hash obsoleto/sin enlaces.
  Vectores numéricos sintéticos de prueba, no mediciones ni predicciones físicas.
- Navegador, proyecto sintético de la sesión anterior: fijar base, Router de prueba
  X=1.125→3 m, resto de condiciones idénticas. Antes de recalcular no aparecen deltas.
  Tras recalcular: −54.5→−50.1 dBm, +4.4 dB en ambos sentidos; margen «Sin datos»,
  evaluación «Sin verificar». Son salidas del estimador analítico actual.
- TX=0→20 dBm y recalcular: tabla bloqueada por condiciones diferentes. Deshacer recupera
  la comparabilidad. Restaurar posiciones devuelve X=1.125 y exige recalcular; deshacer
  devuelve X=3 y la nueva estimación reproduce la tabla anterior.
- Abrir apartamento limpia la base del proyecto previo. Navegación de teclado por
  botones/tabla/posiciones comprobada. [Captura](position-comparison.jpg).
- Pruebas/build finales y límites de toda la entrega en [AGENT_A](../process/AGENT_A.md).

No incluye búsqueda automática, lugares permitidos/enchufes/cableado, persistencia de
variantes ni informes de compra. Esas puertas del producto siguen pendientes.
