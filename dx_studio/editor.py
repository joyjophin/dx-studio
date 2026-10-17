"""dx_studio visual editor: works for any project that follows PROJECT_FORMAT.md.

    python3 -m dx_studio edit projects/my-video

Panels and timeline lanes are generated from the scene's SCHEMA. The preview is rendered by the
project's own scene code, so what you see is exactly what gets built.
"""
import copy, hashlib, io, json, os, re, subprocess, sys, threading, time, webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
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
        self._audio_timer = None
        self.audio_version = 0; self.audio_busy = False; self._audio_again = False
        self.build = {'running': False, 'progress': 0.0, 'log': [], 'done': False, 'ok': None}
        self._thumbs = {}

    # ---------------- helpers
    def env(self):
        e = dict(os.environ); e['PYTHONPATH'] = KIT_ROOT+os.pathsep+e.get('PYTHONPATH', '')
        e['PATH'] = os.path.dirname(sys.executable)+os.pathsep+e.get('PATH', ''); e['PYTHONUNBUFFERED'] = '1'
        return e
    @property
    def audio_path(self): return os.path.join(self.pr.path, '.build', 'mix_raw.wav')
    def has_audio(self): return bool(self.pr.cfg.get('voice') or self.pr.cfg.get('music') or self.pr.cues() or any(m.get('kind') == 'video' for m in self.pr.values.get('__media', [])))

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

    def frame(self, t, scale):
        with self.lock:
            s = self.pr.render(t, scale)
            w, h = s.get_width(), s.get_height()
            a = np.frombuffer(bytes(s.get_data()), np.uint8).reshape(h, s.get_stride()//4, 4)[:, :w, :]
        b = io.BytesIO(); Image.fromarray(a[..., [2, 1, 0]].copy(), 'RGB').save(b, 'JPEG', quality=84); return b.getvalue()

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

    def save(self, values=None, revision=None, autosave=False):
        with self.lock, self.history.writing():
            self.history.check(revision)
            if values is not None: self.apply(values)
            if self.pr.settings_diff() != self.history.read_settings():
                self.history.before_save(self.source_revision)
                self.pr.save_settings()
            self.saved = copy.deepcopy(self.pr.values)
            self.revision = self.history.revision()
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
            state = self.state()
        self.regen_audio()
        return {'ok': True, 'state': state}

    def start_build(self, values=None, revision=None):
        b = self.build
        if b['running']: return
        self.save(values, revision); n = int(round(self.pr.duration*self.pr.fps))
        b.update(running=True, progress=0.0, log=[], done=False, ok=None)
        def run():
            p = subprocess.Popen([sys.executable, '-m', 'dx_studio', 'build', self.pr.path], cwd=KIT_ROOT, env=self.env(),
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in p.stdout:
                line = line.rstrip(); b['log'] = (b['log']+[line])[-40:]
                m = re.match(r'frame (\d+)', line)
                if m: b['progress'] = 0.08+0.88*int(m.group(1))/max(1, n)
                elif line.startswith('mastered'): b['progress'] = 0.08
                elif line.strip() == 'done': b['progress'] = 0.97
            p.wait(); b.update(running=False, done=True, ok=(p.returncode == 0), progress=1.0 if p.returncode == 0 else b['progress'])
        threading.Thread(target=run, daemon=True).start()

    def state(self):
        pr = self.pr
        return {'project': {'name': pr.name, 'id': hashlib.sha256(pr.path.encode()).hexdigest()[:24], 'description': pr.cfg.get('description', ''), 'width': pr.width, 'height': pr.height,
                            'fps': pr.fps, 'duration': pr.duration, 'base_duration': pr.base_duration, 'chapters': pr.cfg.get('chapters', []),
                            'safe_area': pr.cfg.get('safe_area'), 'layout': pr.layout, 'composition_supported': pr.composition_supported, 'output': os.path.basename(pr.output), 'folder': pr.path},
                'schema': pr.schema, 'layers': pr.layer_meta, 'values': pr.values, 'saved': self.saved, 'defaults': pr.defaults,
                'captions': [{k: c[k] for k in ('start', 'show_end', 'text')} for c in pr.captions],
                'stickers': self.stickers(), 'has_audio': self.has_audio(), 'audio_version': self.audio_version,
                'has_captions': pr.has_captions, 'revision': self.revision, 'source_revision': self.source_revision}

    def open_state(self):
        # New/reloaded tabs start from disk, never from another tab's preview.
        with self.lock, self.history.writing():
            self.pr.apply(self.pr.load_settings())
            self.saved = copy.deepcopy(self.pr.values)
            self.revision = self.history.revision()
            return copy.deepcopy(self.state())

def make_handler(ed):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def _send(self, code, body, ctype, extra=None):
            self.send_response(code); self.send_header('Content-Type', ctype); self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            for k, v in (extra or {}).items(): self.send_header(k, v)
            self.end_headers(); self.wfile.write(body)
        def _json(self, o, code=200): self._send(code, json.dumps(o, ensure_ascii=False).encode(), 'application/json')
        def _file(self, path, ctype):
            if not os.path.exists(path): return self._send(404, b'not built yet', 'text/plain')
            size = os.path.getsize(path); rng = self.headers.get('Range')
            with open(path, 'rb') as f:
                if rng:
                    m = re.match(r'bytes=(\d*)-(\d*)', rng); s = int(m.group(1) or 0); e = min(int(m.group(2) or size-1), size-1)
                    f.seek(s); body = f.read(e-s+1); self.send_response(206); self.send_header('Content-Range', f'bytes {s}-{e}/{size}')
                else: body = f.read(); self.send_response(200)
            self.send_header('Content-Type', ctype); self.send_header('Accept-Ranges', 'bytes'); self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store'); self.end_headers(); self.wfile.write(body)
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
        def do_GET(self):
            if not self._allowed(): return
            u = urlparse(self.path); q = parse_qs(u.query)
            try:
                if u.path == '/': return self._send(200, open(os.path.join(HERE, 'editor.html'), 'rb').read(), 'text/html; charset=utf-8')
                if u.path == '/editor-session.js': return self._send(200, open(os.path.join(HERE, 'editor-session.js'), 'rb').read(), 'text/javascript; charset=utf-8')
                if u.path == '/frame': return self._send(200, ed.frame(float(q.get('t', ['0'])[0]), min(1.0, max(0.05, float(q.get('s', ['0.45'])[0])))), 'image/jpeg')
                if u.path == '/api/state': return self._json(ed.open_state())
                if u.path == '/api/versions': return self._json({'versions': ed.history.list(), 'source_revision': ed.source_revision})
                if u.path == '/api/hits':
                    with ed.lock: h = ed.pr.hits(float(q.get('t', ['0'])[0]))
                    return self._json(h)
                if u.path == '/api/status':
                    return self._json({'audio_version': ed.audio_version, 'audio_busy': ed.audio_busy, 'build': ed.build})
                if u.path.startswith('/thumb/'): return self._send(200, ed.thumb(unquote(u.path[7:])), 'image/png', {'Cache-Control': 'max-age=3600'})
                if u.path == '/audio': return self._file(ed.audio_path, 'audio/wav')
                if u.path == '/video': return self._file(ed.pr.output, 'video/mp4')
                self._send(404, b'not found', 'text/plain')
            except (BrokenPipeError, ConnectionResetError): pass
            except Exception as e:
                import traceback; traceback.print_exc()
                self._send(500, f'{type(e).__name__}: {e}'.encode(), 'text/plain')
        def do_POST(self):
            if not self._allowed(mutation=True): return
            try: size = int(self.headers.get('Content-Length', '0'))
            except ValueError: return self._json({'ok':False, 'error':'Invalid Content-Length'}, 400)
            limit = 256*1024*1024 if urlparse(self.path).path == '/api/upload' else 4*1024*1024
            if size < 0 or size > limit: return self._json({'ok':False, 'error':'Request too large'}, 413)
            u = urlparse(self.path)
            try:
                if u.path == '/api/preview':
                    ed.apply(self._body())
                    return self._json({'ok': True, 'layers': ed.pr.layer_meta, 'layout': ed.pr.layout, 'layer_defaults': ed.pr.defaults.get('__layers', {})})
                if u.path == '/api/upload':
                    q = parse_qs(u.query); n = int(self.headers.get('Content-Length', 0)); data = self.rfile.read(n)
                    name = unquote(q.get('name', ['file'])[0]); t = float(q.get('t', ['0'])[0])
                    ctr = (float(q['x'][0]), float(q['y'][0])) if 'x' in q else None
                    with ed.lock:
                        item = ed.pr.media.import_file(name, data, t, ctr)
                        vals = copy.deepcopy(ed.pr.values); vals['__media'] = vals.get('__media', []) + [item]
                        ed.pr.apply(vals)
                    return self._json({'ok': True, 'id': item['id'], 'state': ed.state()})
                if u.path == '/api/save':
                    body = self._body()
                    if 'revision' in body and 'values' in body:
                        if not isinstance(body['revision'], str): raise ValueError('A saved project revision is required')
                        return self._json(ed.save(body['values'], body['revision'], autosave=bool(body.get('autosave'))))
                    return self._json(ed.save(body))
                if u.path == '/api/versions/create':
                    body = self._body()
                    if not isinstance(body.get('revision'), str): raise ValueError('A saved project revision is required')
                    return self._json({'ok': True, 'version': ed.version(body.get('name'), body['revision'])})
                if u.path == '/api/versions/restore':
                    body = self._body()
                    if not isinstance(body.get('revision'), str): raise ValueError('A saved project revision is required')
                    return self._json(ed.restore(body.get('id'), body['revision']))
                if u.path == '/api/revert': ed.apply(copy.deepcopy(ed.saved)); return self._json({'values': ed.pr.values})
                if u.path == '/api/reset': ed.apply(copy.deepcopy(ed.pr.defaults)); return self._json({'values': ed.pr.values})
                if u.path == '/api/build':
                    body = self._body()
                    if 'revision' in body and 'values' in body: ed.start_build(body['values'], body['revision'])
                    else: ed.start_build(body)
                    return self._json({'ok': True, 'revision': ed.revision})
                self._send(404, b'not found', 'text/plain')
            except Exception as e:
                from .history import SaveConflict
                if isinstance(e, SaveConflict): return self._json({'ok': False, 'error': str(e), 'conflict': True}, 409)
                if isinstance(e, ValueError): return self._json({'ok': False, 'error': str(e)}, 400)
                import traceback; traceback.print_exc()
                self._json({'ok': False, 'error': f'{type(e).__name__}: {e}'}, 500)
    return H

def serve(path, port=None, open_browser=None):
    ed = Editor(path)
    if ed.has_audio() and not os.path.exists(ed.audio_path):
        print('Preparing preview audio (first run only)…', flush=True)
        subprocess.run([sys.executable, '-m', 'dx_studio', 'audio', ed.pr.path], cwd=KIT_ROOT, env=ed.env(), stdout=subprocess.DEVNULL)
    port = port or int(os.environ.get('EDITOR_PORT', '8765')); srv = None
    for p in range(port, port+10):
        try: srv = ThreadingHTTPServer(('127.0.0.1', p), make_handler(ed)); break
        except OSError: continue
    if srv is None: sys.exit(f'No free port between {port} and {port+9}')
    url = f'http://localhost:{p}'
    print(f'Editing "{ed.pr.name}" at {url}   (Ctrl+C to stop)', flush=True)
    if open_browser if open_browser is not None else not os.environ.get('NO_BROWSER'):
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try: srv.serve_forever()
    except KeyboardInterrupt: print('\nStopped.')
    finally: srv.server_close()
