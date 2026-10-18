"""Local editor endpoints for creator tools. Preparation never saves project settings."""
import copy
import json
from pathlib import Path
import threading
import uuid
from urllib.parse import parse_qs
from .paths import contained


def project_with(editor,values):
    from .project import Project
    with editor.lock:
        project=Project(editor.pr.path)
        project.apply(project.values_from_settings(values))
    return project


def template_library(editor,workspace):
    from .templates_library import TemplateLibrary
    root=workspace.library.path.parent if workspace else Path(editor.pr.path)/'.build'
    return TemplateLibrary(root/'templates')


def motion_library(editor,workspace):
    from .motion import MotionLibrary
    root=workspace.library.path.parent if workspace else Path(editor.pr.path)/'.build'
    return MotionLibrary(root/'motion.json')


def start_job(editor,kind,values,body):
    if not hasattr(editor,'creator_jobs'):editor.creator_jobs={};editor.creator_job_lock=threading.RLock()
    with editor.creator_job_lock:
        if any(job['running'] for job in editor.creator_jobs.values()):raise ValueError('A creator task is already running; let it finish first')
        identifier=uuid.uuid4().hex;job={'id':identifier,'kind':kind,'running':True,'ok':False,'result':None,'error':None}
        editor.creator_jobs={identifier:job}
    snapshot=copy.deepcopy(values)
    def run():
        try:
            project=project_with(editor,snapshot)
            if kind=='transcribe':
                from .transcripts import recognize
                take=next((t for t in project.voices() if t['id']==body.get('take_id')),None)
                if not take:raise ValueError('Select a narration take')
                result={'take_id':take['id'],'file':take['file'],'transcript':recognize(project,take)}
            elif kind=='quality':
                from .quality import inspect
                result=inspect(project,editor.lock)
            else:raise ValueError('Unknown creator task')
            with editor.creator_job_lock:job.update(result=result,ok=True)
        except Exception as error:
            with editor.creator_job_lock:job['error']=str(error)
        finally:
            with editor.creator_job_lock:job['running']=False
    threading.Thread(target=run,daemon=True).start();return copy.deepcopy(job)


def get(handler,editor,workspace,u,q):
    if u.path=='/editor-motion.js':
        handler._send(200,Path(__file__).with_name('editor-motion.js').read_bytes(),'text/javascript; charset=utf-8');return True
    if u.path=='/editor-creator.js':
        handler._send(200,Path(__file__).with_name('editor-creator.js').read_bytes(),'text/javascript; charset=utf-8');return True
    if editor is None:return False
    if u.path=='/api/creator/motion':handler._json({'styles':motion_library(editor,workspace).list()});return True
    if u.path=='/api/creator/speech':
        from .transcripts import speech_status
        handler._json(speech_status());return True
    if u.path=='/api/creator/job':
        identifier=q.get('id',[''])[0]
        with getattr(editor,'creator_job_lock',editor.lock):job=getattr(editor,'creator_jobs',{}).get(identifier)
        if not job:raise ValueError('This task is no longer available; start it again')
        handler._json({'job':copy.deepcopy(job)});return True
    if u.path=='/api/creator/layout':
        from .creator import layout_at
        with editor.lock:handler._json(layout_at(editor.pr,editor.pr.scene_t(float(q.get('t',['0'])[0]))))
        return True
    if u.path=='/api/creator/templates':handler._json({'templates':template_library(editor,workspace).list()});return True
    if u.path=='/api/creator/template-export':
        data=template_library(editor,workspace).get(q.get('id',[''])[0]);handler._send(200,json.dumps(data).encode(),'application/json',{'Content-Disposition':'attachment; filename="dx-template.json"'});return True
    if u.path=='/api/creator/brand-export':
        from .brand_assets import export_kit
        with editor.lock:data=export_kit(editor.pr,editor.saved)
        handler._send(200,data,'application/zip',{'Content-Disposition':'attachment; filename="dx-brand.zip"'});return True
    return False


def post(handler,editor,workspace,u,size):
    if not u.path.startswith('/api/creator/'):return False
    if u.path=='/api/creator/brand-import':
        from .brand_assets import import_kit
        with editor.lock:result=import_kit(editor.pr,handler.rfile.read(size))
        handler._json(result);return True
    body=handler._body();values=body.get('values',editor.pr.values)
    if not isinstance(values,dict):raise ValueError('Editable values are required')
    if u.path.startswith('/api/creator/motion-'):
        from .motion import capture,prepare
        library=motion_library(editor,workspace)
        if u.path.endswith('/motion-save'):
            project=project_with(editor,values);state=project.values['__layers'].get(body.get('layer_id'))
            if state is None:raise ValueError('Select an existing layer')
            handler._json({'style':library.save(capture(body.get('name'),state))});return True
        if u.path.endswith('/motion-import'):handler._json({'style':library.save(body.get('style'))});return True
        if u.path.endswith('/motion-delete'):library.delete(body.get('id'));handler._json({'ok':True});return True
        if u.path.endswith('/motion-prepare'):
            project=project_with(editor,values)
            handler._json(prepare(project,project.values,library.get(body.get('id')),body.get('ids'),body.get('duration'),body.get('stagger',0),body.get('calm',False)));return True
    if u.path=='/api/creator/job':handler._json({'job':start_job(editor,body.get('kind'),values,body)});return True
    if u.path=='/api/creator/transcript':
        from .transcripts import prepare
        take=next((t for t in values.get('__voice',[]) if t['id']==body.get('take_id')),None)
        if not take:raise ValueError('Select a narration take')
        handler._json({'transcript':prepare(editor.pr,take,body.get('text',''))});return True
    if u.path=='/api/creator/captions':
        from .transcripts import captions_for
        take=next((t for t in values.get('__voice',[]) if t['id']==body.get('take_id')),None)
        if not take:raise ValueError('Select a narration take')
        cues=captions_for(take,body.get('maximum',6))
        cues=[dict(cue,end=min(editor.pr.base_duration,cue['end'])) for cue in cues if cue['start']<editor.pr.base_duration]
        handler._json({'captions':cues});return True
    if u.path in ('/api/creator/retime','/api/creator/revision-review','/api/creator/revision-apply','/api/creator/revision-frame'):
        from . import revisions
        project=project_with(editor,values)
        proposal=revisions.retime(project,values) if u.path.endswith('/retime') else body.get('proposal')
        from .revisions import source_fingerprint
        fingerprint=source_fingerprint(editor.pr)
        if u.path.endswith('/retime'):proposal['source_revision']=fingerprint
        records=revisions.review(project,values,proposal,fingerprint)
        result={'proposal':proposal,'changes':records,'warnings':proposal.get('warnings',[])}
        if u.path.endswith('/revision-frame'):
            import base64,io
            proposed=revisions.apply(project,values,proposal,body.get('selected'),fingerprint)
            time=float(body.get('t',0))
            with editor.lock:
                def image():
                    stream=io.BytesIO();project.render(time,.3).write_to_png(stream);return 'data:image/png;base64,'+base64.b64encode(stream.getvalue()).decode()
                result['before_image']=image();project.apply(proposed);result['after_image']=image()
        if u.path.endswith('/revision-apply'):result['values']=revisions.apply(project,values,proposal,body.get('selected'),fingerprint)
        handler._json(result);return True
    if u.path=='/api/creator/reorder':
        from .creator import reorder
        new=reorder(copy.deepcopy(values),body.get('ids',[]));project_with(editor,new)
        handler._json({'values':new});return True
    if u.path=='/api/creator/block':
        from .blocks import prepare
        project=project_with(editor,values)
        with editor.lock:
            from .timemap import out_time
            project.prepare_frame(out_time(float(body.get('block',{}).get('start',0)),project.edits))
            new=prepare(project,values,body.get('block',{}));project.apply(new)
        handler._json({'values':copy.deepcopy(project.values)});return True
    if u.path=='/api/creator/font':
        from .brand_assets import import_font
        handler._json(import_font(editor.pr,body.get('path','')));return True
    library=template_library(editor,workspace)
    if u.path=='/api/creator/template-save':
        project=project_with(editor,values)
        handler._json(library.capture(project,values,body.get('ids',[]),body.get('name')));return True
    if u.path=='/api/creator/template-import':handler._json(library.save(body.get('template',{})));return True
    if u.path=='/api/creator/template-apply':
        project=project_with(editor,values)
        from .timemap import out_time
        with editor.lock:
            project.prepare_frame(out_time(float(body.get('start',0)),project.edits))
            new=library.apply(project,values,body.get('id'),float(body.get('start',0)),bool(body.get('brand')))
        project=project_with(editor,new)
        handler._json({'values':copy.deepcopy(project.values)});return True
    return False
