# Assistant revisions in current development builds

Use this contract for a settings-only revision requested from DX Editor. It does
not execute generated Python, contact a provider or grant publishing permission.
For source edits, also read [EDITOR_HANDOFF](EDITOR_HANDOFF.md).

1. Read the exported request: `request`, `scene`, `selected_ids`, effective `values`,
   `protected`, `source_revision` and `response_contract`. Infer the smallest set of
   changes that fulfils the request; keep source identities and unrelated edits.
2. Return JSON with `format_version:1`, the exact `source_revision`, and `changes`.
   Each change names an existing values path, an exact `before`, an `after` and a
   short explanation in `label`. Array positions are zero-based. Do not replace a
   whole container when a field change will do, and do not overlap paths.
3. The editor checks current values, protected sections/takes/layers, canvas locks,
   relevant parent/child relationships and the source fingerprint. Conflicts require
   a revised proposal against the current request. Do not tell the creator to
   overwrite settings or remove protections to force a stale change through.
4. The creator can compare frames at the playhead and apply selected changes. The
   resulting whole project is validated before values are returned. Saved versions
   cover settings; they do not revert changed Python or assets.

For a request whose title is `One clear idea`, a response can be:

```json
{
  "format_version":1,
  "source_revision":"COPY_THE_REQUEST_FINGERPRINT",
  "changes":[
    {"path":["title"],"before":"One clear idea","after":"Show how it works",
     "label":"Make the headline promise a visible explanation"}
  ]
}
```

Use the actual existing field and exact before value. Do not return this example
literally. The fingerprint hashes project configuration, scene source and caption
source; changes to saved settings are compared per field, allowing unrelated manual
edits to survive. Media content changed outside the project is not covered by that
source hash; preserve project-owned sources and review replacements separately.

Narration revisions keep `__voice` IDs and source-relative trims. A transcript's
`file` binds its word IDs to that recording; replaced sources need fresh timings.
Use the Transcript review flow for `__anchors` and generated caption timing. Word
matches must be unique and caption sequences consecutive; do not infer missing
words or present proportional phrase splits as measured alignment.

Story ranges and layer/caption starts remain in original source time. A first
`__timeline` reorder maps source ranges to playback order, followed by any ripple
edits. Export `__export.range` is in edited output time. Per-scene presenter presets
are in `__presenter.scenes`; responsive sources consume `project.layout` in setup.
For generated explanation blocks, preserve block and primitive IDs so subsequent
data changes remain editable.
