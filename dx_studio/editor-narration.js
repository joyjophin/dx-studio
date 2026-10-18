/* Narration takes are saved settings; editing them never moves scene graphics or captions. */
let VOICE_SELECTED=null, VOICE_IMPORT_TARGET=null, VOICE_IMPORT_BUSY=false, VOICE_IMPORT_TOKEN=0;
function voiceTakes(){return V.__voice||[];}
function refreshNarrationPanel(){const pane=document.querySelector('.pane[data-p="Narration"]');if(pane)pane.replaceChildren(narrationPanel());}
function selectVoice(id,seek=false){VOICE_SELECTED=id;document.querySelector('.tab[data-p="Narration"]')?.click();refreshNarrationPanel();renderNarrationLane();const take=voiceTakes().find(item=>item.id===id);if(seek&&take){if(playing)pause();goS(take.start);}}
function narrationPanel(){
  const root=el('div');root.append(el('p','note','Import your voice recordings and adjust each take. Timing uses the original scene clock; ripple cuts and holds affect the mix. Captions and graphics keep their existing timing.'));
  const actions=el('div','kbar');actions.append(mediaButton('Add recording',()=>openVoiceImport()),mediaButton('Check narration',checkExport));root.append(actions);
  const list=el('div','clips');
  for(const take of voiceTakes()){const b=mediaButton((take.muted?'Muted · ':'')+take.name,()=>selectVoice(take.id,true));b.classList.toggle('on',take.id===VOICE_SELECTED);b.dataset.voiceId=take.id;list.append(b);}root.append(list);
  if(!voiceTakes().length){root.append(el('p','note','Add a WAV, MP3, M4A or FLAC recording. Imported files are copied into this project as 48 kHz WAV audio.'));return root;}
  let take=voiceTakes().find(item=>item.id===VOICE_SELECTED)||voiceTakes()[0];VOICE_SELECTED=take.id;
  root.append(el('h3',null,'Selected take'),el('p','sub',take.file));
  const update=(key,value)=>{take[key]=value;if(key==='name')for(const button of list.querySelectorAll('[data-voice-id]'))if(button.dataset.voiceId===take.id)button.textContent=(take.muted?'Muted · ':'')+value;changed(key!=='name');renderNarrationLane();};
  const name=el('input','txt');name.value=take.name;name.maxLength=120;name.setAttribute('aria-label','Take name');name.oninput=()=>update('name',name.value);root.append(name);
  for(const [key,label,min,max,step]of[['start','Scene start (seconds)',0,86400,1/FPS],['offset','Source trim in (seconds)',0,86400,1/FPS],['duration','Take duration (seconds)',.001,86400,1/FPS],['gain','Relative voice level',0,4,.05]]){
    const field=el('label','field');field.append(document.createTextNode(label));const input=el('input','num');input.type='number';input.min=min;input.max=max;input.step=step;input.value=+take[key].toFixed(3);input.setAttribute('aria-label',label);
    input.oninput=()=>{if(input.value===''||!Number.isFinite(+input.value)||+input.value<min||+input.value>max)return;update(key,+input.value);};input.onblur=()=>{input.value=+take[key].toFixed(3);};field.append(input);root.append(field);
  }
  root.append(el('p','sub','Voice is normalized as a group. Relative level balances takes against one another; use Mute for silence.'));
  const duckLabel=el('label');duckLabel.textContent='Music ducking';const duck=el('select');duck.setAttribute('aria-label','Music ducking');for(const [value,label]of[['normal','Normal ducking'],['deep','Deeper ducking'],['none','No ducking']]){const option=el('option');option.value=value;option.textContent=label;duck.append(option);}duck.value=take.duck;duck.onchange=()=>update('duck',duck.value);duckLabel.append(duck);root.append(duckLabel);
  const muteLabel=el('label','kbar'),mute=el('input');mute.type='checkbox';mute.checked=take.muted;mute.onchange=()=>{update('muted',mute.checked);refreshNarrationPanel();};muteLabel.append(mute,document.createTextNode('Mute take'));root.append(muteLabel);
  const buttons=el('div','kbar');buttons.append(mediaButton('Start at playhead',()=>{commitHistory();update('start',ST());refreshNarrationPanel();}),mediaButton('Replace recording',()=>openVoiceImport(take.id)),mediaButton('Remove take',()=>{commitHistory();V.__voice=voiceTakes().filter(item=>item.id!==take.id);VOICE_SELECTED=null;changed(true);refreshNarrationPanel();renderNarrationLane();toast('Take removed; the source file is kept');}));root.append(buttons);
  const edits=el('div','kbar');edits.append(mediaButton('Split at playhead',()=>splitVoiceTake(take.id)),mediaButton('Duplicate at playhead',()=>duplicateVoiceTake(take.id)),mediaButton('Audition take',()=>auditionVoiceTake(take.id)));root.append(edits);
  root.append(el('p','sub','Drag a take on the timeline to move it; drag its edges to trim. Alt bypasses snapping. Split keeps each part linked to the same source recording.'));
  root.append(el('p','note',take.start+take.duration>BASE+.02?'This take extends beyond the scene. Only the section inside the scene will play. Trim its duration or ask your assistant to extend the project.':'Replace keeps this take’s name, start, trim, duration, level and ducking. A shorter replacement may finish before the take ends.'));
  return root;
}
function openVoiceImport(id=null){
  VOICE_IMPORT_TOKEN++;VOICE_IMPORT_TARGET=id?{id,file:voiceTakes().find(take=>take.id===id)?.file}:null;
  $('#voiceImportTitle').textContent=id?'Replace voice recording':'Add voice recording';$('#voiceImportPath').value='';$('#voiceImportMessage').textContent='A copy stays inside the project. Previous source files are kept for undo and saved versions.';$('#voiceImportDialog').showModal();
}
async function importVoiceRecording(file=null){
  if(VOICE_IMPORT_BUSY)return;VOICE_IMPORT_BUSY=true;const target=VOICE_IMPORT_TARGET,token=VOICE_IMPORT_TOKEN,button=$('#voiceImportApply');button.disabled=true;$('#voiceImportMessage').textContent='Reading and preparing recording…';
  try{
    let result;
    if(file){if(file.size>256*1024*1024)throw new Error('Use a recording smaller than 256 MB');const response=await fetch(projectURL('/api/narration/upload?name='+encodeURIComponent(file.name)+'&t='+ST()),{method:'POST',headers:{'X-DX-Studio-Client':'1'},body:file});result=await response.json();if(!response.ok||!result.ok)throw new Error(result.error||'Could not import recording');}
    else result=await api('/api/narration/import',{path:$('#voiceImportPath').value,t:ST()});
    if(token!==VOICE_IMPORT_TOKEN)return;
    const take=target?voiceTakes().find(item=>item.id===target.id&&item.file===target.file):null;
    if(target&&!take)throw new Error('This take changed during import. Select it again to replace it.');
    commitHistory();if(take)take.file=result.take.file;else{V.__voice.push(result.take);VOICE_SELECTED=result.take.id;}
    changed(true);refreshNarrationPanel();renderNarrationLane();$('#voiceImportDialog').close();toast(target?'Recording replaced; timing and levels kept':'Recording added at the playhead');
  }catch(error){$('#voiceImportMessage').textContent=error.message;}finally{VOICE_IMPORT_BUSY=false;button.disabled=false;}
}
function renderNarrationLane(){
  const lane=$('#lane-narration');if(!lane)return;lane.replaceChildren();
  for(const take of voiceTakes()){
    for(const [start,end]of mappedRanges(take.start,Math.min(BASE,take.start+take.duration))){if(end<=V0||start>=V0+SPAN()||end<=start)continue;
    const block=el('button','blk');block.type='button';block.classList.toggle('on',take.id===VOICE_SELECTED);const title=el('span');title.textContent=take.name;block.append(title);for(const side of ['l','r']){const handle=el('div','h '+side);block.append(handle);}block.style.left=pctO(Math.max(start,V0));block.style.width=pw(Math.min(end,V0+SPAN())-Math.max(start,V0));block.style.opacity=take.muted?.4:1;block.style.background='#DDF1E9';block.style.color='#215542';block.style.borderColor='#8ABDA6';block.title=`${take.name} · scene ${take.start.toFixed(2)}–${(take.start+take.duration).toFixed(2)} s${take.muted?' · muted':''}`;block.setAttribute('aria-label','Edit narration '+take.name);block.onclick=()=>selectVoice(take.id,true);block.onpointerdown=event=>startVoiceDrag(event,take.id,event.target.classList.contains('l')?'l':event.target.classList.contains('r')?'r':'m');lane.append(block);}
  }
}
function syncAudioAvailability(available){
  HAS_AUDIO=available;
  if(HAS_AUDIO){if(!audio.src)audio.src=projectURL('/audio?v=')+audioVer;}
  else{if(playing)pause();audio.pause();audio.removeAttribute('src');audio.load();WAVEFORM=null;drawWaveform();}
}

function splitVoiceTake(id){
  const take=voiceTakes().find(item=>item.id===id);if(!take)return;
  const at=ST(),left=at-take.start,right=take.duration-left;
  if(left<1/FPS||right<1/FPS)return toast('Place the playhead inside this take, at least one frame from its ends');
  if(voiceTakes().length>=500)return toast('This project already has 500 takes');
  commitHistory();const next=clone(take);next.id='voice_'+crypto.randomUUID().replaceAll('-','').slice(0,16);next.name=(take.name+' (part 2)').slice(0,120);next.start=at;next.offset+=left;next.duration=right;take.duration=left;
  V.__voice.splice(voiceTakes().indexOf(take)+1,0,next);VOICE_SELECTED=next.id;changed(true);refreshNarrationPanel();renderNarrationLane();toast('Take split; captions and graphics keep their timing');
}
function duplicateVoiceTake(id){
  const take=voiceTakes().find(item=>item.id===id);if(!take)return;
  if(voiceTakes().length>=500)return toast('This project already has 500 takes');
  commitHistory();const next=clone(take);next.id='voice_'+crypto.randomUUID().replaceAll('-','').slice(0,16);next.name=(take.name+' copy').slice(0,120);next.start=Math.max(0,Math.min(BASE-1/FPS,ST()));V.__voice.push(next);VOICE_SELECTED=next.id;changed(true);refreshNarrationPanel();renderNarrationLane();toast('Take duplicated at the playhead');
}
function auditionVoiceTake(id){
  const take=voiceTakes().find(item=>item.id===id);if(!take)return;
  const spans=mappedRanges(take.start,Math.min(BASE,take.start+take.duration));if(!spans.length)return toast('This take has no time in the current output');const start=Math.min(...spans.map(s=>s[0])),end=Math.max(...spans.map(s=>s[1]));
  if(end-start<1/FPS)return toast('This take has no time in the current output');
  if(playing)pause();AUDITION.start=start;AUDITION.end=end;AUDITION.enabled=true;refreshAudioPanel();drawWaveform();setT(start);play();toast('Auditioning this range of the full mix');
}
function voiceDragTiming(original,mode,position,base,min){
  if(mode==='m')return {...original,start:Math.max(0,Math.min(Math.max(0,base-Math.min(original.duration,base)),position))};
  if(mode==='l'){
    const delta=Math.max(-Math.min(original.start,original.offset),Math.min(original.duration-min,position-original.start));
    return {...original,start:original.start+delta,offset:original.offset+delta,duration:original.duration-delta};
  }
  return {...original,duration:Math.max(min,Math.min(base,position)-original.start)};
}
function startVoiceDrag(event,id,mode){
  if(sceneOrderActive()){event.preventDefault();event.stopPropagation();selectVoice(id,false);return toast('After scene reordering, use narration source-time fields');}
  if(event.button!==0)return;event.preventDefault();event.stopPropagation();if(playing)pause();
  const take=voiceTakes().find(item=>item.id===id);if(!take)return;
  commitHistory();selectVoice(id,false);const original=clone(take),anchor=x2s(event.clientX),minimum=Math.min(1/FPS,original.duration);
  dragWith(next=>{
    const delta=x2s(next.clientX)-anchor;
    let target=mode==='r'?snapS(original.start+original.duration+delta,take,next):mode==='m'?snapSpan(original.start+delta,original.duration,take,next):snapS(original.start+delta,take,next);
    const updated=voiceDragTiming(original,mode,target,BASE,minimum);Object.assign(take,updated);renderNarrationLane();changed();
  },()=>{refreshNarrationPanel();renderNarrationLane();changed(true);});
}
