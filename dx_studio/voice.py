"""dx_studio.voice: timings of the voiceover lines, for timing animation to the narration.

    VT = VoiceTimes(__file__)          # reads the project.json next to scene.py
    VT.start(2), VT.end(2)             # when line 2 starts / ends (seconds)
    VT.word(2, 'already')              # estimated time a word is spoken (character-proportional)

Durations come from the line's "dur" (written by scripts/tts.py), else the WAV file, else an estimate,
so a scene can be drafted before the voice exists and snaps into sync once it's generated.
"""
import json, os

class VoiceTimes:
    def __init__(self, where):
        d = where if os.path.isdir(where) else os.path.dirname(os.path.abspath(where))
        self.dir = d; self.cfg = json.load(open(os.path.join(d, 'project.json'))); self.lines = self.cfg.get('voice', [])
    def _dur(self, ln):
        if ln.get('dur'): return float(ln['dur'])
        f = os.path.join(self.dir, ln.get('file', '') or '')
        if ln.get('file') and os.path.exists(f):
            try:
                import soundfile as sf; return sf.info(f).duration
            except Exception: pass
        return 0.066*len(ln.get('text', '')) + 0.2
    def start(self, i): return float(self.lines[i].get('start', 0.0))
    def dur(self, i): return self._dur(self.lines[i])
    def end(self, i): return self.start(i) + self.dur(i)
    def word(self, i, word, occurrence=0):
        s = self.lines[i].get('text', ''); pos = -1
        for _ in range(occurrence+1):
            pos = s.find(word, pos+1)
            if pos < 0: raise ValueError(f"Word {word!r} occurrence {occurrence} not found in voice line {i}: {s!r}")
        return self.start(i) + 0.04 + (self.dur(i)-0.12)*pos/max(1, len(s))
