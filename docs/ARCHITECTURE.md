# Architecture

```text
Brief + skill → project.json + scene.py + assets
                              ↓
                      Project loader
                     ↙             ↘
              DX Editor           MP4 build
                  ↓                   ↑
           settings.json ──────────────┘
```

`project.json` declares dimensions, time, voice, audio mix, chapters and file paths.
`scene.py` declares typed SCHEMA parameters, LAYERS and deterministic `draw(c,t,p)`.
`setup()` caches expensive data after a parameter change. `cues()` declares SFX.
`settings.json` stores user differences, including layers, captions and media.
`format_version: 1` is explicit; unsupported versions fail before loading code.

The renderer paints arbitrary frames using Cairo. HarfBuzz shapes text and
FontTools supplies the exact bundled glyph outlines, so no fallback system font
can change glyph indices. FFmpeg encodes H.264 and AAC and masters the audio.
Frames render serially on the CPU. Performance depends on scene complexity.

`layers.py` evaluates transforms, enter/exit presets, keyframes, ordering and
selection outlines. `timemap.py` maps inserted/deleted timeline spans between
scene and output time. `project.py` merges defaults and saved edits. Layer IDs
are the stable interface: keep them when revising scenes.

`editor.py` serves the local UI, preview frames, state, media and build requests.
It binds loopback, validates Host/Origin, requires a custom mutation header and
limits request sizes. These are safeguards for a local single-user tool, not a
hosted-service security boundary. Loading a scene executes trusted Python.

Known limits: no hosted collaboration, GPU renderer, automatic fact checking,
guaranteed multilingual typography, automatic editing of arbitrary scene logic,
or universal portrait/landscape conversion. Optional TTS/transcription tools have
separate models and dependencies. Native Windows is not validated; use WSL2.

Presenter composition lives in `composition.py`. `Project.layout` resolves pixel
rectangles from the saved `__composition` choice before calling scene setup().
Responsive templates recalculate geometry; the browser draws separate guides.
The renderer never bakes those guides into exported video.

Development toward v0.5 adds `history.py`: durable setting snapshots and revision
checks around editor writes, with a process file lock for cooperating editors.
`editor-session.js` serialises autosaves and keeps per-tab browser drafts.
`settings.json` remains the CLI/bundle contract; `.dx-studio` is local working
history and is excluded from portable bundles. Versions do not copy source code
or media. See [saving and recovery](SAVING.md).
