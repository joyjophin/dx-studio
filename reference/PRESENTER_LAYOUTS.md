# Compose around a talking head

Ask about this preference while briefing a new video if it is not already known.
A presenter composited later needs deliberate empty space; a guide alone does
not make an existing full-frame animation safe.

| Preset | Presenter reservation | Template composition |
| --- | --- | --- |
| `none` | None | Use the format's content/caption safe areas |
| `bottom-left` | Bottom-left 32% width × 34% height | Graphics and captions in a band above the presenter |
| `bottom-right` | Bottom-right 32% width × 34% height | Graphics and captions in a band above the presenter |
| `left-half` | Full left 50% of the video | Graphics and captions on the right |
| `right-half` | Full right 50% of the video | Graphics and captions on the left |
| `bottom-band` | Bottom 40% of the video | Graphics and captions above; useful for vertical videos |

All reservations are relative to the actual frame dimensions. A gap equal to 3%
of the shorter frame edge supplies breathing room. The engine returns rectangles
in pixels as `[left, top, right, bottom]`, never `[x, y, width, height]`.

```sh
python -m dx_studio init projects/lesson --format 16:9 --presenter left-half
python -m dx_studio edit projects/lesson
```

In DX Editor choose **Presenter layout** or the **Composition** tab. **Safe zones**
toggles the graphics, caption and presenter guides. The included starter and
explainer reflow immediately; the preference is saved in settings.json and included
in portable bundles. The project default lives in project.json:

```json
{"composition": {"presenter": "left-half"}}
```

## Custom scenes

Declare `RESPONSIVE_COMPOSITION = True` only after implementing reflow. In
`setup(p, project)`, read `project.layout['content']`, `['captions']` and
`['presenter']`. Recalculate positions, text widths, caption wrapping and sizes
from those rectangles. Use callable layer boxes so selection follows the new
geometry. The template scene demonstrates the full pattern.

The engine does not crop or scale an arbitrary scene automatically. Unsupported
scenes show a clear guide-only notice in the editor. For a different presenter
footprint, use a custom `safe_area` and scene layout; do not label a default preset
as an exact fit for footage with different framing.

## Final review

Render each story beat with the selected layout. Essential graphics, captions,
callouts and stickers should clear the reserved region. Check reading size as
well as overlap; squeezing a complete diagram into half the frame can require
rewriting the shot. The verifier warns about selection boxes that intersect the
reservation, but visual inspection is still necessary.

A blank presenter zone is part of the video composition. Guides and their labels
are editor overlays only and never appear in the MP4. Adding actual presenter
footage, masking it, or changing the camera crop is a separate production decision.
User moves, scale edits and added media can cross the safe area; review them before
export. To deliver several presenter positions, build and inspect each version.
