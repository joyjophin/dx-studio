/* Caption editing helpers preserve canonical scene time. Import is reviewed before application. */
let CAPTION_SEARCH='',CAPTION_IMPORT=null;
function captionTools(parent){
  const row=el('div','kbar');row.append(mediaButton('Import SRT / VTT',()=>$('#captionFile').click()),mediaButton('Paste subtitles',pasteCaptions),mediaButton('Export SRT',()=>exportCaptions('srt')),mediaButton('Export VTT',()=>exportCaptions('vtt')));parent.append(row);
  const search=el('input','txt');search.type='search';search.placeholder='Search captions';search.setAttribute('aria-label','Search captions');search.value=CAPTION_SEARCH;search.oninput=()=>{CAPTION_SEARCH=search.value;renderCapList();};parent.append(search);
  const offset=el('input','num');offset.type='number';offset.step=.05;offset.value=0;offset.setAttribute('aria-label','Shift captions by seconds');
  const shift=el('div','kbar');shift.append(offset,mediaButton('Shift all captions',()=>shiftCaptions(+offset.value)));parent.append(shift);
  parent.append(el('p','sub','Timing uses scene seconds. Dense-text and overlap hints are review prompts; they do not score engagement.'));
}
function detachCaptionWords(c){for(const key of ['voice_id','word_ids','words','word_highlight'])delete c[key];return c;}
function captionHints(c,index){const hints=[];if(c.end<=c.start||c.start<0||c.end>BASE)hints.push('Check timing');else if(c.text.trim().length/(c.end-c.start)>20)hints.push('Dense text');if(CAPV().some((other,i)=>i!==index&&other.start<c.end&&other.end>c.start))hints.push('Overlap');return hints;}
function splitCaption(){
  const c=CAPV()[selCap],at=r2(ST());if(!c)return;
  const words=c.text.trim().split(/\s+/);if(at<=c.start+.03||at>=c.end-.03||words.length<2)return showErr('Put the playhead inside a caption with at least two words.');
  const point=Math.max(1,Math.min(words.length-1,Math.round(words.length*(at-c.start)/(c.end-c.start)))),left=words.slice(0,point).join(' '),right=words.slice(point).join(' ');
  commitHistory();detachCaptionWords(c);const tail={...clone(c),start:at,text:right,hl:c.hl&&right.includes(c.hl)?c.hl:null};c.end=at;c.text=left;if(c.hl&&!left.includes(c.hl))c.hl=null;CAPV().splice(selCap+1,0,tail);refreshCaptions('Caption split; review the word timing');
}
function mergeCaption(){
  const ordered=CAPV().slice().sort((a,b)=>a.start-b.start),first=CAPV()[selCap],next=ordered[ordered.indexOf(first)+1];if(!first||!next)return toast('Select a caption with another one after it');
  commitHistory();detachCaptionWords(first);first.text=(first.text.trim()+' '+next.text.trim()).trim();first.end=Math.max(first.end,next.end);first.start=Math.min(first.start,next.start);first.hl=first.hl||next.hl||null;CAPV().splice(CAPV().indexOf(next),1);refreshCaptions('Captions merged');
}
function shiftCaptions(delta){
  if(!Number.isFinite(delta)||!CAPV().length)return;
  if(CAPV().some(c=>c.start+delta<0||c.end+delta>BASE))return showErr('That shift puts captions outside the scene. Use a smaller offset.');
  commitHistory();for(const c of CAPV()){detachCaptionWords(c);c.start=r2(c.start+delta);c.end=r2(c.end+delta);}refreshCaptions('Caption timing shifted');
}
function refreshCaptions(message){const selected=CAPV()[selCap];CAPV().sort((a,b)=>a.start-b.start);selCap=selected?CAPV().indexOf(selected):null;buildCapLane();renderCapList();fillCapEditor();changed(true);if(message)toast(message);}
async function exportCaptions(format){
  try{await session.flush();const link=el('a');link.href=projectURL('/api/captions/export?format='+format);link.download='captions.'+format;link.click();}
  catch(error){showErr(error.message);}
}
async function reviewCaptionImport(file){
  if(!file)return;if(file.size>1000000)return showErr('Use a subtitle file smaller than 1 MB');
  try{CAPTION_IMPORT={text:await file.text(),name:file.name};$('#captionImportText').value=CAPTION_IMPORT.text;$('#captionImportDialog').showModal();await previewCaptionImport();}
  catch(error){showErr(error.message);}
}
function pasteCaptions(){CAPTION_IMPORT={text:'',name:'Pasted subtitles'};$('#captionImportText').value='';$('#captionImportPreview').textContent='';$('#captionImportSummary').textContent='Paste SRT or WebVTT, then preview the cues before applying.';$('#captionImportApply').disabled=true;$('#captionImportDialog').showModal();$('#captionImportText').focus();}
async function previewCaptionImport(){
  if(!CAPTION_IMPORT)CAPTION_IMPORT={name:'Pasted subtitles'};CAPTION_IMPORT.text=$('#captionImportText').value;
  const apply=$('#captionImportApply'),pending=CAPTION_IMPORT,token=(pending.token||0)+1;pending.token=token;apply.disabled=true;
  try{const result=await api('/api/captions/import',{text:pending.text,timing:$('#captionImportTiming').value});if(CAPTION_IMPORT!==pending||pending.token!==token)return;CAPTION_IMPORT.result=result;
    $('#captionImportSummary').textContent=`${CAPTION_IMPORT.name}: ${result.cues.length} cues ready. ${result.warnings.join(' ')}`;
    $('#captionImportPreview').textContent=result.cues.slice(0,8).map(c=>`${c.start.toFixed(2)}–${c.end.toFixed(2)}  ${c.text}`).join('\n');apply.disabled=false;
  }catch(error){if(CAPTION_IMPORT!==pending||pending.token!==token)return;$('#captionImportSummary').textContent=error.message;$('#captionImportPreview').textContent='';}
}
function applyCaptionImport(){
  if(!CAPTION_IMPORT?.result)return;commitHistory();const incoming=CAPTION_IMPORT.result.cues;
  V.__captions=($('#captionImportMode').value==='append'?[...CAPV(),...incoming]:incoming).sort((a,b)=>a.start-b.start);selCap=null;CAPTION_SEARCH='';const search=document.querySelector('[aria-label="Search captions"]');if(search)search.value='';CAPTION_IMPORT=null;$('#captionImportDialog').close();refreshCaptions('Captions imported');
}
