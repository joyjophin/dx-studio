# Maintainer release

v1.0.0 is the first full product launch; the planned v0.5 work is incorporated.
Keep the release title distinct from earlier v0.1 preview downloads.

## Release gates

- Finish the [launch scope](V1_LAUNCH.md), inspect both ratios in the editor and
  document actual checks in [VALIDATION](VALIDATION.md).
- Run critical regression checks and one full release suite. Export and fully
  decode both formats, including presenter reservations. Verify narration/media
  timing and portable save/reopen against the matching packaged engine.
- Install the wheel/source in a fresh virtual environment, run doctor, and open
  a sample. Record OS/dependency limits without implying a clean-machine or new-user
  study that was not performed.
- Check MIT/OFL notices, archive contents and local documentation links. Exclude
  caches, local projects, credentials, personal media and model weights.
- Keep `pyproject.toml`, engine version, changelog, release notes and assets aligned.

```sh
python -m pytest
python scripts/smoke_test.py
python scripts/release_journey.py --output /tmp/dx-release-journey
python scripts/benchmark_preview.py --output /tmp/dx-preview.json
python -m build
python scripts/package_release.py --output ../release-artifacts/1.1.0 --distributions dist
```

Package from the reviewed release commit. `SHA256SUMS` covers the source ZIP,
`dx-studio-video.zip`, wheel and sdist when `--distributions` is supplied. Verify
it after downloading release attachments too. Publish the tag at the merged,
passing commit and attach those five assets to the GitHub release. Do not mutate
an existing release's source silently; ship a patch version for a code change.

The source ZIP and skill ZIP carry the same engine and public resources under
different root names. The skill ZIP has `dx-studio-video/SKILL.md`. The wheel
contains the engine/editor/templates; the skill/source distribution supplies
assistant instructions and production helpers. Do not publish to PyPI without
checking package-name ownership; GitHub is the distribution channel.

See [GALLERY](GALLERY.md) before refreshing visuals. Capture real controls in a
wide viewport, identify synthetic examples and keep roadmap features separate.
