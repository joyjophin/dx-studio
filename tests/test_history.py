import copy
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from zipfile import ZipFile

import pytest

from dx_studio.bundle import pack
from dx_studio.editor import Editor
from dx_studio.history import SaveConflict
from dx_studio.project import Project
from dx_studio.scaffold import create
from test_editor import editor_server, request

HEADERS = {'Content-Type': 'application/json', 'X-DX-Studio-Client': '1'}


def post(port, path, body):
    status, raw = request(port, 'POST', path, json.dumps(body), HEADERS)
    return status, json.loads(raw)


def test_autosave_roundtrip_captions_layers_and_render(tmp_path):
    folder = create(tmp_path/'demo')
    ed = Editor(folder); ed.regen_audio = lambda: None
    values = copy.deepcopy(ed.saved)
    values['title'] = 'Saved automatically'
    values['__captions'][0]['text'] = 'A corrected caption'
    values['__layers']['row1'].update(x=154, scale=1.3, visible=False)
    values['__composition'] = 'bottom-right'
    result = ed.save(values, ed.revision, autosave=True)
    reopened = Editor(folder)
    assert reopened.saved == values
    assert reopened.revision == result['revision']
    assert bytes(ed.pr.render(1,.1).get_data()) == bytes(reopened.pr.render(1,.1).get_data())
    assert reopened.history.list()[0]['kind'] == 'initial'


def test_named_restore_preserves_current_settings_as_backup(tmp_path):
    folder = create(tmp_path/'demo')
    ed = Editor(folder); ed.regen_audio = lambda: None
    values = copy.deepcopy(ed.saved); values['title'] = 'First cut'
    ed.save(values, ed.revision)
    version = ed.version('Before sponsor change', ed.revision)
    values['title'] = 'Sponsor cut'; ed.save(values, ed.revision)
    restored = ed.restore(version['id'], ed.revision)
    assert restored['state']['values']['title'] == 'First cut'
    backup = next(v for v in ed.history.list() if v['kind'] == 'before-restore')
    assert ed.history.get(backup['id'])['settings']['title'] == 'Sponsor cut'
    assert Project(folder).values['title'] == 'First cut'
    ed.restore(backup['id'], ed.revision)
    assert Project(folder).values['title'] == 'Sponsor cut'


def test_stale_editor_cannot_overwrite_or_restore_newer_save(tmp_path):
    folder = create(tmp_path/'demo'); first = Editor(folder); second = Editor(folder)
    first.regen_audio = second.regen_audio = lambda: None
    original = first.version('Original', first.revision)
    stale = second.revision
    values = copy.deepcopy(first.saved); values['title'] = 'Other window'
    first.save(values, first.revision)
    values['title'] = 'Stale window'
    with pytest.raises(SaveConflict): second.save(values, stale)
    with pytest.raises(SaveConflict): second.restore(original['id'], stale)
    assert Project(folder).values['title'] == 'Other window'
    assert second.open_state()['saved']['title'] == 'Other window'


def test_simultaneous_writers_are_serialised(tmp_path):
    folder = create(tmp_path/'demo'); editors = [Editor(folder), Editor(folder)]
    gate = Barrier(2)
    def write(index):
        editor = editors[index]; editor.regen_audio = lambda: None
        values = copy.deepcopy(editor.saved); values['title'] = str(index)
        gate.wait()
        try: editor.save(values, editor.revision); return 'saved'
        except SaveConflict: return 'conflict'
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(write, range(2))) == ['conflict', 'saved']


def test_interrupted_write_keeps_previous_settings_and_named_version(tmp_path, monkeypatch):
    import dx_studio.history as history
    folder = create(tmp_path/'demo'); ed = Editor(folder); ed.regen_audio = lambda: None
    values = copy.deepcopy(ed.saved); values['title'] = 'Good cut'; ed.save(values, ed.revision)
    version = ed.version('Good cut', ed.revision)
    before = Path(ed.pr.settings_path).read_bytes()
    replace = history.os.replace
    def fail_settings(source, target):
        if Path(target).name == 'settings.json': raise OSError('Simulated disk failure')
        return replace(source, target)
    monkeypatch.setattr(history.os, 'replace', fail_settings)
    values['title'] = 'Interrupted edit'
    with pytest.raises(OSError): ed.save(values, ed.revision)
    assert Path(ed.pr.settings_path).read_bytes() == before
    assert ed.history.get(version['id'])['settings']['title'] == 'Good cut'
    assert not list(folder.glob('.dx-write-*'))


def test_automatic_history_is_bounded_but_named_versions_survive(tmp_path):
    ed = Editor(create(tmp_path/'demo')); ed.regen_audio = lambda: None
    ed.history.AUTO_INTERVAL = 0; ed.history.AUTO_LIMIT = 3
    named = ed.version('Keep this', ed.revision)
    for index in range(7):
        values = copy.deepcopy(ed.saved); values['title'] = str(index); ed.save(values, ed.revision)
    records = ed.history.list()
    assert len([v for v in records if v['kind'] == 'automatic']) == 3
    assert ed.history.get(named['id'])['name'] == 'Keep this'


def test_history_is_private_to_local_project_but_saved_result_bundles(tmp_path):
    folder = create(tmp_path/'demo'); ed = Editor(folder); ed.regen_audio = lambda: None
    values = copy.deepcopy(ed.saved); values['title'] = 'Portable cut'; ed.save(values, ed.revision)
    ed.version('Private working note', ed.revision)
    archive = pack(folder, tmp_path/'project.zip')
    with ZipFile(archive) as bundle:
        assert not any('.dx-studio/' in name for name in bundle.namelist())
        assert 'engine/dx_studio/editor-session.js' in bundle.namelist()
        assert json.loads(bundle.read('project/settings.json'))['title'] == 'Portable cut'


def test_autosave_http_revision_and_reload_does_not_adopt_preview(editor_server):
    ed, port = editor_server
    values = copy.deepcopy(ed.saved); values['title'] = 'On disk'
    status, result = post(port, '/api/save', {'values':values, 'revision':ed.revision, 'autosave':True})
    assert status == 200 and result['revision']
    preview = copy.deepcopy(values); preview['title'] = 'Uncommitted preview'
    assert post(port, '/api/preview', preview)[0] == 200
    state = json.loads(request(port, 'GET', '/api/state')[1])
    assert state['values']['title'] == state['saved']['title'] == 'On disk'
    stale = copy.deepcopy(values); stale['title'] = 'Stale edit'
    status, result = post(port, '/api/save', {'values':stale, 'revision':'obsolete'})
    assert status == 409 and result['conflict']
    assert Project(ed.pr.path).values['title'] == 'On disk'


def test_version_http_create_list_restore_and_input_errors(editor_server):
    ed, port = editor_server
    status, record = post(port, '/api/versions/create', {'name':'My version', 'revision':ed.revision})
    assert status == 200
    versions = json.loads(request(port, 'GET', '/api/versions')[1])['versions']
    assert versions[0]['name'] == 'My version' and 'settings' not in versions[0]
    status, result = post(port, '/api/versions/restore', {'id':record['version']['id'], 'revision':ed.revision})
    assert status == 200 and result['state']['saved'] == ed.saved
    assert post(port, '/api/versions/create', {'name':'', 'revision':ed.revision})[0] == 400
    assert post(port, '/api/versions/create', {'name':'x'})[0] == 400
    assert post(port, '/api/save', {'values':ed.saved, 'revision':None})[0] == 400
    assert post(port, '/api/versions/restore', {'id':'../../outside', 'revision':ed.revision})[0] == 400
    assert post(port, '/api/versions/restore', {'id':'a'*32, 'revision':ed.revision})[0] == 400
    status, script = request(port, 'GET', '/editor-session.js')
    assert status == 200 and b'DXEditorSession' in script


@pytest.mark.parametrize('route', ['/api/save', '/api/versions/create', '/api/versions/restore'])
def test_new_writes_require_local_editor_header(editor_server, route):
    _, port = editor_server
    assert request(port, 'POST', route, '{}')[0] == 403


def test_bad_history_file_does_not_hide_named_version(tmp_path):
    ed = Editor(create(tmp_path/'demo'))
    version = ed.version('Readable', ed.revision)
    (ed.history.directory/('f'*32+'.json')).write_text('broken')
    (ed.history.directory/('d'*32+'.json')).write_text('[]')
    bad = dict(version, id='e'*32, created_at=None)
    (ed.history.directory/('e'*32+'.json')).write_text(json.dumps(bad))
    assert ed.history.list()[0]['id'] == version['id']


def test_audio_refresh_requested_during_a_mix_is_not_lost(tmp_path, monkeypatch):
    import threading
    import time
    import dx_studio.editor as module
    ed = Editor(create(tmp_path/'demo'))
    first_started, release_first, finished = threading.Event(), threading.Event(), threading.Event()
    calls = []
    def mix(*args, **kwargs):
        calls.append(args)
        if len(calls) == 1:
            first_started.set(); assert release_first.wait(2)
        else: finished.set()
    monkeypatch.setattr(module.subprocess, 'run', mix)
    ed.regen_audio(); assert first_started.wait(2)
    ed.regen_audio(); release_first.set(); assert finished.wait(2)
    deadline = time.monotonic() + 2
    while ed.audio_busy and time.monotonic() < deadline: time.sleep(.01)
    assert len(calls) == ed.audio_version == 2
