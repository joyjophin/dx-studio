"""Fast, actionable file checks before a costly export; no frame rendering."""
from pathlib import Path
from .paths import contained
import os
import shutil


def inspect_project(project):
    findings = []
    destination=Path(project.output)
    parent=destination.parent
    while not parent.exists() and parent!=parent.parent:parent=parent.parent
    try:
        if not parent.is_dir() or not os.access(parent,os.W_OK):raise OSError('The export folder is not writable')
        free=shutil.disk_usage(parent).free
        if free<16*1024*1024:raise OSError('Less than 16 MB of disk space remains')
        if free<1024*1024*1024:findings.append({'severity':'warning','kind':'storage','layers':[],'message':'Less than 1 GB of disk space remains. Exports and decoded footage need working space.','fix':'Free disk space before a longer export. The final size depends on your project.'})
    except OSError as error:findings.append({'severity':'error','kind':'storage','layers':[],'message':str(error),'fix':'Choose a writable export folder inside the project and free disk space.'})
    from .relink import references
    if str(destination.resolve()) in references(project):findings.append({'severity':'error','kind':'output','layers':[],'message':'The export filename is also a source asset.','fix':'Choose a separate MP4 filename in Export.'})
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
    for item in project.values.get('__media',[]):
        state=project.values['__layers'].get(item['id'],{})
        if item.get('kind') not in ('video','gif') or item.get('loop') or not state.get('visible',True):continue
        try:duration=project.media.inspect(item['file'])['duration']
        except (OSError,ValueError,RuntimeError):continue
        offset=item.get('source_offset',0)
        if duration and offset>=duration:findings.append({'severity':'error','kind':'media','layers':[item['id']],'message':item.get('name','Clip')+': source in point is beyond the recording.','fix':'Choose an earlier source in point or replace this clip.'})
        elif duration and offset+state.get('end',item['t0']+item['dur'])-state.get('start',item['t0'])>duration+.05:findings.append({'severity':'warning','kind':'media','layers':[item['id']],'message':item.get('name','Clip')+': the clip extends beyond its source.','fix':'Trim the clip or enable Loop. Video holds its last frame after the recording ends; its audio stops.'})
    from .subtitles import findings as caption_findings
    findings.extend(caption_findings(project))
    return {'ok':not any(f['severity']=='error' for f in findings), 'findings':findings}


def require_ready(project):
    report = inspect_project(project)
    errors = [f['message'] for f in report['findings'] if f['severity']=='error']
    if errors: raise ValueError('Export needs attention: ' + '; '.join(errors))
    return report
