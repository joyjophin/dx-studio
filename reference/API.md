# dx_studio API (import with `from dx_studio import *`)

Colours are `(r, g, b, a)` tuples in 0–1. `hexc('#7846EB')` makes one; `mixc(c1, c2, u)` blends two.
Times are in seconds. `c` is a `cairo.Context` in frame pixels (1080 × 1920 unless `project.json` says otherwise).

## Time and easing
| function | notes |
|---|---|
| `P(t, a, b, ease=eo)` | 0 → 1 as t goes from a to b, eased. The core animation primitive. |
| `lerp(a, b, u)`, `clamp(x, lo=0, hi=1)` | |
| `eo`, `eio`, `ei`, `lin` | ease-out, ease-in-out, ease-in, linear |
| `back_ease(u, s=1.7)` | overshoot, for tactile moments |
| `window(t, a, b, c, d, ease)` | rise from a to b, fall from c to d |

## Text (HarfBuzz-shaped Inter)
| function | notes |
|---|---|
| `text(c, s, x, y, size, w='semi', col, a=1, align='l'\|'c'\|'r', track=0, maxw=None)` | y is the baseline. Returns the width. `maxw` shrinks the text to fit. |
| `ktext(c, s, x, y, size, w, col, t, t0, a=1, align='c', track=-0.02, stagger=0.022, dur=0.38, rise=26)` | per-glyph kinetic reveal starting at t0 |
| `tw(s, size, w, track=0)` | text width |

Weights: `reg`, `med`, `semi`, `bold`, `xb`. Tabular figures: `med_t`, `xb_t`.

## Shapes and effects
| function | notes |
|---|---|
| `rrect(c, x, y, w, h, r)` | path only; then `fill(c, col, a)`, `fillp(...)` (keeps the path) or `stroke(c, col, width, a)` |
| `card(c, x, y, w, h, r, a=1, col=WHITE, border=None, sh=1)` | rounded card with a soft two-layer shadow |
| `shadow(c, x, y, w, h, r, a=1, strength=1)` | shadow only (cached) |
| `check(c, cx, cy, r, frac, col=WHITE, a=1, wdt=None)` | checkmark drawn to `frac` (0–1) |
| `star(c, cx, cy, ro, ri, rot=0)` | path |
| `glow(c, cx, cy, r0, r1, col, a)` | radial glow |
| `arrow_curve(c, [p0, c1, c2, p1], col, a, wdt=3.2, frac=1, head=True)` | hand-drawn-style curved arrow |
| `sparks(c, cx, cy, t, t0, n=8, r0=30, r1=70, col, dur=0.45, wdt=4)` | burst of short rays at t0 |
| `make_bg(top, bottom, blobs, w, h)` | pre-rendered gradient with soft blobs `[(x, y, r, col, alpha)]`; call it in `setup()` |
| `Motes(n=14, seed=3).draw(c, t, col, freeze_after)` | quiet drifting background shapes |

## Stickers and GIFs (from the project's `assets/`)
| function | notes |
|---|---|
| `draw_avatar(c, pose, cx, cy, size, t, t_in, t_out, mirror=False, bob=True, a=1)` | pop-in with overshoot, idle bob, pop-out |
| `draw_walker(c, t, t0, t1, x0, x1, ybottom, height=340, mirror=False, name='walking')` | walks a sticker across the frame |
| `draw_gif(c, name, x, y, w, h, t, t0, t1, speed=1, color=VIOLET, a=1)` | plays once, holds the last frame; the strokes are recoloured |

## Captions
`draw_captions(c, t, caps, cx=540, cy=1462, backing, edge, color, highlight, size=50, maxw=720)`: pass `project.captions`, stored in `setup()`.

## Layers
`Layer(id, label, draw, box, start, end, group, params=[], motion=None, children=[], child_ctx=None, alive=None, locked=False, help=None)`

Call `render_layers(c, t, p, LAYERS)` inside `draw()`. See PROJECT_FORMAT.md for the full contract.

## Voice timings
`VT = VoiceTimes(__file__)`, then `VT.start(i)`, `VT.end(i)`, `VT.dur(i)`, and `VT.word(i, 'word', occurrence=0)`.

## Parameters in a scene
`p.key` gives the typed value: colour → tuple, time/number → float, point → `(x, y)` or `None`, clips → a list of objects with `.start`, `.end` and fields. `p.raw('key')` gives the stored JSON value.

## Sounds for `cues(p)`
`chime`, `click`, `tap(level)`, `slide(dur, level, lo, hi)`, `paper`, `stamp`, `tick`, `rise(dur)`, `pop(level)`, `step(level)`, `scribble(dur, level)`.

Each cue is `{"sound", "at", "gain"?, "layer"?, ...kwargs}`.

## Timing notes (added)

- `VoiceTimes.word(i, 'word', occurrence=0)` **estimates** a word's time from its character position in the line.
  It is close for Kokoro lines; for human recordings use `assets/words.json` from `scripts/transcribe.py`
  (`[[line, word, start, end], ...]`) and look words up directly (see VOICE_DRIVEN.md). A word that isn't in the line
  raises `ValueError`, including a missing requested occurrence.
- `tw('')` returns 0 in this version (it used to raise inside text-measuring helpers).
- `make_bg(top, bot, blobs, w=1080, h=1920)`: pass `w=1920, h=1080` for 16:9 projects.
