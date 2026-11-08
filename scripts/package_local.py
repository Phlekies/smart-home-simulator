"""Zip the local application with its compiled interface, for people without Node (B-131).

    python scripts/package_local.py [--output build/local-app] [--name smart-environment-local-0.1.0]

Needs ``apps/web/dist`` (``npm --prefix apps/web run build``). The zip holds only what
``scripts/start.py`` needs: the simulator sources and pinned dependencies, the compiled
interface, the Java examples served by ``/api/examples``, the scripts, the licence and a short
guide. No project of the person, no virtual environment and no build cache goes in. Unzip it
anywhere and run ``python scripts/start.py``.
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENTS = ["services/simulator/src", "services/simulator/pyproject.toml",
            "services/simulator/requirements-dev.lock.txt", "services/simulator/examples",
            "apps/web/dist", "examples", "scripts/start.py", "LICENSE"]
SKIPPED_PARTS = {"__pycache__", ".pytest_cache"}
SKIPPED_SUFFIXES = {".pyc", ".pyo"}
GUIDE = """Smart Environment · aplicación local

Requisito: Python 3.11 o posterior. No hace falta Node.

1. Abre una terminal en esta carpeta.
2. Ejecuta: python scripts/start.py
   La primera vez crea .venv aquí e instala las dependencias fijadas (necesita Internet).
3. Abre http://127.0.0.1:8000/ en el navegador. Ctrl+C detiene el servicio.

Todo se ejecuta en este ordenador y solo escucha en 127.0.0.1.

Límites: estimación de trayecto directo, sin calibración experimental. No garantiza la
conexión ni el funcionamiento de un producto. Un margen positivo no es una recomendación de compra.
"""


def version() -> str:
    text = (ROOT / "services" / "simulator" / "pyproject.toml").read_text(encoding="utf-8")
    return re.search(r'^version = "([^"]+)"', text, re.MULTILINE).group(1)


def files() -> list[Path]:
    if not (ROOT / "apps" / "web" / "dist" / "index.html").is_file():
        raise SystemExit("Falta apps/web/dist: compila antes la interfaz con npm --prefix apps/web run build")
    found = []
    for entry in CONTENTS:
        path = ROOT / entry
        if not path.exists():
            raise SystemExit(f"Falta {entry}")
        candidates = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
        found += [p for p in candidates
                  if not SKIPPED_PARTS & set(p.relative_to(ROOT).parts) and p.suffix not in SKIPPED_SUFFIXES]
    return found


def build(output: Path, name: str) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    target = output / f"{name}.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files():
            archive.write(path, f"{name}/{path.relative_to(ROOT).as_posix()}")
        archive.writestr(f"{name}/LEEME.txt", GUIDE)
    return target


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Empaqueta la aplicación local con la interfaz compilada")
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "local-app")
    parser.add_argument("--name", default=f"smart-environment-local-{version()}")
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    target = build(args.output, args.name)
    print(f"Paquete: {target} ({target.stat().st_size / 1e6:.1f} MB)", flush=True)


if __name__ == "__main__":
    main()
