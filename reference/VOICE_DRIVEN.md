# Narration and timing

The project can be silent, use recorded takes, or use optional local speech models.
A normal rendered demo needs no speech model, API key or network access.

## Recorded takes

Ask for the audio files when the user wants to record. Keep the script copy-ready,
one thought per line, with delivery notes outside the spoken text. From the repository:

```sh
python -m pip install -e '.[asr]'
python scripts/transcribe.py projects/my-video take1.mp3 take2.mp3
```

The first run downloads a roughly 480 MB Parakeet model into the user's cache.
This optional recogniser is English-oriented. Review names, numbers and punctuation;
do not claim support for languages that were not tested. The script writes trimmed
WAVs, voice entries, word timing data and caption phrases. It does not time-stretch.
The recogniser's timing is useful but still requires review against the recording.

## Generated voice

```sh
python -m pip install -e '.[tts]'
python scripts/tts.py projects/my-video --voice af_heart --fit-duration
python scripts/captions.py projects/my-video
```

Kokoro downloads roughly 330 MB on first use. Choose a voice appropriate to the
brief; `af_heart` is a default example, not a required identity. These downloaders
need `curl`. Consult the model's upstream licensing before redistributing its
weights; DX Studio's MIT licence does not relicense models or voices.

## Scene timing

`VoiceTimes(__file__)` reads line starts/durations from project.json. Its `word()`
method estimates timing from text length and raises when the requested substring
or occurrence is missing. Estimates are not exact word alignment. Recorded word
positions live in assets/words.json as `[line, word, start, end]` entries.

After changing voice or duration, update scene layer windows, chapters, captions,
end holds and music fade positions together. The engine does not invent a new
story edit when speech gets longer. Inspect opening, transitions and ending again.
