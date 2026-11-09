# Decisiones de arquitectura

## ADR-001 — Migración incremental

Java permaneció en su estructura hasta superar las puertas de sustitución (retirado en ADR-009). Nueva aplicación
en `apps/web` y `services/simulator`. Los JSON Java v1 se importan conservando la entrada
original en `legacy_source`; la conversión declara cada supuesto importante. No se exige
igualdad numérica con Java cuando cambia el modelo físico.

## ADR-002 — Contrato antes que motor

Pydantic define validación y JSON Schema; TypeScript se genera del JSON Schema. OpenAPI
se genera desde FastAPI. Los archivos generados se verifican en CI para detectar deriva.
El formato independiente del motor representa edificios, radios y enlaces explícitos.
Protocolo desconocido permanece desconocido. No asumir Wi-Fi por usar 2.4 GHz.

## ADR-003 — Motor rápido con alcance honesto

Primer recorrido: pérdida log-distance + cruces de paredes verticales y ruido térmico.
Calcula cada dirección usando transmisor y receptor propios. La geometría de distancia
es 3D; no se modelan aún forjados, reflexiones, difracción, fading, tráfico ni interferencias.
No calcula BER, velocidad útil ni latencia. Las cifras empíricas de materiales heredadas
no tienen precisión experimental certificada. Sensibilidad es un umbral configurado,
no una prueba de conexión. Una radio heredada sin protocolo/canal tiene compatibilidad
sin verificar aunque el presupuesto de enlace sea favorable.

## ADR-004 — Motores especializados opcionales

Sionna RT es candidato de propagación; ns-3 es una extensión para tráfico/interferencia
cuando el producto la necesite y exista modelo adecuado. No es obligatorio para la primera
versión centrada en cobertura Wi-Fi. El registro distingue instalado,
adaptador implementado y verificado. No se importan librerías GPU al iniciar la API ni se
instalan automáticamente. Peticiones a motores no implementados devuelven error explícito.
El estimador rápido nunca sustituye silenciosamente otro motor solicitado.

## ADR-008 — Motor con el que se cierra la migración: estimador directo

Decisión del usuario del 2026-11-08 (B-130). La migración se cierra con la estimación rápida
(`quick-estimate`): trayecto directo, paredes verticales y ambos sentidos, con sus límites
declarados. Sionna RT queda evaluado (B-102: 18/18 referencias en WSL2/CPU) y **no se integra**
en la API.

Motivos:
- En este equipo no se ejecuta en Windows nativo y exige WSL con LLVM.
- Sin medidas reales no hay datos para saber qué motor acierta más en una vivienda.
- El contraste con el multipath Java (B-121) ya documenta cuánto puede separarse el estimador:
  de +0.3 a +3.6 dB en viviendas y oficinas, y hasta +33 dB en el almacén.

Consecuencias:
- `sionna-rt` y `ns-3` siguen respondiendo 501, sin recurrir al estimador.
- Los resultados se presentan como «trayecto directo, sin calibrar».
- El estimador no equivale al motor multipath Java y no se anuncia como tal.
- Integrar un motor avanzado pasa a ser una decisión de producto (P4), cuando haya medidas
  independientes con las que comparar ambos.

## ADR-009 — Java fuera de `main` una vez superadas las puertas

Decisión del usuario del 2026-11-09 (B-136): con M0–M5 completas, el código Java ya no hace falta en el
repositorio. Se retiran de `main` `src/`, Gradle, `packaging/` y las capturas de la aplicación JavaFX.
Se conservan:
- la etiqueta `java-desktop-final`, que apunta al último `main` que contenía Java (23ace32);
- la release v1.0.0, con sus ejecutables nativos;
- los ejemplos `examples/*.shsim.json`, que la API sigue importando.

El arnés de paridad (B-121) extrae las fuentes Java de esa etiqueta, así que la comparación sigue siendo
reproducible sin tener Java en el árbol. La CI y las releases pasan a ser solo de la aplicación nueva.

## ADR-005 — Reproducibilidad y obsolescencia

Cada ejecución incluye hash SHA-256 del escenario canónico, ID/versión del motor,
duración y supuestos. La web borra resultados al editar y descarta respuestas de revisiones
anteriores. Futuras semillas, versiones nativas y parámetros se incorporarán al registro.
No mezclar resultados entre motores, escenarios o distintas revisiones.

## ADR-006 — Ejecución local primero

API en loopback; web usa proxy `/api`. No despliegue, cuentas, telemetría ni envío de
planos a terceros. La API inicial es síncrona, acotada y para el estimador rápido; los
trabajos pesados requieren cola y procesos cancelables antes de activar sus adaptadores.

## ADR-007 — Decisión de cobertura antes de compra como objetivo rector

Prioridad confirmada el 2026-10-29: Wi-Fi primero, inicialmente 2.4 GHz. El mapa se
condiciona al perfil, altura y configuración; la conexión se evalúa en ambos sentidos.
La compatibilidad de radio, el margen y la estabilidad bajo tráfico son conclusiones
distintas. Un margen positivo no acredita una compra segura. Las recomendaciones se
apoyan en datos, incertidumbre y validación independiente.

La paridad con Java se limita a funciones que ayudan a preparar la vivienda, calcular o
explicar cobertura, comparar alternativas o preservar/verificar datos. Las animaciones
decorativas y las métricas académicas sin relación validada con el uso no bloquean la
migración. Automatizaciones y compatibilidad funcional completa quedan fuera del alcance
inicial. Referencia: `docs/PRODUCT_OBJECTIVE.md` y `docs/product/DEVELOPMENT_PLAN.md`.
