"""Use the user's own voiceover: transcribe it offline, lay the takes out on the timeline, write word timings + captions.

    python3 scripts/transcribe.py <project> take1.mp3 [take2.mp3 ...] [--gap 0.8] [--lead 0.5] [--tail 3.0]
                                  [--max-words 6] [--fix "draw=drawer,form=Form"]
    python3 scripts/transcribe.py --print take.mp3          # just print the transcript and timed words

One take per chapter or one take for the whole video both work; takes are placed in the order given.
Model: NVIDIA Parakeet TDT 0.6B v2 (int8) through sherpa-onnx. It is downloaded once (~480 MB) from the
sherpa-onnx GitHub releases into ~/.cache/dx_studio/asr (Hugging Face is often blocked; GitHub release assets are not).

Writes into <project>:
  vo/NN.wav            48 kHz mono, dead air trimmed at both ends, no speed change
  project.json         "voice" lines (text, file, start, dur), "duration" = last line end + --tail
  assets/words.json    [[line, word, start, end], ...] in project time (use it for cue timing, see VOICE_DRIVEN.md)
  captions.json        phrases split at punctuation (<= --max-words words), timed from the real words
and prints every word with its time, so cues can name the right occurrence of repeated words.
"""
import argparse, json, os, subprocess, sys, tarfile
import numpy as np

CACHE = os.path.expanduser('~/.cache/dx_studio/asr')
MODEL = 'sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8'
URL = f'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{MODEL}.tar.bz2'

def ensure_model():
    try: import sherpa_onnx
    except ImportError as exc:
        raise RuntimeError('Install optional speech support in your virtual environment: pip install -e .[asr]') from exc
    import sherpa_onnx
    d = os.path.join(CACHE, MODEL)
    if not os.path.exists(os.path.join(d, 'encoder.int8.onnx')):
        os.makedirs(CACHE, exist_ok=True); tb = os.path.join(CACHE, MODEL + '.tar.bz2')
        print('downloading the speech model (~480 MB) …', flush=True)
        subprocess.run(['curl', '--fail', '-sSL', '-o', tb, URL], check=True)
        with tarfile.open(tb) as tf: tf.extractall(CACHE, filter='data')
        os.remove(tb)
    return sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=os.path.join(d, 'encoder.int8.onnx'), decoder=os.path.join(d, 'decoder.int8.onnx'),
        joiner=os.path.join(d, 'joiner.int8.onnx'), tokens=os.path.join(d, 'tokens.txt'), model_type='nemo_transducer', num_threads=4)

def load(path, sr):
    import soundfile as sf
    tmp = f'/tmp/_asr_{os.getpid()}_{sr}.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-ar', str(sr), '-ac', '1', tmp], check=True)
    a, _ = sf.read(tmp, dtype='float32'); os.remove(tmp); return a

def words_of(rec, a16):
    s = rec.create_stream(); s.accept_waveform(16000, a16); rec.decode_stream(s); r = s.result
    words = []
    for tk, ts in zip(r.tokens, r.timestamps):
        if tk.startswith(' ') or not words: words.append([tk.strip(), float(ts), float(ts)])
        else: words[-1][0] += tk; words[-1][2] = float(ts)
    for i in range(len(words) - 1):          # a word ends just before the next starts (capped)
        words[i][2] = max(words[i][2] + 0.08, min(words[i + 1][1] - 0.02, words[i][2] + 0.45))
    if words: words[-1][2] += 0.35
    return r.text, words

def trim_bounds(a, sr, db=-45.0, pre=0.06, post=0.12):
    env = np.convolve(np.abs(a), np.ones(int(0.01*sr))/(0.01*sr), mode='same'); idx = np.where(env > 10**(db/20))[0]
    if len(idx) == 0: return 0, len(a)
    return max(0, idx[0] - int(pre*sr)), min(len(a), idx[-1] + int(post*sr))

def phrases(words, max_words):
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(w); end = w[1][-1] in '.?!'; comma = w[1][-1] in ',:;'
        if end or (comma and len(cur) >= 3) or len(cur) >= max_words: out.append(cur); cur = []
    if cur:
        if out and len(cur) < 2: out[-1] += cur
        else: out.append(cur)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('project', nargs='?'); ap.add_argument('takes', nargs='*')
    ap.add_argument('--print', dest='only', metavar='AUDIO'); ap.add_argument('--gap', type=float, default=0.8)
    ap.add_argument('--lead', type=float, default=0.5); ap.add_argument('--tail', type=float, default=3.0)
    ap.add_argument('--max-words', type=int, default=6); ap.add_argument('--fix', default='')
    a = ap.parse_args()
    rec = ensure_model()
    if a.only:
        text, words = words_of(rec, load(a.only, 16000)); print(text); print(' '.join(f'{w}@{s:.2f}' for w, s, e in words)); return
    if not a.project or not a.takes: ap.error('give a project and at least one take (or --print AUDIO)')
    import soundfile as sf
    fix = dict(kv.split('=', 1) for kv in a.fix.split(',') if '=' in kv)
    pf = os.path.join(a.project, 'project.json'); cfg = json.load(open(pf))
    os.makedirs(os.path.join(a.project, 'vo'), exist_ok=True); os.makedirs(os.path.join(a.project, 'assets'), exist_ok=True)
    t = a.lead; voice, allw = [], []
    for i, take in enumerate(a.takes):
        a48 = load(take, 48000); s0, s1 = trim_bounds(a48, 48000)
        sf.write(os.path.join(a.project, 'vo', f'{i:02d}.wav'), a48[s0:s1], 48000)
        head, dur = s0/48000, (s1 - s0)/48000
        text, words = words_of(rec, load(take, 16000))
        def fixw(w):
            core = w.strip('.,:;?!'); rep = fix.get(core.lower())
            return w.replace(core, rep, 1) if rep else w
        words = [[fixw(w), ws - head + t, we - head + t] for w, ws, we in words]
        voice.append({'text': ' '.join(w for w, _, _ in words), 'file': f'vo/{i:02d}.wav', 'start': round(t, 3), 'dur': round(dur, 3)})
        allw += [[i, w, round(ws, 3), round(we, 3)] for w, ws, we in words]
        print(f'\n== line {i}  start {t:.2f}s  dur {dur:.2f}s  ({os.path.basename(take)})')
        print(' '.join(f'{w}@{ws:.1f}' for w, ws, we in words))
        t += dur + a.gap
    cfg['voice'] = voice; cfg['duration'] = round(t - a.gap + a.tail, 2)
    json.dump(cfg, open(pf, 'w'), indent=1, ensure_ascii=False)
    json.dump(allw, open(os.path.join(a.project, 'assets', 'words.json'), 'w'))
    caps = []
    for i in range(len(voice)):
        lw = [w for w in allw if w[0] == i]
        for ph in phrases(lw, a.max_words):
            caps.append({'line': i, 'text': ' '.join(w[1] for w in ph), 'hl': None, 'start': ph[0][2], 'end': ph[-1][3]})
    for k, cp in enumerate(caps):
        nxt = caps[k + 1]['start'] if k + 1 < len(caps) else cp['end'] + 1.0
        cp['show_end'] = round(min(nxt, cp['end'] + 0.4), 3)
    json.dump(caps, open(os.path.join(a.project, 'captions.json'), 'w'), indent=1, ensure_ascii=False)
    print(f"\nruntime {cfg['duration']:.2f}s · {len(voice)} lines · {len(allw)} words · {len(caps)} captions")

if __name__ == '__main__':
    main()
