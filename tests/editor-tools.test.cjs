const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
for(const file of ['editor.html','home.html']){const html=fs.readFileSync('dx_studio/'+file,'utf8');for(const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g))new vm.Script(match[1],{filename:file});}
for(const file of ['editor-bulk.js','editor-tools.js','editor-media.js'])new vm.Script(fs.readFileSync('dx_studio/'+file,'utf8'),{filename:file});
const tools=require(process.cwd()+'/dx_studio/editor-tools.js');
assert.deepEqual(tools.roots(['parent','child'],[{id:'parent',parent:null},{id:'child',parent:'parent'}]),['parent']);
const hit=(id,x,y,w,h,base=[1,0,0,1])=>({id,corners:[[x,y],[x+w,y],[x+w,y+h],[x,y+h]],base});
assert.deepEqual(tools.localDelta(hit('rotated',0,0,1,1,[0,2,-2,0]),20,0),[0,-10]);
assert.deepEqual(tools.align([hit('a',10,20,20,30)],'center',[0,0,100,100]),[{id:'a',dx:30,dy:0}]);
const spacing=tools.align([hit('a',0,0,10,10),hit('b',20,0,10,10),hit('c',90,0,10,10)],'space-x');assert.equal(spacing.find(x=>x.id==='b').dx,25);
console.log('Editor scripts parse; selection hierarchy, transformed movement, alignment and spacing passed.');

// A replacement updates source identity only; all manual editing state stays intact.
const old={id:'media_a',file:'Media/a.png',name:'a.png',kind:'image',has_audio:false,box:[1,2,300,200],t0:2,dur:4,muted:true,volume:.5,radius:18};
const locked={...old,id:'media_locked'},state={x:120,scale:1.5,start:3,end:7,keys:[{t:1,x:20}]};
const context={V:{__media:[old,locked],__layers:{media_a:state}},mediaItem:id=>id===old.id?old:locked,isLayerLocked:id=>id==='media_locked',commitHistory:()=>{},changed:()=>{},fillInspector:()=>{},renderMediaAssets:()=>{},toast:()=>{},$:()=>null};
vm.createContext(context);vm.runInContext(fs.readFileSync('dx_studio/editor-media.js','utf8'),context);
vm.runInContext('applyMediaReplacement(["media_a","media_locked"],{file:"Media/b.mp4",name:"b.mp4",kind:"video",has_audio:true})',context);
assert.equal(old.file,'Media/b.mp4');assert.equal(locked.file,'Media/a.png');assert.deepEqual(old.box,[1,2,300,200]);assert.equal(old.t0,2);assert.equal(old.dur,4);assert.equal(old.volume,.5);assert.equal(old.muted,true);assert.equal(context.V.__layers.media_a,state);
console.log('Media replacement preserves layout, timing, transforms and locked sources.');
