# Project compatibility and upgrades

v1.0 keeps `project.json.format_version` at **1**. Existing v0.1 and development
projects receive defaults for newer settings. Their explicit canvas sizes, safe
areas and saved offsets are retained. New portrait projects use symmetric 130px
horizontal margins; existing authored layouts are not silently rewritten.

Keep a full project copy or portable backup before an engine upgrade. Named
settings versions restore editable values; they do not roll back scene.py,
project.json, source media or fonts. For a portable backup, include older settings
versions explicitly. Ordinary handoffs exclude them.

A project ZIP includes its matching engine and an `OPEN-ME.md`. Install that engine
to reproduce the project. Test upgrades on a separate copy. Older engines may
ignore newer editable keys; do not save a v1.0 project with an older engine and
assume every feature will survive. Unsupported project format versions fail with
an explicit error instead of being interpreted as version 1.

The ZIP's `DX-BUNDLE.json` records engine version, project format and SHA-256 for
all included files. `dx-studio verify-bundle project.zip` checks integrity without
extracting or executing scenes. Hashes detect changes relative to the manifest;
they are not a signature or an assurance that arbitrary Python is safe. Existing
older bundles without a manifest remain usable with their original instructions,
but cannot receive a v1.0 manifest verification result.

Projects must keep required paths inside the project folder. Custom Python may
read additional dependencies the asset scanner cannot infer; include and review
those yourself. Fonts, footage, stickers and optional model licences remain the
creator's responsibility. No model weights are bundled by default.

For missing sources, folder recovery copies unambiguous known references to their
original locations without overwriting existing files. It does not guess among
duplicate filenames. Moving a project changes its browser draft key; flush saved
edits before moving, or download a pending recovery draft first.
