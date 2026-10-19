"""dx_studio visual editor: works for any project that follows PROJECT_FORMAT.md.

    python3 -m dx_studio edit projects/my-video

Panels and timeline lanes are generated from the scene's SCHEMA. The preview is rendered by the
project's own scene code, so what you see is exactly what gets built.
"""
import contextlib, copy, hashlib, io, json, os, re, subprocess, sys, threading, time, webbrowser, signal, uuid
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from .paths import contained
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.dirname(HERE)          # folder that contains dx_studio/

class Editor:
    def __init__(self, path):
        from .project import Project
        self.pr = Project(path)
        self.lock = threading.RLock()
        self.saved = copy.deepcopy(self.pr.values)
        from .history import SettingsHistory
        self.history = SettingsHistory(self.pr.path)
        self.revision = self.history.revision()
        source = hashlib.sha256()
        for name in ('project.json', self.pr.cfg.get('scene', 'scene.py'), self.pr.cfg.get('captions', 'captions.json')):
            file = os.path.join(self.pr.path, name)
            if os.path.isfile(file):
                with open(file, 'rb') as stream: source.update(stream.read())
        self.source_revision = source.hexdigest()
        from .source_sync import snapshot
        self.disk_files = snapshot(self.pr,self.saved)
        self.source_generation = 0
        self._audio_timer = None
        self.audio_version = 0; self.audio_busy = False; self._audio_again = False
        self.build_lock=threading.RLock();self.build_process=None;self.build_thread=None
        self.build = {'running':False,'progress':0.0,'log':[],'done':False,'ok':None,'id':None,
                      'state':'idle','cancelled':False,'cancel_requested':False,'revision':None,'started_at':None}
        self._thumbs = {}
        from .preview_cache import PreviewCache
        self.preview_cache=PreviewCache()
        self.share_directory=None;self.shared_bundles={}

    # ---------------- helpers
    def env(self):
        e = dict(os.environ); e['PYTHONPATH'] = KIT_ROOT+os.pathsep+e.get('PYTHONPATH', '')
        e['PATH'] = os.path.dirname(sys.executable)+os.pathsep+e.get('PATH', ''); e['PYTHONUNBUFFERED'] = '1'
        return e
    @property
    def audio_path(self): return os.path.join(self.pr.path, '.build', 'mix_raw.wav')
    def has_audio(self):
        from .mix_controls import settings, level
        mix=settings(self.pr)
        return bool((level(mix,'voice')>0 and any(not take.get('muted') and take.get('gain',1)>0 for take in self.pr.voices())) or
                    (level(mix,'music')>0 and self.pr.cfg.get('music')) or
                    (level(mix,'effects')>0 and self.pr.cues()) or
                    (level(mix,'footage')>0 and any(m.get('kind')=='video' and not m.get('muted') and
                     self.pr.values['__layers'].get(m['id'],{}).get('visible',True) for m in self.pr.values.get('__media',[]))))

    def stickers(self):
        d = os.path.join(self.pr.path, self.pr.cfg.get('assets', 'assets'), 'Avatars')
        return sorted(f[:-4] for f in os.listdir(d) if f.endswith('.png')) if os.path.isdir(d) else []

    def thumb(self, name):
        if name not in self._thumbs:
            from .stickers import sticker_path
            im = Image.open(sticker_path(name)).convert('RGBA')
            bb = im.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox()
            if bb: im = im.crop(bb)
            im.thumbnail((140, 140)); b = io.BytesIO(); im.save(b, 'PNG'); self._thumbs[name] = b.getvalue()
        return self._thumbs[name]

    @contextlib.contextmanager
    def preview(self, solo=None):
        with self.lock:
            if not solo:
                yield
                return
            if not isinstance(solo,list) or len(solo)>200 or any(not isinstance(x,str) for x in solo): raise ValueError('Invalid solo selection')
            parents = {m['id']:m['parent'] for m in self.pr.layer_meta}
            keep = set(solo) & parents.keys()
            for identifier in list(keep):
                parent = parents[identifier]
                while parent:
                    keep.add(parent); parent = parents.get(parent)
            for identifier in parents:
                parent = identifier
                while parent:
                    if parent in solo: keep.add(identifier); break
                    parent = parents.get(parent)
            original = copy.deepcopy(self.pr.values)
            isolated = copy.deepcopy(original)
            for identifier,state in isolated['__layers'].items():
                if identifier not in keep: state['visible'] = False
            try:
                self.pr.apply(isolated)
                yield
            finally: self.pr.apply(original)

    def frame(self, t, scale, solo=None):
        with self.preview(solo):
            key=self.preview_cache.key(self.pr,t,scale,solo)
            cached=self.preview_cache.get(key)
            if cached is not None:return cached
            s = self.pr.render(t, scale)
            w, h = s.get_width(), s.get_height()
            a = np.frombuffer(bytes(s.get_data()), np.uint8).reshape(h, s.get_stride()//4, 4)[:, :w, :]
            b = io.BytesIO(); Image.fromarray(a[..., [2, 1, 0]].copy(), 'RGB').save(b, 'JPEG', quality=84)
            data=b.getvalue();self.preview_cache.put(key,data);return data

    def apply(self, values):
        if not isinstance(values, dict): raise ValueError('Editable values must be an object')
        clean = copy.deepcopy(self.pr.defaults)
        clean.update({k: v for k, v in values.items() if k in clean})
        with self.lock:
            before = copy.deepcopy(self.pr.values)
            try: self.pr.apply(clean)
            except Exception:
                self.pr.apply(before)
                raise

    def regen_audio(self):
        with self.lock:
            if self.audio_busy:
                self._audio_again = True
                return
            if not self.has_audio(): return
            self.audio_busy = True; self._audio_again = False
        def run():
            try: subprocess.run([sys.executable, '-m', 'dx_studio', 'audio', self.pr.path], cwd=KIT_ROOT, env=self.env(),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            finally:
                with self.lock:
                    self.audio_version += 1; self.audio_busy = False
                    again = self._audio_again
                if again: self.regen_audio()
        threading.Thread(target=run, daemon=True).start()

    def require_loaded_source(self):
        from .source_sync import status
        update=status(self)
        if update.get('error') or any(self.disk_files.get(name,{}).get('kind')=='source' or name.endswith('.py') for name in update['files']):
            from .history import SaveConflict
            raise SaveConflict('Scene files changed outside the editor. Reload AI changes before saving; your browser draft is kept.')

    def save(self, values=None, revision=None, autosave=False):
        with self.lock, self.history.writing():
            self.history.check(revision)
            self.require_loaded_source()
            if values is not None: self.apply(values)
            if self.pr.settings_diff() != self.history.read_settings():
                self.history.before_save(self.source_revision)
                self.pr.save_settings()
            self.saved = copy.deepcopy(self.pr.values)
            self.revision = self.history.revision()
            from .source_sync import acknowledge_save
            acknowledge_save(self)
            result = {'ok': True, 'revision': self.revision, 'values': copy.deepcopy(self.saved)}
        if self._audio_timer: self._audio_timer.cancel()
        if autosave:
            self._audio_timer = threading.Timer(2, self.regen_audio)
            self._audio_timer.daemon = True; self._audio_timer.start()
        else: self.regen_audio()
        return result

    def version(self, name, revision):
        with self.lock, self.history.writing():
            self.history.check(revision)
            return self.history.snapshot(self.history.read_settings(), self.source_revision, name)

    def restore(self, version_id, revision):
        with self.lock, self.history.writing():
            self.history.check(revision)
            self.require_loaded_source()
            record = self.history.get(version_id)
            values = self.pr.values_from_settings(record['settings'])
            before = copy.deepcopy(self.pr.values)
            self.apply(values)
            try:
                self.history.snapshot(self.history.read_settings(), self.source_revision, 'Before restoring ' + record['name'][:95], 'before-restore')
                self.pr.save_settings()
            except Exception:
                self.pr.apply(before)
                raise
            self.saved = copy.deepcopy(self.pr.values)
            self.revision = self.history.revision()
            from .source_sync import acknowledge_save
            acknowledge_save(self)
            state = self.state()
        self.regen_audio()
        return {'ok': True, 'state': state}

    def _terminate_build(self,process):
        if process.poll() is not None:return
        try:
            if os.name=='nt':subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            else:os.killpg(process.pid,signal.SIGTERM)
        except ProcessLookupError:return
        def force_stop():
            if os.name!='nt':
                time.sleep(3)
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
            else:
                try:process.wait(timeout=3)
                except subprocess.TimeoutExpired:process.kill()
        threading.Thread(target=force_stop,daemon=True).start()

    def cancel_build(self, identifier=None):
        with self.build_lock:
            if identifier is not None and identifier!=self.build['id']:raise ValueError('The export changed. Reopen progress before cancelling.')
            if not self.build['running']:return dict(self.build)
            self.build.update(cancel_requested=True,state='cancelling')
            process=self.build_process
        if process:self._terminate_build(process)
        return dict(self.build)

    def start_build(self,values=None,revision=None):
        from .preflight import require_ready
        from .history import atomic_json
        with self.build_lock,self.lock:
            if self.build['running']:raise ValueError('An export is already running. Open its progress or cancel it first.')
            self.save(values,revision)
            with self.lock:require_ready(self.pr)
            from .export_profiles import resolve as export_options
            options=export_options(self.pr);output=self.pr.output
            n=int(round(options['duration']*options['fps']));b=self.build
            job_id=uuid.uuid4().hex
            snapshot=os.path.join(self.pr.path,'.build','export-'+job_id+'.settings.json')
            os.makedirs(os.path.dirname(snapshot),exist_ok=True)
            atomic_json(snapshot,copy.deepcopy(self.saved))
            b.update(running=True,progress=0.0,log=[],done=False,ok=None,id=job_id,
                     output_file=os.path.relpath(output,self.pr.path),sidecar=options['captions']=='sidecar',state='preparing',cancelled=False,cancel_requested=False,revision=self.revision,started_at=time.time())
            self.build_process=None
            candidate=os.path.join(self.pr.path,'.build','export-'+b['id']+'.mp4')
        def run():
            code=None
            try:
                options={'start_new_session':True} if os.name!='nt' else {'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP}
                process=subprocess.Popen([sys.executable,'-m','dx_studio','build',self.pr.path,'--output',candidate,'--settings',snapshot],cwd=KIT_ROOT,env=self.env(),
                                         stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,**options)
                with self.build_lock:self.build_process=process;cancel=b['cancel_requested']
                if cancel:self._terminate_build(process)
                for line in process.stdout:
                    line=line.rstrip()
                    if line.startswith('Done ->'):line='Video encoded; finishing export'
                    with self.build_lock:
                        b['log']=(b['log']+[line])[-40:]
                        if not b['cancel_requested']:
                            match=re.match(r'frame (\d+)',line)
                            if match:b.update(state='rendering',progress=.08+.88*int(match.group(1))/max(1,n))
                            elif line.startswith('mastered'):b['progress']=.08
                            elif line.startswith('muxing'):b.update(state='muxing',progress=.97)
                code=process.wait()
            except Exception as error:
                with self.build_lock:b['log']=(b['log']+[f'{type(error).__name__}: {error}'])[-40:]
            finally:
                with self.build_lock:
                    cancelled=b['cancel_requested']
                    ok=code==0 and not cancelled
                    try:
                        if ok:
                            from .publishing import publish
                            captions=os.path.splitext(candidate)[0]+'.srt' if b.get('sidecar') else None
                            publish(candidate,output,captions);b['log']=(b['log']+['Saved '+os.path.basename(output)])[-40:]
                        elif os.path.isfile(candidate):os.unlink(candidate)
                        if os.path.isfile(os.path.splitext(candidate)[0]+'.srt'):os.unlink(os.path.splitext(candidate)[0]+'.srt')
                    except OSError as error:
                        ok=False;b['log']=(b['log']+[str(error)])[-40:]
                    b.update(running=False,done=True,ok=ok,cancelled=cancelled,
                             state='done' if ok else 'cancelled' if cancelled else 'failed',progress=1.0 if ok else b['progress'])
                    try:
                        if os.path.isfile(snapshot):os.unlink(snapshot)
                    except OSError:pass
                    self.build_process=None
        self.build_thread=threading.Thread(target=run,daemon=True);self.build_thread.start()

    def state(self):
        pr = self.pr
        return {'project': {'name': pr.name, 'id': hashlib.sha256(pr.path.encode()).hexdigest()[:24], 'description': pr.cfg.get('description', ''), 'width': pr.width, 'height': pr.height,
                            'fps': pr.fps, 'duration': pr.duration, 'base_duration': pr.base_duration, 'chapters': pr.cfg.get('chapters', []),
                            'safe_area': pr.cfg.get('safe_area'), 'layout': pr.layout, 'composition_supported': pr.composition_supported, 'output': os.path.basename(pr.output), 'folder': pr.path},
                'schema': pr.schema, 'layers': pr.layer_meta, 'values': pr.values, 'saved': self.saved, 'defaults': pr.defaults,
                'captions': [{k: c[k] for k in ('start', 'show_end', 'text')} for c in pr.captions],
                'stickers': self.stickers(), 'has_audio': self.has_audio(), 'audio_version': self.audio_version,
                'audio_busy':self.audio_busy,'has_captions': pr.has_captions, 'revision': self.revision, 'source_revision': self.source_revision,'source_generation':self.source_generation}

    def disk_status(self):
        from .source_sync import status
        with self.lock:return {**status(self),'generation':self.source_generation}

    def reload_source(self, revision, disk_revision):
        from pathlib import Path
        from .history import SaveConflict
        from .source_sync import snapshot, digest
        from .project import Project
        with self.build_lock,self.lock,self.history.writing():
            if self.build['running']:raise ValueError('Finish or cancel the current export before reloading source files')
            if getattr(self,'audio_busy',False) or any(job.get('running') for job in getattr(self,'creator_jobs',{}).values()):
                raise ValueError('Let the current audio or creator task finish, then reload')
            if revision!=self.revision:raise SaveConflict('Another editor tab reloaded this project. Refresh this tab; its browser draft is retained.')
            before=snapshot(self.pr,self.saved)
            if disk_revision!=digest(before):raise SaveConflict('Project files changed again. Review the latest update notice and retry.')
            # A broken or partly written scene never replaces the working editor.
            import importlib
            importlib.invalidate_caches()
            local_modules={name:module for name,module in list(sys.modules.items())
                           if getattr(module,'__file__',None) and Path(module.__file__).resolve().is_relative_to(Path(self.pr.path).resolve())}
            for name,module in local_modules.items():
                cached=getattr(module,'__cached__',None)
                if cached and Path(cached).is_file() and Path(cached).resolve().is_relative_to(Path(self.pr.path).resolve()):
                    Path(cached).unlink()
                sys.modules.pop(name,None)
            try:
                candidate=Project(self.pr.path)
                from .preflight import require_ready
                require_ready(candidate)
                candidate.render(min(.9,candidate.duration/2),min(.15,320/candidate.width))
                overrides=self.pr.settings_diff(self.saved)
                lost=[key for key in overrides if not key.startswith('__') and key not in candidate.defaults]
                new_ids={m['id'] for m in candidate.layer_meta}
                lost.extend('layer:'+key for key in overrides.get('__layers',{}) if key not in new_ids)
                if lost:raise ValueError('AI removed controls with saved edits: '+', '.join(lost[:8])+'. Ask it to preserve parameter keys and layer IDs; hide unused layers instead.')
                if snapshot(candidate,candidate.values)!=before:raise SaveConflict('Project files changed while loading. Wait for the assistant to finish and retry.')
            except Exception:
                sys.modules.update(local_modules)
                raise
            self.source_generation+=1
            self.pr=candidate;self.saved=copy.deepcopy(candidate.values)
            self.revision=self.history.revision()
            source=hashlib.sha256()
            for name in ('project.json',candidate.cfg.get('scene','scene.py'),candidate.cfg.get('captions','captions.json')):
                file=Path(candidate.path)/name
                if file.is_file():source.update(file.read_bytes())
            self.source_revision=source.hexdigest();self.disk_files=snapshot(candidate,self.saved)
            from .preview_cache import PreviewCache
            self.preview_cache=PreviewCache();self._thumbs.clear()
            if self._audio_timer:self._audio_timer.cancel()
            self.regen_audio()
            return {'ok':True,'state':copy.deepcopy(self.state())}

    def open_state(self):
        # New/reloaded tabs start from disk, never from another tab's preview.
        with self.lock, self.history.writing():
            update=self.disk_status()
            if update.get('error') or any(name!='settings.json' for name in update['files']):return copy.deepcopy(self.state())
            if update['changed']:self.source_generation+=1
            self.pr.apply(self.pr.load_settings())
            self.saved = copy.deepcopy(self.pr.values)
            self.revision = self.history.revision()
            from .source_sync import acknowledge_save
            acknowledge_save(self)
            return copy.deepcopy(self.state())

def make_handler(ed=None, workspace=None):
    from .brands import BrandLibrary
    brands=workspace.brands if workspace else BrandLibrary()
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def _send(self, code, body, ctype, extra=None):
            self.send_response(code); self.send_header('Content-Type', ctype); self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            for k, v in (extra or {}).items(): self.send_header(k, v)
            self.end_headers(); self.wfile.write(body)
        def _json(self, o, code=200): self._send(code, json.dumps(o, ensure_ascii=False).encode(), 'application/json')
        def _file(self, path, ctype, attachment=None):
            if not os.path.exists(path): return self._send(404, b'not built yet', 'text/plain')
            with open(path, 'rb') as f:
                size=os.fstat(f.fileno()).st_size;rng=self.headers.get('Range');s=0;e=size-1
                if rng:
                    m=re.fullmatch(r'bytes=(\d*)-(\d*)',rng)
                    if not m or not any(m.groups()):return self._send(416,b'Invalid range','text/plain',{'Content-Range':f'bytes */{size}'})
                    if m[1]:s=int(m[1]);e=min(int(m[2]) if m[2] else size-1,size-1)
                    else:s=max(0,size-int(m[2]))
                    if s>e or s>=size:return self._send(416,b'Invalid range','text/plain',{'Content-Range':f'bytes */{size}'})
                    self.send_response(206);self.send_header('Content-Range',f'bytes {s}-{e}/{size}')
                else:self.send_response(200)
                self.send_header('Content-Type',ctype);self.send_header('Accept-Ranges','bytes');self.send_header('Content-Length',str(max(0,e-s+1)));self.send_header('Cache-Control','no-store')
                if attachment:self.send_header('Content-Disposition',f'attachment; filename="{attachment}"')
                self.end_headers();f.seek(s);remaining=e-s+1
                while remaining>0:
                    data=f.read(min(1024*1024,remaining))
                    if not data:break
                    self.wfile.write(data);remaining-=len(data)
        def _body(self):
            n = int(self.headers.get('Content-Length', 0)); return json.loads(self.rfile.read(n) or b'{}')
        def _allowed(self, mutation=False):
            port = self.server.server_port
            hosts = {f'localhost:{port}', f'127.0.0.1:{port}'}
            origin = self.headers.get('Origin')
            if self.headers.get('Host') not in hosts or (origin and origin not in {f'http://{h}' for h in hosts}):
                self._json({'ok': False, 'error': 'This editor accepts local requests only'}, 403); return False
            if mutation and self.headers.get('X-DX-Studio-Client') != '1':
                self._json({'ok': False, 'error': 'Missing editor request header'}, 403); return False
            return True
        def _project_editor(self):
            if workspace and self.path.startswith('/project/'):
                parts = self.path.split('/', 3)
                if len(parts) < 4: raise ValueError('Open a project from the project home')
                self.path = '/' + parts[3]
                return workspace.editor(parts[2])
            return ed

        def _library_get(self, u):
            if not workspace: return False
            if u.path == '/home' or (u.path == '/' and ed is None):
                self._send(200, open(os.path.join(HERE,'home.html'),'rb').read(), 'text/html; charset=utf-8'); return True
            if u.path == '/api/library':
                from .scaffold import CATALOG
                self._json({'projects':workspace.library.list(),'templates':CATALOG, 'default_folder':os.path.join(os.path.expanduser('~'),'DX Studio Projects')}); return True
            if u.path.startswith('/template-preview/'):
                name=u.path.rsplit('/',1)[-1]
                if name not in {'showcase.jpg','comparison.jpg'}:raise ValueError('Unknown template preview')
                self._file(os.path.join(HERE,'template_previews',name),'image/jpeg');return True
            if u.path == '/api/library/thumbnail':
                identifier = parse_qs(u.query).get('id',[''])[0]
                workspace.library.find(identifier)
                thumbnail = workspace.thumbnail(identifier)
                self._send(200 if thumbnail else 404, thumbnail or b'No preview yet', 'image/jpeg' if thumbnail else 'text/plain'); return True
            return False

        def _library_post(self, u):
            if not workspace or not u.path.startswith('/api/library/'): return False
            body = self._body()
            if u.path == '/api/library/open': editor = workspace.open(body.get('path',''))
            elif u.path == '/api/library/create': editor = workspace.create(body)
            elif u.path == '/api/library/sample':
                editor=workspace.create({'name':'Your first explainer '+uuid.uuid4().hex[:6],'format':body.get('format','16:9'),'folder':body.get('folder')})
                self._json({'ok':True,'url':'/project/'+editor.state()['project']['id']+'/?tour=1'});return True
            elif u.path == '/api/library/forget':
                workspace.library.forget(body.get('id')); self._json({'ok':True}); return True
            else: return False
            self._json({'ok':True,'url':'/project/'+editor.state()['project']['id']+'/'}); return True

        def do_GET(self):
            if not self._allowed(): return
            u = urlparse(self.path); q = parse_qs(u.query)
            try:
                if self._library_get(u): return
                editor = self._project_editor()
                u = urlparse(self.path); q = parse_qs(u.query)
                if u.path == '/': return self._send(200, open(os.path.join(HERE, 'editor.html'), 'rb').read(), 'text/html; charset=utf-8')
                if u.path == '/theme.js': return self._send(200, open(os.path.join(HERE, 'theme.js'), 'rb').read(), 'text/javascript; charset=utf-8')
                if u.path == '/theme.css': return self._send(200, open(os.path.join(HERE, 'theme.css'), 'rb').read(), 'text/css; charset=utf-8')
                if u.path == '/motion.css': return self._send(200, open(os.path.join(HERE, 'motion.css'), 'rb').read(), 'text/css; charset=utf-8')
                if u.path == '/editor-shell.css':return self._send(200,open(os.path.join(HERE,'editor-shell.css'),'rb').read(),'text/css; charset=utf-8')
                if u.path == '/editor-ai.js':return self._send(200,open(os.path.join(HERE,'editor-ai.js'),'rb').read(),'text/javascript; charset=utf-8')
                if u.path == '/editor-shell.js':return self._send(200,open(os.path.join(HERE,'editor-shell.js'),'rb').read(),'text/javascript; charset=utf-8')
                if u.path == '/editor-view.js': return self._send(200, open(os.path.join(HERE, 'editor-view.js'), 'rb').read(), 'text/javascript; charset=utf-8')
                if u.path == '/editor-brand.js': return self._send(200, open(os.path.join(HERE, 'editor-brand.js'), 'rb').read(), 'text/javascript; charset=utf-8')
                if u.path == '/editor-captions.js': return self._send(200, open(os.path.join(HERE, 'editor-captions.js'), 'rb').read(), 'text/javascript; charset=utf-8')
                if u.path == '/editor-narration.js': return self._send(200, open(os.path.join(HERE, 'editor-narration.js'), 'rb').read(), 'text/javascript; charset=utf-8')
                if u.path == '/editor-audio.js': return self._send(200, open(os.path.join(HERE, 'editor-audio.js'), 'rb').read(), 'text/javascript; charset=utf-8')
                if u.path == '/editor-media.js': return self._send(200, open(os.path.join(HERE, 'editor-media.js'), 'rb').read(), 'text/javascript; charset=utf-8')
                if u.path == '/editor-bulk.js': return self._send(200, open(os.path.join(HERE, 'editor-bulk.js'), 'rb').read(), 'text/javascript; charset=utf-8')
                if u.path == '/editor-tools.js': return self._send(200, open(os.path.join(HERE, 'editor-tools.js'), 'rb').read(), 'text/javascript; charset=utf-8')
                if u.path == '/editor-guide.js': return self._send(200, open(os.path.join(HERE, 'editor-guide.js'), 'rb').read(), 'text/javascript; charset=utf-8')
                if u.path == '/api/system':
                    from .doctor import report
                    return self._json(report())
                if u.path == '/editor-session.js': return self._send(200, open(os.path.join(HERE, 'editor-session.js'), 'rb').read(), 'text/javascript; charset=utf-8')
                from .creator_api import get as creator_get
                if creator_get(self,editor,workspace,u,q):return
                if editor is None: return self._send(404,b'Open a project first','text/plain')
                if u.path == '/frame': return self._send(200, editor.frame(float(q.get('t', ['0'])[0]), min(1.0, max(0.05, float(q.get('s', ['0.45'])[0]))), json.loads(q.get('solo',['[]'])[0])), 'image/jpeg')
                if u.path == '/api/state': return self._json(editor.open_state())
                if u.path == '/api/source-status':return self._json(editor.disk_status())
                if u.path == '/api/brands': return self._json({'presets':brands.list()})
                if u.path == '/api/captions/export':
                    from .subtitles import export
                    format=q.get('format',['srt'])[0]
                    with editor.lock: data=export(editor.pr,format).encode('utf-8')
                    return self._send(200,data,'text/vtt; charset=utf-8' if format=='vtt' else 'application/x-subrip; charset=utf-8',{'Content-Disposition':f'attachment; filename="captions.{format}"'})
                if u.path == '/api/waveform':
                    from .waveform import cached_peaks
                    if not editor.has_audio(): return self._json({'ready':False,'message':'No preview audio'})
                    if editor.audio_busy: return self._json({'ready':False,'message':'Preparing preview audio…'})
                    try: return self._json(cached_peaks(editor.audio_path))
                    except (OSError,RuntimeError): return self._json({'ready':False,'message':'Preview audio is being updated. Try again shortly.'})
                if u.path == '/api/media':
                    with editor.lock: return self._json({'assets':editor.pr.media.catalog()})
                if u.path=='/api/bundle/download':
                    identifier=q.get('id',[''])[0]
                    path=editor.shared_bundles.get(identifier)
                    if not path:raise ValueError('This download expired. Prepare a new portable project.')
                    return self._file(path,'application/zip','dx-project.zip')
                if u.path == '/api/preflight':
                    from .preflight import inspect_project
                    with editor.lock: return self._json(inspect_project(editor.pr))
                if u.path == '/api/media/thumbnail':
                    with editor.lock: data = editor.pr.media.thumbnail(q.get('file',[''])[0])
                    return self._send(200,data,'image/jpeg')
                if u.path == '/api/versions': return self._json({'versions': editor.history.list(), 'source_revision': editor.source_revision})
                if u.path == '/api/hits':
                    with editor.preview(json.loads(q.get('solo',['[]'])[0])): h = editor.pr.hits(float(q.get('t', ['0'])[0]))
                    return self._json(h)
                if u.path == '/api/status':
                    return self._json({'external':editor.disk_status(),'audio_version': editor.audio_version, 'audio_busy': editor.audio_busy, 'build': editor.build, 'has_video':os.path.isfile(contained(editor.pr.path,editor.build.get('output_file') or os.path.relpath(editor.pr.output,editor.pr.path)))})
                if u.path.startswith('/thumb/'): return self._send(200, editor.thumb(unquote(u.path[7:])), 'image/png', {'Cache-Control': 'max-age=3600'})
                if u.path == '/audio': return self._file(editor.audio_path, 'audio/wav')
                if u.path in ('/video','/export-captions'):
                    identifier=q.get('job',[None])[0]
                    if identifier and identifier!=editor.build.get('id'):raise ValueError('This export is no longer selected')
                    path=contained(editor.pr.path,editor.build['output_file']) if identifier and editor.build.get('output_file') else editor.pr.output
                    return self._file(os.path.splitext(path)[0]+'.srt','application/x-subrip') if u.path=='/export-captions' else self._file(path,'video/mp4')
                self._send(404, b'not found', 'text/plain')
            except (BrokenPipeError, ConnectionResetError): pass
            except (ValueError, FileNotFoundError) as e: self._json({'ok':False,'error':str(e)},400)
            except Exception as e:
                import traceback; traceback.print_exc()
                self._json({'ok':False,'error':f'{type(e).__name__}: {e}'},500)
        def do_POST(self):
            if not self._allowed(mutation=True): return
            try: size = int(self.headers.get('Content-Length', '0'))
            except ValueError: return self._json({'ok':False, 'error':'Invalid Content-Length'}, 400)
            limit = 256*1024*1024 if urlparse(self.path).path.endswith(('/api/upload','/api/narration/upload','/api/creator/brand-import')) else 32*1024*1024 if urlparse(self.path).path.endswith('/api/creator/template-import') else 4*1024*1024
            if size < 0 or size > limit: return self._json({'ok':False, 'error':'Request too large'}, 413)
            u = urlparse(self.path)
            try:
                if self._library_post(u): return
                editor = self._project_editor(); u = urlparse(self.path)
                if editor is None: return self._json({'ok':False,'error':'Open a project first'},404)
                if u.path in ('/api/bundle','/api/bundle/prepare'):
                    import tempfile
                    from .bundle import pack
                    body=self._body()
                    if u.path.endswith('/prepare'):
                        with editor.lock:
                            if editor.share_directory is None:editor.share_directory=tempfile.TemporaryDirectory(prefix='dx-shares-')
                            identifier=uuid.uuid4().hex
                            path=pack(editor.pr.path,os.path.join(editor.share_directory.name,identifier+'.zip'),include_history=body.get('include_history') is True)
                            editor.shared_bundles[identifier]=path
                            for key in list(editor.shared_bundles)[:-2]:
                                old=editor.shared_bundles.pop(key)
                                try:old.unlink()
                                except OSError:pass
                        return self._json({'id':identifier,'url':'/api/bundle/download?id='+identifier,'bytes':path.stat().st_size})
                    with tempfile.TemporaryDirectory(prefix='dx-share-') as directory:
                        with editor.lock:path=pack(editor.pr.path,os.path.join(directory,'dx-project.zip'),include_history=body.get('include_history') is True)
                        size=path.stat().st_size
                        self.send_response(200);self.send_header('Content-Type','application/zip');self.send_header('Content-Length',str(size));self.send_header('Content-Disposition','attachment; filename="dx-project.zip"');self.send_header('Cache-Control','no-store');self.end_headers()
                        with path.open('rb') as stream:
                            while data:=stream.read(1024*1024):self.wfile.write(data)
                    return
                from .creator_api import post as creator_post
                if creator_post(self,editor,workspace,u,size):return
                if u.path == '/api/preview':
                    editor.apply(self._body())
                    with editor.lock:editor.pr.prepare_frame(float(parse_qs(u.query).get('t',['0'])[0]))
                    return self._json({'ok': True, 'layers': editor.pr.layer_meta, 'layout': editor.pr.layout, 'layer_defaults': editor.pr.defaults.get('__layers', {}), 'has_audio':editor.has_audio(),'output':os.path.basename(editor.pr.output)})
                if u.path == '/api/brands/resolve':
                    from .brands import resolve
                    body=self._body();return self._json(resolve(brands.get(body.get('id')),editor.pr.schema))
                if u.path == '/api/brands/save':
                    from .brands import capture
                    body=self._body()
                    with editor.lock: preset=capture(body.get('name'),editor.pr.schema,body.get('values'),body.get('keys'))
                    return self._json({'ok':True,'preset':brands.save(preset)})
                if u.path == '/api/brands/import':
                    body=self._body()
                    if body.get('format_version')!=1:raise ValueError('Unsupported brand preset format')
                    return self._json({'ok':True,'preset':brands.save(body)})
                if u.path == '/api/captions/import':
                    from .subtitles import prepare_import
                    body=self._body()
                    with editor.lock: result=prepare_import(body.get('text',''),editor.pr,body.get('timing','output'))
                    return self._json(result)
                if u.path == '/api/narration/upload':
                    from .narration import import_take
                    q=parse_qs(u.query)
                    take=import_take(editor.pr,unquote(q.get('name',['Recording'])[0]),self.rfile.read(size),q.get('t',['0'])[0])
                    return self._json({'ok':True,'take':take})
                if u.path == '/api/narration/import':
                    from .narration import import_take
                    from pathlib import Path
                    body=self._body(); source=Path(body.get('path','')).expanduser().resolve()
                    if not source.is_file() or source.stat().st_size>256*1024*1024: raise ValueError('Choose an audio file smaller than 256 MB')
                    take=import_take(editor.pr,source.name,source.read_bytes(),body.get('t',0))
                    return self._json({'ok':True,'take':take})
                if u.path == '/api/media/prepare':
                    body = self._body()
                    with editor.lock: item = editor.pr.media.item_for(body.get('file',''),float(body.get('t',0)))
                    return self._json({'ok':True,'item':item})
                if u.path == '/api/media/clip':
                    from .clips import prepare
                    body=self._body()
                    with editor.lock:
                        values=body.get('values',editor.pr.values)
                        editor.apply(values)
                        result=prepare(editor.pr,values,body.get('id'),body.get('operation'),body.get('at'),body.get('start'),body.get('end'))
                    return self._json(result)
                if u.path == '/api/media/relink':
                    from pathlib import Path
                    body = self._body(); source = Path(body.get('path','')).expanduser().resolve()
                    from .media import kind_of
                    if not kind_of(source.name): raise ValueError('Choose an image, GIF or video file')
                    if source.stat().st_size > 256*1024*1024: raise ValueError('Use a file smaller than 256 MB')
                    with editor.lock: item = editor.pr.media.import_file(source.name,source.read_bytes(),float(body.get('t',0)))
                    return self._json({'ok':True,'item':item})
                if u.path in ('/api/media/relink-folder','/api/media/relink-folder-apply'):
                    from .relink import plan,restore
                    body=self._body()
                    with editor.lock:
                        editor.apply(body.get('values',editor.pr.values))
                        result=restore(editor.pr,body.get('folder',''),body.get('selected',[])) if u.path.endswith('-apply') else plan(editor.pr,body.get('folder',''))
                    return self._json(result)
                if u.path == '/api/upload':
                    q = parse_qs(u.query); n = int(self.headers.get('Content-Length', 0)); data = self.rfile.read(n)
                    name = unquote(q.get('name', ['file'])[0]); t = float(q.get('t', ['0'])[0])
                    ctr = (float(q['x'][0]), float(q['y'][0])) if 'x' in q else None
                    with editor.lock:
                        item = editor.pr.media.import_file(name, data, t, ctr)
                        if q.get('library',['0'])[0]=='1': return self._json({'ok':True,'item':item})
                        vals = copy.deepcopy(editor.pr.values); vals['__media'] = vals.get('__media', []) + [item]
                        editor.pr.apply(vals)
                    return self._json({'ok': True, 'id': item['id'], 'state': editor.state()})
                if u.path == '/api/source-reload':
                    body=self._body()
                    return self._json(editor.reload_source(body.get('revision'),body.get('disk_revision')))
                if u.path == '/api/handoff':
                    body=self._body()
                    with editor.lock,editor.history.writing():
                        editor.history.check(body.get('revision'))
                        if editor.disk_status()['changed']:raise ValueError('Reload external project changes before preparing the handoff')
                        from .handoff import export,prompt
                        # Another tab's unsaved preview is not part of this handoff.
                        previous=copy.deepcopy(editor.pr.values)
                        try:
                            editor.pr.apply(editor.saved)
                            data=export(editor.pr,body.get('request',''),editor.revision,editor.source_revision)
                        finally:editor.pr.apply(previous)
                        return self._json({'document':data,'prompt':prompt(editor.pr.path,body.get('request',''))})
                if u.path == '/api/save':
                    body = self._body()
                    if 'revision' in body and 'values' in body:
                        if not isinstance(body['revision'], str): raise ValueError('A saved project revision is required')
                        return self._json(editor.save(body['values'], body['revision'], autosave=bool(body.get('autosave'))))
                    return self._json(editor.save(body))
                if u.path == '/api/versions/create':
                    body = self._body()
                    if not isinstance(body.get('revision'), str): raise ValueError('A saved project revision is required')
                    return self._json({'ok': True, 'version': editor.version(body.get('name'), body['revision'])})
                if u.path == '/api/versions/restore':
                    body = self._body()
                    if not isinstance(body.get('revision'), str): raise ValueError('A saved project revision is required')
                    return self._json(editor.restore(body.get('id'), body['revision']))
                if u.path == '/api/revert': editor.apply(copy.deepcopy(editor.saved)); return self._json({'values': editor.pr.values})
                if u.path == '/api/reset': editor.apply(copy.deepcopy(editor.pr.defaults)); return self._json({'values': editor.pr.values})
                if u.path == '/api/build/cancel':
                    body=self._body()
                    if not isinstance(body.get('id'),str):raise ValueError('The current export ID is required')
                    return self._json({'ok':True,'build':editor.cancel_build(body['id'])})
                if u.path == '/api/build':
                    body = self._body()
                    if 'revision' in body and 'values' in body: editor.start_build(body['values'], body['revision'])
                    else: editor.start_build(body)
                    return self._json({'ok': True, 'revision': editor.revision, 'build':dict(editor.build)})
                self._send(404, b'not found', 'text/plain')
            except Exception as e:
                from .history import SaveConflict
                if isinstance(e, SaveConflict): return self._json({'ok': False, 'error': str(e), 'conflict': True}, 409)
                if isinstance(e, (ValueError, OSError)): return self._json({'ok': False, 'error': str(e)}, 400)
                import traceback; traceback.print_exc()
                self._json({'ok': False, 'error': f'{type(e).__name__}: {e}'}, 500)
    return H

def serve(path=None, port=None, open_browser=None):
    from .library import Workspace
    workspace = Workspace()
    ed = workspace.open(path) if path else None
    port = port or int(os.environ.get('EDITOR_PORT', '8765')); srv = None
    for p in range(port, port+10):
        try: srv = ThreadingHTTPServer(('127.0.0.1', p), make_handler(ed, workspace)); break
        except OSError: continue
    if srv is None: sys.exit(f'No free port between {port} and {port+9}')
    url = f'http://localhost:{p}'
    print((f'Editing {ed.pr.name}' if ed else 'DX Studio projects') + f' at {url}   (Ctrl+C to stop)', flush=True)
    if open_browser if open_browser is not None else not os.environ.get('NO_BROWSER'):
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try: srv.serve_forever()
    except KeyboardInterrupt: print('\nStopped.')
    finally:
        editors=list(workspace.editors.values())
        for editor in editors:
            editor.cancel_build()
            if editor._audio_timer:editor._audio_timer.cancel()
        deadline=time.monotonic()+4
        for editor in editors:
            if editor.build_thread:editor.build_thread.join(max(0,deadline-time.monotonic()))
            if editor.share_directory:editor.share_directory.cleanup()
        srv.server_close()
