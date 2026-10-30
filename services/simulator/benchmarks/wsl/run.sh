#!/usr/bin/env bash
# Run a Python script/command with the isolated WSL Sionna environment from the repository root.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
CACHE="$HOME/.cache/smart-home-simulator"
export DRJIT_LIBLLVM_PATH="${DRJIT_LIBLLVM_PATH:-$(ls /usr/lib/x86_64-linux-gnu/libLLVM-*.so 2>/dev/null | sort -V | tail -1)}"
[ -d "$CACHE/libatomic/root" ] && export LD_LIBRARY_PATH="$CACHE/libatomic/root/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PYTHONPATH="$REPO/services/simulator/src"
cd "$REPO"
exec "$CACHE/sionna-venv/bin/python" -u "$@"
