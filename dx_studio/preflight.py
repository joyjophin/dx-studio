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
    sources = [(line.get('file'), 'Narration') for line in project.cfg.get('voice', [])]
    music = project.cfg.get('music')
    if isinstance(music, dict): sources.append((music.get('file'), 'Music'))
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
    return {'ok':not any(f['severity']=='error' for f in findings), 'findings':findings}


def require_ready(project):
    report = inspect_project(project)
    errors = [f['message'] for f in report['findings'] if f['severity']=='error']
    if errors: raise ValueError('Export needs attention: ' + '; '.join(errors))
    return report
