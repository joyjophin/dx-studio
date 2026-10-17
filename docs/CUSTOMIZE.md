# Make it yours

Start with `dx-studio init projects/demo --format 9:16` or `--format 16:9`.
The neutral explainer works without recorded narration or artwork.

Create a brand file:

```json
{"bg":"#F8F6F1", "ink":"#182126", "accent":"#286B62", "surface":"#FFFFFF", "highlight":"#D9F86F"}
```

Pass `--brand brand.json` at creation. Keys matching the scene's SCHEMA replace
its defaults. Other keys are retained in project.json for custom scenes and have
no effect until the scene exposes them. Colours and text remain editable.

In DX Editor, click a layer or pick it from Layers. Change its words, position,
scale, angle, opacity or visibility. Drag its timeline bar to change when it
appears. Captions have text, highlight and timing controls. **+ Text**, **+ Shape**
and **+ Media** add overlays. Save writes only differences into settings.json.

For new animation logic, ask the assistant to edit scene.py while preserving IDs
and settings.json. Expose parameters rather than baking text or colours into
images. The same Project renderer supplies editor preview and final export.

The supplied demo changes its headline between four beats. Its time parameters
control reveal animation and sounds; layer bars control visibility windows.
When moving an entire chapter, update its windows and cues together. Arbitrary
scene dependencies are not automatically recomposed by dragging one time field.

## Portrait and landscape

The explainer chooses different card dimensions, spacing, caption size and
headline placement for the two formats. Both produce full-resolution native
frames. It is a starting point for responsive scene code, not automatic intelligent
reframing of every future video. Review each composition independently.

## Sharing

Save first, then `dx-studio pack projects/demo --output outputs/demo.zip`.
The zip contains project source, assets, saved edits, engine source and notices.
It excludes render caches, output MP4 and hidden files. Recipients install the
bundled engine and open `project` in DX Editor. Treat scenes as executable code.

## Leave room for a presenter

Create with `--presenter bottom-left`, `bottom-right`, `left-half`, `right-half`,
or `bottom-band`. The default is `none`. In DX Editor, **Presenter layout** opens
**Composition**, where you can change the reservation and see its pixel dimensions.
**Safe zones** toggles the guide. Both included templates reflow graphics and
captions live; the guide is never exported. Save to keep the choice in the project.

The corners reserve 32% of width and 34% of height; halves reserve a full 50% side;
the bottom band reserves 40% of height. Every preset includes breathing room for
surrounding content. Custom scenes must consume `project.layout` to support reflow.
User transforms and added media can still overlap the guide.
[Full presenter layout guide](../reference/PRESENTER_LAYOUTS.md).
