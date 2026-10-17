# Assets, replacements and rights

The public distribution excludes the original creator's 37 character poses and
8 GIF stickers. Those private files are preserved outside this repository. The
included templates use vector shapes and fonts only and require no replacements.

To use your own character pack, add transparent PNGs to a project's
`assets/Avatars/`. The filename stem is the pose ID (`thinking.png` → `thinking`).
Existing `draw_avatar` and `clips` APIs retain the Avatars directory convention
for compatibility. An avatar can be a mascot, illustration or product cutout.
Use names and poses appropriate to your pack, not the private example filenames.

For ordinary overlays choose **+ Media** in DX Editor. PNG, JPEG, WebP, GIF and
video layers can be positioned, scaled, hidden and retimed. Built-in sound effects
and the music bed are synthesised; no commercial sample pack is bundled.

For each external asset record its filename, author, source URL, licence and any
required attribution in `assets/ATTRIBUTION.md`. Keep model weights out of source
control. MIT covers the DX Studio code and original documentation, not imported
artwork, recordings, font software, product trademarks or optional speech models.
See [third-party notices](../THIRD_PARTY_NOTICES.md).

When replacing assets, preserve filenames or update every scene/schema reference.
Inspect transparency, aspect ratio, selection boxes and caption overlap. The
creator should have permission to use and share the asset before bundling it.
