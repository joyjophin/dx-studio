# Style is a project choice

DX Studio has no mandatory channel identity, colour palette, avatar, voice or CTA.
Start with the supplied neutral demo, then adapt it to the brief. The product name
DX expands to DesignXstream; this does not require videos to display DX branding.

Use `--brand brand.json` to set matching SCHEMA defaults such as `bg`, `ink`,
`accent`, `surface` and `highlight`. These remain editable in DX Editor. Add brand
fonts deliberately by updating the scene's text configuration and shipping their
licence; the built-in toolkit uses bundled DX Sans outlines derived from Inter.

For 1080×1920, the default content bounds are x=130–950, y=170–1560;
captions use x=130–950, y=1370–1550. Equal 130px side margins keep the 820px-wide
composition centred at x=540. Derive horizontal placement from `project.layout`
so headline, visual-group and caption centres agree. For an intentionally asymmetric
safe area or presenter half, centre within the available region instead of forcing
everything to the frame centre. Preserve internal left-aligned labels where useful.
For 1920×1080, start with 96 px side margins,
64 px top/bottom margins, and a clear caption band. Platform overlays change:
these are starting composition guides, not verified platform specifications.

Older projects may explicitly store the former portrait bounds x=80–900, whose
centre is x=490. When asked to recenter such a project, preserve `settings.json`
and change only those default horizontal bounds to x=130–950 in both
`project.json` safe-area rectangles; keep their vertical values. Re-render and
review saved layer offsets. Custom scenes must consume `project.layout` for this
to reflow. An intentional custom safe area or existing art direction takes priority.

Use portrait stacks and landscape side-by-side compositions where appropriate.
Rework labels, crop, spacing and typography for each format. The supplied explainer
supports both through explicit geometry; custom scenes need the same care.

Aim for readable type and strong contrast. Use real contrast measurements where
teaching accessibility. Keep illustrations labelled when they could be mistaken
for real data or product output. Avoid unnecessary motion and supply a calmer
version when the audience or brief calls for one.

Before delivery inspect stills at the hook, each reveal, transitions, payoff and
final hold. Check long text edits, caption wrapping, selection outlines, safe
areas and overlap. Run the verifier, inspect the full-size output, and explain
any limitations instead of calling every result production-ready automatically.
