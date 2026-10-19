"""A bounded JPEG cache. Keys include editable values and source file identities."""
from collections import OrderedDict
import hashlib
import json
from pathlib import Path
from .paths import contained


class PreviewCache:
    def __init__(self,limit=32*1024*1024,entries=120):
        self.limit=limit;self.entries=entries;self.data=OrderedDict();self.bytes=0;self.hits=0;self.misses=0

    def key(self,project,t,scale,solo):
        from .relink import references
        files=set(references(project))
        files.update(contained(project.path,project.cfg.get(key,default)) for key,default in [('scene','scene.py'),('captions','captions.json')])
        files.add(str(Path(project.path)/'project.json'))
        identity=[]
        for name in sorted(files):
            try:stat=Path(name).stat();identity.append((name,stat.st_size,stat.st_mtime_ns))
            except OSError:identity.append((name,None,None))
        payload=[project.values,identity,float(t),float(scale),sorted(solo or [])]
        return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).digest()

    def get(self,key):
        if key not in self.data:self.misses+=1;return None
        self.hits+=1;self.data.move_to_end(key);return self.data[key]

    def put(self,key,value):
        if key in self.data:self.bytes-=len(self.data.pop(key))
        if len(value)>self.limit:return
        self.data[key]=value;self.bytes+=len(value)
        while self.bytes>self.limit or len(self.data)>self.entries:
            _,old=self.data.popitem(last=False);self.bytes-=len(old)
