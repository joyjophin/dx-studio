"""Dense error pass: render every `step` seconds at quarter size and report every frame that raises, before a long build.

    python3 scripts/framecheck.py <project> [step=0.1]

A 6-minute video renders ~3,600 checks in under two minutes. Also lists VoiceTimes.word() lookups whose word is not
in the line (missing words now raise immediately). Run from the work folder that contains dx_studio/.
A frame that fails here would abort `dx_studio build` minutes into the render.
"""
import os, sys, time, traceback
sys.path.insert(0, os.getcwd())
from dx_studio import voice
misses = {}
_orig = voice.VoiceTimes.word
def _word(self, i, w, occurrence=0):
    if w not in self.lines[i].get('text', ''): misses[(i, w)] = self.lines[i]['text'][:60]
    return _orig(self, i, w, occurrence)
voice.VoiceTimes.word = _word
from dx_studio import cli

def main():
    if len(sys.argv) < 2: sys.exit(__doc__)
    pr = cli._project(sys.argv[1]); step = float(sys.argv[2]) if len(sys.argv) > 2 else 0.1
    if step <= 0: sys.exit("step must be positive")
    t0 = time.time(); n = 0; fails = []; t = 0.0
    while t < pr.duration:
        try: pr.render(t, 0.25)
        except Exception as ex: fails.append((round(t, 3), repr(ex), traceback.format_exc(limit=3)))
        n += 1; t += step
    try: pr.cues()
    except Exception as ex: fails.append(('cues()', repr(ex), traceback.format_exc(limit=3)))
    print(f'rendered {n} frames in {time.time()-t0:.1f}s · {len(fails)} failing')
    for f in fails[:12]: print('FAIL', f[0], f[1]); print(f[2])
    for (i, w), s in sorted(misses.items()): print('MISS line', i, repr(w), '|', s)
    sys.exit(1 if fails else 0)

if __name__ == '__main__':
    main()
