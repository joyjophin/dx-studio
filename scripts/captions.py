"""Build captions.json from the voiceover: phrase captions timed to the audio.

    python3 scripts/captions.py <project>

Each voice line may define its phrases (3–7 words, split at natural boundaries), optionally with one highlight:
    "captions": ["So why does this app say", ["you haven't started?", "haven't started?"]]
The phrases must join back into the line's text. Lines without "captions" are split automatically.
Phrase boundaries are placed at the quietest point near the estimated word position.
"""
import json, os, re, sys
import numpy as np, soundfile as sf

def auto_phrases(text, lo=3, hi=7):
    words = text.split(); out, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= hi or (len(cur) >= lo and re.search(r'[,.;:!?—]$', w)): out.append(' '.join(cur)); cur = []
    if cur:
        if out and len(cur) < 2: out[-1] += ' ' + ' '.join(cur)
        else: out.append(' '.join(cur))
    return out

def quietest(a, sr, est, lo, hi):
    win, best = int(0.04*sr), None
    for t in np.arange(max(0.05, lo), min(len(a)/sr-0.05, hi), 0.01):
        k = int(t*sr); e = float(np.sqrt(np.mean(a[max(0, k-win//2):k+win//2]**2)))
        if best is None or e < best[0]: best = (e, t)
    return best[1] if best else est

def main():
    proj = sys.argv[1]; cfg = json.load(open(os.path.join(proj, 'project.json'))); out = []
    for ln in cfg.get('voice', []):
        a, sr = sf.read(os.path.join(proj, ln['file']))
        if a.ndim > 1: a = a.mean(axis=1)
        dur = len(a)/sr; text = ln['text']
        caps = ln.get('captions') or auto_phrases(text)
        caps = [c if isinstance(c, list) else [c, None] for c in caps]
        joined = ' '.join(c[0] for c in caps)
        if re.sub(r'\s+', ' ', joined).strip() != re.sub(r'\s+', ' ', text).strip():
            print(f'WARNING: captions for line "{text[:40]}…" do not join back to its text');
        starts, pos = [0.0], 0
        for c in caps[1:]:
            pos = text.find(c[0], pos) if text.find(c[0], pos) >= 0 else pos
            est = 0.04 + (dur-0.12)*pos/max(1, len(text)); starts.append(quietest(a, sr, est, est-0.28, est+0.28))
        for i, (phrase, hl) in enumerate(caps):
            s0 = ln['start'] + starts[i] - (0.05 if i == 0 else 0)
            e0 = ln['start'] + (starts[i+1] if i+1 < len(caps) else dur)
            if hl and hl not in phrase: print(f'WARNING: highlight "{hl}" is not in "{phrase}"'); hl = None
            out.append({'line': cfg['voice'].index(ln), 'text': phrase, 'hl': hl, 'start': round(max(0, s0), 3), 'end': round(e0, 3)})
    for i, c in enumerate(out):
        nxt = out[i+1]['start'] if i+1 < len(out) else cfg.get('duration', 1e9)
        c['show_end'] = round(min(nxt, c['end']+0.45), 3)
    json.dump(out, open(os.path.join(proj, 'captions.json'), 'w'), indent=1, ensure_ascii=False)
    print(f'{len(out)} captions written to captions.json')
if __name__ == '__main__': main()
