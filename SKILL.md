---
name: dx-studio-video
description: Create animated explainers, tutorial videos, Shorts and video essays as editable DX Studio projects, with narration, captions, sound and separate selectable layers. Use for generating or revising videos in 9:16 or 16:9, including projects intended for DX Editor. Requires a coding environment; does not publish videos or manage social accounts.
---

# DX Studio video production

Deliver a video **and its editable project**. DX means DesignXstream; the toolkit is
`dx_studio`, the local visual editor is **DX Editor**. Support the user's subject,
audience and visual identity; no personal avatar, voice or channel style is required.

Use this skill with Claude, ChatGPT, Codex, or another assistant that can run Python,
read local files and inspect rendered images. When execution is unavailable, provide
the scene/project source and runnable instructions, and state that rendering was not verified.

## Start with the right resources

Read [PROJECT_FORMAT](reference/PROJECT_FORMAT.md) before writing a scene, and consult
[API](reference/API.md) for drawing helpers. Read only the relevant production guide:

| Job | Resource |
| --- | --- |
| Hooks, story structure, pacing and payoff | [ENGAGEMENT](reference/ENGAGEMENT.md) |
| Custom palette, type, accessibility and composition | [STYLE_NOTES](reference/STYLE_NOTES.md) |
| Recorded narration or optional local TTS | [VOICE_DRIVEN](reference/VOICE_DRIVEN.md) |
| Product footage and talking-head layouts | [FOOTAGE_SHORTS](reference/FOOTAGE_SHORTS.md) |
| Teaching video with several chapters | [TEACHING_LONGFORM](reference/TEACHING_LONGFORM.md) |
| Landscape product walkthrough | [LONGFORM_16x9](reference/LONGFORM_16x9.md) |
| Returning to manual edits or preparing an editor handoff | [EDITOR_HANDOFF](reference/EDITOR_HANDOFF.md) |
| Optional Figma UI kit | [FIGMA_TUTORIALS](reference/FIGMA_TUTORIALS.md) |

Templates live in `dx_studio/templates/`. The explainer is a complete 16-second,
voice-free demo that reflows for either ratio; starter is a minimal layered scene.
`kits/` contains optional specialised UI drawing helpers, copied beside `scene.py`
when needed. They are examples, not a requirement for a particular topic or style.

## Produce the video

1. **Brief.** Infer audience, format, duration, one central idea, tone and desired action
   from the request. For a new video, if presenter placement is not already known,
   ask one concise preference question before locking composition: “Will you add a
   talking head: none, bottom-left, bottom-right, left half, right half, or a bottom
   band?” Use the supplied dimensions or these presets. Continue script/research
   work while awaiting the answer. If the user asks you to make all decisions,
   state your layout assumption and proceed. Never ask again when it is specified. Respect an existing
   approved script. Use a short beat plan for substantial work; do not introduce an
   approval checkpoint when the user has already authorised full production.
2. **Story.** Open with a specific question, contradiction, result or visible problem.
   Demonstrate the mechanism and deliver the promised answer before a relevant closing
   action. Record voice lines and a beat sheet with time, narration, visual evidence,
   motion, captions, audio cue and editable layers. Keep a source list for factual claims.
3. **Create.** From the skill/repository root, install the package in a virtual environment
   (see [INSTALL](docs/INSTALL.md)). Run:
   ```sh
   python -m dx_studio init ./projects/my-video --format 9:16 --name "My video"
   # For landscape, choose --format 16:9 at creation.
   python -m dx_studio check ./projects/my-video
   ```
   Reserve presenter space at creation, for example:
   `python -m dx_studio init ./projects/my-video --format 16:9 --presenter left-half`.
   Read [PRESENTER_LAYOUTS](reference/PRESENTER_LAYOUTS.md) when reserving camera space.
   Use `--brand ./brand.json` for parameter defaults. Both ratios need deliberate
   composition; changing dimensions alone does not reflow an arbitrary custom scene.
4. **Narration.** Use the creator's recordings, a supplied voice track, no voice, or optional
   local TTS. Keep speech packages and model downloads optional; never install into a
   system Python. `scripts/tts.py` and `scripts/transcribe.py` document their downloads.
   Build timing from real audio. Generated word cues are estimates; do not describe them
   as forced alignment. Regenerate captions after narration changes.
5. **Scene.** Adapt the template using the contract below. Prefer geometry and visual
   demonstrations to walls of text. Expose the user's likely changes directly in DX Editor.
6. **Review.** Render stills at each beat and transition, inspect them, then run:
   ```sh
   python scripts/verify.py ./projects/my-video
   python scripts/framecheck.py ./projects/my-video 0.1
   ```
   Review the contact sheet, full-size frames, caption timing, reading time and the
   first/final frames. The checker detects errors; it cannot judge storytelling or prove
   visual quality. Fix every error; explain justified warnings. Preview both ratios when
   delivering both. Re-run affected checks after edits.
7. **Build and deliver.**
   ```sh
   python -m dx_studio build ./projects/my-video
   python scripts/novoice.py ./projects/my-video ./outputs/my-video-no-voice.mp4
   python -m dx_studio pack ./projects/my-video --output ./outputs/my-video-project.zip
   ```
   Deliver the MP4, portable project zip, voiceover sheet (text, timing, sources), and
   no-voice master when useful. Read [EDITOR_HANDOFF](reference/EDITOR_HANDOFF.md) when
   revising saved edits or delivering sidecar captions for the final edited timeline. Confirm
   output dimensions, duration, audio and completion before claiming success. Never
   claim a render or visual inspection that did not happen. `pack` preserves saved edits.
   Explain: extract the bundle, install its engine, run `python -m dx_studio edit project`.

## Keep the project editable

- Every independent visible element gets a stable `Layer` ID, meaningful label, accurate
  selection `box`, tight time window and linked `params`. Split headlines, annotations,
  diagrams, rows, captions and media. A group should not swallow its children's controls.
- On-screen words, palette and important cue times belong in `SCHEMA`. Read typed values
  from `p`. Keep background and decorative choices editable too.
- `draw(c,t,p)` must be deterministic and support arbitrary frame order. Cache expensive
  work in `setup(p,project)`. No incremental simulation or unseeded random draws.
- Use layer-relative animation around its default timing; the engine shifts a layer's
  clock when its bar moves. Tie SFX to `cues(p)` using `layer`. Hiding a layer silences
  its cues. Keep group/child IDs stable when revising existing projects.
- Captions come from `project.captions` in `setup()`. Draw them through their own layer
  and expose size, style and visibility. Never reread captions.json inside drawing code.
- Preserve `settings.json`: it contains the creator's text, transforms, captions, media
  and timing edits. Do not reset it or omit it from a handoff unless requested.
- Sticker artwork is opt-in. Add licensed PNGs in `assets/Avatars/`; declare poses as
  `clips` parameters or import them as media. Read [ASSETS](docs/ASSETS.md). A scene
  must work without a character unless the brief explicitly includes one.
- Derive highlights, arrows and crops from the same geometry that draws the subject.
  Keep captions and labels inside format-specific safe areas. Read `project.layout`
  in `setup()` for the active graphics, captions and presenter rectangles. Keep
  essential visuals, captions, pointers and stickers outside the presenter rectangle
  and its breathing room. The reserved rectangle stays blank for later compositing;
  do not bake in a placeholder, guide, presenter or label unless requested. Inspect
  every beat with the intended talking-head framing before delivering. Declare
  `RESPONSIVE_COMPOSITION=True` only when the scene actually reflows using this data.
  Existing templates do; arbitrary custom scenes must be adapted. User layer
  transforms and added media can still cross the guide and need review. Hold the camera still
  while the viewer reads. Make high-energy motion optional for accessible variants.
- Do not promise virality, invent statistics, fake product behaviour or imply platform
  endorsement. Research current claims when needed. Optimise clarity and retention;
  evaluate actual watch-time data when the creator provides it.
