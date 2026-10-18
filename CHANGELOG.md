# Changelog

## 0.5.0.dev0 — unreleased development toward 0.5.0

- Fix default 9:16 graphics/captions shifted 50px left: equal 130px side margins centre the existing 820px content band on a 1080px canvas. Update portrait generation/review guidance in the skill; explicit custom safe areas and saved offsets remain respected.
- Shared System/Light/Dark appearance preference for the dashboard and editor, with live system changes, browser persistence and tab synchronization. Dark controls, dialogs and timeline tracks preserve video and export colours.
- Project-focused dashboard with preview cards, search and compact creation/open dialogs.
- Light editor shell with six primary tool groups, a large preview, playback below the canvas and a contextual selection inspector.
- Scene-focused text controls, compact media cards and collapsed secondary caption/inspector controls reduce initial options.
- Compact scene/audio/caption timeline with expandable graphics tracks; advanced tools and project actions live in menus.
- Narrow-desktop layout swaps the tool browser for the selected layer inspector without covering the preview; existing edits and export contracts are preserved.

- Correctable source-relative word transcripts, optional cached local English ASR, active-word captions and reviewed word-linked layer/caption retiming.
- Conflict-aware assistant settings patches with protected decisions, current/proposed frame comparisons and validation before applying selected changes.
- Storyboard scene notes and playback reordering, preserving source clocks and remapping visuals, captions and audio; reorder precedes ripple cuts/holds.
- Actual presenter-video placement, cover/contain crop, source trim/audio controls and per-scene responsive layout presets.
- Editable comparison, steps, flow-diagram, quote, CSV bar-chart and title/sponsor blocks, plus portable selection templates with copied dependencies and new IDs.
- Project-owned TTF/OTF roles, logo placement, asset-credit notes and reviewed portable brand ZIPs.
- Saved source/1080p/720p profiles, output fps, selected-range exports and burned/clean/SRT caption modes with matching audio and sidecar timing.
- Background sampled frame/font/audio review, actionable findings, intentional warning dismissals and rollback-safe video/sidecar publication.

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

- Reusable brand presets with included palettes, selected-field application, custom style capture and portable JSON import/export.
- Compatible-field matching and scene size limits preserve unrelated content; named presets use atomic writes and a shared writer lock.
- Explainer captions keep a dark backing when a light text colour is chosen.

- Adjustable inspector and layer-list dividers, keyboard resizing and canvas/timeline workspace layouts.
- Saved browser view preferences and preview quality choices, with a delayed rendering status.

- Cancellable export jobs with page-reload progress recovery, settings snapshots and stale-job cancellation protection.
- Completed MP4s survive failed/cancelled jobs; successful exports publish atomically from isolated intermediates.
- Concurrent media decodes use locked, completed caches; output paths cannot overwrite referenced sources.

- Assistant handoff guidance preserves manual edits, stable identities, media needed by versions and output-timed sidecars.
- Development package/CLI versions are distinct from v0.1; release packaging uses versioned directories and refuses to overwrite existing artifacts.

- No-narration exports reuse completed MP4s with isolated temporary audio; an optional flag also mutes footage audio.

- Editable imported narration takes with replacement, source trims, scene timing, relative levels, mute and music ducking.
- Saved narration overrides travel in portable projects and are used by preflight, exports and no-narration variants.

- Inspector scrolling and timeline placement stay within the viewport when the recovery banner is hidden.
- Direct narration timeline movement and edge trims, split/duplicate at playhead, take audition and narration snapping targets.

- Saved voice/music/effects/footage balance and mute controls, with export loudness and true-peak targets separate from preview monitoring.

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
