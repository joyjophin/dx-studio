# DX Studio project format

A **DX Studio project** is a folder that the dx_studio tools can check, render, build and open in the visual editor:

```
my-video/
  project.json      what the video is: size, length, voice, music, captions, chapters
  scene.py          how it looks: SCHEMA (editable parameters), setup(), draw(), cues()
  assets/           Avatars/*.png stickers, GIFs/*.gif, any images the scene uses
  vo/               voiceover lines (optional)
  captions.json     timed captions (optional)
  settings.json     the user's edits, written by the editor (never hand-authored)
```

Commands, after installing the package in your virtual environment:

```bash
python3 -m dx_studio check  projects/my-video          # validates everything, renders a test frame
python3 -m dx_studio still  projects/my-video 1.5 4 9  # stills + contact sheet in projects/my-video/stills/
python3 -m dx_studio build  projects/my-video          # final MP4 (mix, master to target loudness, render, mux)
python3 -m dx_studio edit   projects/my-video          # visual editor
```

## project.json

| key | meaning |
|---|---|
| `format_version` | project contract version; 1 in this release |
| `brand` | optional SCHEMA default overrides |
| `composition.presenter` | default presenter reservation; see PRESENTER_LAYOUTS.md |
| `name`, `description` | shown in the editor |
| `width`, `height`, `fps`, `duration` | output format (seconds) |
| `final_hold` | seconds of stillness at the end; idle motion freezes here (default 0.8) |
| `scene` | scene file (default `scene.py`) |
| `assets` | sticker/asset folder (default `assets`) |
| `captions` | caption file (default `captions.json`) |
| `output` | MP4 file name |
| `chapters` | `[[start, end, "label"], …]`: labelled bands on the editor timeline |
| `safe_area` | `{"content": [x0,y0,x1,y1], "captions": [x0,y0,x1,y1]}` for the editor overlay |
| `voice` | `[{"file": "vo/00.wav", "start": 0.3, "text": "…", "duck": "deep", "gain": 1.1}, …]`. `duck: "deep"` lowers the music further under that line |
| `music` | synthesised bed: `bpm`, `level`, `chords` (MIDI), `roots`, `final_chord`, `final_root`, `final_arp`, `final_at`, `thin` (`[[t0,t1]]` sparser sections), `perc_from`, `end_fade_at`. Or `{"file": "music.wav", "level": 0.3}` |
| `mix` | `duck` (music level under voice, 0–1), `duck_deep`, `loudness` (LUFS, default −14), `peak` (dBTP, default −1.2) |

## captions.json

A list of `{"start": s, "show_end": s, "text": "…", "hl": "phrase to highlight" | null}`. Captions are drawn by the scene with `dx_studio.draw_captions(c, t, CAPS, …)` so their style belongs to the project.

## scene.py

```python
from dx_studio import *

SCHEMA = [
    {"key": "accent", "type": "color", "label": "Accent", "group": "Palette", "default": "#7846EB"},
    {"key": "title",  "type": "text",  "label": "Title", "group": "Opening", "default": "Hello", "at": 1.0},
    {"key": "t_pop",  "type": "time",  "label": "Title pops in", "group": "Opening", "default": 0.8},
    {"key": "characters", "type": "clips", "label": "Characters", "panel": "Characters",
     "label_field": "pose", "fields": [
        {"key": "pose", "type": "sticker", "label": "Pose"},
        {"key": "size", "type": "number", "label": "Size", "min": 120, "max": 460, "step": 5, "unit": "px"},
        {"key": "pos",  "type": "point",  "label": "Position", "auto_label": "scene default"},
        {"key": "mirror", "type": "bool", "label": "Mirror"}],
     "default": [{"pose": "thumbs-up", "start": 2.0, "end": 4.0, "size": 280, "pos": None, "mirror": False}]},
]

def setup(p, project):      # optional: called on load and after every edit
    ...                     # precompute backgrounds, layouts, derived colours

def draw(c, t, p):          # required: draw the frame at t seconds (c is a cairo.Context, full resolution)
    ...

def cues(p):                # optional: sound effects that follow the parameters
    return [{"sound": "pop", "at": p.t_pop}] + [{"sound": "pop", "at": k.start} for k in p.characters]
```

`p` gives typed values: `p.accent` → `(r, g, b, a)`, `p.t_pop` → float seconds, `p.characters` → list of clips with `.start .end .pose .size .pos .mirror` (`pos` is `(x, y)` or `None` for "let the scene decide"). `p.raw("accent")` returns the stored JSON value.

### Parameter types

| type | value | editor control |
|---|---|---|
| `time` | seconds | number field + draggable ◆ on the Beats lane |
| `number` | float (`min`, `max`, `step`, `unit`) | slider + field |
| `color` | `"#RRGGBB"` | colour picker |
| `text` | string (`at` = seconds to jump to when editing) | text field |
| `bool` | true/false | checkbox |
| `choice` | one of `options` | dropdown |
| `point` | `[x, y]` or `null` (`auto_label`) | drag on the preview |
| `sticker` | file name in `assets/Avatars` (no extension) | thumbnail picker |
| `clips` | list of `{start, end, …fields}` | a timeline lane of draggable, resizable blocks + a panel |

Common keys: `key`, `type`, `label`, `default`, `group` (sub-heading), `panel` (editor tab; defaults to Timing / Text / Colours / Settings by type, or the clip list's own label), `help`.


## Layers (recommended)

Build the scene from named layers and the editor can select every element on the preview, move / scale / rotate / fade it, retime it, hide it, keyframe it, and give it an entrance or exit, with no extra schema work.

```python
from dx_studio import *

def draw_title(c, t, p):  ktext(c, p.title, 540, 520, 84, 'xb', p.ink, t, p.t_title)
def draw_card(c, t, p):   card(c, 160, 700, 760, 420, 40)
def draw_check(c, t, p):  check(c, 540, 870, 90, P(t, p.t_card+0.4, p.t_card+0.8, eo), p.accent)

LAYERS = [
    Layer('title', 'Title', draw_title, box=(140, 440, 800, 110), start=0.0, group='Opening', params=['title', 't_title']),
    Layer('card', 'Card', draw_card, box=(160, 700, 760, 420), start=1.0, group='Card', children=[
        Layer('check', 'Checkmark', draw_check, box=(450, 780, 180, 180), start=1.5, group='Card')]),
]

def draw(c, t, p):
    ...background...
    render_layers(c, t, p, LAYERS)          # can be called more than once, e.g. with characters in between
```

`Layer(id, label, draw, box, start, end, group, params, motion, children, child_ctx, alive, locked, help)`:

| argument | meaning |
|---|---|
| `draw(c, t, p)` | draws the element in frame coordinates (or its parent's space). `t` is the timeline time **shifted by however far the user moved the layer**, so absolute-time animation code follows the layer bar automatically |
| `box` | `(x, y, w, h)` or a function of `t`: the selection outline and the pivot for scale/rotation |
| `start`, `end` | default time window. The layer draws only inside it, so start it where the element first appears |
| `group` | label shown in the Layers list |
| `params` | keys of SCHEMA parameters that belong to this element; the editor shows them when it's selected |
| `motion(c, t)` | the element's own built-in movement (applied before the user's transform, inherited by children) |
| `children`, `child_ctx(c, t)` | nested layers; `child_ctx` applies a clip/translate first (e.g. a phone screen) |
| `alive(t)` | whether the element is actually visible at `t` (click-selection ignores it otherwise) |
| `locked` | not selectable itself (e.g. a camera "stage" that holds everything) |

Every layer automatically gets, in `settings.json` under `__layers`: start/end, visible, x/y offset, scale, rotation, opacity, keyframes (`[{t, x, y, scale, rotation, opacity, ease}]`, `t` relative to the layer's start; eases `ease`, `ease-in`, `ease-out`, `linear`, `back`, `hold`), and entrance/exit presets (`fade`, `pop`, `zoom`, `slide-up/down/left/right`) with durations.

Current development editors also save optional display `label` and `locked` fields.
Labels do not change stable IDs. Locks cover direct layer editing, including descendants
of a locked parent; global parameters and scene source still affect those layers.
Read [EDITOR_HANDOFF](EDITOR_HANDOFF.md) before revising a manually edited project.

A sound cue can name its layer, `{"sound": "stamp", "at": p.T_ST1, "layer": "card_b"}`, so the sound moves when the layer is moved and goes silent when it's hidden.

## Captions and media are editable automatically

- If a project has `captions.json`, the editor edits captions as the `__captions` parameter: text, highlight, start/end, add, and delete. Scenes read the current captions from `project.captions` inside `setup(p, project)`, and should not re-read the file.
- Every project accepts user media (`__media`): PNG, JPG, WEBP, GIF and MP4 files added in the editor become layers drawn above the scene. Videos' own sound is mixed into the build. Nothing is needed in `scene.py` for this.

## Elements, arrangement and ripple edits (automatic)

- `__media` also holds user **text** and **shape** elements (`kind: "text" | "shape"`). They are drawn above the scene as layers, like imported media.
- Every layer state may carry `order`, its z-order among siblings, set by bring forward / send back.
- `__timeline` holds **ripple edits**: `{"op": "insert", "at", "dur"}` (hold a frame) and `{"op": "delete", "start", "end"}`. The editor and build work in *output time*. The scene always receives *scene time*, and all stored times stay in scene time, so scenes need no changes. Audio is remapped the same way, and the music is regenerated at the output length.

## Rules for editable scenes

1. **Every visible element is a layer, and every on-screen string, colour and key moment is a parameter.** Split drawing per element (a card, a headline, a row, a sticker annotation) rather than one big function. If a value is written as a literal inside `draw()`, the editor can't touch it.
2. **Derive, don't duplicate.** Tints, shadows and backgrounds should be computed from palette parameters in `setup()`, so one colour change restyles everything consistently.
3. **Tie dependent motion to its parameter.** If a checkmark ticks 1.35 s after a chip lands, write `T_CHIP + 1.35`, not `38.45`. Then dragging `T_CHIP` moves the whole sequence.
4. **Sounds come from `cues(p)`.** Reference the same parameters, and link each cue to its layer, so sounds move with the visuals.
5. **`draw()` must be a pure function of `t` and the parameters.** No state carried between frames, so the editor can jump anywhere instantly.
6. **Keep frames fast.** Aim for under 60 ms at full size. Pre-render heavy things (blurred backgrounds, shadows) in `setup()` or cache them. Draw at full resolution; the editor handles scaling.
7. **Check with stills before building.** Use `python3 -m dx_studio still …`.

## Toolkit (import with `from dx_studio import *`)

- **Time and easing:** `P(t, a, b, ease)` goes from 0 to 1 between times a and b. Also `lerp`, `mixc`, `window`, and the easing curves `eo` / `eio` / `ei` / `lin` / `back_ease`. `hexc` converts a hex string to a colour.
- **Text:** `text` (HarfBuzz-kerned) and `ktext` (kinetic, per-glyph reveal). `tw()` measures text width. Font keys are `reg`, `med`, `semi`, `bold`, `xb`, plus `med_t` and `xb_t` for tabular figures.
- **Shapes:** `rrect`, `fill`, `fillp`, `stroke`, `shadow`, `card`, `check`, `star`, `glow`, `arrow_curve`, `sparks`. `make_bg` builds a gradient with soft blobs, and `Motes` draws quiet drifting background shapes.
- **Stickers:** `draw_avatar` pops a sticker in with an overshoot, bobs it idly, then pops it out. `draw_walker` walks a sticker across the frame, and `draw_gif` plays a GIF recoloured to any colour.
- **Captions:** `draw_captions`.
- **Sounds for `cues()`:** `chime`, `click`, `tap`, `slide`, `paper`, `stamp`, `tick`, `rise`, `pop`, `step`, `scribble`. Run `python3 -m dx_studio sounds` for the list.


Sticker pose names in examples require your own matching licensed PNGs. No character pack is bundled. The default templates use no stickers.


## Presenter composition

The loader adds `__composition` (a choice parameter in the Composition panel).
It defaults to `project.json` → `composition.presenter`, or `none`, and is saved
non-destructively in settings.json. `Project.layout` provides graphics, captions
and presenter rectangles in pixels. Scenes opting into responsive composition
use these rectangles in setup() and update their selection boxes. See
[PRESENTER_LAYOUTS](PRESENTER_LAYOUTS.md) for the contract and presets.
