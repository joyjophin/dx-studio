const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
for(const file of ['editor.html','home.html']){const html=fs.readFileSync('dx_studio/'+file,'utf8');for(const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g))new vm.Script(match[1],{filename:file});}
for(const file of ['editor-bulk.js','editor-tools.js'])new vm.Script(fs.readFileSync('dx_studio/'+file,'utf8'),{filename:file});
const tools=require(process.cwd()+'/dx_studio/editor-tools.js');
assert.deepEqual(tools.roots(['parent','child'],[{id:'parent',parent:null},{id:'child',parent:'parent'}]),['parent']);
const hit=(id,x,y,w,h,base=[1,0,0,1])=>({id,corners:[[x,y],[x+w,y],[x+w,y+h],[x,y+h]],base});
assert.deepEqual(tools.localDelta(hit('rotated',0,0,1,1,[0,2,-2,0]),20,0),[0,-10]);
assert.deepEqual(tools.align([hit('a',10,20,20,30)],'center',[0,0,100,100]),[{id:'a',dx:30,dy:0}]);
const spacing=tools.align([hit('a',0,0,10,10),hit('b',20,0,10,10),hit('c',90,0,10,10)],'space-x');assert.equal(spacing.find(x=>x.id==='b').dx,25);
console.log('Editor scripts parse; selection hierarchy, transformed movement, alignment and spacing passed.');
