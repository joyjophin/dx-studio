const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
for(const file of ['editor.html','home.html']){const html=fs.readFileSync('dx_studio/'+file,'utf8');for(const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g))new vm.Script(match[1],{filename:file});}
for(const file of ['editor-bulk.js','editor-tools.js','editor-media.js','editor-audio.js','editor-narration.js','editor-captions.js','editor-brand.js','editor-view.js','editor-creator.js','editor-shell.js'])new vm.Script(fs.readFileSync('dx_studio/'+file,'utf8'),{filename:file});
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

const preview={DUR:10,FPS:30,t:2,audio:{},document:{querySelector:()=>null,querySelectorAll:()=>[]},$:()=>null};
vm.createContext(preview);vm.runInContext(fs.readFileSync('dx_studio/editor-audio.js','utf8'),preview);
vm.runInContext('setAuditionPoint("start");PREVIEW_RATE=1.5;PREVIEW_VOLUME=.4;PREVIEW_MUTED=true;syncPreviewAudio()',preview);
assert.equal(preview.audio.playbackRate,1.5);assert.equal(preview.audio.volume,.4);assert.equal(preview.audio.muted,true);
preview.DUR=1;vm.runInContext('normalizeAudition()',preview);assert.ok(vm.runInContext('AUDITION.start<auditionEnd() && auditionEnd()<=DUR',preview));
console.log('Preview listening controls and audition bounds remain separate from editable settings.');

const cues=[{start:0,end:4,text:'Make the story keep the layers',hl:'story',voice_id:'voice_a',word_ids:['a'],words:[{text:'Make',start:0,end:.5}],word_highlight:true},{start:4,end:6,text:'Finish your cut',hl:null}];
const captionContext={CAPV:()=>cues,selCap:0,ST:()=>2,r2:value=>Math.round(value*100)/100,clone:value=>JSON.parse(JSON.stringify(value)),commitHistory:()=>{},changed:()=>{},buildCapLane:()=>{},renderCapList:()=>{},fillCapEditor:()=>{},toast:()=>{},showErr:message=>{throw new Error(message)},BASE:8};
vm.createContext(captionContext);vm.runInContext(fs.readFileSync('dx_studio/editor-captions.js','utf8'),captionContext);
vm.runInContext('splitCaption()',captionContext);assert.equal(cues.length,3);assert.equal(cues[0].end,2);assert.equal(cues[1].start,2);assert.equal(cues[0].voice_id,undefined);assert.equal(cues[1].words,undefined);assert.equal(cues.map(c=>c.text).join(' '),'Make the story keep the layers Finish your cut');
vm.runInContext('mergeCaption()',captionContext);assert.equal(cues.length,2);assert.equal(cues[0].text,'Make the story keep the layers');assert.equal(cues[0].end,4);
assert.throws(()=>vm.runInContext('shiftCaptions(-1)',captionContext),/outside/);assert.equal(cues[0].start,0);
console.log('Caption split/merge preserve words; invalid bulk timing shifts leave cues unchanged.');

// Moving/left trimming must preserve source identity and the remaining sample positions.
const take={id:'voice_original',name:'Opening',file:'assets/voice.wav',start:2,offset:1,duration:4,gain:.7,duck:'deep',muted:false};
const narration={V:{__voice:[take]},FPS:30,BASE:12,ST:()=>4,crypto:require('node:crypto'),clone:value=>JSON.parse(JSON.stringify(value)),commitHistory:()=>{},changed:()=>{},document:{querySelector:()=>null},$:()=>null,toast:()=>{}};
vm.createContext(narration);vm.runInContext(fs.readFileSync('dx_studio/editor-narration.js','utf8'),narration);
const trim=vm.runInContext('voiceDragTiming(V.__voice[0],"l",3,12,1/30)',narration);
assert.equal(trim.start,3);assert.equal(trim.offset,2);assert.equal(trim.duration,3);assert.equal(trim.start-trim.offset,take.start-take.offset);
const extend=vm.runInContext('voiceDragTiming(V.__voice[0],"l",-10,12,1/30)',narration);
assert.equal(extend.start,1);assert.equal(extend.offset,0);assert.equal(extend.duration,5);
const moved=vm.runInContext('voiceDragTiming(V.__voice[0],"m",11,12,1/30)',narration);assert.equal(moved.start,8);assert.equal(moved.offset,1);assert.equal(moved.duration,4);
const shortened=vm.runInContext('voiceDragTiming(V.__voice[0],"r",5,12,1/30)',narration);assert.equal(shortened.duration,3);assert.equal(shortened.offset,1);
vm.runInContext('splitVoiceTake("voice_original")',narration);assert.equal(narration.V.__voice.length,2);
const [left,right]=narration.V.__voice;assert.equal(left.duration,2);assert.equal(right.start,4);assert.equal(right.offset,3);assert.equal(right.duration,2);assert.equal(right.file,left.file);assert.notEqual(right.id,left.id);assert.equal(right.gain,.7);
vm.runInContext('duplicateVoiceTake("voice_original")',narration);assert.equal(narration.V.__voice.length,3);assert.equal(narration.V.__voice[2].start,4);assert.equal(narration.V.__voice[2].offset,1);
console.log('Narration trims retain sample positions; split and duplicate keep source and mix controls.');
