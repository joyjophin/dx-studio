"""Critical batch checks: navigation isolation and non-destructive layer controls."""
import copy
import json
from pathlib import Path
import threading
from http.server import ThreadingHTTPServer

from dx_studio.editor import Editor, make_handler
from dx_studio.library import ProjectLibrary, Workspace
from dx_studio.project import Project
from dx_studio.scaffold import create
from test_editor import request


def test_recent_projects_do_not_execute_scenes_and_forgetting_keeps_files(tmp_path):
    folder=create(tmp_path/'video');library=ProjectLibrary(tmp_path/'library.json')
    record=library.remember(folder)
    (folder/'scene.py').write_text("raise RuntimeError('must not run while listing recents')")
    assert library.list()[0]['id']==record['id']
    library.forget(record['id'])
    assert library.list()==[] and (folder/'scene.py').is_file()


def test_workspace_routes_keep_two_projects_and_saves_separate(tmp_path):
    workspace=Workspace(ProjectLibrary(tmp_path/'library.json'))
    folders=[create(tmp_path/'first'),create(tmp_path/'second',format='16:9')]
    editors=[workspace.open(folder) for folder in folders]
    for editor in editors:editor.regen_audio=lambda:None
    server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(workspace=workspace))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        port=server.server_port
        assert b'Your next story' in request(port,'GET','/')[1]
        records=json.loads(request(port,'GET','/api/library')[1])['projects']
        assert len(records)==2
        identifier=editors[0].state()['project']['id'];prefix='/project/'+identifier
        state=json.loads(request(port,'GET',prefix+'/api/state')[1]);values=state['values'];values['title']='First project only'
        status,_=request(port,'POST',prefix+'/api/save',json.dumps({'values':values,'revision':state['revision']}),{'X-DX-Studio-Client':'1','Content-Type':'application/json'})
        assert status==200 and Project(folders[0]).values['title']=='First project only'
        assert Project(folders[1]).values['title']!='First project only'
        assert request(port,'GET',prefix+'/frame?t=1&s=.1')[0]==200
        assert request(port,'GET','/api/library/thumbnail?id=../outside')[0]==400
    finally:server.shutdown();server.server_close();thread.join()


def test_lock_rename_and_solo_preserve_the_export(tmp_path):
    folder=create(tmp_path/'video');editor=Editor(folder);editor.regen_audio=lambda:None
    values=copy.deepcopy(editor.saved);values['__layers']['row1'].update(locked=True,label='My custom label')
    editor.save(values,editor.revision)
    reopened=Project(folder)
    assert 'row1' not in {hit['id'] for hit in reopened.hits(1)}
    assert next(m for m in reopened.layer_meta if m['id']=='row1')['label']=='My custom label'
    surface=editor.pr.render(1,.1);before=bytes(surface.get_data());settings=Path(editor.pr.settings_path).read_bytes()
    editor.frame(1,.1,['title'])
    surface=editor.pr.render(1,.1)
    assert bytes(surface.get_data())==before
    assert Path(editor.pr.settings_path).read_bytes()==settings
