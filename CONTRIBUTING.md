# Contributing

Start with a reproducible issue or a focused pull request. Describe the viewer or
editor problem and include a minimal project when possible. Do not attach assets
you cannot redistribute. New features should preserve the editable-project contract.

```sh
python -m pip install -e '.[dev]'
python -m pytest
python scripts/smoke_test.py
python -m build
```

The smoke test exports short videos in both formats and decodes the results.
It requires Cairo, FFmpeg and ffprobe. Tests cover rendering, saved edits, hit
selection, captions, cue timing, bundles and local editor request protections.
Review full-size frames for visual changes; a passing unit test does not prove
that a composition reads well. Include tests for meaningful new behaviour.

Preserve stable layer IDs and version the project format if its meaning changes.
Keep scene drawing deterministic, assets optional and setup local to a virtual
environment. Avoid network access in core rendering and tests.

By contributing, you agree to license your contribution under MIT. Font changes
must comply with the included OFL. Be respectful and specific in reviews; critique
the work rather than the contributor. Security reporting: see SECURITY.md.

Autosave session tests use the Node built-in test runner through pytest when Node
is available (including the GitHub hosted runner). Node is not required to use DX
Studio. See [saving and recovery](docs/SAVING.md) for the development workflow.
