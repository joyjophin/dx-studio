#!/usr/bin/env bash
DX_ROOT="$(cd "$(dirname "$0")" && pwd)"
bash "$DX_ROOT/launch.sh" "$@"
DX_RESULT=$?
if [ "$DX_RESULT" -ne 0 ]; then
  printf '\nPress Return to close this window.'
  read -r _DX_DISMISS
fi
exit "$DX_RESULT"
