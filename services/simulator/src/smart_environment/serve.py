"""Serve the compiled web interface and the API from one local process (B-128).

Running it needs only Python and the simulator's dependencies: the interface is compiled once
(``npm --prefix apps/web run build``, the only step that needs Node) and its ``dist`` folder is
served next to the API on loopback. The web calls ``/api`` on its own origin, so nothing else
has to run. Without a compiled interface it stops with the command to build one.

    python -m smart_environment.serve [--port 8000] [--dist apps/web/dist]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.routing import Mount

from .api import ROOT, app

DIST = ROOT / "apps" / "web" / "dist"
HOST = "127.0.0.1"  # local data stays local: never listen on other interfaces


def mount_web(target: FastAPI, dist: Path = DIST) -> Mount:
    """Serve ``dist`` at ``/`` after every API route, so ``/api`` keeps answering first."""
    if not (dist / "index.html").is_file():
        raise SystemExit(f"No hay interfaz compilada en {dist}.\n"
                         "Compílala una vez con Node: npm --prefix apps/web run build")
    target.mount("/", StaticFiles(directory=dist, html=True), name="web")
    return next(route for route in target.routes if isinstance(route, Mount) and route.name == "web")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Interfaz compilada y API en un solo proceso local")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--dist", type=Path, default=DIST, help="carpeta de la interfaz compilada")
    args = parser.parse_args(argv)
    mount_web(app, args.dist)
    import uvicorn

    print(f"Interfaz y API: http://{HOST}:{args.port}/ · documentación: http://{HOST}:{args.port}/docs\n"
          "Ctrl+C detiene el servicio.", flush=True)
    uvicorn.run(app, host=HOST, port=args.port)


if __name__ == "__main__":
    main()
