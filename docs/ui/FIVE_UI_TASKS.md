# Cinco consumidores de interfaz — A-109 a A-113

Entrega del 2026-10-30 (Europe/Madrid). Base: main 6fb42e2 (PR #8, #9 y #10 integrados),
más persistencia A-102 de PR #12. Solo interfaz y pruebas; no cambia el modelo físico,
contratos, código generado ni Java. La revisión de las cinco tareas es independiente de
la aceptación de M2/M4 y de la validación experimental del producto.

| Tarea | Resultado verificable | Límite |
|---|---|---|
| A-109 | Perfil de equipo o genérico para el mapa; valor/procedencia/fuente/notas visibles, TX opcional con fuente; respeta canal/ancho del AP y rechaza banda/protocolo distintos | Perfiles preliminares, tabla HT pendiente de cotejo; no catálogo comercial |
| A-110 | Lugares exactos y zonas con altura/paso, prioridades por enlaces, comparación base/alternativa en ambos sentidos, exclusiones, aplicación explícita y undo | Un AP, lugares declarados por la persona; parámetros/resultados de sesión |
| A-111 | Pared normal o puerta abierta/cerrada/desconocida; JSON/historial/invalidation; indicadores en 2D/3D | El segmento completo representa la puerta, sin crear un hueco en otra pared ni difracción |
| A-112 | Rangos por material en 2.4/5 GHz y fuente; se exige mínimo ≤ nominal ≤ máximo; editar nominal respeta el rango; retirar rango y undo | Compartido por todas las paredes del material; hipótesis, no probabilidades |
| A-113 | Nominal/mejor/peor por enlace y sentido, rangos de potencia, márgenes, hipótesis inspeccionables y datos incompletos | Solo tres escenarios automáticos; sin escenarios personalizados ni exportación persistente |

## Recorrido reproducible

Abrir [la vivienda sintética](five-tasks-demo.shsim.json). Sus equipos, materiales y
potencias son valores de QA, sin datos comerciales ni mediciones.

1. En el mapa, elegir origen genérico y HT20 MCS0. La TX del cliente queda desconocida:
   mapa de 12×8 m, resolución0.5 m, altura1.4 m →384 celdas parciales, vuelta sin calcular.
   Declarar TX0 dBm y una fuente sintética produce384 completas. El equipo del proyecto
   no se modifica. AP a5 GHz o TX200 dBm se rechazan con error, sin fallback.
2. En búsqueda, AP de prueba/r, prioridad Cliente de prueba. Añadir (5.125,4,1.4),
   otro lugar (6,4,1.4) y zona X2–4/Y3–5/paso1/altura1.4:11 posiciones declaradas,
   10 evaluadas y1 excluida por pared. Confirmar viabilidad de alimentación/cableado/montaje.
   Margen limitante actual4.94 dB, alternativa9.46 dB, cambio+4.52 dB; retorno limitante.
   Aplicar mueve solo el AP a X5.125; deshacer vuelve a X2 y exige recalcular.
3. Vaciar TX del AP y buscar: sin orden, sin margen completo ni delta ficticio; se
   conservan los valores disponibles del retorno. Corregir TX retira la búsqueda anterior.
4. Seleccionar pared1: puerta desconocida, material de prueba nominal6/8 dB, rangos
   1–30/1–40 dB y fuente sintética. Una fuente vacía o nominal35 fuera del rango se rechaza.
5. Comparar escenarios: ida−79.06 a−49.06 dBm, vuelta−104.06 a−74.06 dBm. Márgenes:
   nominal29.94/4.94, mejor35.94/10.94, peor5.94/−19.06 dB. Se señala cambio de signo,
   sin clasificar fiabilidad. Inspeccionar la hipótesis enfoca Centro X y conserva el cálculo.
6. Marcar puerta abierta: invalida; al recalcular, los tres casos dan−49.06/−74.06 dBm.
   Deshacer restaura desconocida y retira escenarios. El 3D muestra la puerta abierta
   transparente; el 2D la dibuja discontinua y distingue desconocidas en violeta.
7. Guardar JSON y recargar/restaurar conserva puerta y rango/fuente. Los resultados y
   opciones de análisis se recalculan. Descarga real verificada: `entorno.shsim (6).json`.

La etiqueta «completas» solo indica disponibilidad de magnitudes; no acredita estabilidad
ni una reserva de diseño suficiente. Declarar límites de5 GHz no valida esa banda.

## Verificación y evidencia

- **120 pruebas web/editor**:94 anteriores y26 nuevas de perfiles, límites/referencias
  de ubicaciones, rangos/puertas/historial, coherencia de escenarios y carreras HTTP.
- **199 pruebas Python**, sin cambios de backend. Aviso conocido httpx/Starlette.
- TypeScript/Vite correcto; aviso previo del chunk3D≈933 kB. Navegador sin errores;
  al abrir3D aparece la deprecación ya conocida de THREE.Clock.
- Contratos canónicos sin deriva; script `contracts` ahora incluye placement-search.ts,
  radio-profile.ts y scenario-result.ts. Regenerar no cambia su contenido.
- Rechazo de respuestas tardías o de otras entradas, abortar transporte, vaciar resultados
  tras errores y desmontaje silencioso comprobados mediante pruebas inyectables.
- Navegador/API separados en5175/8001 durante QA. La prueba previa5174 se conserva hasta
  terminar la entrega; el estado del servidor de usuario se registra localmente.

[Perfiles y procedencia](radio-profiles.jpg) · [Búsqueda](placement-search.jpg) ·
[Puertas/materiales](door-material-editor.jpg) · [Escenarios](scenario-comparison.jpg).

## Observaciones para B / integrador

- B-105 calcula delta si coincide el número de enlaces completos. Dos conjuntos distintos
  pueden tener el mismo tamaño: A suprime ese delta comparando identidades de enlaces completos
  (prueba de regresión incluida). Revisar también la condición del productor para futuros consumidores.
- El validador de búsqueda enumera `zone.positions()` antes de verificar el total; un
  rectángulo muy grande/paso pequeño puede asignar demasiados puntos. A limita por conteo
  escalar antes de enviar, sin enumerar. No se ejecutó una petición gigante contra la API.
  B debería acotar el conteo antes de construir listas en el contrato/cálculo.
- Consolidar WORKBOARD/STATUS/checklists con esta evidencia; no marcar motor avanzado,
  precisión física, informes ni todo el producto como terminados.
