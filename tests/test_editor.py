import copy
import http.client
import json
import threading
from http.server import ThreadingHTTPServer
import pytest
from dx_studio.editor import Editor, make_handler
from dx_studio.scaffold import create

@pytest.fixture
def editor_server(tmp_path):
    ed=Editor(create(tmp_path/'demo'))
    # Keep request tests independent of FFmpeg; audio regeneration is tested by export smoke.
    ed.regen_audio=lambda:None
    srv=ThreadingHTTPServer(('127.0.0.1',0),make_handler(ed))
    thread=threading.Thread(target=srv.serve_forever,daemon=True);thread.start()
    yield ed,srv.server_port
    srv.shutdown();srv.server_close();thread.join()

def request(port,method,path,body=None,headers=None):
    c=http.client.HTTPConnection('127.0.0.1',port)
    c.request(method,path,body,headers or {})
    r=c.getresponse();result=(r.status,r.read());c.close();return result

def test_editor_can_save_reopen_and_render_caption_edits(editor_server):
    ed,port=editor_server
    status,raw=request(port,'GET','/api/state')
    assert status==200
    values=json.loads(raw)['values'];values['title']='From the editor'
    values['__captions'][0]['text']='New caption'
    status,raw=request(port,'POST','/api/save',json.dumps(values),{'Content-Type':'application/json','X-DX-Studio-Client':'1'})
    assert status==200 and json.loads(raw)['ok']
    assert json.load(open(ed.pr.settings_path))['title']=='From the editor'
    status,jpeg=request(port,'GET','/frame?t=1&s=0.1')
    assert status==200 and jpeg.startswith(b'\xff\xd8')

@pytest.mark.parametrize('headers',[{}, {'X-DX-Studio-Client':'1','Origin':'https://example.com'}, {'X-DX-Studio-Client':'1','Host':'attacker.example'}])
def test_editor_rejects_cross_origin_writes(editor_server,headers):
    _,port=editor_server
    status,_=request(port,'POST','/api/reset','{}',headers)
    assert status==403

def test_editor_rejects_oversized_body_without_reading_it(editor_server):
    _,port=editor_server
    status,_=request(port,'POST','/api/save',None,{'X-DX-Studio-Client':'1','Content-Length':str(5*1024*1024)})
    assert status==413


def test_presenter_preference_updates_guides_and_is_saved(editor_server):
    ed,port=editor_server
    values=copy.deepcopy(ed.pr.values);values['__composition']='right-half'
    headers={'Content-Type':'application/json','X-DX-Studio-Client':'1'}
    status,raw=request(port,'POST','/api/preview',json.dumps(values),headers)
    assert status==200
    layout=json.loads(raw)['layout']
    assert layout['preset']=='right-half'
    assert layout['presenter']==[ed.pr.width/2,0,ed.pr.width,ed.pr.height]
    status,raw=request(port,'POST','/api/save',json.dumps(values),headers)
    assert status==200
    assert json.load(open(ed.pr.settings_path))['__composition']=='right-half'
    state=json.loads(request(port,'GET','/api/state')[1])
    assert state['project']['layout']==layout
    assert state['project']['composition_supported']
