"""Sampled visual review and fresh mix checks; warnings are never a quality guarantee."""
import copy
import os
from pathlib import Path
import tempfile
from .preflight import inspect_project
from .paths import contained


def inspect(project,lock):
    report=inspect_project(project);findings=report['findings'];seen=set()
    from .timemap import out_time
    for finding in findings:
        finding['id']=finding['kind']+':'+str(finding.get('file',finding.get('caption','')))+':'+finding['message']
        if finding.get('at') is not None:finding['source_at']=finding['at'];finding['at']=out_time(finding['at'],project.edits)
    def add(kind,message,fix,at=None,layers=None,severity='warning'):
        key=kind+':'+','.join(layers or [])+':'+message
        if key in seen:return
        seen.add(key);findings.append({'id':key,'severity':severity,'kind':kind,'message':message,'fix':fix,'at':at,'layers':layers or []})
    from fontTools.ttLib import TTFont
    for role,file in project.values.get('__brand_assets',{}).get('fonts',{}).items():
        try:
            font=TTFont(contained(project.media.assets,file));cmap=font.getBestCmap() or {};font.close()
            texts=[str(project.values[e['key']]) for e in project.schema if e['type']=='text']+[c.get('text','') for c in project.values.get('__captions',[])]+[item.get('text','') for item in project.values['__media'] if item['kind']=='text']
            missing={char for char in ''.join(texts) if not char.isspace() and ord(char) not in cmap}
            if missing:add('font','Font '+role+' lacks '+str(len(missing))+' characters used in this project.','Review language coverage or choose another font.')
        except Exception as error:add('font','Font unavailable: '+file,'Replace it in Brand, or restore the bundled font.',severity='error')
    times={0.0,max(0,project.duration-1/project.fps),project.duration/2}
    from .timemap import out_time
    for scene in project.values.get('__story',[]):times.add(out_time((scene['start']+scene['end'])/2,project.edits))
    candidates=sorted(times);sampled=[candidates[round(i*(len(candidates)-1)/23)] for i in range(24)] if len(candidates)>24 else candidates
    for t in sampled:
        try:
            with lock:
                project.render(t,.08);hits=project.hits(t);area=project.layout.get('presenter')
                exempt=set(getattr(project.scene,'COMPOSITION_EXEMPT_LAYERS',()))
                presenter=project.values.get('__presenter',{}).get('media_id')
                for hit in hits:
                    points=hit['corners'];xs=[p[0] for p in points];ys=[p[1] for p in points]
                    if min(xs)<-2 or max(xs)>project.width+2 or min(ys)<-2 or max(ys)>project.height+2:add('bounds','Layer extends outside the frame.','Review its position or dismiss this intentional crop.',t,[hit['id']])
                    if area and hit['id']!=presenter and hit['id'] not in exempt and max(min(xs),area[0])<min(max(xs),area[2]) and max(min(ys),area[1])<min(max(ys),area[3]):add('presenter','Layer overlaps the presenter area.','Move it, change the scene layout or dismiss an intentional overlap.',t,[hit['id']])
        except Exception as error:add('frame','A sampled frame failed: '+str(error),'Repair the scene or media before export.',t,severity='error')
    try:
        import numpy as np
        import soundfile as sf
        from .audio import build_mix
        work=Path(project.path)/'.build';work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='quality-',dir=work) as folder:
            raw=build_mix(project,str(Path(folder)/'mix.wav'));peak=0.0;energy=0.0
            for chunk in sf.blocks(raw,blocksize=48000):
                peak=max(peak,float(np.max(np.abs(chunk))));energy+=float(np.sum(chunk*chunk))
            if peak>1:add('audio-peak',f'The unmastered mix peaks at {peak:.2f}.','Lower source balances and listen to the mastered export; limiting may change the sound.')
            if energy<1e-10:add('audio-silence','The current mix is silent.','Check whether narration and music should be audible, or dismiss if intentional.')
    except Exception as error:add('audio','Could not review the mix: '+str(error),'Repair missing sources or adjust Audio/Narration settings.',severity='error')
    ignored=set(project.values.get('__quality_ignores',[]))
    for finding in findings:finding['dismissed']=finding.get('id') in ignored and finding['severity']!='error'
    return {'ok':not any(f['severity']=='error' for f in findings),'findings':findings,'sampled_frames':min(len(times),24),'scope':'Sampled frames and the unmastered audio mix; review the final export too.'}
