"""Run the browser-independent autosave tests when a Node runtime is available."""
from pathlib import Path
import shutil
import subprocess
import pytest


def test_browser_autosave_session():
    node = shutil.which('node')
    if not node: pytest.skip('Node is optional locally; GitHub hosted runners exercise the browser session tests')
    root = Path(__file__).resolve().parents[1]
    subprocess.run([node, '--test', str(root/'tests/editor-session.test.cjs'), str(root/'tests/editor-tools.test.cjs')], cwd=root, check=True)
