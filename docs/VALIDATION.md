# v1.0 release validation

Local release pass: 2026-10-19, macOS arm64, Python 3.13.3, Cairo 1.18.4,
FFmpeg 7.1 and FFprobe n4.4.1. Native libraries were supplied through an isolated
local runtime; this is not a fresh operating-system installation study.

## Editing and recovery

- Full local regression pass: **130 tests passed**. Focused launch/session checks
  were repeated after the browser-facing timestamp fix. Existing coverage includes
  stale-save protection, drafts, history, export cancellation and previous-master preservation.
- Render comparisons across a clip split preserve transform keys and entrance/exit
  phase, including the split boundary. Trim advances source timing; locked clips
  reject direct edits. Saved selection groups reopen with the project.
- Live browser checks exercised sample creation and the guide, folder match review
  and recovery, clip splitting/trimming, group selection/renaming after reopen,
  installation diagnostics and portable-project download. Browser console errors: none.
- The actual downloaded portable ZIP passed manifest verification with the matching
  v1.0 engine. Normal handoffs exclude older settings versions; an opt-in backup
  was separately unpacked and its named version restored.

## Export and portable workflow

- Four full-HD one-second exports fully decoded: both 1080×1920 and 1920×1080
  starter projects, plus explainer presenter layouts (vertical bottom band and
  landscape left half). Each had the expected duration and audio stream.
- [Scripted creator journey](release-journey.json): both ratios used generated
  test-pattern footage and test-tone recordings. The sequence changed text and
  captions, split a clip, compared source audio sample-for-sample, saved groups,
  moved a verified project bundle, loaded its included engine, exported a selected
  range and restored a named settings version.
- Journey outputs: three seconds at 24 fps, 1280×720 with burned captions and
  720×1280 with clean video/SRT. Both fully decoded; audio/video duration difference
  was zero. SRT timestamps were relative to the exported range.
- Every normal MP4 build now checks encoded dimensions, frame rate, duration and
  audio/video streams before publishing over a previous completed export.

## Preview measurements

The [reproducible benchmark](preview-benchmark.json) uses a ten-minute synthetic
project with 632 declared layers, 200 captions, 60 test-tone takes and a looping
short video. At 25% preview scale over 24 sample frames on this Mac:

| Measure | Result |
| --- | --- |
| Cold median | 10.03 ms |
| Cold maximum | 67.73 ms |
| Repeated-frame median | 5.31 ms |
| Repeated-frame cache hits | 24 / 24 |

A separate 12-second colour-section fixture checked seeking to later chunks and
confirmed only the requested four-second section decoded. JPEG preview storage
is bounded to 32 MiB/120 entries per open project; decoded video-frame memory is
bounded to 64 MiB except a single oversize frame. Disk caches grow with visited
footage sections. This benchmark does not establish real-time playback, a long
full-HD export time, 4K readiness or performance on all creator hardware.

## Installation and packages

- The release wheel installed its declared dependencies in a fresh temporary
  virtual environment outside the checkout. Doctor, project creation, frame check,
  installed-wheel portable packaging and bundle verification passed.
- The extracted source launcher's first setup installed dependencies in its own
  environment. The explicit nonstandard Cairo library option, doctor-only mode
  and editor-server startup were verified on this Mac. macOS may strip native
  library environment variables at shell entry; the launcher applies them afterward.
- Wheel/source builds, source/skill ZIPs, engine version consistency, licence
  notices and local documentation links were checked. Release SHA256SUMS covers
  the four downloadable distributions.
- Ubuntu CI exercises Python 3.10 and 3.13, export smoke and packaging. Its result
  must pass on the release commit before merging/publishing.

## Limits of this pass

No independent fresh-user study, full clean-OS installation, native Windows,
separate WSL2 run, Safari/Firefox/mobile validation, optional TTS/ASR model download,
real spoken-word forced-alignment review or long full-HD export was performed.
Synthetic timing fixtures are not speech-quality evidence. Scenes execute trusted
Python; archive integrity checks are not a code sandbox or an authenticity signature.
The broader feature backlog remains separate from the v1.0 launch scope.
