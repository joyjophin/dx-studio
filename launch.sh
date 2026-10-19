#!/usr/bin/env bash
# Guided local setup; system package installation remains an explicit user action.
set -euo pipefail
DX_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$DX_ROOT"
if [ "$(uname -s)" = Darwin ]; then export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"; fi
trap 'printf "\nDX Studio could not start. Read the message above and docs/INSTALL.md.\n" >&2' ERR
DX_PYTHON="${DX_STUDIO_PYTHON:-python3}"
DX_REPAIR=0
if [ "${1:-}" = --repair ]; then DX_REPAIR=1; shift; fi
if ! command -v "$DX_PYTHON" >/dev/null 2>&1; then
  printf 'Install Python 3.10 or newer, then open DX Studio again. See docs/INSTALL.md.\n' >&2
  exit 1
fi
"$DX_PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else "Python 3.10 or newer is required.")'
if [ "$(uname -s)" = Darwin ]; then
  if [ -n "${DX_STUDIO_CAIRO_LIB:-}" ]; then
    export DYLD_FALLBACK_LIBRARY_PATH="$DX_STUDIO_CAIRO_LIB${DYLD_FALLBACK_LIBRARY_PATH:+:$DYLD_FALLBACK_LIBRARY_PATH}"
  else
    for DX_LIB in /opt/homebrew/lib /usr/local/lib; do
      if [ -f "$DX_LIB/libcairo.2.dylib" ]; then
        export DYLD_FALLBACK_LIBRARY_PATH="$DX_LIB${DYLD_FALLBACK_LIBRARY_PATH:+:$DYLD_FALLBACK_LIBRARY_PATH}"
        break
      fi
    done
  fi
fi
if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  printf 'FFmpeg is needed to open and export videos.\nmacOS: brew install ffmpeg cairo python\nUbuntu / WSL2: sudo apt install ffmpeg libcairo2 python3-venv\nThen open DX Studio again.\n' >&2
  exit 1
fi
if [ ! -x "$DX_ROOT/.venv/bin/python" ]; then
  printf 'Creating your local DX Studio environment…\n'
  "$DX_PYTHON" -m venv "$DX_ROOT/.venv"
fi
DX_FINGERPRINT="$("$DX_PYTHON" -c 'import hashlib,pathlib; print(hashlib.sha256(pathlib.Path("pyproject.toml").read_bytes()).hexdigest())')"
if [ "$DX_REPAIR" = 1 ] || [ ! -f .venv/.dx-installed ] || [ "$(cat .venv/.dx-installed)" != "$DX_FINGERPRINT" ]; then
  printf 'Installing DX Studio dependencies (internet required on first setup)…\n'
  if [ "$DX_REPAIR" = 1 ]; then
    "$DX_ROOT/.venv/bin/python" -m pip install --force-reinstall -e "$DX_ROOT"
  else
    "$DX_ROOT/.venv/bin/python" -m pip install -e "$DX_ROOT"
  fi
  printf '%s' "$DX_FINGERPRINT" > .venv/.dx-installed
fi
"$DX_ROOT/.venv/bin/python" -m dx_studio doctor
if [ "${1:-}" = --doctor ]; then exit 0; fi
exec "$DX_ROOT/.venv/bin/python" -m dx_studio edit "$@"
