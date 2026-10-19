# Revise and hand off an edited project

Read this when returning to a project that has been opened in DX Editor, or when
preparing the editable handoff. Keep the creator's changes usable after your work.

For the same-chat file workflow and editor-created JSON skeleton, read
[AI_HANDOFF](AI_HANDOFF.md). The editor’s **Continue with AI** prepares the brief;
**Review file updates → Reload AI changes** adopts completed source revisions.

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

DX Studio v1.0 add saved `__layers[id].label` and `locked` fields.
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

DX Studio v1.0 expose effective narration through `project.voices()`
and saved `__voice` takes. Preserve take IDs, trims, timing, levels and mute when
replacing recordings. `VoiceTimes` and speech-authoring scripts still read the
original project voice list; updating that list does not replace saved narration
overrides by itself. DX Studio v1.0 can propose word-linked timing after a new
timed transcript, with explicit conflict/protection review; see
[ASSISTANT_REVISIONS](ASSISTANT_REVISIONS.md). Inspect both source and saved values before
revising spoken content. Saved `__mix` balance, mute and mastering controls also
override the original mix defaults; keep them unless the requested revision
changes the audio balance.

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


## Current creator workspace state

Preserve `__groups`, `__story`, `__anchors`, `__protected`, `__presenter`, `__blocks`,
`__brand_assets`, `__export` and `__quality_ignores` when revising a project.
Read [PROJECT_FORMAT](PROJECT_FORMAT.md) for their clocks and contracts. A reorder
is a source-to-output mapping, not permission to rewrite original timing fields.
Keep complete block IDs so data updates remain possible. Portable templates and
brand kits copy their dependencies; retain required font licences and credits.

A saved export range/profile changes the CLI build too. Check its output clock,
caption mode and filename before producing delivery files. A clean mode removes
engine-managed captions only. Review the mastered MP4 and current job's sidecar;
sampled preflight results are useful findings, not a full-frame quality certificate.

Portable ZIPs include all non-cache project source files and may include unused
assets. Review what you share. `verify-bundle` checks the manifest without executing
Python. Preserve the included engine for reproduction; test upgrades on a copy.
Older settings versions are excluded by default and can be included for a backup.
