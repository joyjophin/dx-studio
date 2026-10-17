#!/usr/bin/env bash
# Run from any directory. System packages are documented in docs/INSTALL.md.
set -euo pipefail
DX_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 -m venv "$DX_ROOT/.venv"
"$DX_ROOT/.venv/bin/python" -m pip install -e "$DX_ROOT[dev]"
"$DX_ROOT/.venv/bin/python" -m dx_studio doctor
