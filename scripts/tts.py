"""Generate the voiceover for a project with Kokoro TTS (open source), one WAV per line.

    python3 scripts/tts.py <project> [--voice af_heart] [--speed 0.9] [--gap 0.35] [--lead 0.3] [--fit-duration]

Reads project.json "voice": [{"text": "...", "speed"?: 0.85, "pause_before"?: 0.6, "start"?: fixed seconds, "duck"?: "deep"}, ...]
Writes vo/NN.wav (silence-trimmed), then lays lines out one after another (unless a line has a fixed "start")
and saves "file" and "start" back into project.json. --fit-duration sets duration = last line end + 1.6 s.
Model files (~330 MB) are downloaded once to ~/.cache/dx_studio/kokoro from the kokoro-onnx GitHub releases.
Good voices: af_heart (warm, female, default), af_bella, am_michael, am_fenrir, bm_george, bf_emma.
"""
import argparse, json, os, subprocess, sys
import numpy as np, soundfile as sf
CACHE = os.path.expanduser('~/.cache/dx_studio/kokoro')
URLS = {'kokoro.onnx': 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx',
        'voices.bin': 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin'}

def ensure_model():
    os.makedirs(CACHE, exist_ok=True)
    try: import kokoro_onnx
    except ImportError as exc:
        raise RuntimeError('Install optional speech support in your virtual environment: pip install -e .[tts]') from exc
    for f, u in URLS.items():
        p = os.path.join(CACHE, f)
        if not os.path.exists(p) or os.path.getsize(p) < 1_000_000:
            print('downloading', f, '…', flush=True); subprocess.run(['curl', '--fail', '-sSL', '-o', p, u], check=True)
    from kokoro_onnx import Kokoro
    return Kokoro(os.path.join(CACHE, 'kokoro.onnx'), os.path.join(CACHE, 'voices.bin'))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('project'); ap.add_argument('--voice', default='af_heart'); ap.add_argument('--speed', type=float, default=0.9)
    ap.add_argument('--gap', type=float, default=0.35); ap.add_argument('--lead', type=float, default=0.3); ap.add_argument('--fit-duration', action='store_true')
    ap.add_argument('--only', type=int, nargs='*', help='regenerate only these line indices')
    a = ap.parse_args()
    pf = os.path.join(a.project, 'project.json'); cfg = json.load(open(pf)); lines = cfg.get('voice', [])
    if not lines: sys.exit('project.json has no "voice" lines')
    k = ensure_model(); os.makedirs(os.path.join(a.project, 'vo'), exist_ok=True)
    for i, ln in enumerate(lines):
        f = f'vo/{i:02d}.wav'; ln['file'] = f
        if a.only is not None and i not in a.only and os.path.exists(os.path.join(a.project, f)): continue
        s, sr = k.create(ln['text'], voice=ln.get('voice', a.voice), speed=ln.get('speed', a.speed), lang='en-us')
        amp = np.abs(s); idx = np.where(amp > 0.01*amp.max())[0]
        if not len(idx): raise ValueError(f'TTS produced silence for line {i}')
        s = s[max(0, idx[0]-int(0.03*sr)):min(len(s), idx[-1]+int(0.08*sr))]
        sf.write(os.path.join(a.project, f), s, sr); print(f'{i:02d}  {len(s)/sr:5.2f}s  {ln["text"]}', flush=True)
    t = a.lead
    for ln in lines:
        d = sf.info(os.path.join(a.project, ln['file'])).duration
        if 'start' in ln and ln.get('lock'): t = ln['start']
        else: t = t + (ln.get('pause_before', a.gap) if ln is not lines[0] else 0); ln['start'] = round(t, 3)
        ln['dur'] = round(d, 3); t = ln['start'] + d
    if a.fit_duration: cfg['duration'] = round(t + 1.6, 1)
    json.dump(cfg, open(pf, 'w'), indent=2, ensure_ascii=False)
    print(f'voice ends at {t:.2f}s; project duration {cfg.get("duration")}s')
    if t > cfg.get('duration', 0) - 0.5: print('WARNING: narration runs past the end; use --fit-duration or tighten the script')
if __name__ == '__main__': main()
