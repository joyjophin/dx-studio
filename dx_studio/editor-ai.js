/* A file-based AI round trip. No provider SDK, chat transport or silent source reload. */
let AI_HANDOFF=null,AI_PROMPT='',SOURCE_UPDATE=null,SOURCE_GENERATION=0,AI_SAVE_BLOCK=false;
function aiNote(text){const p=document.createElement('p');p.className='sub';p.textContent=text;return p;}
async function aiCopy(text,status){try{await navigator.clipboard.writeText(text);status.textContent='Copied. Paste this into the same AI chat.';}catch(_){status.textContent='Select the prompt below and copy it into your AI chat.';}}
function aiDownload(name,data){const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function showAIWorkflow(){
 if(playing)pause();$('#projectMenu').open=false;
 $('#aiProjectFolder').textContent=PJ.folder;
 $('#aiProjectSummary').textContent=`${PJ.width} × ${PJ.height} · ${DUR.toFixed(1)} seconds · ${PJ.layout?.label||'Full graphics'}`;
 $('#aiHandoffMessage').textContent='';$('#aiWorkflowDialog').showModal();
}
async function prepareAIHandoff(){
 const button=$('#aiPrepare');button.disabled=true;
 try{
  await session.flush();
  const result=await api('/api/handoff',{request:$('#aiRequest').value,revision:session.revision});
  AI_HANDOFF=result.document;AI_PROMPT=result.prompt;
  $('#aiFollowupPrompt').value=AI_PROMPT;$('#aiPrepared').hidden=false;
  $('#aiHandoffMessage').textContent='Ready. A copy is saved as dx-ai-handoff.json in your project folder, with a source/settings checkpoint in .dx-studio/ai-handoffs.';
 }catch(error){$('#aiHandoffMessage').textContent=error.message;}finally{button.disabled=false;}
}
function sourceNotice(update){
 if(!update||!session)return;
 const refresh=update.generation!==SOURCE_GENERATION;
 SOURCE_UPDATE={...update,refresh};
 const changed=update.changed||refresh;
 $('#sourceNotice').hidden=!changed;
 if(!changed){if(AI_SAVE_BLOCK){AI_SAVE_BLOCK=false;session.blocked=false;if(session.dirty)session.changed(V);else session.status('saved','All changes saved');updateRecoveryBar();}return;}
 $('#sourceNoticeText').textContent=refresh?'A newer project version was loaded in another tab.':update.error?'Project files are being updated. Review before reloading.':'Project files changed outside DX Editor. AI updates are ready to review.';
 if(!session.blocked)AI_SAVE_BLOCK=true;
 session.blocked=true;
 if(session.dirty)session.remember();
 session.status('external',session.dirty?'Save paused · browser draft kept':'File updates available');
}
async function reviewSourceUpdates(){
 if(playing)pause();
 try{
  const update=await api('/api/source-status');sourceNotice(update);
  $('#sourceUpdateFiles').replaceChildren();
  for(const name of update.files){const item=document.createElement('li');item.textContent=name;$('#sourceUpdateFiles').append(item);}
  if(!update.files.length)$('#sourceUpdateFiles').append(aiNote(update.error||'No file differences detected. You can still reload to refresh the renderer.'));
  $('#sourceUpdateMessage').textContent=session.dirty?'Your pending changes are retained as a browser draft. Download them before reloading, then review Recovery against the updated project.':'Current saved edits will be read from settings.json. Source files are loaded only when you choose Reload AI changes.';
  $('#aiDraftDownload').hidden=!session.dirty;$('#sourceReloadButton').disabled=false;$('#sourceReloadDialog').showModal();
 }catch(error){showErr(error.message);}
}
async function reloadAISource(){
 const button=$('#sourceReloadButton');button.disabled=true;
 try{
  if(session.active)await session.active;
  if(session.dirty)session.remember();
  if(SOURCE_UPDATE?.refresh){session.dispose();location.reload();return;}
  const result=await api('/api/source-reload',{revision:session.revision,disk_revision:SOURCE_UPDATE?.revision});
  session.dispose();location.reload();
 }catch(error){$('#sourceUpdateMessage').textContent=error.message;button.disabled=false;}
}
function setupAIWorkflow(state){
 SOURCE_GENERATION=state.source_generation||0;
 $('#bAI').onclick=showAIWorkflow;$('#bAIMenu').onclick=showAIWorkflow;
 $('#aiWorkflowClose').onclick=()=>$('#aiWorkflowDialog').close();
 $('#aiPrepare').onclick=prepareAIHandoff;
 $('#aiRequest').oninput=()=>{AI_HANDOFF=null;AI_PROMPT='';$('#aiPrepared').hidden=true;$('#aiHandoffMessage').textContent='';};
 $('#aiCopyPrompt').onclick=()=>aiCopy(AI_PROMPT,$('#aiHandoffMessage'));
 $('#aiDownloadJSON').onclick=()=>AI_HANDOFF&&aiDownload('dx-ai-handoff.json',AI_HANDOFF);
 $('#aiFullProject').onclick=()=>{$('#aiWorkflowDialog').close();$('#bBundle').click();};
 $('#aiCheckUpdates').onclick=()=>{$('#aiWorkflowDialog').close();reviewSourceUpdates();};
 $('#sourceReview').onclick=reviewSourceUpdates;$('#sourceReloadClose').onclick=()=>$('#sourceReloadDialog').close();$('#sourceReloadButton').onclick=reloadAISource;
 $('#aiDraftDownload').onclick=()=>aiDownload('dx-pending-edits.json',{values:clone(V),revision:session.revision,source_revision:session.sourceRevision,updated_at:new Date().toISOString()});
 const previous=$('#bReload').onclick;$('#bReload').onclick=()=>SOURCE_UPDATE?.changed||SOURCE_UPDATE?.refresh?reviewSourceUpdates():previous();
}
