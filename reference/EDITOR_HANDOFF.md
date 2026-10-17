# Revise and hand off an edited project

Read this when returning to a project that has been opened in DX Editor, or when
preparing the editable handoff. Keep the creator's changes usable after your work.

## Start from the saved project

Read project.json, scene.py and settings.json before revising an existing cut.
Load the installed engine's Project to inspect effective values and layer IDs;
settings contains differences from scene defaults, not necessarily the whole state.
Keep the existing environment unless the task needs an engine upgrade.

Layer IDs are stable identities. Display labels may have been renamed in the
editor; do not generate new IDs just because a label changed. Keep declared
parameter keys and media IDs when the element's role remains the same. A broad
source rewrite needs a recoverable source copy or the project's existing version
control: named editor versions contain settings, not Python or source assets.

Current development builds add saved `__layers[id].label` and `locked` fields.
Locks guard editor gestures; Python edits and global parameters can still affect
locked layers. Treat locks and saved overrides as evidence of manual intent when
revising. Preserve them where compatible with the requested change. Follow an
explicit user request to change them; otherwise explain a necessary conflict and
continue work that does not depend on resolving it.

## Keep layout and timing consistent

Use the active `project.layout` rectangles, not the original default presenter
reservation. User transforms and imported media can cross these rectangles, so
inspect the final composition after applying saved settings.

A parent layer's start offset already shifts its children's rendering clock.
Do not add the same offset to every child. Stored captions and cue times use
scene time; the watched output can differ after ripple cuts and holds. Use the
engine's time mapping when converting between them.

Source changes may alter selection boxes, defaults or built-in motion. Inspect
affected layers with saved transforms at the revised beats, not just a fresh
render using default settings. A settings-only version cannot undo a changed
scene implementation.

## Retain the right files

When replacing an imported source, keep its layer ID, box, timing, transform,
keyframes and deliberate audio controls. DX Editor's Media tools copy replacement
files into the project. Keep old sources needed by saved versions, even if the
current cut no longer uses them. Do not clean the assets folder by guessing what
looks unused. Portable bundles include source assets and saved settings.

Newer editors provide palette/size presets, layer solo, audition ranges and view
preferences. Solo and audition are preview tools; they do not define a partial or
muted export. Exit solo and inspect the complete video before delivery. Brand
presets match public parameter keys/types, so custom scenes may apply only a subset.

## Deliver captions for the actual edit

Use the installed CLI help to check for `captions` export support. When available:

```sh
python -m dx_studio captions ./projects/my-video --format srt --output ./outputs/my-video.srt
python -m dx_studio captions ./projects/my-video --format vtt --output ./outputs/my-video.vtt
```

These sidecars reflect saved editable captions and output-time cuts/holds. A
sidecar made directly from the original captions.json may disagree with the
finished edit. On older engines, deliver sidecars only after verifying their
output timing; do not imply that new editor commands exist in the v0.1 release.
Splitting a phrase proportionally is not word-level speech alignment.

## Leave a useful handoff

Include brief project notes with the actual format, duration, presenter reservation,
source/asset rights, narration files and the controls most likely to need revision.
Name the important layers and any deliberate overlaps or deviations. Give the
working open/build/pack commands for the supplied engine. Link to the relevant
editor guide instead of listing every possible control.

Verify that the MP4 is complete and matches the saved settings being delivered.
Current export jobs capture settings at launch; later saved edits need a new
export. Distinguish a browser preview from a completed render, and settings
versions from source backups. Preserve the existing scope of the user's task;
creating a project handoff does not authorise publishing the video.
