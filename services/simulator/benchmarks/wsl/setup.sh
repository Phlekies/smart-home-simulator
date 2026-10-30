#!/usr/bin/env bash
# Isolated Sionna RT environment inside WSL/Ubuntu for the B-102 evaluation. No sudo and
# nothing installed system-wide: the venv and libatomic live under ~/.cache/smart-home-simulator.
# Prerequisites: python3 (3.11+), an LLVM >= 18 shared library (Ubuntu 24.04 ships libLLVM-20.so
# with Mesa), and a pip wheel downloaded beforehand into <repo>/.local/wheels-pip, e.g. from
# Windows: .venv/Scripts/python.exe -m pip download --no-deps --dest .local/wheels-pip pip==25.2
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
CACHE="$HOME/.cache/smart-home-simulator"
VENV="$CACHE/sionna-venv"
WHEEL="$(ls "$REPO"/.local/wheels-pip/pip-*.whl 2>/dev/null | head -1 || true)"
[ -n "$WHEEL" ] || { echo "Missing pip wheel in $REPO/.local/wheels-pip" >&2; exit 1; }
mkdir -p "$CACHE"
[ -x "$VENV/bin/python" ] || python3 -m venv --without-pip "$VENV"
"$VENV/bin/python" "$WHEEL/pip" install -q --no-index "$WHEEL"
grep -E "^(pydantic|pydantic_core|annotated-types|typing-inspection|typing_extensions)==" \
    "$REPO/services/simulator/requirements-dev.lock.txt" > "$CACHE/pydantic-pins.txt"
"$VENV/bin/python" -m pip install -q "sionna-rt==2.2.0" -r "$CACHE/pydantic-pins.txt"
if ! ldconfig -p | grep -q "libatomic.so.1"; then
    # Dr.Jit needs libatomic; fetch the distro package and unpack it locally (no sudo).
    mkdir -p "$CACHE/libatomic/deb" && (cd "$CACHE/libatomic/deb" && apt-get download libatomic1)
    dpkg-deb -x "$(ls "$CACHE"/libatomic/deb/libatomic1_*.deb | head -1)" "$CACHE/libatomic/root"
fi
"$VENV/bin/python" -m pip check
"$VENV/bin/python" -m pip list 2>/dev/null | grep -i -E "^(sionna-rt|mitsuba|drjit|pydantic) "
