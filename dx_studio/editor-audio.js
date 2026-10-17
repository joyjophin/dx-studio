/* Listening controls are preview-only; they never alter settings or the exported mix. */
let WAVEFORM=null, WAVE_BUSY=false, PREVIEW_RATE=1, PREVIEW_VOLUME=1, PREVIEW_MUTED=false;
const AUDITION={start:0,end:null,enabled:false,loop:false};
function normalizeAudition(){if(AUDITION.end!==null)AUDITION.end=Math.max(1/FPS,Math.min(DUR,AUDITION.end));AUDITION.start=Math.max(0,Math.min(AUDITION.start,auditionEnd()-1/FPS));}
function auditionEnd(){return Math.min(DUR,AUDITION.end??DUR);}
function syncPreviewAudio(){audio.playbackRate=PREVIEW_RATE;audio.volume=PREVIEW_VOLUME;audio.muted=PREVIEW_MUTED;audio.preservesPitch=true;}
function audioPanel(){
  const root=el('div');root.append(el('p','note','Listen closely, find a beat and rehearse a section. These controls affect the editor preview only; exports keep their original speed, levels and duration.'));
  const title=el('h3');title.textContent='Listening';root.append(title);
  const speed=el('select');speed.setAttribute('aria-label','Playback speed');
  for(const rate of [.5,.75,1,1.25,1.5,2]){const option=el('option');option.value=rate;option.textContent=rate+'× speed';speed.append(option);}speed.value=PREVIEW_RATE;
  speed.onchange=()=>{if(playing)pause();PREVIEW_RATE=+speed.value;syncPreviewAudio();};root.append(speed);
  const level=el('input');level.type='range';level.min=0;level.max=1;level.step=.05;level.value=PREVIEW_VOLUME;level.setAttribute('aria-label','Preview volume');level.oninput=()=>{PREVIEW_VOLUME=+level.value;syncPreviewAudio();};root.append(el('p','sub','Preview volume'),level);
  const check=(label,key,object)=>{const row=el('label','kbar'),box=el('input');box.type='checkbox';box.checked=object[key];box.onchange=()=>{object[key]=box.checked;syncPreviewAudio();drawWaveform();};row.append(box,document.createTextNode(label));root.append(row);};
  const mute=el('label','kbar'),muteBox=el('input');muteBox.type='checkbox';muteBox.checked=PREVIEW_MUTED;muteBox.onchange=()=>{PREVIEW_MUTED=muteBox.checked;syncPreviewAudio();};mute.append(muteBox,document.createTextNode('Mute preview'));root.append(mute);
  root.append(el('h3',null,'Audition a range'));
  check('Use audition range','enabled',AUDITION);check('Loop the range','loop',AUDITION);
  const fields=el('div','kbar');for(const [key,label]of[['start','Range in (seconds)'],['end','Range out (seconds)']]){
    const wrap=el('label'),input=el('input','num');input.type='number';input.min=0;input.max=DUR;input.step=1/FPS;input.value=(key==='start'?AUDITION.start:auditionEnd()).toFixed(2);input.setAttribute('aria-label',label);input.dataset.audition=key;
    input.oninput=()=>{const value=+input.value;if(input.value===''||!Number.isFinite(value))return;AUDITION[key]=Math.max(0,Math.min(DUR,value));if(auditionEnd()<=AUDITION.start){if(key==='start')AUDITION.start=Math.max(0,auditionEnd()-1/FPS);else AUDITION.end=Math.min(DUR,AUDITION.start+1/FPS);}syncAuditionFields();drawWaveform();};wrap.append(document.createTextNode(label),input);fields.append(wrap);
  }root.append(fields);
  const buttons=el('div','kbar');buttons.append(mediaButton('Set in at playhead',()=>setAuditionPoint('start')),mediaButton('Set out at playhead',()=>setAuditionPoint('end')),mediaButton('Play range',playAudition),mediaButton('Full video',()=>{AUDITION.start=0;AUDITION.end=null;AUDITION.enabled=false;refreshAudioPanel();drawWaveform();}));root.append(buttons);
  root.append(el('p','sub','Click the waveform to seek. Shift-drag to choose a range, or press I / O at the playhead. The waveform shows the combined preview mix, including narration, music and effects.'));
  const status=el('p','note');status.id='waveformStatus';root.append(status,mediaButton('Refresh waveform',loadWaveform));setTimeout(loadWaveform,0);return root;
}
function refreshAudioPanel(){const pane=document.querySelector('.pane[data-p="Audio"]');if(pane){pane.replaceChildren(audioPanel());}}
function syncAuditionFields(){for(const input of document.querySelectorAll('[data-audition]'))if(input!==document.activeElement)input.value=(input.dataset.audition==='start'?AUDITION.start:auditionEnd()).toFixed(2);}
function setAuditionPoint(key){
  if(key==='start')AUDITION.start=Math.max(0,Math.min(t,auditionEnd()-1/FPS));
  else AUDITION.end=Math.max(AUDITION.start+1/FPS,Math.min(DUR,t));
  AUDITION.enabled=true;refreshAudioPanel();drawWaveform();
}
function playAudition(){if(playing)pause();AUDITION.enabled=true;setT(AUDITION.start);refreshAudioPanel();play();}
async function loadWaveform(){
  if(WAVE_BUSY)return;WAVE_BUSY=true;
  try{const result=await api('/api/waveform');if(result.ready)WAVEFORM=result;
    const status=$('#waveformStatus');if(status)status.textContent=result.ready?'Waveform ready · preview mix':result.message||'Preparing preview audio…';drawWaveform();
  }catch(error){const status=$('#waveformStatus');if(status)status.textContent=error.message;}finally{WAVE_BUSY=false;}
}
function buildWaveformLane(grid){
  const label=el('div','lanelab','Mix audio'),lane=el('div','lane waveform');lane.id='waveformLane';lane.setAttribute('role','slider');lane.setAttribute('aria-label','Audio waveform playhead');lane.setAttribute('aria-valuemin','0');lane.setAttribute('aria-valuemax',DUR);lane.tabIndex=0;
  lane.onkeydown=event=>{if(event.key==='ArrowRight'||event.key==='ArrowLeft'){event.preventDefault();event.stopPropagation();if(playing)pause();setT(t+(event.key==='ArrowRight'?1:-1)*(event.shiftKey?1:1/FPS));}};
  lane.onpointerdown=event=>{event.preventDefault();event.stopPropagation();if(playing)pause();const start=clampT(x2t(event.clientX));if(!event.shiftKey){setT(start);dragWith(next=>setT(x2t(next.clientX)));return;}
    dragWith(next=>{const end=clampT(x2t(next.clientX));AUDITION.end=Math.min(DUR,Math.max(start,end)+1/FPS);AUDITION.start=Math.min(Math.min(start,end),AUDITION.end-1/FPS);AUDITION.enabled=true;drawWaveform();},()=>refreshAudioPanel());};
  grid.append(label,lane);requestAnimationFrame(drawWaveform);
}
function drawWaveform(){
  const lane=$('#waveformLane');if(!lane)return;lane.replaceChildren();lane.setAttribute('aria-valuenow',t.toFixed(2));
  if(AUDITION.enabled){const selection=el('div','audition-range');selection.style.left=pctO(AUDITION.start);selection.style.width=pw(auditionEnd()-AUDITION.start);lane.append(selection);}
  if(!WAVEFORM?.peaks.length){lane.append(el('span','waveform-note',HAS_AUDIO?'Preparing waveform…':'No preview audio'));return;}
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 1000 44');svg.setAttribute('preserveAspectRatio','none');svg.setAttribute('aria-hidden','true');
  const path=document.createElementNS('http://www.w3.org/2000/svg','path');let d='';
  for(let x=0;x<1000;x+=2){const from=Math.max(0,Math.floor((V0+x/1000*SPAN())/WAVEFORM.step)),to=Math.min(WAVEFORM.peaks.length,Math.ceil((V0+(x+2)/1000*SPAN())/WAVEFORM.step));let peak=0;for(let i=from;i<to;i++)peak=Math.max(peak,WAVEFORM.peaks[i]);const height=Math.max(.35,Math.min(1,peak)*20);d+=`M${x},${22-height}V${22+height}`;}
  path.setAttribute('d',d);path.setAttribute('stroke','#6962CF');path.setAttribute('stroke-width','1.4');svg.append(path);lane.append(svg);
}
