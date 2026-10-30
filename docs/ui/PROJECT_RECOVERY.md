# Recuperación local — A-101

Entrega de interfaz del 2026-10-30 (Europe/Madrid), pendiente de integración por B.
No modifica el contrato de proyecto ni el backend.

## Comportamiento

- Cada cambio del proyecto programa una copia tras 500 ms de inactividad. Se valida con
  el endpoint existente `/api/projects/import` antes de sustituir la copia anterior.
- La copia guarda solo el proyecto canónico y su fecha: incluye notas y original Java,
  sin resultados, selección ni historial. Restaurar reinicia historial y exige recalcular.
- Al recargar/cerrar y volver a abrir, si existe una copia no se carga el ejemplo encima.
  Se ofrecen restauración, descarga del registro local y descarte para abrir el ejemplo.
- Una restauración fallida mantiene la copia y permite reintentarlo. Datos dañados,
  formatos/versiones desconocidos y límites de tamaño se explican antes de abrirlos;
  pueden descargarse sin modificarlos o descartarse explícitamente.
- Errores de validación, cuota o permisos no sustituyen la última copia disponible.
  La interfaz muestra el problema y permite reintentar. El guardado JSON manual continúa
  disponible. Durante una edición pendiente se solicita al navegador aviso de salida.
- Antes de escribir o descartar se comprueba si otra pestaña cambió la copia leída.
  Si hay discrepancia, se conserva y se recomienda exportar JSON y recargar.

## Almacenamiento y límites

`localStorage`, clave `smart-environment.project-recovery`, envoltura versión 1 con
`savedAt` y `project`. Límite del proyecto: 2 000 000 bytes UTF-8, coherente con el límite
de importación existente. La descarga «copia local» conserva la envoltura exacta para
diagnóstico/recuperación, incluso si está dañada; no sustituye al JSON de proyecto
exportado desde el editor, que es el archivo directamente importable.

Una copia por origen del navegador: cambiar de puerto, navegador o borrar sus datos
no conserva esa copia. No es un catálogo de proyectos ni una copia de seguridad externa.
Solo se llama a la API local configurada por el proyecto. No se envían datos a terceros.

La API debe estar disponible para guardar una nueva copia válida y restaurarla. Una
caída abrupta puede perder las ediciones posteriores a la última validación; el estado
visible distingue copia actualizada y trabajo pendiente. El aviso de salida depende del
navegador y no protege contra fallos del proceso/equipo. No se promete durabilidad absoluta.

La comprobación entre pestañas detecta cambios observables antes de la escritura; no es
una transacción ni un bloqueo atómico. La edición simultánea del mismo proyecto requiere
una futura política de concurrencia si se amplía este alcance.

## Evidencia

Pruebas automatizadas en `apps/web/src/editor/recovery.test.ts`: round-trip con datos Java,
datos dañados/versiones, tamaño en bytes, permisos, cuota/reintento, descarte selectivo,
cambios desde otra pestaña, validación fallida, respuestas desordenadas/canceladas y
normalización canónica. Usan almacenamiento y validación inyectables; no requieren otro
contrato ni dependencias nuevas.

Recorrido real en navegador con la API y Vite locales:

1. Apartamento: nombre `Prueba recuperación A-101`, X del termostato `7.125`; estimar.
2. Esperar estado «Copia local actualizada», recargar: aparece elección de recuperación.
3. Restaurar: nombre y X conservados, siete dispositivos, once paredes, siete notas;
   historial vacío, resultados anteriores ausentes y aviso de volver a estimar.
4. Exportar JSON: descarga real `entorno.shsim (1).json` completada.
5. Vaciar nombre: error de validación visible y aviso de conservar la última copia;
   corregir nombre: vuelve el estado actualizado sin intervención manual.
6. Recargar y descartar copia respaldada: se abre apartamento original, nombre inicial
   y X `7`, sin historial ni resultados. Nueva recarga ofrece la nueva copia del ejemplo.
7. Captura de esa pantalla: [recovery.jpg](recovery.jpg).

Los casos de cuota/datos dañados/versiones se verifican automáticamente; no se atribuye
su prueba a una manipulación real del almacenamiento del navegador. La captura utiliza
un ejemplo sintético del repositorio, no un plano del usuario.

Comandos y resultado final se registran en [la entrega de A](../process/AGENT_A.md).
B debe integrar la entrega y actualizar el tablero, STATUS y checklist M2; A no edita
esos archivos compartidos. No se da por terminada toda M2 ni la migración.
