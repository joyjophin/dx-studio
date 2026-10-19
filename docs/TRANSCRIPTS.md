# Transcripts and word timing

Open Captions → Transcript in the current tool rail.

DX Studio v1.0 add a **Transcript** workspace. Import a recording in
Narration first, then choose its take. Spelling corrections change text, not audio.
Clicking a word seeks to the matching source position, adjusted for the take trim.

## Import timings

Choose **Import timed words** and paste JSON or select a JSON file. Each time is
in seconds from the beginning of the original recording, before trims or placement:

```json
{"words":[
  {"text":"Make","start":0.1,"end":0.4},
  {"text":"clear","start":0.5,"end":0.8},
  {"text":"stories.","start":1.0,"end":1.5}
]}
```

A `word` key instead of `text`, or `["Make",0.1,0.4]` triples, also work. Phrase
subtitles are not word alignment; use Captions to import SRT/VTT. Imports validate
ordered, finite times against the source duration. Each imported word gets a stable
ID and the transcript records the source file and timing provenance.

Select a word to correct spelling or source start/end times. Generate captions
separately, choosing 1–12 words per phrase and append or replace. These captions
highlight the active word. Manual caption text is preserved during linked retiming;
changing its word count disables the automatic highlight. Manually moving, trimming,
splitting, merging or duplicating a caption detaches its word links, keeping later
retiming from overriding that manual timing decision.

## Replace a take without losing decisions

Select a canvas layer, choose a word, then **Link selected layer to this word**.
Replace a recording in Narration, import timings for the replacement, then choose
**Review timing updates**. Matching stable IDs are preferred; a unique word-text
match can relink a replacement. Repeated or missing words produce a review warning.
Generated caption phrases require consecutive matching words. No semantic timing
is guessed. Layer duration, transforms and unrelated edits remain intact. Linked
sound cues follow the layer. Protected sections and canvas locks block changes.

Review individual values and a before/after frame before applying selected changes.
A frame comparison uses the current playhead; scrub to the changed beat first.
Transcription or import does not silently regenerate captions or move graphics.

## Optional offline English transcription

The editor never downloads a model or installs a speech package. Timed-word import
works without either. To opt into local English recognition, from a source checkout
with the project virtual environment active:

```sh
python -m pip install -e '.[asr]'
# Explicit one-time model download and initialisation, approximately 480 MB:
python -c "from scripts.transcribe import ensure_model; ensure_model()"
```

The setup helper in `scripts/transcribe.py` downloads the Parakeet TDT v2 int8
archive from the k2-fsa/sherpa-onnx GitHub release and caches it under
`~/.cache/dx_studio/asr/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8/`.
The editor requires `encoder.int8.onnx`, `decoder.int8.onnx`, `joiner.int8.onnx`
and `tokens.txt` there. Check the model's licence before redistribution; models
are not included in project or skill bundles.

Choose **Transcribe locally** once setup is complete. This is an optional speech
adapter with estimated word boundaries, not a forced aligner for a supplied script.
Review names, word boundaries and uncertain speech. Recordings over an hour must
be split first. No provider account or API key is involved. Results are discarded
if the take or transcript changes while the task is running.

Timed import, correction, caption generation and linked timing are covered by the
creator workflow checks. The optional speech model is not installed in the
maintainer's feature verification environment, so recognition accuracy is not
claimed by those checks.
