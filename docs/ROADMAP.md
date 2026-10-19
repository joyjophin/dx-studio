# Roadmap

DX Studio's direction is to make strong explainers with an assistant and let the
creator finish the important details in DX Editor without rebuilding the video.

See the [creator workflows and feature plan](FEATURE_PLAN.md) for 48 proposed
improvements, real creator scenarios, delivery responsibilities, dependencies and
acceptance criteria. These are proposals, not shipped features or scheduled
promises. Current capabilities and limits are in [README.md](../README.md).

## Release milestones

- **v0.1.0:** publish the current editable explainer workflow, open source under
  MIT, with reproducible examples and clearly documented limits.
- **v1.0.0:** first full product launch. The planned v0.5 work is incorporated into
  this release, with guided setup/onboarding, clip trim/split, selection groups,
  reviewed folder recovery, portable backups, bounded preview caching and verified
  exports. The wider 48-item plan remains a backlog, not a launch-completion claim.

## Shipped foundation in v1.0

- **M02, motion controls:** visual named/custom Bézier easing, drag/keyboard/numeric
  curve handles, reusable local/JSON motion styles, selection staggering and a
  fade-only application option are implemented. Curves drive the shared transform
  progression; separate per-property value graphs and independent camera controls
  remain outside this increment. See [motion controls](MOTION.md).
- **F01, saving and project home:** autosave, browser draft recovery, named setting
  versions, automatic backups and stale-save protection are implemented. The project
  home adds creation, folder opening, searchable recents and thumbnails. See
  [saving and recovery](SAVING.md) and [workspace controls](WORKSPACE.md).
- **F02, everyday layer editing:** search, renaming, multi-selection, bulk movement
  and timing, lock/solo, alignment, distribution and snapping controls are implemented.
  Source-aware imported clip trimming/splitting and persistent selection groups are included;
  nested transform groups and broader track editing remain future work.
- **B02, media:** searchable project assets, metadata, thumbnails, reusable imports,
  per-file relinking/replacement and reviewed folder recovery for known missing sources are implemented.
- **X01, initial file preflight:** missing/unreadable imported media and configured
  audio files are checked before export. Sampled frame bounds/presenter collisions, font coverage and a fresh audio-mix
  review are also implemented; comprehensive text/overlap/gap analysis remains planned. See [media and file checks](MEDIA.md).
- **V01, listening foundation:** preview-mix waveforms, playback speed, monitor
  volume/mute and loopable audition ranges are implemented. Imported narration takes
  support replacement, draggable trims and timing, split/duplicate, relative levels,
  mute, music ducking and take audition.
  Correctable timed-word transcripts, optional cached English recognition and
  reviewed word-anchored layer/caption retiming are implemented. In-browser recording
  and speech removal/crossfade editing remain planned. See
  [audio workspace](AUDIO_WORKSPACE.md) and [narration](NARRATION.md).
- **Audio balance:** saved voice/music/effects/footage balances and mutes, with
  editable export loudness and true-peak targets, are implemented. Preview
  listening controls stay separate.
- **C01, caption revision:** reviewed SRT/VTT imports and exports, search, split/merge,
  offset tools and timing/density hints are implemented. Imported/recognized word timings now drive active-word captions. A supplied-script
  forced aligner, richer styles and pronunciation management remain planned. See [captions](CAPTIONS.md).
- **B01, palette foundation:** included palettes, named reusable colour/size presets,
  field-by-field application and JSON sharing are implemented. Copied font/logo assets, rights notes, portable brand kits and reusable selection
  templates are implemented. Broader brand rules remain planned. See [brand presets](BRAND_PRESETS.md).
- **F03/F04, workspace controls:** panel dividers, accessible size controls, canvas/timeline
  layouts and preview quality choices are implemented. Proxies and scene-range caching
  remain planned. See [view controls](VIEW.md).
- **X02, dependable jobs:** cancellation, settings snapshots, reloadable progress,
  isolated intermediates and atomic MP4 publication are implemented. Profiles, fps, selected ranges and caption modes with matching SRT are implemented.
  Queues and restart-resumable rendering remain planned. See [export jobs](EXPORTS.md).
- **Narration-led creator workflow:** storyboard notes and actual scene order,
  protected assistant patches with before/after frame previews, presenter recordings
  with per-scene layouts, and six editable explanation block types are implemented.
  See the [creator workflow](CREATOR_WORKFLOW.md) and its explicit first-version limits.
- The earlier v0.1.0 assets remain available unchanged. See [launch scope](V1_LAUNCH.md)
  and [release validation](VALIDATION.md) for v1.0 additions and evidence.

## Recommended sequence

1. **Dependable editing:** autosave/recovery, practical timeline and canvas
   controls, responsive previews, media relinking, preflight and reliable exports.
2. **Narration and assistant revisions:** waveform/transcript editing, replaceable
   voice takes, word-anchored visuals, caption alignment, protected manual edits
   and scene-level change previews. Add actual presenter placement and per-scene
   composition to complete the explainer workflow.
3. **Production range:** editable explanation blocks, richer motion, brand kits,
   recurring templates, screen tutorials, presenter production and deliberate
   landscape-to-portrait repurposing.
4. **Expansion:** reviewed language versions, advanced speech editing, feedback
   integrations and learning from real audience data.

The first signature workflow is replacing one narration take and improving one
scene with an assistant while preserving the creator's text, layout and timing
decisions. The feature plan defines a concrete fixture and acceptance criteria.

Before large implementations, propose a reproducible creator workflow in an
issue. Keep optional models/services separate from the local editing workflow,
and do not describe roadmap features as available before they ship.
