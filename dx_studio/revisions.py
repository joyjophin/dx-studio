"""Reviewable settings patches with field-level conflict and protection checks."""
import copy
import json
from .paths import contained

FORBIDDEN={'__proto__','prototype','constructor','__protected'}


def get(values,path):
    obj=values
    for key in path:obj=obj[key]
    return obj


def set_value(values,path,value):
    target=values
    for key in path[:-1]:target=target[key]
    target[path[-1]]=copy.deepcopy(value)


def blocked(values,path):
    protected=values.get('__protected',[])
    if path[0] in protected:return 'This section is protected'
    if path[0]=='__layers' and len(path)>1:
        if 'layer:'+str(path[1]) in protected:return 'This layer is protected'
        if values.get('__layers',{}).get(path[1],{}).get('locked'):return 'This layer is locked'
    if path[0]=='__media':
        items=values.get('__media',[])
        if len(path)==1:
            if any('layer:'+item['id'] in protected or values['__layers'].get(item['id'],{}).get('locked') for item in items):return 'Replace individual unlocked media fields instead'
        elif isinstance(path[1],int) and 0<=path[1]<len(items):
            identifier=items[path[1]]['id']
            if 'layer:'+identifier in protected or values['__layers'].get(identifier,{}).get('locked'):return 'This media layer is protected or locked'
    if path[0]=='__voice' and len(path)>1 and isinstance(path[1],int):
        take=values['__voice'][path[1]]
        if 'voice:'+take['id'] in protected:return 'This take is protected'
    # Whole-container replacement must not bypass protected or locked descendants.
    if len(path)==1 and path[0]=='__layers' and (any(x.startswith('layer:') for x in protected) or any(s.get('locked') for s in values.get('__layers',{}).values())):return 'Replace individual unlocked layer fields instead'
    if len(path)==1 and path[0]=='__voice' and any(x.startswith('voice:') for x in protected):return 'Replace individual unprotected take fields instead'
    return None


def review(project,values,proposal,source_revision=None):
    if not isinstance(proposal,dict) or proposal.get('format_version')!=1:raise ValueError('Use a DX Studio revision with format_version 1')
    changes=proposal.get('changes')
    if not isinstance(changes,list) or len(changes)>2000:raise ValueError('Use at most 2,000 changes')
    stale=source_revision and proposal.get('source_revision')!=source_revision
    result=[];seen=[]
    for change in changes:
        path=change.get('path') if isinstance(change,dict) else None
        if not isinstance(path,list) or not 1<=len(path)<=6 or any(not isinstance(p,(str,int)) or isinstance(p,bool) or p in FORBIDDEN for p in path) or path[0] not in project.defaults:raise ValueError('Revision paths must refer to existing editable values')
        reason='Scene source changed since this request' if stale else blocked(values,path)
        if path[0]=='__layers' and len(path)>1:
            relatives=project._ancestors(path[1])
            if any(path[1] in project._ancestors(m['id']) and (values.get('__layers',{}).get(m['id'],{}).get('locked') or 'layer:'+m['id'] in values.get('__protected',[])) for m in project.layer_meta):reason='A child layer is locked or protected'
            if any(values.get('__layers',{}).get(parent,{}).get('locked') or 'layer:'+parent in values.get('__protected',[]) for parent in relatives):reason='A parent layer is locked or protected'
        if not path[0].startswith('__'):
            if any(('layer:'+m['id'] in values.get('__protected',[]) or values.get('__layers',{}).get(m['id'],{}).get('locked')) and path[0] in m.get('params',[]) for m in project.layer_meta):reason='An affected layer is protected'
        if any(path[:len(other)]==other or other[:len(path)]==path for other in seen):raise ValueError('Revision changes must not overlap or repeat paths')
        seen.append(path)
        try:current=get(values,path)
        except (KeyError,IndexError,TypeError):current=None;reason='This target no longer exists'
        if 'before' not in change:reason='A before value is required to detect conflicts'
        elif current!=change['before']:reason='This value changed after the assistant request'
        if 'after' not in change:raise ValueError('Every change needs an after value')
        result.append({'path':path,'before':copy.deepcopy(current),'after':copy.deepcopy(change['after']),
                       'allowed':not reason,'reason':reason,'label':str(change.get('label') or ' / '.join(map(str,path)))[:200]})
    return result


def apply(project,values,proposal,selected=None,source_revision=None):
    records=review(project,values,proposal,source_revision);new=copy.deepcopy(values)
    selected=list(range(len(records))) if selected is None else selected
    if not isinstance(selected,list) or any(isinstance(i,bool) or not isinstance(i,int) or not 0<=i<len(records) for i in selected):raise ValueError('Choose valid revision changes')
    for i in selected:
        record=records[i]
        if not record['allowed']:raise ValueError(record['reason'])
        set_value(new,record['path'],record['after'])
    # Validate the entire resulting project without making the preview the committed revision.
    previous=project.values
    try:project.apply(new);new=copy.deepcopy(project.values)
    finally:project.apply(previous)
    return new


def retime(project,values):
    from .transcripts import visible_words
    changes=[];warnings=[]
    takes={take['id']:take for take in values.get('__voice',[])}
    for anchor_index,anchor in enumerate(values.get('__anchors',[])):
        take=takes.get(anchor.get('voice_id'))
        words=visible_words(take) if take else []
        word=next((w for w in words if w['id']==anchor.get('word_id')),None)
        if word is None:
            matches=[w for w in words if w['text'].casefold().strip('.,!?;:')==str(anchor.get('text','')).casefold().strip('.,!?;:')]
            if len(matches)==1:word=matches[0]
        if word is None:warnings.append('Missing or ambiguous word for '+str(anchor.get('layer_id','layer')));continue
        identifier=anchor.get('layer_id');state=values.get('__layers',{}).get(identifier)
        if not state or identifier not in {m['id'] for m in project.layer_meta}:warnings.append('Layer no longer exists: '+str(identifier));continue
        if any(values['__layers'].get(parent,{}).get('locked') for parent in project._ancestors(identifier)):warnings.append('Parent layer is locked: '+identifier);continue
        inherited=sum(values['__layers'][p]['start']-project.defaults['__layers'][p]['start'] for p in project._ancestors(identifier))
        target=word['start']+float(anchor.get('offset',0))-inherited;delta=target-state['start']
        if target<0 or state['end']+delta+inherited>project.base_duration: warnings.append('Retimed layer would leave the scene: '+identifier);continue
        if word['id']!=anchor['word_id']:changes.append({'path':['__anchors',anchor_index,'word_id'],'before':anchor['word_id'],'after':word['id'],'label':'Relink word reference'})
        for field in ('start','end'):
            changes.append({'path':['__layers',identifier,field],'before':state[field],'after':state[field]+delta,'label':identifier+' '+field})
    # Generated captions carry word references; manually edited text is retained.
    for index,cue in enumerate(values.get('__captions',[])):
        if not cue.get('voice_id') or not cue.get('word_ids'):continue
        take=takes.get(cue['voice_id']);words=visible_words(take) if take else []
        by_id={w['id']:w for w in words};aligned=[by_id.get(key) for key in cue['word_ids']]
        if not all(aligned):
            aligned=[]
            for old in cue.get('words',[]):
                matches=[w for w in words if w['text'].casefold().strip('.,!?;:')==old['text'].casefold().strip('.,!?;:')]
                aligned.append(matches[0] if len(matches)==1 else None)
        if not aligned or not all(aligned) or len(aligned)!=len(cue['word_ids']) or any(words.index(b)!=words.index(a)+1 for a,b in zip(aligned,aligned[1:])):warnings.append('Caption needs word review: '+cue.get('text','')[:40]);continue
        for field,value in [('start',aligned[0]['start']),('end',aligned[-1]['end']),('words',aligned),('word_ids',[w['id'] for w in aligned])]:
            changes.append({'path':['__captions',index,field],'before':copy.deepcopy(cue.get(field)),'after':value,'label':'Caption '+str(index+1)+' '+field})
    return {'format_version':1,'changes':[change for change in changes if change['before']!=change['after']],'warnings':warnings}


def source_fingerprint(project):
    import hashlib
    from pathlib import Path
    digest=hashlib.sha256()
    for name in ('project.json',project.cfg.get('scene','scene.py'),project.cfg.get('captions','captions.json')):
        path=Path(contained(project.path,name))
        if path.is_file():digest.update(path.read_bytes())
    return digest.hexdigest()
