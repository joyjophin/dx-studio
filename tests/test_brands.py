"""Brand presets must stay portable, type-safe and scoped to compatible style fields."""
import pytest
from dx_studio.brands import BrandLibrary,capture,resolve


def test_brand_capture_reopen_and_compatible_application(tmp_path):
    schema=[{'key':'accent','label':'Accent','type':'color'}, {'key':'caption_size','label':'Caption size','type':'number','min':22,'max':80}, {'key':'title','label':'Title','type':'text'}]
    preset=capture('My channel',schema,{'accent':'#123ABC','caption_size':90,'title':'Keep these words'})
    assert {token['key'] for token in preset['tokens']}=={'accent','caption_size'}
    library=BrandLibrary(tmp_path/'brands.json');saved=library.save(preset)
    reopened=BrandLibrary(tmp_path/'brands.json').get(saved['id'])
    result=resolve(reopened,schema)
    assert result['values']=={'accent':'#123ABC','caption_size':80}
    assert result['clamped']==['caption_size'] and 'title' not in result['values']
    assert resolve(reopened,[schema[0]])['skipped']==['caption_size']


def test_brand_import_rejects_private_state_and_duplicate_names(tmp_path):
    library=BrandLibrary(tmp_path/'brands.json')
    with pytest.raises(ValueError,match='public'):library.save({'name':'Bad','tokens':[{'key':'__layers','type':'number','value':1}]})
    preset={'name':'A palette','tokens':[{'key':'accent','type':'color','value':'#123ABC'}]}
    library.save(preset)
    with pytest.raises(ValueError,match='already exists'):library.save(preset)
    assert len(library.read())==1
