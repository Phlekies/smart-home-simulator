# Proceso de trabajo con dos agentes

Actualizado: 2026-10-29. Entrada local obligatoria: `AGENTS.md` en la raíz del repositorio.
Por petición del usuario se excluye mediante `.git/info/exclude` y no se publica. Un clon
nuevo no lo incluye: este proceso y el tablero siguen siendo documentación versionable.
No añadir el archivo con `git add -f` ni asumir que la exclusión local se transmite al clonar.
El reparto organiza sesiones futuras; este documento no inicia agentes ni publica cambios.

## Fuentes de verdad

| Información | Archivo responsable |
|---|---|
| Qué producto construimos y qué excluimos | [PRODUCT_OBJECTIVE](../PRODUCT_OBJECTIVE.md) |
| Qué existe y cómo se verificó | [STATUS](../migration/STATUS.md), resumen vigente al principio y evidencia de cada entrega |
| Qué falta de migración | [CHECKLIST técnico](../migration/CHECKLIST.md) |
| Qué falta para aceptar el producto | [CHECKLIST de producto](../product/ACCEPTANCE_CHECKLIST.md) |
| Orden y dependencias | [ROADMAP](../migration/ROADMAP.md), [plan del producto](../product/DEVELOPMENT_PLAN.md) |
| Próximas tareas asignables | [WORKBOARD](WORKBOARD.md), mantenido por B |
| Qué está tocando cada sesión y su traspaso | [registro A](AGENT_A.md), [registro B](AGENT_B.md), uno por rol |

No mantengas copias contradictorias de estas listas. El tablero no marca como aceptado
lo que el checklist aún no acredita. El número de tests registrado es evidencia fechada,
no una promesa de que cualquier checkout posterior esté correcto.

## Ciclo de una tarea

1. **Leer y elegir:** confirmar checkout, estado de archivos, objetivo, checklists y ambos
   registros. Elegir una tarea `ready` del propio rol con dependencias satisfechas.
2. **Reservar:** escribir en el propio registro ID de tarea, identidad de sesión/chat si
   se conoce, rama/worktree, hora con zona, estado `claimed` y archivos previstos.
   No inventar IDs ni asumir que una reserva caducó porque pasó un tiempo.
3. **Implementar:** cambios dentro del ámbito; conservar trabajo previo. Antes de tocar
   otro ámbito, registrar la necesidad como solicitud y separar tareas dependientes.
4. **Verificar:** pruebas pertinentes y recorrido real cuando corresponda. Anotar comando,
   resultado, contexto y límites. No declarar prueba superada por estar configurada.
5. **Entregar:** cambiar el registro a `review`, con resumen, lista de archivos, evidencia,
   riesgos y siguiente tarea sugerida. `blocked` debe indicar la dependencia concreta y
   qué trabajo independiente sigue siendo posible; no es una petición automática al usuario.
6. **Integrar (B):** comprobar diff/contratos, pruebas de la entrega y, si procede, ambas
   capas. Consolidar documentación común, marcar aceptación acreditada y actualizar el
   tablero. No atribuir pruebas de A a una ejecución propia: enlazar su evidencia.
7. **Cerrar:** tarea `done` y registro libre para otra tarea. Conservar traspasos anteriores
   breves en la sección histórica; no borrar decisiones o límites todavía relevantes.

Solo una sesión puede asumir el mismo rol/ámbito a la vez. Si dos chats quieren el rol A,
uno debe esperar su turno o recibir un subalcance explícito de archivos disjuntos. Abrir
otra rama en la misma carpeta no aísla los archivos de una sesión ya activa.

## Agente A — Interfaz, vivienda y proyectos

Responsable exclusivo de componentes React, estado/historial del editor, estilos,
accesibilidad, pruebas del editor y dependencias web. Usa contratos publicados por B.

Próximas entregas:

- Recuperación local tras recarga/cierre, con elección de restaurar o descartar y manejo
  de datos corruptos/cuota/versiones. Mantener importación/exportación JSON.
- Imagen de referencia con escala y cotas; acordar persistencia de geometría/referencia
  con B antes de cambiar el contrato. No enviar imágenes a terceros.
- Recorrido accesible y después visualización de mapas recibidos del motor, mostrando
  perfil, altura, resolución y datos no evaluados.

No calcula propagación en componentes ni cambia estados desconocidos a favorables por
motivos de presentación. No añade fórmulas o datos comerciales para rellenar huecos del API.

## Agente B — Motor, API y evidencia; integrador

Responsable exclusivo de modelos Pydantic, importador, contratos, generación de tipos,
estimador, adaptadores, mediciones, benchmarks y pruebas científicas/API.

Próximas entregas:

- Preparar casos analíticos y protocolo piloto de mediciones, sin inventar medidas.
- Evaluar motor avanzado en entorno aislado y registrar compatibilidad CPU/GPU,
  versiones, interacciones soportadas y resultados reproducibles.
- Definir contrato de mapas por perfil/altura y requisitos de trabajo cancelable antes
  de exponer simulaciones pesadas a la interfaz.
- Integrar los traspasos y consolidar evidencia/checklists/CI, de forma serializada.

No reescribe la UI. Si genera TypeScript, solo modifica `src/generated/` y deja indicado
qué endpoint/tipo cambia para que A implemente el consumidor. No obliga a migrar métricas
académicas irrelevantes ni a integrar ns-3 para completar cobertura inicial.

## Contrato entre A y B

Una solicitud de cambio compartido contiene:

```text
Solicitante / tarea:
Pregunta de usuario que resuelve:
Contrato actual y cambio propuesto:
Compatibilidad de archivos/clientes existentes:
Archivos de cada rol afectados:
Pruebas y migración de datos necesarias:
Dependencia / tarea receptora:
```

B implementa el productor y genera contratos; A integra el consumidor. Si el cambio
rompe clientes anteriores, se divide en pasos compatibles o se reserva una ventana de
integración secuencial. No marcarlo `done` con la mitad ausente. Una nota en un archivo
no autoriza enviar mensajes a otros chats/servicios: seguir la autorización del usuario.

## Git e integración inicial

Al crear este proceso hay cambios locales de entregas anteriores, sin commits nuevos ni
push de la migración en esta sesión. Verificar Git antes de cada trabajo: esto es una
instantánea, no una condición permanente.

La preparación de la primera entrega publicable debe revisar esos archivos como base
común, separarlos de nuevos trabajos de A/B y comprobar que el conjunto compila. No
atribuirse todo el diff ni cometerlo como si fuera una sola tarea recién implementada.
Antes de integrar un commit en checkout compartido, los archivos incluidos deben estar
liberados por su propietario y el traspaso en `review`; no integrar archivos que A esté
editando. Preparar una base local identificable antes de mezclar nuevas entregas si
siguen presentes todos los archivos iniciales sin versionar.
Subir, crear PR o fusionar son acciones diferentes: ejecutar solo lo autorizado por el
usuario. Si aún no pidió subir, se puede preparar localmente la entrega y documentarla.

## Definición de terminado

- Resuelve el criterio de la tarea y respeta el objetivo Wi-Fi 2.4 GHz inicial.
- No hay pérdida silenciosa de datos ni resultados obsoletos presentados como actuales.
- Pruebas pertinentes y evidencia de UI/física según el tipo de cambio.
- Contratos y tipos sincronizados si cambiaron; consumidor compatible.
- Registro de traspaso completo, tablero y documentación comunes consolidados por B.
- Estado publicado/CI remota descrito solo si se verificó.
- Las limitaciones restantes están identificadas; no se confunden con otras fases completas.

## Instrucciones breves para arrancar dos sesiones

**Sesión A:** «Trabaja como agente A según AGENTS.md. Lee ambos registros, toma la siguiente
tarea A lista y limita tus cambios al ámbito de interfaz/editor. Deja un traspaso con pruebas».

**Sesión B:** «Trabaja como agente B según AGENTS.md. Lee ambos registros, toma la siguiente
tarea B lista y limita tus cambios a API/motor/contratos. Integra solo entregas revisadas
y actualiza los documentos compartidos».
