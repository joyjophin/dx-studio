# Recreate the gallery

The current gallery uses **Make it click**, an original ten-second DX Studio film.
Both formats are native compositions, not crops. The scene, score and artwork can
be regenerated locally without a model, account or downloaded media.

[Watch, customise and render the showcase →](../examples/showcase/README.md)

## Render the film and artwork

After [installation](INSTALL.md), from the repository:

```sh
python scripts/render_showcase.py --build --stills --gallery
```

The two projects and verified full-HD masters live in `outputs/showcase`.
The gallery pass writes posters for all four beats, the format comparison,
landscape and portrait GIFs, and a storyboard to `docs/images`.
Use a new `--output` folder to preserve an edited project.

## Capture the working editor

```sh
python -m dx_studio edit outputs/showcase/landscape
```

Use a wide desktop window; the current captures use the browser's native
1280 × 720 viewport. Dismiss the first-use guide, open **Text**, and seek to:

- **0.9 s:** the opening sculpture and editable headline.
- **2.9 s:** the resolved mesh on citron.
- **5.9–6.0 s:** the poster and its editable words.

For the layer capture, open **Media → Layers**, select **Ivory poster**, then
collapse the tool panel. The inspector and actual transformed selection handles
remain visible. Its child typography and artwork inherit the parent transform.

Open the companion portrait folder through **Projects → Open project** and repeat
at 5.9 s. The dashboard capture shows only these two original demo projects in a
separate local project library; it contains no personal project footage.

`showcase-edit.gif` holds two actual editor captures: the original “Yours.” headline
and the same scene after changing it to “Editable.” in Text. Undo restores the
master. This is an interaction comparison, not a continuous screen recording.

## Asset map

| Asset | Source |
| --- | --- |
| `showcase-landscape.gif`, `showcase-portrait.gif` | Real final MP4s, sampled at 15 fps from 0.45 s so their first frame has a readable headline; no audio. |
| `showcase-<format>-<beat>.png` | Native project renders at 1.35, 3.45, 6.35 and 9 seconds. |
| `showcase-formats.png` | Uncropped native renders arranged on an editorial sheet. |
| `showcase-storyboard.jpg` | Four landscape beat frames. |
| `showcase-social.png` | A 1280 × 640 brand variant rendered from the opening scene. |
| `showcase-editor-*.jpg` | Actual browser captures from DX Editor. |
| `showcase-dashboard*.jpg` | Actual project dashboard in system/dark and light appearances. |
| `showcase-edit.gif` | Two actual editor states held for comparison. |

Earlier feature-specific screenshots remain in the documentation history and image
folder where they support individual feature guides. The README leads with this
consistent, original showcase. No third-party product screenshots or UI mockups
are presented as DX Studio.
