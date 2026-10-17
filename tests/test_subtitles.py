"""Caption interchange and timeline mapping are the critical regression boundaries."""
from types import SimpleNamespace
import pytest
from dx_studio.subtitles import parse,prepare_import,output_cues,export


def project(cues,edits=None,duration=6):
    from dx_studio.timemap import out_duration
    edits=edits or []
    return SimpleNamespace(values={'__captions':cues},base_duration=duration,duration=out_duration(duration,edits),edits=edits)


def test_srt_and_vtt_parse_plain_text_and_reject_broken_timing():
    srt='1\r\n00:00:01,000 --> 00:00:02,500\r\nA <b>clear</b> idea &amp; proof\r\n'
    cue=parse(srt)[0]
    assert cue=={'start':1,'end':2.5,'text':'A clear idea & proof','hl':None}
    assert parse('WEBVTT\n\nintro\n00:01.000 --> 00:02.500 align:start\nA clear idea &amp; proof')[0]==cue
    with pytest.raises(ValueError,match='end after'):parse('1\n00:00:02,000 --> 00:00:01,000\nNo')


def test_subtitle_exports_follow_holds_and_cuts_including_hold_boundary():
    cues=[{'start':a,'end':b,'text':text} for a,b,text in [(0,2,'Before'),(2,4,'Hold and play'),(4,5,'Removed'),(5,6,'After')]]
    pr=project(cues,[{'op':'insert','at':2,'dur':2},{'op':'delete','start':6,'end':7}])
    assert output_cues(pr)==[{'start':0,'end':2,'text':'Before'},{'start':2,'end':6,'text':'Hold and play'},{'start':6,'end':7,'text':'After'}]
    assert '00:00:02,000 --> 00:00:06,000' in export(pr)
    assert export(pr,'vtt').startswith('WEBVTT\n\n00:00:00.000')
    result=prepare_import('1\n00:00:06,000 --> 00:00:07,000\nAfter',pr)
    assert result['cues'][0]['start']==5 and result['cues'][0]['end']==6
    assert pr.values['__captions']==cues


from test_editor import editor_server,request
import json


def test_import_preview_does_not_replace_current_captions(editor_server):
    editor,port=editor_server;before=list(editor.pr.values['__captions'])
    headers={'Content-Type':'application/json','X-DX-Studio-Client':'1'}
    status,data=request(port,'POST','/api/captions/import',json.dumps({'text':'1\n00:00:01,000 --> 00:00:02,000\nA new caption'}),headers)
    assert status==200 and json.loads(data)['cues'][0]['text']=='A new caption'
    assert editor.pr.values['__captions']==before
    status,data=request(port,'GET','/api/captions/export?format=vtt')
    assert status==200 and data.startswith(b'WEBVTT\n\n')
