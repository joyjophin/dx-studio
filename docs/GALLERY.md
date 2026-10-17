# Recreate the gallery

README screenshots come from the working DX Editor. The animation and format
examples come from the same Project renderer used for exports. No third-party
product screenshots, personal artwork or generated UI mockups are used.

## Open the full-frame example

After [installation](INSTALL.md):

```sh
python -m dx_studio init projects/gallery --format 16:9 --name "Editable explainer"
python -m dx_studio edit projects/gallery
```

Use a wide desktop window. The repository captures use a 1600 × 900 viewport.
**Text** exposes the scene's words. In **Layers**, select Opening headline to see
its selection handles and transform controls. In **Captions**, select a phrase
for its text, highlight and timing controls. The screenshots show existing
controls and the included fictional demonstration, rather than a finished
narrated production or a claim about measured audience engagement.

## Reserve presenter space

```sh
python -m dx_studio init projects/presenter --format 16:9 --presenter left-half
python -m dx_studio edit projects/presenter
```

Open **Presenter layout**. The half-frame screenshot uses `left-half`; the corner
screenshot uses `bottom-right`. **Safe zones** shows the graphics, caption and
presenter rectangles. Guides are editor overlays and do not appear in the export.

## Render the editing loop

```sh
python scripts/render_showcase.py
```

This creates a temporary project from the explainer template, renders four edits,
and writes `docs/images/editable-demo.gif` plus four PNG stills. Each frame holds
for two seconds. These are source-parameter changes, not a screen recording:

1. Original scene.
2. Headline changed to “My story. My final cut.”
3. Accent changed to green.
4. The third example row hidden with its layer visibility setting.

The sequence is silent and deliberately holds the scene time fixed so the edits
are easy to compare. Use `python -m dx_studio build` for a complete MP4 production.

## Render both formats

```sh
python -m dx_studio init projects/portrait --format 9:16
python -m dx_studio init projects/landscape --format 16:9
python -m dx_studio still projects/portrait 9
python -m dx_studio still projects/landscape 9
```

The template's source lives in
[dx_studio/templates/explainer/scene.py](../dx_studio/templates/explainer/scene.py).
The project folder can be bundled with `dx-studio pack` after saving edits.
