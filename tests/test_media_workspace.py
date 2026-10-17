"""Only critical media paths: safe staging, relinking, cache identity and export blockers."""
import copy
import io
import json
from pathlib import Path
from PIL import Image
import pytest
from dx_studio.preflight import inspect_project, require_ready
from test_editor import editor_server, request


def png(color):
    out=io.BytesIO(); Image.new('RGB',(40,20),color).save(out,'PNG'); return out.getvalue()


def test_import_and_relink_stage_sources_without_overwriting_edits(editor_server,tmp_path):
    editor,port=editor_server
    headers={'X-DX-Studio-Client':'1','Content-Type':'application/json'}
    status,raw=request(port,'POST','/api/upload?library=1&name=logo.png',png('red'),headers)
    item=json.loads(raw)['item']; assert status==200 and editor.pr.values['__media']==[]
    values=copy.deepcopy(editor.pr.values); values['__media'].append(item)
    editor.save(values,editor.revision)
    editor.pr.values['__layers'][item['id']].update(x=70,start=2,end=5)
    saved=Path(editor.pr.settings_path).read_bytes()
    source=tmp_path/'new-logo.png'; source.write_bytes(png('blue'))
    status,raw=request(port,'POST','/api/media/relink',json.dumps({'path':str(source)}),headers)
    replacement=json.loads(raw)['item']; assert status==200
    assert item['file']!=replacement['file']
    assert Path(editor.pr.media.path(item)).is_file() and Path(editor.pr.media.path(replacement)).is_file()
    assert Path(editor.pr.settings_path).read_bytes()==saved
    assert editor.pr.values['__layers'][item['id']]['x']==70
    assert editor.pr.media.frames_dir(item)!=editor.pr.media.frames_dir(replacement)
    assert request(port,'GET','/api/media/thumbnail?file=../project.json')[0]==400
    assert request(port,'GET','/api/media/thumbnail?file='+item['file'])[1].startswith(b'\xff\xd8')


def test_missing_media_stays_editable_but_blocks_visible_exports(editor_server):
    editor,port=editor_server
    item=editor.pr.media.import_file('source.png',png('red'),0)
    values=copy.deepcopy(editor.pr.values);values['__media'].append(item);editor.apply(values)
    Path(editor.pr.media.path(item)).unlink()
    assert request(port,'GET','/frame?t=1&s=.1')[0]==200
    report=inspect_project(editor.pr)
    assert not report['ok'] and report['findings'][0]['layers']==[item['id']]
    with pytest.raises(ValueError,match='Export needs attention'):require_ready(editor.pr)
    editor.pr.values['__layers'][item['id']]['visible']=False
    assert require_ready(editor.pr)['ok']
    assert inspect_project(editor.pr)['findings'][0]['severity']=='warning'
