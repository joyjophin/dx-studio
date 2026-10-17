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
- **v0.5.0 (next planned milestone):** develop the reliability and narration-led
  revision workflow below in small, reviewable increments. The wider 48-item
  feature plan guides prioritisation; individual items need acceptance checks
  before being included in the release. No release date is committed.

## Development progress toward v0.5.0

- **F01, saving foundation:** autosave, browser draft recovery and named editable-setting
  versions are implemented on `feat/project-recovery` for review. Automatic backups,
  restore safeguards and stale-save protection are included. See [saving and recovery](SAVING.md).
- The recent-project home and project thumbnails portion of F01 remains planned.
- Next: project navigation, then faster timeline/layer editing (F02).

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
