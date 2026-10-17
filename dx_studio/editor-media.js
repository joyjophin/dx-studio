/* Asset operations stage normal editable values so undo, recovery and autosave keep working. */
let MEDIA_ASSETS = [], MEDIA_SEARCH = '', MEDIA_KIND = 'all', MEDIA_REPLACE_IDS = [], MEDIA_BUSY = false;
const mediaButton = (label, action) => {const b=el('button','btn small');b.textContent=label;b.onclick=action;return b;};
function mediaPanel() {
  const root=el('div');
  root.append(el('p','note','Import reusable assets, add them to the playhead, or replace and relink files while keeping layer size, timing and animation.'));
  const actions=el('div','kbar');
  actions.append(mediaButton('Import assets',()=>{MEDIA_REPLACE_IDS=[];$('#libraryFile').click();}),mediaButton('Refresh',refreshMedia),mediaButton('Check export',checkExport));root.append(actions);
  const search=el('input','txt');search.type='search';search.placeholder='Search assets';search.setAttribute('aria-label','Search assets');search.value=MEDIA_SEARCH;
  search.oninput=()=>{MEDIA_SEARCH=search.value;renderMediaAssets();};root.append(search);
  const filter=el('select');filter.setAttribute('aria-label','Asset filter');
  for(const [value,label]of[['all','All assets'],['used','Used in this video'],['missing','Needs attention'],['image','Images'],['gif','GIFs'],['video','Video']]){const o=el('option');o.value=value;o.textContent=label;filter.append(o);}
  filter.value=MEDIA_KIND;filter.onchange=()=>{MEDIA_KIND=filter.value;renderMediaAssets();};root.append(filter);
  const status=el('p','sub');status.id='mediaStatus';status.setAttribute('role','status');root.append(status);
  const list=el('div');list.id='mediaAssets';root.append(list);setTimeout(refreshMedia,0);return root;
}
async function refreshMedia() {
  const status=$('#mediaStatus');if(!status)return;
  try {status.textContent='Reading project assets…';MEDIA_ASSETS=(await api('/api/media')).assets;renderMediaAssets();}
  catch(error){status.textContent=error.message;}
}
function mediaUses(asset){return (V.__media||[]).filter(item=>item.file===asset.file);}
function renderMediaAssets() {
  const list=$('#mediaAssets'),status=$('#mediaStatus');if(!list)return;list.replaceChildren();
  const query=MEDIA_SEARCH.trim().toLowerCase();
  const assets=MEDIA_ASSETS.filter(asset=>(asset.name+' '+asset.file).toLowerCase().includes(query)&&
    (MEDIA_KIND==='all'||(MEDIA_KIND==='used'?mediaUses(asset).length>0:MEDIA_KIND==='missing'?asset.status!=='ready':asset.kind===MEDIA_KIND)));
  status.textContent=`${assets.length} asset${assets.length===1?'':'s'} · ${MEDIA_ASSETS.filter(a=>a.status!=='ready').length} need attention`;
  if(!assets.length){list.append(el('p','note',MEDIA_ASSETS.length?'No matching assets.':'Import images, GIFs or footage to begin. Files stay inside this project.'));return;}
  for(const asset of assets){
    const card=el('article','asset-card');
    if(asset.status==='ready'){const thumbnail=el('img','asset-thumb');thumbnail.loading='lazy';thumbnail.alt=asset.name+' thumbnail';thumbnail.src=projectURL('/api/media/thumbnail?file='+encodeURIComponent(asset.file));card.append(thumbnail);}
    const title=el('b');title.textContent=asset.name;card.append(title);
    const path=el('div','sub');path.textContent=asset.file;card.append(path);
    const info=el('p','sub');info.textContent=asset.status==='ready'?`${asset.width} × ${asset.height}${asset.duration?' · '+asset.duration.toFixed(1)+' s':''} · ${Math.max(.1,asset.bytes/1048576).toFixed(1)} MB${asset.has_audio?' · audio':''}`:asset.error;card.append(info);
    const used=mediaUses(asset),buttons=el('div','kbar');
    if(asset.status==='ready')buttons.append(mediaButton('Add to video',()=>addLibraryAsset(asset.file)));
    if(used.length){
      buttons.append(mediaButton('Replace uses',()=>pickMediaReplacement(used.map(item=>item.id))),mediaButton('Relink uses',()=>showRelink(used.map(item=>item.id))));
      for(const item of used){const label=LM(item.id)?.label||item.name;buttons.append(mediaButton('Select '+label,()=>selectLayer(item.id,true)));}
    }
    card.append(buttons);list.append(card);
  }
}
async function addLibraryAsset(file) {
  try{const result=await api('/api/media/prepare',{file,t:ST()});commitHistory();V.__media.push(result.item);PENDING_SELECT=result.item.id;changed(true);toast('Asset added at the playhead');}
  catch(error){showErr(error.message);}
}
function pickMediaReplacement(ids){MEDIA_REPLACE_IDS=ids.filter(id=>mediaItem(id)&&!isLayerLocked(id));if(!MEDIA_REPLACE_IDS.length)return toast('Unlock a media layer first');$('#libraryFile').click();}
function applyMediaReplacement(ids,source) {
  const targets=ids.map(mediaItem).filter(item=>item&&!isLayerLocked(item.id));if(!targets.length)return toast('No unlocked media layers to replace');
  commitHistory();
  for(const item of targets)for(const key of ['file','name','kind','has_audio'])item[key]=source[key];
  changed(true);fillInspector();renderMediaAssets();toast(`${targets.length} media layer${targets.length===1?'':'s'} updated; layout and timing kept`);
}
async function importLibraryFiles(files) {
  if(MEDIA_BUSY)return;MEDIA_BUSY=true;
  const ids=MEDIA_REPLACE_IDS.slice();MEDIA_REPLACE_IDS=[];
  try{
    for(const file of files){
      if(file.size>256*1024*1024)throw new Error('Use files smaller than 256 MB');
      const response=await fetch(projectURL('/api/upload?library=1&name='+encodeURIComponent(file.name)+'&t='+ST()),{method:'POST',headers:{'X-DX-Studio-Client':'1'},body:file});
      const result=await response.json();if(!response.ok||!result.ok)throw new Error(result.error||'Could not import this file');
      if(ids.length){applyMediaReplacement(ids,result.item);break;}
    }
    await refreshMedia();if(!ids.length)toast('Assets imported. Add them to the video when ready.');
  }catch(error){showErr(error.message);}finally{MEDIA_BUSY=false;}
}
function showRelink(ids){
  MEDIA_REPLACE_IDS=ids.filter(id=>mediaItem(id)&&!isLayerLocked(id));if(!MEDIA_REPLACE_IDS.length)return toast('Unlock a media layer first');
  $('#relinkPath').value='';$('#relinkMessage').textContent='The selected file will be copied into this project. Existing sources and saved versions stay available.';
  $('#relinkDialog').showModal();$('#relinkPath').focus();
}
async function relinkMedia() {
  const button=$('#relinkApply');button.disabled=true;
  try{const result=await api('/api/media/relink',{path:$('#relinkPath').value,t:ST()});applyMediaReplacement(MEDIA_REPLACE_IDS,result.item);MEDIA_REPLACE_IDS=[];$('#relinkDialog').close();await refreshMedia();}
  catch(error){$('#relinkMessage').textContent=error.message;}finally{button.disabled=false;}
}
function addMediaSourceActions(parent,id){
  const row=el('div','kbar');row.append(mediaButton('Replace file',()=>pickMediaReplacement([id])),mediaButton('Relink file',()=>showRelink([id])));parent.append(row);
}
async function checkExport() {
  try{await session.flush();const report=await api('/api/preflight');showPreflight(report);}
  catch(error){showErr(error.message);}
}
function showPreflight(report){
  const list=$('#preflightList');list.replaceChildren();$('#preflightTitle').textContent=report.ok?'Files ready for export':'Export needs attention';
  if(!report.findings.length)list.append(el('p','note','File and caption timing checks passed. These checks do not analyse every frame, text overflow or final audio levels.'));
  for(const finding of report.findings){const row=el('div','asset-card'),message=el('b'),fix=el('p','sub');message.textContent=(finding.severity==='error'?'Fix: ':'Warning: ')+finding.message;fix.textContent=finding.fix;row.append(message,fix);
    if(finding.kind==='caption')row.append(mediaButton('Show caption',()=>{$('#preflightDialog').close();const index=CAPV().findIndex(c=>c.start===finding.at);if(index>=0)selectCap(index,true);}));
    for(const id of finding.layers||[])row.append(mediaButton('Show layer',()=>{$('#preflightDialog').close();selectLayer(id,true);}));list.append(row);}
  $('#preflightDialog').showModal();
}
