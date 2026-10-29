"""Start both local services; terminate owned processes when stopped or on service failure."""

import importlib.util
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    node = shutil.which("node")
    vite = ROOT / "apps/web/node_modules/vite/bin/vite.js"
    if not node or not vite.exists() or importlib.util.find_spec("uvicorn") is None:
        raise SystemExit("Dependencies missing. Follow docs/migration/LOCAL_DEVELOPMENT.md using the project .venv.")
    processes = []
    def stop(_signum=None, _frame=None):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        for command, cwd in [
            ([sys.executable, "-m", "uvicorn", "smart_environment.api:app", "--host", "127.0.0.1", "--port", "8000"], ROOT),
            ([node, str(vite), "--host", "127.0.0.1", "--port", "5174", "--strictPort"], ROOT / "apps/web"),
        ]:
            processes.append(subprocess.Popen(command, cwd=cwd, creationflags=flags))
        print("Local interface: http://127.0.0.1:5174/\nAPI documentation: http://127.0.0.1:8000/docs\nCtrl+C stops both services.", flush=True)
        while True:
            for process in processes:
                if process.poll() is not None:
                    raise SystemExit(f"A service stopped (exit {process.returncode}); check the log above.")
            time.sleep(.25)
    except KeyboardInterrupt:
        print("Stopping local services...", flush=True)
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    main()
