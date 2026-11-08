"""Prepare and start the local application with Python only (B-131).

    python scripts/start.py                  # prepare what is missing, then serve on 127.0.0.1:8000
    python scripts/start.py --port 8010
    python scripts/start.py --prepare-only   # leave everything ready without starting

Each step is skipped when it is already done:
1. ``.venv`` in this folder with the simulator and its pinned dependencies
   (``services/simulator/requirements-dev.lock.txt``); this is the only step that needs Internet;
2. the compiled interface in ``apps/web/dist``: a package made by ``scripts/package_local.py``
   already has it, and a source checkout builds it once with Node if Node is installed;
3. ``python -m smart_environment.serve`` from that ``.venv``, listening on 127.0.0.1 only.

Nothing is installed outside this folder and nothing runs in the background after it stops.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"
LOCK = ROOT / "services" / "simulator" / "requirements-dev.lock.txt"
WEB = ROOT / "apps" / "web"
MINIMUM_PYTHON = (3, 11)


def venv_python(venv: Path | None = None) -> Path:
    return (venv or VENV) / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def run(command: list[str | Path], cwd: Path = ROOT) -> None:
    print("→", " ".join(str(part) for part in command), flush=True)
    subprocess.run([str(part) for part in command], cwd=cwd, check=True)


def python_ready(python: Path) -> bool:
    probe = subprocess.run([str(python), "-c", "import fastapi, pydantic, uvicorn, smart_environment"],
                           cwd=ROOT, capture_output=True)
    return probe.returncode == 0


def ensure_python() -> Path:
    if sys.version_info < MINIMUM_PYTHON:
        raise SystemExit(f"Se necesita Python {MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]} o posterior.")
    python = venv_python()
    if not python.exists():
        run([sys.executable, "-m", "venv", VENV])
    if not python_ready(python):
        run([python, "-m", "pip", "install", "-r", LOCK])
        run([python, "-m", "pip", "install", "--no-deps", "--no-build-isolation", "-e", ROOT / "services" / "simulator"])
    return python


def web_plan(rebuild: bool = False) -> str:
    """'ready', 'build' or 'missing': what step 2 has to do in this folder."""
    if (WEB / "dist" / "index.html").is_file() and not rebuild:
        return "ready"
    if (WEB / "package.json").is_file() and shutil.which("npm") is not None:
        return "build"
    return "missing"


def ensure_web(rebuild: bool = False) -> None:
    plan = web_plan(rebuild)
    if plan == "missing":
        raise SystemExit("Falta la interfaz compilada (apps/web/dist). Usa el paquete creado con "
                         "scripts/package_local.py, que ya la incluye, o instala Node una vez y repite.")
    if plan == "build":
        npm = shutil.which("npm")
        if not (WEB / "node_modules").is_dir():
            run([npm, "ci"], cwd=WEB)
        run([npm, "run", "build"], cwd=WEB)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Prepara y arranca la aplicación local solo con Python")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--prepare-only", action="store_true", help="dejarlo todo listo sin arrancar")
    parser.add_argument("--rebuild-web", action="store_true", help="volver a compilar la interfaz con Node")
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles and redirected logs default to cp1252
    python = ensure_python()
    ensure_web(args.rebuild_web)
    if args.prepare_only:
        print(f"Listo. Para arrancar: {python} -m smart_environment.serve --port {args.port}", flush=True)
        return
    try:
        run([python, "-m", "smart_environment.serve", "--port", str(args.port)])
    except KeyboardInterrupt:
        print("Servicio detenido.", flush=True)


if __name__ == "__main__":
    main()
