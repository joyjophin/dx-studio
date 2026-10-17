"""Portable named palettes and exposed type-size presets, independent of scene code."""
import contextlib
import copy
import json
import math
from pathlib import Path
import re
import threading
import uuid
from .history import atomic_json
from .paths import file_lock


def eligible(entry):
    return entry['type']=='color' or (entry['type']=='number' and entry['key'].endswith('_size'))


def validate(name,tokens):
    if not isinstance(name,str) or not name.strip() or len(name)>80:raise ValueError('Use a preset name of up to 80 characters')
    if not isinstance(tokens,list) or not 1<=len(tokens)<=100:raise ValueError('A preset needs between 1 and 100 colour or size fields')
    clean=[];seen=set()
    for token in tokens:
        if not isinstance(token,dict):raise ValueError('Invalid preset field')
        key=token.get('key');kind=token.get('type');value=token.get('value')
        if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,99}',key) or key in seen:raise ValueError('Preset field keys must be unique public parameter names')
        if kind=='color':
            if not isinstance(value,str) or not re.fullmatch(r'#[a-fA-F0-9]{6}',value):raise ValueError('Use six-digit hex colours')
        elif kind=='number' and key.endswith('_size'):
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<value<=500:raise ValueError('Type sizes must be finite numbers between 0 and 500')
        else:raise ValueError('Only colour and exposed type-size fields belong in a brand preset')
        clean.append({'key':key,'label':str(token.get('label') or key)[:100],'type':kind,'value':value});seen.add(key)
    return {'name':name.strip(),'tokens':clean}


def capture(name,schema,values,keys=None):
    if not isinstance(values,dict):raise ValueError('Current project values are required')
    if keys is not None and (not isinstance(keys,list) or any(not isinstance(key,str) for key in keys)):raise ValueError('Choose parameter keys for this preset')
    return validate(name,[{'key':entry['key'],'label':entry['label'],'type':entry['type'],'value':values[entry['key']]}
                          for entry in schema if eligible(entry) and (keys is None or entry['key'] in keys)])


def resolve(preset,schema):
    fields={entry['key']:entry for entry in schema if eligible(entry)};values={};skipped=[];clamped=[]
    for token in preset['tokens']:
        field=fields.get(token['key'])
        if not field or field['type']!=token['type']:skipped.append(token['key']);continue
        value=token['value']
        if token['type']=='number':
            if field.get('min') is not None:value=max(field['min'],value)
            if field.get('max') is not None:value=min(field['max'],value)
            if value!=token['value']:clamped.append(token['key'])
        values[token['key']]=value
    return {'values':values,'skipped':skipped,'clamped':clamped}


def builtin(identifier,name,colors):
    return {'id':identifier,'builtin':True,**validate(name,[{'key':key,'type':'color','value':value} for key,value in colors.items()])}

BUILTINS=[
    builtin('editorial','Editorial paper',dict(bg='#F5F3ED',ink='#182126',accent='#5056F4',surface='#FFFFFF',highlight='#D9F86F')),
    builtin('electric','Electric violet',dict(bg='#F1EFFF',ink='#26194A',accent='#7045E8',surface='#FFFFFF',highlight='#FFCA70')),
    builtin('midnight','Midnight',dict(bg='#141927',ink='#F4F6FC',accent='#8EA7FF',surface='#272F45',highlight='#A8F2D0')),
]


class BrandLibrary:
    def __init__(self,path=None):
        if path is None:
            from .library import ProjectLibrary
            path=ProjectLibrary().path.parent/'brands.json'
        self.path=Path(path).expanduser().resolve();self.lock=threading.RLock()

    @contextlib.contextmanager
    def writing(self):
        with self.lock,file_lock(self.path.with_suffix('.lock')):yield

    def read(self):
        if not self.path.is_file():return []
        data=json.loads(self.path.read_text(encoding='utf-8'))
        if data.get('format_version')!=1:raise ValueError('Unsupported brand library format')
        return data['presets']

    def list(self):
        with self.lock:return copy.deepcopy(BUILTINS+self.read())

    def get(self,identifier):
        preset=next((preset for preset in self.list() if preset['id']==identifier),None)
        if preset is None:raise ValueError('Unknown brand preset')
        return preset

    def save(self,preset):
        clean=validate(preset.get('name'),preset.get('tokens'))
        with self.writing():
            records=self.read()
            if len(records)>=100:raise ValueError('The local library already contains 100 brand presets')
            if any(record['name'].casefold()==clean['name'].casefold() for record in BUILTINS+records):raise ValueError('That preset name already exists. Choose a new name.')
            clean['id']=uuid.uuid4().hex[:16]
            self.path.parent.mkdir(parents=True,exist_ok=True)
            atomic_json(self.path,{'format_version':1,'presets':records+[clean]})
        return clean
