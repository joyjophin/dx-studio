# 0.1.0 release validation

Local validation on 2026-10-17: macOS arm64, Python 3.13.3, Cairo 1.18.4,
FFmpeg 7.1, and ffprobe 5.0.1. Native dependencies were isolated for this review;
normal installation instructions are in INSTALL.md.

- 72 regression tests passed, including local HTTP requests to DX Editor.
- Both starter templates exported and fully decoded: 1080×1920 and 1920×1080,
  with the expected duration and an audio stream. Short explainer exports also
  passed for a landscape half-frame presenter and a vertical bottom band.
- Both 16-second explainer demos exported at 30 fps, H.264 video plus AAC audio.
- Both explainer verifiers returned OK; dense 0.1-second sampling reported zero
  failing frames. Full-size stills and the beat sheets were inspected visually.
- The music/SFX demo master measured approximately −14.2 LUFS integrated and
  −1.7 dB true peak. A silent starter cannot meet an audible loudness target.
- In the actual browser UI, a multiline headline and layer scale were changed,
  saved, and verified; the editor screenshot records the working interface.
- Presenter reservations were tested across both ratios, both templates, every preset
  and each story beat, including pixel checks for a clear reserved region.
- The editor was checked at 1600×900 with no horizontal page overflow. Both corner
  and half-frame preferences reflowed live, saved, and survived reloading.
- Skill frontmatter and local Markdown links passed validation.
- Wheel, source distribution, portable projects and source/skill archives were built.

GitHub Actions is configured for Ubuntu with Python 3.10 and 3.13. Those remote
runs will only occur after the repository is uploaded. Native Windows, additional
Python/OS combinations, optional TTS/ASR model downloads and a generated narrated
production were not validated in this release pass. This is an initial public
release; these checks do not constitute an exhaustive security or media audit.

README presentation was reviewed in a local GitHub-style Markdown preview. All
gallery images loaded without horizontal page overflow. The four-frame editing
loop was generated with scripts/render_showcase.py from the included template,
with an eight-second duration. Feature captures use the real editor at 1600×900.
