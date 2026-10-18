"""dx_studio.audio: a small synthesised sound vocabulary, a gentle generative music bed,
voice placement with ducking, and mastering to a loudness target.

A scene declares sound effects with cues(p) -> [{"sound": "stamp", "at": 16.46, "gain": 1.0, ...kwargs}]
so sounds follow the timings the editor changes."""
import json, os, re, subprocess
import numpy as np, soundfile as sf
from scipy import signal

SR = 48000
rng = np.random.default_rng(7)
def lp(x, fc, order=2): b, a = signal.butter(order, fc/(SR/2)); return signal.lfilter(b, a, x)
def hp(x, fc, order=2): b, a = signal.butter(order, fc/(SR/2), 'high'); return signal.lfilter(b, a, x)
def bp(x, lo, hi, order=2): b, a = signal.butter(order, [lo/(SR/2), hi/(SR/2)], 'band'); return signal.lfilter(b, a, x)
def fade_in(x, ms):
    k = min(len(x), max(0, int(ms*SR/1000))); x = x.copy()
    if k: x[:k] *= np.linspace(0, 1, k)
    return x

# ---------------- SFX vocabulary ----------------
def sfx_chime():
    out=np.zeros(int(1.4*SR))
    for delay,f,g in [(0,1318.5,1.0),(0.085,1975.5,0.8)]:
        n=int(1.2*SR); tt=np.arange(n)/SR
        tone=(np.sin(2*np.pi*f*tt)+0.25*np.sin(2*np.pi*2*f*tt)*np.exp(-tt*9)+0.12*np.sin(2*np.pi*2.76*f*tt)*np.exp(-tt*14))
        tone*=np.exp(-tt*4.2)*g; tone=fade_in(tone,4)
        k=int(delay*SR); out[k:k+n]+=tone
    return out*0.22
def sfx_click(level=1.0):
    n=int(0.05*SR); tt=np.arange(n)/SR
    nz=hp(rng.standard_normal(n),1800)*np.exp(-tt*260)
    body=np.sin(2*np.pi*1150*tt)*np.exp(-tt*150)
    return (0.35*nz+0.6*body)*0.30*level
def sfx_tap(level=1.0):
    n=int(0.06*SR); tt=np.arange(n)/SR
    body=np.sin(2*np.pi*(700+500*np.exp(-tt*80))*tt)*np.exp(-tt*110)
    nz=bp(rng.standard_normal(n),1500,6000)*np.exp(-tt*300)*0.25
    return (body+nz)*0.16*level
def sfx_slide(dur=0.38, level=1.0, lo=500, hi=3500):
    n=int(dur*SR); tt=np.arange(n)/SR
    nz=bp(rng.standard_normal(n),lo,hi)
    e=np.sin(np.pi*np.clip(tt/dur,0,1))**1.6
    return nz*e*0.07*level
def sfx_paper():
    n=int(0.45*SR); tt=np.arange(n)/SR
    nz=bp(rng.standard_normal(n),900,7000)
    grain=1+0.6*signal.lfilter([1],[1,-0.995],rng.standard_normal(n))*0.05
    e=np.sin(np.pi*np.clip(tt/0.45,0,1))**1.3
    return nz*grain*e*0.085
def sfx_stamp():
    n=int(0.3*SR); tt=np.arange(n)/SR
    thump=np.sin(2*np.pi*(95+60*np.exp(-tt*40))*tt)*np.exp(-tt*22)
    slap=lp(rng.standard_normal(n),2500)*np.exp(-tt*70)
    rub=bp(rng.standard_normal(n),300,1200)*np.exp(-tt*30)*0.4
    return (0.9*thump+0.55*slap+rub)*0.30
def sfx_tick():
    n=int(0.12*SR); tt=np.arange(n)/SR
    a=np.sin(2*np.pi*2200*tt)*np.exp(-tt*90)
    b=np.zeros(n); k=int(0.035*SR); tb=np.arange(n-k)/SR
    b[k:]=np.sin(2*np.pi*2950*tb)*np.exp(-tb*70)
    return fade_in(a+0.8*b,2)*0.14
def sfx_rise(dur=0.85):
    n=int((dur+0.5)*SR); tt=np.arange(n)/SR
    f=np.where(tt<dur, 523.25*(2**(tt/dur*0.58)), 523.25*2**0.58)
    ph=2*np.pi*np.cumsum(f)/SR
    e=np.clip(tt/0.08,0,1)*np.where(tt<dur,1,np.exp(-(tt-dur)*6))
    return (np.sin(ph)+0.3*np.sin(2*ph)+0.1*np.sin(3*ph))*e*0.07


# --- character + sticker micro-sounds (quiet, same small vocabulary)
def sfx_pop(level=1.0):
    n=int(0.09*SR); tt=np.arange(n)/SR
    f=420+520*np.exp(-tt*55)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*38)*0.10*level
def sfx_step(level=1.0):
    n=int(0.07*SR); tt=np.arange(n)/SR
    return lp(rng.standard_normal(n),900)*np.exp(-tt*70)*0.10*level
def sfx_scribble(dur=0.45, level=1.0):
    n=int(dur*SR); tt=np.arange(n)/SR
    nz=bp(rng.standard_normal(n),1800,5500)*(0.6+0.4*np.sin(2*np.pi*14*tt))
    e=np.sin(np.pi*np.clip(tt/dur,0,1))**0.8
    return nz*e*0.035*level

SOUNDS = {'chime': sfx_chime, 'click': sfx_click, 'tap': sfx_tap, 'slide': sfx_slide, 'paper': sfx_paper,
          'stamp': sfx_stamp, 'tick': sfx_tick, 'rise': sfx_rise, 'pop': sfx_pop, 'step': sfx_step, 'scribble': sfx_scribble}
SOUND_HELP = {
    'chime': 'soft two-note success chime', 'click': 'dry UI click', 'tap': 'light UI tap (level)',
    'slide': 'soft card slide (dur, level, lo, hi)', 'paper': 'paper slide', 'stamp': 'rubber stamp thump',
    'tick': 'checkmark tick', 'rise': 'gentle rising progress tone (dur)', 'pop': 'sticker pop-in (level)',
    'step': 'soft footstep (level)', 'scribble': 'pencil scribble (dur, level)'}

def make_sound(name, **kw):
    if name not in SOUNDS: raise ValueError(f"unknown sound '{name}'. Available: {', '.join(SOUNDS)}")
    return SOUNDS[name](**kw)

# ------------------------------------------------------------------ music bed
def m2f(m): return 440*2**((m-69)/12)
def _ks(f, dur, bright=0.5):
    n = int(dur*SR); p = int(SR/f)
    buf = lp(rng.standard_normal(p), 2000+4000*bright, 1)
    y = np.zeros(n); y[:p] = buf
    for i in range(p, n): y[i] = 0.996*0.5*(y[i-p]+y[i-p-1 if i-p-1 >= 0 else 0])
    return y*np.exp(-np.arange(n)/SR*2.2)

def synth_music(duration, spec):
    """plucked arpeggio + pad + soft bass + light percussion.
    spec: bpm, chords [[midi...]...], roots [midi...], final_chord, final_root, final_arp, final_at,
          thin [[t0,t1]...] (sparser section), perc_from, end_fade_at"""
    N = int(SR*duration)
    bpm = spec.get('bpm', 100); beat = 60/bpm; bar = 4*beat
    chords = spec.get('chords', [[53, 57, 60, 64], [50, 53, 57, 60, 64], [46, 50, 53, 57], [48, 52, 55, 57]])
    roots = spec.get('roots', [41, 38, 34, 36])
    final_chord = spec.get('final_chord', [53, 57, 60, 64, 67]); final_root = spec.get('final_root', 41)
    final_arp = spec.get('final_arp', [72, 76, 79, 84]); final_at = spec.get('final_at', duration-2.5)
    thin = spec.get('thin', []); perc_from = spec.get('perc_from', 2.4)
    in_thin = lambda tn: any(a <= tn < b for a, b in thin)
    music = np.zeros(N); pad = np.zeros(N); perc = np.zeros(N); bass = np.zeros(N)
    cache = {}
    def pluck(m, dur=1.1):
        if (m, dur) not in cache: cache[(m, dur)] = _ks(m2f(m), dur)
        return cache[(m, dur)]
    def add(buf, x, t):
        k = int(t*SR); m_ = min(len(x), N-k)
        if m_ > 0: buf[k:k+m_] += x[:m_]
    arp = [0, 2, 1, 3, 2, 1, 3, 2]
    for b in range(int(np.ceil(duration/bar))):
        t0 = b*bar; last = t0 >= final_at
        ch = final_chord if last else chords[b % len(chords)]
        n = int(bar*SR*(1.6 if last else 1.05)); tt = np.arange(n)/SR; sig = np.zeros(n)
        for m in ch:
            for det in (-0.07, 0.07):
                f = m2f(m+det); sig += np.sin(2*np.pi*f*tt)+0.18*np.sin(2*np.pi*2*f*tt)
        sig *= np.clip(tt/0.5, 0, 1)*np.clip((n/SR-tt)/0.6, 0, 1)/len(ch); add(pad, sig, t0)
        nb = int(beat*1.9*SR); tb = np.arange(nb)/SR
        for off in ((0, 2*beat) if not last else (0,)):
            add(bass, np.sin(2*np.pi*m2f(final_root if last else roots[b % len(roots)])*tb)*np.clip(tb/0.02, 0, 1)*np.exp(-tb*1.6), t0+off)
        if last:
            for j, m in enumerate(final_arp): add(music, pluck(m, 2.0)*0.8, t0+j*beat*0.5)
            continue
        for j in range(8):
            tn = t0+j*beat/2
            if in_thin(tn) and j % 2 == 1: continue
            add(music, pluck(ch[arp[j] % len(ch)]+12)*[1, 0.55, 0.75, 0.55, 0.9, 0.5, 0.7, 0.6][j], tn)
        for j in range(8):
            tn = t0+j*beat/2
            if tn < perc_from or in_thin(tn): continue
            if j in (0, 4):
                nk = int(0.25*SR); tk = np.arange(nk)/SR
                add(perc, np.sin(2*np.pi*(55+70*np.exp(-tk*35))*tk)*np.exp(-tk*14)*0.55, tn)
            if j % 2 == 1:
                nh = int(0.08*SR); th = np.arange(nh)/SR
                add(perc, hp(rng.standard_normal(nh), 6000)*np.exp(-th*60)*0.10*(1.0 if j != 3 else 0.7), tn)
    out = 0.20*lp(music, 5000)+0.10*lp(pad, 1800)+0.20*lp(bass, 300)+0.28*perc
    return fade_in(out, 1500)

# ------------------------------------------------------------------ full mix
def _compress(x, thr=0.25, ratio=2.5):
    env = signal.lfilter([0.002], [1, -0.998], np.abs(x))
    gain = np.where(env > thr, (thr+(env-thr)/ratio)/np.maximum(env, 1e-9), 1.0)
    return x*gain

def build_mix(project, out_path):
    """voice lines + ducked music + sound cues -> float WAV (unmastered).
    Everything except the music is built in scene time and then remapped through the ripple edits
    (holds are silent, deleted ranges are skipped); the music is generated directly at the output length."""
    global rng
    rng = np.random.default_rng(7)
    from .timemap import segments, out_time
    edits = getattr(project, 'edits', []) or []
    dur = project.base_duration if hasattr(project, 'base_duration') else project.duration
    N = int(SR*dur); cfg = project.cfg
    from .mix_controls import settings as mix_settings, level
    balance=mix_settings(project)
    sfx = np.zeros(N)
    for cue in project.cues() if level(balance,'effects')>0 else []:
        kw = {k: v for k, v in cue.items() if k not in ('sound', 'at', 'gain')}
        x = make_sound(cue['sound'], **kw)*cue.get('gain', 1.0)
        k = int(cue['at']*SR)
        if 0 <= k < N: m = min(len(x), N-k); sfx[k:k+m] += x[:m]
    vo = np.zeros(N); spans = []
    for line in project.voices() if hasattr(project, 'voices') else cfg.get('voice', []):
        if line.get('muted') or line.get('gain',1)<=0 or level(balance,'voice')<=0: continue
        path = os.path.join(project.path, line['file'])
        info = sf.info(path); offset = line.get('offset',0)
        if offset>=info.duration: continue
        count = max(0, min(info.frames-int(offset*info.samplerate), int(line.get('duration',info.duration)*info.samplerate)))
        if not count: continue
        a, sr = sf.read(path,start=int(offset*info.samplerate),frames=count)
        if a.ndim > 1: a = a.mean(axis=1)
        a = signal.resample_poly(a, SR, sr) if sr != SR else a
        a = hp(a, 75)*line.get('gain', 1.0)
        k = int(line['start']*SR); m = min(len(a), N-k)
        if m<=0: continue
        vo[k:k+m] += a[:m]
        if line.get('duck')!='none': spans.append((line['start'], min(dur,line['start']+len(a)/SR), line.get('duck', 'normal')))
    if np.max(np.abs(vo)) > 0:
        vo = vo/np.max(np.abs(vo))*0.70; vo = _compress(vo); vo = vo/np.max(np.abs(vo))*0.70
    scene_mix = vo*level(balance,'voice')+sfx*level(balance,'effects')
    # (video sound is added below, still in scene time)
    odur = project.duration; NO = int(SR*odur)
    def remap(buf):
        if not edits: return buf[:NO] if len(buf) >= NO else np.pad(buf, (0, NO-len(buf)))
        out = np.zeros(NO); fade = int(0.008*SR)
        for o0, o1, s0, s1, kind in segments(dur, edits):
            if kind == 'hold': continue
            a, b = int(o0*SR), int(o1*SR); sa = int(s0*SR); n = min(b-a, len(buf)-sa)
            if n <= 0: continue
            seg = buf[sa:sa+n].copy()
            if n > 2*fade: seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
            out[a:a+n] += seg
        return out
    spans_out = []
    for o0,o1,s0,s1,kind in segments(project.base_duration,edits):
        if kind=='hold':continue
        for a,b,k in spans:
            left,right=max(a,s0),min(b,s1)
            if right>left:spans_out.append((o0+left-s0,min(o1,o0+right-s0),k))
    N_scene = N; N = NO; dur_scene = dur; dur = odur
    music = np.zeros(N); mcfg = cfg.get('music')
    if mcfg and level(balance,'music')>0:
        if mcfg.get('file'):
            a, sr = sf.read(os.path.join(project.path, mcfg['file']))
            if a.ndim > 1: a = a.mean(axis=1)
            a = signal.resample_poly(a, SR, sr) if sr != SR else a; music[:min(N, len(a))] = a[:N]
        else:
            spec = dict(mcfg)
            for k in ('final_at', 'end_fade_at', 'perc_from'):
                if k in spec: spec[k] = out_time(spec[k], edits)
            if 'thin' in spec: spec['thin'] = [[out_time(a, edits), out_time(b, edits)] for a, b in spec['thin']]
            music = synth_music(dur, spec)
        mx = cfg.get('mix', {}); duck = np.ones(N)
        for s0, s1, kind in spans_out:
            a = int(max(0, s0-0.12)*SR); b = int(min(dur, s1+0.18)*SR)
            duck[a:b] = np.minimum(duck[a:b], mx.get('duck_deep', 0.30) if kind == 'deep' else mx.get('duck', 0.50))
        duck = signal.lfilter([0.0006], [1, -0.9994], duck); duck = signal.filtfilt([0.00025], [1, -0.99975], duck)
        music *= duck*mcfg.get('level', 0.32)
        fe_at = out_time(mcfg['end_fade_at'], edits) if 'end_fade_at' in mcfg else dur-2.8
        fe = np.ones(N); k = min(N, int(fe_at*SR)); fe[k:] = np.linspace(1, 0, N-k)**1.5; music *= fe
    media = np.zeros(N_scene)                 # sound from imported videos (follows the layer; hidden or muted = silent)
    lst = project.values.get('__layers', {})
    for it in project.values.get('__media', []):
        st = lst.get(it['id'], {})
        if level(balance,'footage')<=0 or it.get('kind') != 'video' or it.get('muted') or not st.get('visible', True): continue
        wav = project.media.audio_wav(it)
        if not wav: continue
        a, sr = sf.read(wav)
        if a.ndim > 1: a = a.mean(axis=1)
        s0, s1 = st.get('start', it['t0']), st.get('end', it['t0']+it['dur'])
        a=a[int(float(it.get('source_offset',0))*SR):]
        n = int(max(0, s1-s0)*SR)
        if it.get('loop') and len(a): a = np.tile(a, int(np.ceil(n/len(a)))+1)
        a = a[:n]*float(it.get('volume', 1.0))
        if len(a) > 400: a[:200] *= np.linspace(0, 1, 200); a[-400:] *= np.linspace(1, 0, 400)
        k = int(s0*SR); m = min(len(a), N_scene-k)
        if m > 0: media[k:k+m] += a[:m]*0.8
    mix = remap(scene_mix+media*level(balance,'footage')) + music*level(balance,'music')
    sf.write(out_path, np.stack([mix, mix], 1), SR, subtype='FLOAT')
    return out_path

def _lufs(path):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True)
    s = r.stderr[r.stderr.rfind('Summary'):]
    i = float(re.search(r'I:\s+(-?[\d.]+) LUFS', s).group(1)); pk = re.search(r'Peak:\s+(-?[\d.]+|-inf) dBFS', s)
    return i, (float(pk.group(1)) if pk and pk.group(1) != '-inf' else -99)

def master(raw, out, target=-14.0, peak=-1.2):
    """gentle compression, then gain + limiter solved so integrated loudness hits `target`
    and the true peak stays at or below `peak` (dBTP)"""
    def run(gain, lim_db):
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', raw, '-af',
                        f'acompressor=threshold=-24dB:ratio=3:attack=6:release=120:makeup=4dB,volume={gain:.2f}dB,'
                        f'alimiter=limit={10**(lim_db/20):.4f}:attack=2:release=60:level=false', '-ar', str(SR), '-c:a', 'pcm_s24le', out], check=True)
        return _lufs(out)
    gain, lim_db = 8.5, peak-0.55          # true peaks overshoot the limiter slightly
    for _ in range(6):
        i, pk = run(gain, lim_db)
        ok_l, ok_p = abs(i-target) < 0.25, pk <= peak+0.05
        if ok_l and ok_p: break
        if not ok_p: lim_db -= (pk-peak)+0.1
        if not ok_l: gain += (target-i)*1.05
    return i, pk
