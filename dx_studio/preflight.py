"""Fast, actionable file checks before a costly export; no frame rendering."""
from pathlib import Path
from .paths import contained


def inspect_project(project):
    findings = []
    for asset in project.media.catalog(include_unused=False):
        if asset['status'] == 'ready' or not asset['used_by']: continue
        active = [identifier for identifier in asset['used_by']
                  if project.values['__layers'].get(identifier, {}).get('visible', True)]
        findings.append({'severity':'error' if active else 'warning', 'kind':'media',
                         'file':asset['file'], 'layers':asset['used_by'],
                         'message':f"{asset['name']}: {asset.get('error','Media unavailable')}",
                         'fix':'Relink or replace this asset in Media, or hide its layers.'})
    from .mix_controls import settings as mix_settings, level
    balance=mix_settings(project)
    sources = []
    for take in project.voices():
        if take.get('muted') or take.get('gain',1)<=0 or level(balance,'voice')<=0: continue
        file = take['file']; label = take['name']
        try:
            import soundfile as sf
            info = sf.info(contained(project.path,file))
            if take['offset']>=info.duration:
                raise ValueError('Source trim starts after the end of the recording')
            if take['start']>=project.base_duration:
                raise ValueError('Take starts after the end of the scene')
            if take['offset']+take['duration']>info.duration+.02 or take['start']+take['duration']>project.base_duration+.02:
                findings.append({'severity':'warning','kind':'narration','file':file,'layers':[],
                                 'message':f'{label}: the take extends beyond the recording or scene; only the available section plays.',
                                 'fix':'Adjust the source trim or duration in Narration.'})
        except (OSError,ValueError,RuntimeError) as error:
            findings.append({'severity':'error','kind':'narration','file':file,'layers':[],
                             'message':f'{label}: {error}',
                             'fix':'Replace the take, adjust its timing, or mute it in Narration.'})
    music = project.cfg.get('music')
    if isinstance(music, dict) and level(balance,'music')>0: sources.append((music.get('file'), 'Music'))
    for file, label in sources:
        if not file: continue
        try:
            path = contained(project.path, file)
            if not Path(path).is_file(): raise ValueError('File is missing')
            import soundfile as sf
            sf.info(path)
        except (OSError,ValueError,RuntimeError) as error:
            findings.append({'severity':'error','kind':'audio','file':file,'layers':[],
                             'message':f'{label}: {file} — {error}',
                             'fix':'Restore the audio file or update its path in project.json.'})
    from fontTools.ttLib import TTFont
    for role,file in project.values.get('__brand_assets',{}).get('fonts',{}).items():
        try:
            font=TTFont(contained(project.media.assets,file));font.getGlyphSet();font.close()
        except Exception as error:
            findings.append({'severity':'error','kind':'font','file':file,'layers':[],'message':'Brand font unavailable: '+file,'fix':'Replace it in Brand or restore the bundled fonts.'})
    from .subtitles import findings as caption_findings
    findings.extend(caption_findings(project))
    return {'ok':not any(f['severity']=='error' for f in findings), 'findings':findings}


def require_ready(project):
    report = inspect_project(project)
    errors = [f['message'] for f in report['findings'] if f['severity']=='error']
    if errors: raise ValueError('Export needs attention: ' + '; '.join(errors))
    return report
