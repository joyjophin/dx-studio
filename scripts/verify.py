"""Verify a dx_studio project before handing it over: editor compatibility, timing, speed, and a contact sheet.

    python3 scripts/verify.py <project> [--every 2.0] [--no-sheet]

Exits non-zero if there are ERRORS. WARNINGS are things the editor can't control or that look off.
Run from the folder that contains dx_studio/.
"""
import argparse, json, os, re, sys, time
sys.path.insert(0, os.getcwd())

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--every', type=float, default=2.0); ap.add_argument('--no-sheet', action='store_true')
    a = ap.parse_args()
    if a.every <= 0: ap.error("--every must be positive")
    errors, warns = [], []
    try:
        from dx_studio.project import Project
        pr = Project(a.project)
    except Exception as e:
        import traceback; traceback.print_exc(); print('\nERROR: project failed to load'); sys.exit(1)
    cfg, sch = pr.cfg, pr.schema
    keys = {e['key'] for e in sch}
    kinds = {}
    for e in sch: kinds[e['type']] = kinds.get(e['type'], 0)+1
    print(f"{pr.name}: {pr.width}x{pr.height} @ {pr.fps} fps, {pr.duration:.1f} s")
    print('parameters:', ', '.join(f'{v} {k}' for k, v in sorted(kinds.items()) if not k in ('media', 'timeline')))
    # ---- layers
    if not pr.layers: errors.append('scene has no LAYERS: every visible element must be a Layer so the editor can select it')
    ids = [m['id'] for m in pr.layer_meta]
    if len(ids) != len(set(ids)): errors.append('duplicate layer ids')
    from dx_studio.layers import walk
    n_layers = 0
    for L, P, d in walk(pr.layers):
        n_layers += 1
        if L.box is None and not L.locked and L.children == []: warns.append(f'layer "{L.id}" has no box (it cannot be selected on the preview)')
        for k in L.params:
            if k not in keys: errors.append(f'layer "{L.id}" links unknown parameter "{k}"')
        if L.draw is None and not L.children: warns.append(f'layer "{L.id}" draws nothing and has no children')
    print(f'layers: {n_layers}')
    # ---- parameters used by at least one layer (so they show up when that element is selected)
    linked = {k for L, _, _ in walk(pr.layers) for k in L.params}
    unlinked = [e['key'] for e in sch if e['type'] in ('text', 'time') and e['key'] not in linked]
    if unlinked: warns.append(f'{len(unlinked)} text/time parameters are not linked to any layer (still editable in the Text/Timing tabs): {", ".join(unlinked[:8])}{"…" if len(unlinked) > 8 else ""}')
    # ---- hard-coded strings in draw code
    src = open(os.path.join(pr.path, cfg.get('scene', 'scene.py'))).read()
    lits = re.findall(r'\b(?:k?text)\(c,\s*(["\'])(.{2,60}?)\1', src)
    lits = [s for _, s in lits if re.search(r'[A-Za-z]{3,}', s)]
    if lits: warns.append(f'{len(lits)} on-screen strings are hard-coded in scene.py (make them "text" parameters): ' + '; '.join(f'"{s}"' for s in lits[:6]))
    hexes = set(re.findall(r"hexc\('(#[0-9A-Fa-f]{6})'\)", src.split('SCHEMA')[0]))
    if len(hexes) > 6: warns.append(f'{len(hexes)} colours are hard-coded in drawing code; derive tints from palette parameters in setup()')
    # ---- cues
    try:
        raw = list(pr.scene.cues(pr.params)) if hasattr(pr.scene, 'cues') else []
        from dx_studio.audio import SOUNDS
        for c in raw:
            if c.get('layer') and c['layer'] not in ids: errors.append(f'sound cue links unknown layer "{c["layer"]}"')
            if c['sound'] not in SOUNDS: errors.append(f'unknown sound "{c["sound"]}"')
            if not (0 <= c['at'] <= pr.duration): warns.append(f'sound "{c["sound"]}" at {c["at"]:.2f}s is outside the video')
        unlinked_cues = sum(1 for c in raw if not c.get('layer'))
        if raw and unlinked_cues > len(raw)*0.5: warns.append(f'{unlinked_cues}/{len(raw)} sound cues are not linked to a layer (they won\'t follow when layers move)')
        print(f'sound cues: {len(raw)}')
    except Exception as e: errors.append(f'cues() failed: {e}')
    # ---- voice / captions
    from dx_studio.mix_controls import settings as mix_settings, level
    vo = sorted((take for take in (pr.voices() if level(mix_settings(pr),'voice')>0 else []) if not take.get('muted') and take.get('gain',1)>0),key=lambda take:take['start']); last = 0
    for i, ln in enumerate(vo):
        p = os.path.join(pr.path, ln.get('file', ''))
        if not ln.get('file') or not os.path.isfile(p): errors.append(f'voice line {i} file missing: {ln.get("file")}'); continue
        import soundfile as sf
        d = min(ln['duration'],max(0,sf.info(p).duration-ln['offset']))
        if ln['start'] < last - 0.02: warns.append(f'voice line {i} overlaps the previous line')
        last = ln['start'] + d
    if vo and last > pr.base_duration + 0.02: errors.append(f'narration ends at {last:.2f}s but the scene is {pr.base_duration:.2f}s')
    if vo: print(f'voice: {len(vo)} lines, ends at {last:.2f}s')
    if pr.has_captions:
        for c in pr.captions:
            if c['show_end'] > pr.duration + 0.01: warns.append(f'caption "{c["text"][:30]}" runs past the end')
        print(f'captions: {len(pr.captions)}')
    # ---- presenter reservations (guides alone cannot validate a custom scene)
    if pr.layout['presenter']:
        from dx_studio.composition import presenter_collisions
        if not pr.composition_supported:
            warns.append('presenter reservation is guide-only: this scene does not declare responsive composition')
        collisions=presenter_collisions(pr,[i*pr.duration/12 for i in range(12)])
        if collisions: warns.append('layers overlap the reserved presenter area: '+', '.join(collisions))
    # ---- speed + contact sheet
    ts = [min(pr.duration-0.05, x*pr.duration/6) for x in range(6)]
    t0 = time.time(); [pr.render(t) for t in ts]; ms = (time.time()-t0)/len(ts)*1000
    print(f'render: {ms:.0f} ms/frame (first frames include caching)')
    if ms > 150: warns.append(f'frames are slow ({ms:.0f} ms); cache heavy drawing in setup()')
    for t in (0.0, pr.duration/2, pr.duration-0.05):
        if not pr.hits(t) and pr.layers: warns.append(f'nothing is selectable at {t:.1f}s')
    if not a.no_sheet:
        from PIL import Image
        n = int(pr.duration // a.every) + 1; cols = min(10, n); rows = (n+cols-1)//cols; tw_, th_ = 216, int(216*pr.height/pr.width)
        sheet = Image.new('RGB', (cols*tw_, rows*th_), 'white')
        for i in range(n):
            t = min(pr.duration-0.05, i*a.every); s = pr.render(t, 0.2)
            import numpy as np
            arr = np.frombuffer(bytes(s.get_data()), np.uint8).reshape(s.get_height(), s.get_stride()//4, 4)[:, :s.get_width(), [2, 1, 0]]
            sheet.paste(Image.fromarray(arr.copy()).resize((tw_, th_)), ((i % cols)*tw_, (i//cols)*th_))
        os.makedirs(os.path.join(pr.path, 'stills'), exist_ok=True)
        out = os.path.join(pr.path, 'stills', 'contact.png'); sheet.save(out); print('contact sheet:', out)
    for w in warns: print('WARNING:', w)
    for e in errors: print('ERROR:', e)
    print('OK' if not errors else f'{len(errors)} error(s)')
    sys.exit(1 if errors else 0)

if __name__ == '__main__': main()
