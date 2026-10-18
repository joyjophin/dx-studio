/* Local workspace preferences; project values and export settings are untouched. */
const VIEW_DEFAULT={width:288,rows:128,inspector:true,timeline:true,quality:'auto'};
let VIEW={...VIEW_DEFAULT},frameStatusTimer=null;
function sanitizeView(value){const number=(key,min,max)=>Number.isFinite(value?.[key])?Math.max(min,Math.min(max,value[key])):VIEW_DEFAULT[key];return {width:number('width',240,440),rows:number('rows',48,400),inspector:typeof value?.inspector==='boolean'?value.inspector:true,timeline:typeof value?.timeline==='boolean'?value.timeline:true,quality:['auto','fast','balanced','sharp'].includes(value?.quality)?value.quality:'auto'};}
function saveView(){try{localStorage.setItem('dx-studio:view:v2',JSON.stringify(VIEW));}catch(_){};}
function applyView(remember=true){
  document.documentElement.style.setProperty('--inspector-width',VIEW.width+'px');document.documentElement.style.setProperty('--layer-rows-height',VIEW.rows+'px');
  const app=document.querySelector('.app');app.classList.toggle('inspector-hidden',!VIEW.inspector);app.classList.toggle('timeline-hidden',!VIEW.timeline);app.classList.toggle('canvas-focused',!VIEW.inspector&&!VIEW.timeline);
  $('#viewWidth').value=VIEW.width;$('#viewRows').value=VIEW.rows;$('#viewInspector').checked=VIEW.inspector;$('#viewTimeline').checked=VIEW.timeline;$('#viewQuality').value=VIEW.quality;
  $('#inspectorResize').setAttribute('aria-valuenow',Math.round(VIEW.width));$('#timelineResize').setAttribute('aria-valuenow',Math.round(VIEW.rows));
  $('#viewSizes').textContent=`Tools ${Math.round(VIEW.width)} px · expanded layers ${Math.round(VIEW.rows)} px, limited by the window size`;
  if(remember)saveView();requestAnimationFrame(()=>{if(PJ){placePlayhead();drawWaveform();overlaySoon();requestFrame();}});
}
function setViewPreset(preset){VIEW={...VIEW,inspector:true,timeline:true,width:288,rows:128};if(preset==='balanced'&&SHELL_TRACKS)toggleTimelineLayers();if(preset==='canvas'){VIEW.inspector=false;VIEW.timeline=false;}if(preset==='timeline'){VIEW.width=264;VIEW.rows=320;if(!SHELL_TRACKS)toggleTimelineLayers();}applyView();}
function resizeView(event,key,axis){
  event.preventDefault();const handle=event.currentTarget;handle.setPointerCapture?.(event.pointerId);const initial=VIEW[key],origin=axis==='x'?event.clientX:event.clientY;
  const move=next=>{VIEW=sanitizeView({...VIEW,[key]:initial+(axis==='x'?next.clientX-origin:origin-next.clientY)});applyView(false);};
  const up=()=>{window.removeEventListener('pointermove',move);window.removeEventListener('pointerup',up);window.removeEventListener('pointercancel',up);if(handle.hasPointerCapture?.(event.pointerId))handle.releasePointerCapture(event.pointerId);saveView();};
  window.addEventListener('pointermove',move);window.addEventListener('pointerup',up,{once:true});window.addEventListener('pointercancel',up,{once:true});
}
function resizeViewKey(event,key){const decrease=key==='width'?'ArrowLeft':'ArrowDown',increase=key==='width'?'ArrowRight':'ArrowUp';if(event.key!==decrease&&event.key!==increase)return;event.preventDefault();event.stopPropagation();VIEW=sanitizeView({...VIEW,[key]:VIEW[key]+(event.key===increase?10:-10)});applyView();}
function setupView(){
  try{const saved=JSON.parse(localStorage.getItem('dx-studio:view:v2')),previous=JSON.parse(localStorage.getItem('dx-studio:view:v1'));VIEW=sanitizeView(saved||{quality:previous?.quality});}catch(_){VIEW={...VIEW_DEFAULT};}
  $('#bView').onclick=()=>{$('#viewDialog').showModal();};$('#viewClose').onclick=()=>$('#viewDialog').close();
  for(const id of ['viewWidth','viewRows','viewInspector','viewTimeline','viewQuality']){
    const control=$('#'+id),update=()=>{VIEW=sanitizeView({width:+$('#viewWidth').value,rows:+$('#viewRows').value,inspector:$('#viewInspector').checked,timeline:$('#viewTimeline').checked,quality:$('#viewQuality').value});applyView();};control.addEventListener(control.type==='range'?'input':'change',update);
  }
  for(const button of document.querySelectorAll('[data-view-preset]'))button.onclick=()=>setViewPreset(button.dataset.viewPreset);
  $('#inspectorResize').onpointerdown=event=>resizeView(event,'width','x');$('#timelineResize').onpointerdown=event=>resizeView(event,'rows','y');
  $('#inspectorResize').onkeydown=event=>resizeViewKey(event,'width');$('#timelineResize').onkeydown=event=>resizeViewKey(event,'rows');applyView(false);
}
function viewFrameScale(automatic){if(VIEW.quality==='auto')return automatic;return ({fast:playing?.18:.25,balanced:playing?.3:.5,sharp:playing?.5:.9})[VIEW.quality];}
function frameLoading(){clearTimeout(frameStatusTimer);frameStatusTimer=setTimeout(()=>{if(inflight&&!playing)$('#previewState').hidden=false;},180);}
function frameLoaded(){clearTimeout(frameStatusTimer);$('#previewState').hidden=true;}
