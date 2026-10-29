# Ejecutar la nueva aplicación local

La interfaz se abre en un navegador; la API y los cálculos se ejecutan en el mismo
ordenador. No requiere cuenta, publicación ni servidor externo. Instalación de
dependencias requiere Internet; el recorrido básico posterior utiliza recursos locales.
Solo se enlaza a `127.0.0.1`, no a todas las interfaces de red.

## Preparación (Windows / PowerShell)

Desde `C:/Simulador_smart_homes3D/smart-home-simulator`:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r services/simulator/requirements-dev.lock.txt
.venv/Scripts/python.exe -m pip install --no-deps --no-build-isolation -e services/simulator
npm.cmd --prefix apps/web ci
```

La instalación editable necesita setuptools en el entorno (incluido en el lock).
No hace falta activar el entorno ni cambiar la política de ejecución de PowerShell.
Entorno inicial probado: Windows x64, Python 3.13.7, Node 22.20.0. Las versiones
resueltas están en el lock Python y `apps/web/package-lock.json`. Otros entornos
se deben verificar antes de anunciar soporte.

## Arranque conjunto

```powershell
.venv/Scripts/python.exe scripts/dev.py
```

Abrir http://127.0.0.1:5174/ . API interactiva: http://127.0.0.1:8000/docs .
Ctrl+C detiene los procesos creados por el lanzador. Si un puerto está ocupado, el
servicio falla de forma visible; no se busca un puerto alternativo silenciosamente.

Para desarrollo también pueden ejecutarse en dos terminales:

```powershell
.venv/Scripts/python.exe -m uvicorn smart_environment.api:app --host 127.0.0.1 --port 8000
```

```powershell
npm.cmd --prefix apps/web run dev
```

## Comprobaciones

```powershell
.venv/Scripts/python.exe -m pytest services/simulator/tests -q
.venv/Scripts/python.exe scripts/export_contracts.py --check
npm.cmd --prefix apps/web run check
npm.cmd --prefix apps/web run build
npm.cmd --prefix apps/web test
```

Si cambias modelos/contratos, regenerar y revisar el diff:

```powershell
.venv/Scripts/python.exe scripts/export_contracts.py
npm.cmd --prefix apps/web run contracts
```

El JSON Schema describe la representación canónica serializada, con todos los campos
normalizados. La API también acepta los valores por defecto definidos por Pydantic.
No editar los tipos generados a mano. JSON de API limitado a 2 MB; las escenas también
tienen límites explícitos de dispositivos, enlaces y paredes en el contrato.

## Recorrido de prueba

1. Abrir apartamento, oficina o almacén.
2. Seleccionar un dispositivo; cambiar X a un decimal y la altura.
3. Ejecutar estimación; revisar ida, vuelta y motivos de «sin verificar».
4. Cambiar un parámetro: los resultados anteriores desaparecen.
5. Inspeccionar la vista 3D; regresar al plano para arrastrar dispositivos.
6. Guardar JSON, abrirlo y comprobar posiciones y datos originales conservados.
7. Crear proyecto nuevo, añadir dos equipos y un enlace; completar parámetros conocidos.
8. Pulsar **Dibujar pared** y elegir inicio/final en el plano. La creación ajusta a 0.1 m;
   Escape cancela. Seleccionar una pared para cambiar centro, longitud, ángulo, altura,
   espesor o material; se puede seleccionar también desde la lista de paredes y en 3D.
9. Arrastrar una pared y pulsar **Deshacer** una vez: se recupera la posición anterior.
   **Rehacer** restaura el movimiento. Atajos: Ctrl/Cmd+Z, Ctrl/Cmd+Shift+Z y Ctrl/Cmd+Y.
   Las flechas desplazan el objeto del plano enfocado 0.1 m; Shift usa pasos de 1 m.
10. Cambiar material y simular: comprobar el cambio de pérdidas en enlaces que cruzan la
    pared. Las propiedades avanzadas del material se comparten con todas sus paredes;
    al editarlas se marcan como hipótesis del usuario sin calibración.

Las pruebas nativas de Node verifican historial, agrupación de gestos, límites y
transformaciones. Los tests `.test.ts` se ejecutan con Node 22 y strip-types; no forman
parte del typecheck de la interfaz. El historial se reinicia al abrir otro proyecto o
crear uno nuevo. La recuperación automática y la imagen de plano calibrada siguen pendientes;
guardar JSON manualmente antes de recargar o cerrar la aplicación.

El estimador no calcula tráfico, Mbps reales o latencia. Las versiones Sionna RT y
ns-3 aún no están integradas. Su ausencia no activa una sustitución automática.
Las notas Java indican qué se ha inferido; rellenar campos no demuestra compatibilidad
funcional de un producto comercial.

## Java sigue disponible

`gradlew.bat run` y `gradlew.bat test` conservan su funcionamiento original. Su entorno
se mantiene separado del nuevo stack; la migración no elimina ninguna fuente Java.

## Linux/macOS

Sustituir `.venv/Scripts/python.exe` por `.venv/bin/python` y `npm.cmd` por `npm`.
La CI de migración verifica Linux/Python 3.13; instalación de escritorio y aceleración
por GPU tienen su propia puerta de aceptación y no están terminadas.
