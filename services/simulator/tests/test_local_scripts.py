"""Python-only installation (B-131): start.py prepares only what is missing; the package is self-contained."""

import importlib.util
import sys
import zipfile
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


start = load("start")
package = load("package_local")


def test_venv_python_matches_the_platform(tmp_path):
    expected = "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
    assert start.venv_python(tmp_path) == tmp_path / expected


@pytest.mark.parametrize("dist, sources, npm, plan", [
    (True, True, True, "ready"),     # compiled interface present: never rebuilt by default
    (False, True, True, "build"),    # source checkout with Node: build once
    (False, True, False, "missing"),  # source checkout without Node: explain how to get a package
    (False, False, True, "missing"),  # package without dist (broken): never try to build
])
def test_web_step_depends_on_what_is_in_the_folder(tmp_path, monkeypatch, dist, sources, npm, plan):
    web = tmp_path / "apps" / "web"
    (web / "dist").mkdir(parents=True)
    if dist:
        (web / "dist" / "index.html").write_text("<!doctype html>", encoding="utf-8")
    if sources:
        (web / "package.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(start, "WEB", web)
    monkeypatch.setattr(start.shutil, "which", lambda name: "npm" if npm else None)
    assert start.web_plan() == plan
    if plan == "missing":
        with pytest.raises(SystemExit, match="package_local.py"):
            start.ensure_web()


def test_python_step_installs_only_when_needed(tmp_path, monkeypatch):
    python = start.venv_python(tmp_path)
    python.parent.mkdir(parents=True)
    python.write_text("", encoding="utf-8")
    monkeypatch.setattr(start, "VENV", tmp_path)
    commands = []
    monkeypatch.setattr(start, "run", lambda command, cwd=start.ROOT: commands.append([str(c) for c in command]))
    monkeypatch.setattr(start, "python_ready", lambda _: True)
    assert start.ensure_python() == python and commands == []
    monkeypatch.setattr(start, "python_ready", lambda _: False)
    start.ensure_python()
    assert [c[3:5] for c in commands] == [["install", "-r"], ["install", "--no-deps"]]
    assert commands[0][-1].endswith("requirements-dev.lock.txt") and commands[1][-1].endswith("simulator")


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    """Minimal source tree, so the test needs no compiled interface in the real checkout."""
    root = tmp_path / "checkout"
    for name in ("services/simulator/src/smart_environment/serve.py",
                 "services/simulator/src/smart_environment/__pycache__/serve.cpython-313.pyc",
                 "services/simulator/tests/test_x.py", "services/simulator/pyproject.toml",
                 "services/simulator/requirements-dev.lock.txt", "services/simulator/examples/template.json",
                 "apps/web/dist/index.html", "apps/web/src/App.tsx", "apps/web/node_modules/x/index.js",
                 "examples/smart-apartment.shsim.json", "scripts/start.py", "scripts/dev.py", "LICENSE",
                 ".venv/Scripts/python.exe"):
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text("x", encoding="utf-8")
    monkeypatch.setattr(package, "ROOT", root)
    return root


def test_package_holds_what_start_needs_and_nothing_else(checkout, tmp_path):
    target = package.build(tmp_path / "out", "app")
    names = set(zipfile.ZipFile(target).namelist())
    for required in ("app/scripts/start.py", "app/apps/web/dist/index.html", "app/LEEME.txt", "app/LICENSE",
                     "app/services/simulator/pyproject.toml", "app/services/simulator/requirements-dev.lock.txt",
                     "app/services/simulator/src/smart_environment/serve.py", "app/examples/smart-apartment.shsim.json"):
        assert required in names
    assert not [n for n in names if "__pycache__" in n or n.endswith(".pyc") or "/tests/" in n or ".venv" in n
                or "node_modules" in n or n.startswith("app/apps/web/src") or n.endswith("dev.py")]


def test_package_refuses_to_build_without_the_compiled_interface(checkout):
    (checkout / "apps" / "web" / "dist" / "index.html").unlink()
    with pytest.raises(SystemExit, match="npm --prefix apps/web run build"):
        package.files()


def test_the_real_package_lists_existing_paths_only():
    missing = [entry for entry in package.CONTENTS
               if entry != "apps/web/dist" and not (package.ROOT / entry).exists()]
    assert missing == [], "CONTENTS must follow the repository layout"
