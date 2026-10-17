"""Render a music + sound-effects-only version of a built project (same master chain, voice muted).

    python3 scripts/novoice.py <project> <out.mp4>

Run from the work folder that contains dx_studio/, after `python3 -m dx_studio build <project>`
(it reuses .build/video.mp4 and the build's mix). Deliver it next to the master so the user can record their own voice.
"""
import os, subprocess, sys
sys.path.insert(0, os.getcwd())
from dx_studio import cli, audio

def main():
    if len(sys.argv) < 3: sys.exit(__doc__)
    pr = cli._project(sys.argv[1]); out = sys.argv[2]; b = os.path.join(pr.path, '.build'); SR = audio.SR
    if not os.path.exists(os.path.join(b, 'video.mp4')): sys.exit('build the project first (python3 -m dx_studio build <project>)')
    mx = pr.cfg.get('mix', {}); target, peak = mx.get('loudness', -14.0), mx.get('peak', -1.2)
    def chain(raw, dst, gain, lim_db):
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', raw, '-af',
                        f'acompressor=threshold=-24dB:ratio=3:attack=6:release=120:makeup=4dB,volume={gain:.2f}dB,'
                        f'alimiter=limit={10**(lim_db/20):.4f}:attack=2:release=60:level=false', '-ar', str(SR), '-c:a', 'pcm_s24le', dst], check=True)
        return audio._lufs(dst)
    # find the gain the full mix needed, then apply the same chain to the voiceless mix (music/sfx keep their level)
    tmp = os.path.join(b, 'tmp_full.wav'); gain, lim = 8.5, peak - 0.55
    for _ in range(6):
        i, pk = chain(os.path.join(b, 'mix_raw.wav'), tmp, gain, lim)
        if abs(i - target) < 0.25 and pk <= peak + 0.05: break
        if pk > peak + 0.05: lim -= (pk - peak) + 0.1
        if abs(i - target) >= 0.25: gain += (target - i)*1.05
    for line in pr.cfg.get('voice', []): line['gain'] = 0.0
    nv_raw = os.path.join(b, 'mix_novoice_raw.wav'); audio.build_mix(pr, nv_raw)
    nv = os.path.join(b, 'master_novoice.wav'); chain(nv_raw, nv, gain, lim)
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', os.path.join(b, 'video.mp4'), '-i', nv, '-map', '0:v', '-map', '1:a',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-t', str(pr.duration), '-movflags', '+faststart', out], check=True)
    os.remove(tmp); print('wrote', out)

if __name__ == '__main__':
    main()
