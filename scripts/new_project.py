"""Compatibility helper; prefer `dx-studio init`."""
import sys
from dx_studio.cli import main
if __name__ == '__main__': raise SystemExit(main(['init',*sys.argv[1:]]))
