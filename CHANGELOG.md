# Changelog

## Unreleased — toward 0.5.0

- Autosave editable settings with explicit save/failure status and browser draft recovery.
- Named setting versions, bounded automatic backups and recoverable restore/reset actions.
- Revision checks and editor write locks prevent stale saves from silently replacing newer edits.
- Durable atomic JSON writes and separately tested browser persistence logic.
- Project home with local recents, cached previews, search, and project creation for 16:9 or 9:16 with presenter space.
- Project-scoped navigation keeps editing sessions, media and saves separate.
- Layer search, editable names, multi-selection, inherited locks and preview-only solo.
- Bulk move, retime, show/hide, duplicate added layers and delete/hide actions.
- Alignment and equal spacing against the selection, frame or graphics safe zone; safe-zone fitting and a snapping toggle.
- Nested layer retiming and snapping respect parent timing without applying shifts twice.


- Media library with search/type/usage filters, metadata, thumbnails and reusable imports.
- Replace or relink imported media while keeping layer edits; sources remain available for undo and saved versions.
- Source-aware video/audio caches and graphics-safe placement for new imported media.
- Missing-media placeholders and actionable file preflight before editor or CLI exports.

- Preview-mix waveform with seeking, zoom/scroll and cached stereo peaks.
- Preview-only playback speed, volume/mute and loopable audition ranges with I/O shortcuts.

- Reviewed SRT/VTT file or pasted-text imports, plus sidecar exports matched to the edited timeline.
- Caption search, phrase split/merge, whole-set timing shifts, density/overlap hints and caption preflight findings.

## 0.1.0 — 2026-10-17

Initial public release of DX Studio (DesignXstream) and DX Editor.

- Presenter reservations, live template reflow, and safe-zone guides for portrait/landscape.
- Desktop editor width and verified wide screenshot.
- Installable Python package, diagnostic command and project scaffolding.
- Explainer and starter templates with explicit 9:16 and 16:9 layouts.
- Assistant-neutral skill, storytelling guide and customisation documentation.
- Personal artwork removed from public distribution; bring-your-own assets.
- Bundled font outlines, missing-word errors and repeatable audio generation.
- Portable bundles preserve saved edits and include matching engine source.
- Local editor request protections, containment checks and atomic settings writes.
- Automated regression tests, export smoke checks and GitHub Actions.
