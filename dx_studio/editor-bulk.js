function layerRelativeTime(id){return ST()-layerTimeOffset(id)-LS(id).start;}
/* Layer workspace controls. These share the editor's selection and undo state. */
function isLayerLocked(id) {
  let current=LM(id);while(current){if(LS(current.id)?.locked ?? current.locked)return true;current=LM(current.parent);}return false;
}
function layerTimeOffset(id){let result=0,parent=LM(id)?.parent;while(parent){result+=(LS(parent)?.start||0)-(LM(parent)?.default_start||0);parent=LM(parent)?.parent;}return result;}
function bulkSelectResults(){SELECTED.clear();for(const m of LAY)if(matchesLayer(m)&&!isLayerLocked(m.id))SELECTED.add(m.id);selLayer=[...SELECTED].at(-1)||null;selectionRefresh();}
function selectedRoots(unlocked=true) {return DXLayerTools.roots([...SELECTED].filter(id=>LM(id)&&LS(id)&&(!unlocked||!isLayerLocked(id))),LAY);}
function selectionGroup(id){return(V.__groups||[]).find(group=>group.layers.includes(id));}
function selectionGroupMembers(id){const group=selectionGroup(id);return group?group.layers.filter(key=>LM(key)):[id];}
function selectionGroupList(parent){
 const host=el('div');host.id='selectionGroups';parent.append(host);renderSelectionGroups(host);
}
function renderSelectionGroups(host=$('#selectionGroups')){
 if(!host)return;const open=host.querySelector('details')?.open;host.replaceChildren();
 const groups=(V.__groups||[]).filter(group=>group.layers.some(id=>LM(id)));if(!groups.length)return;
 const details=el('details','tool-help'),summary=el('summary');summary.textContent='Selection groups · '+groups.length;details.append(summary);
 details.open=!!open;for(const group of groups){const button=el('button','btn small');button.textContent=group.name;button.onclick=()=>selectLayer(group.layers.find(id=>LM(id)),true);details.append(button);}host.append(details);
}
function selectionGroupControls(parent){
 const ids=selectedRoots(false),groups=(V.__groups||[]).filter(group=>group.layers.some(id=>SELECTED.has(id))),wrap=el('div','kbar');
 if(groups.length===1&&groups[0].layers.every(id=>SELECTED.has(id)||!LM(id))){
  const name=el('input','txt');name.setAttribute('aria-label','Selection group name');name.maxLength=120;name.value=groups[0].name;const identifier=groups[0].id;name.oninput=()=>{const current=V.__groups.find(group=>group.id===identifier);if(!current)return;current.name=name.value.trim()||'Selection group';changed();renderSelectionGroups();};parent.append(name);
 }
 if(ids.length>1){const button=el('button','btn small','Group selection');button.onclick=()=>{commitHistory();const members=new Set(ids);V.__groups=(V.__groups||[]).map(group=>({...group,layers:group.layers.filter(id=>!members.has(id))})).filter(group=>group.layers.length);V.__groups.push({id:'group_'+crypto.randomUUID(),name:'Selection group '+(V.__groups.length+1),layers:ids});bulkChanged('Selection grouped');};wrap.append(button);}
 if(groups.length){const button=el('button','btn small','Ungroup');button.onclick=()=>{commitHistory();V.__groups=V.__groups.filter(group=>!groups.includes(group));bulkChanged('Selection ungrouped');};wrap.append(button);}
 parent.append(wrap,el('p','sub','Groups select their members together for moving, alignment, visibility and timing. Ungroup to edit individual members. Locked layers stay protected.'));
}
function matchesLayer(m){const q=layerSearch.trim().toLowerCase();return !q||(m.label+' '+m.id+' '+m.group).toLowerCase().includes(q)||LAY.some(child=>isDescendant(child.id,m.id)&&(child.label+' '+child.id).toLowerCase().includes(q));}
function selectionRefresh(){renderLayerTree();renderLayerRows();fillInspector();renderSelectionGroups();overlaySoon();}
function bulkChanged(message){changed(true);selectionRefresh();if(message)toast(message);}
function bulkVisibility(visible){const ids=selectedRoots();for(const id of ids)LS(id).visible=visible;bulkChanged(ids.length?`${ids.length} layer${ids.length===1?'':'s'} ${visible?'shown':'hidden'}`:'Unlock a layer before changing it');}
function bulkLock(){const ids=[...SELECTED].filter(id=>LS(id)),unlock=ids.length&&ids.every(id=>LS(id).locked);for(const id of ids)LS(id).locked=!unlock;bulkChanged(unlock?'Selection unlocked':'Selection locked');}
function soloQuery(){return SOLO.size?'&solo='+encodeURIComponent(JSON.stringify([...SOLO].filter(id=>LM(id)))):'';}
function bulkSolo(){SOLO.clear();for(const id of selectedRoots(false))SOLO.add(id);refreshSolo();}
function refreshSolo(){const button=document.querySelector('#bSoloExit');button.hidden=!SOLO.size;button.textContent=`Exit solo (${SOLO.size})`;hitsFor='';ver++;requestFrame();overlaySoon();}
function bulkToolbar(parent){
  const search=el('input','txt');search.type='search';search.placeholder='Search layers';search.setAttribute('aria-label','Search layers');search.value=layerSearch;
  search.oninput=()=>{layerSearch=search.value;renderLayerTree();renderLayerRows();};search.onkeydown=e=>{if(e.key==='Escape'){search.value='';layerSearch='';renderLayerTree();renderLayerRows();}};parent.append(search);
  const row=el('div','kbar');for(const [label,run] of [['Select results',bulkSelectResults],['Clear',()=>{SELECTED.clear();selLayer=null;selectionRefresh();}]]){const b=el('button','btn small',label);b.onclick=run;row.append(b);}parent.append(row);
  selectionGroupList(parent);
}
function bulkInspector(parent){
  const ids=[...SELECTED].filter(id=>LS(id));if(!ids.length)return false;
  const title=el('div','row');title.append(el('b',null,`${ids.length} layers selected`));parent.append(title);
  const row=el('div','kbar');for(const [label,run] of [['Show',()=>bulkVisibility(true)],['Hide',()=>bulkVisibility(false)],['Lock / unlock',bulkLock],['Solo graphics',bulkSolo]]){const b=el('button','btn small',label);b.onclick=run;row.append(b);}parent.append(row);
  parent.append(el('p','note','Shift-click layers or use their checkboxes to select more. Move the selection together on the canvas or timeline. Locked layers are skipped. Solo affects the preview only.'));
  const actions=el('div','kbar');for(const [label,run] of [['Duplicate added layers',bulkDuplicate],['Delete / hide',bulkDelete]]){const b=el('button','btn small',label);b.onclick=run;actions.append(b);}parent.append(actions);
  selectionGroupControls(parent);
  motionStylesPanel(parent);bulkArrangePanel(parent);return true;
}
function bulkArrangePanel(parent){
  parent.append(el('h3',null,'Align and space'));
  const target=el('select');target.setAttribute('aria-label','Alignment reference');for(const [value,label]of[['selection','Selection bounds'],['frame','Full frame'],['safe','Graphics safe zone']]){const option=el('option');option.value=value;option.textContent=label;target.append(option);}target.value=alignTarget;target.onchange=()=>alignTarget=target.value;parent.append(target);
  const row=el('div','kbar');for(const [mode,label]of[['left','Left'],['center','Centre'],['right','Right'],['top','Top'],['middle','Middle'],['bottom','Bottom'],['space-x','Space H'],['space-y','Space V']]){const b=el('button','btn small',label);b.title='Align '+label.toLowerCase();b.onclick=()=>bulkArrange(mode);row.append(b);}parent.append(row);
  if(SELECTED.size===1){const fit=el('button','btn small','Fit graphics safe zone');fit.onclick=bulkFit;parent.append(fit);}
}
async function arrangeHits(){await loadHits();const ids=selectedRoots(),hits=ids.map(id=>HITS.find(hit=>hit.id===id));if(!ids.length)throw new Error('Select an unlocked layer first');if(hits.some(hit=>!hit))throw new Error('Move the playhead to where all selected layers are visible');return hits;}
function arrangeBounds(hits){if(alignTarget==='safe')return PJ.layout?.content||[0,0,PJ.width,PJ.height];if(alignTarget==='frame'||hits.length===1)return [0,0,PJ.width,PJ.height];return null;}
async function bulkArrange(mode){try{const hits=await arrangeHits(),map=new Map(hits.map(h=>[h.id,h]));commitHistory();for(const offset of DXLayerTools.align(hits,mode,arrangeBounds(hits))){const hit=map.get(offset.id),[dx,dy]=DXLayerTools.localDelta(hit,offset.dx,offset.dy),current=transformAt(LS(hit.id),layerRelativeTime(hit.id));setTransform(hit.id,{x:r2(current.x+dx),y:r2(current.y+dy)});}bulkChanged('Selection arranged');}catch(error){showErr(error.message);}}
async function bulkFit(){try{const hits=await arrangeHits();if(hits.length!==1)return;const hit=hits[0],b=DXLayerTools.bounds(hit),r=PJ.layout?.content||[0,0,PJ.width,PJ.height],scale=Math.min((r[2]-r[0])/Math.max(1,b[2]-b[0]),(r[3]-r[1])/Math.max(1,b[3]-b[1])),current=transformAt(LS(hit.id),layerRelativeTime(hit.id)),[dx,dy]=DXLayerTools.localDelta(hit,(r[0]+r[2]-b[0]-b[2])/2,(r[1]+r[3]-b[1]-b[3])/2);commitHistory();setTransform(hit.id,{x:r2(current.x+dx),y:r2(current.y+dy),scale:r2(Math.max(.01,current.scale*scale))});bulkChanged('Layer fitted to graphics space');}catch(error){showErr(error.message);}}
function bulkNudge(code,px){const dx=code==='ArrowLeft'?-px:code==='ArrowRight'?px:0,dy=code==='ArrowUp'?-px:code==='ArrowDown'?px:0;for(const id of selectedRoots()){const hit=HITS.find(h=>h.id===id)||{base:[1,0,0,1]},[x,y]=DXLayerTools.localDelta(hit,dx,dy),current=transformAt(LS(id),layerRelativeTime(id));setTransform(id,{x:r2(current.x+x),y:r2(current.y+y)});}overlaySoon();}
function bulkDelete(){const ids=selectedRoots();commitHistory();for(const id of ids){if(isItem(id)){V.__media=V.__media.filter(item=>item.id!==id);delete V.__layers[id];LAY=LAY.filter(m=>m.id!==id);SELECTED.delete(id);SOLO.delete(id);}else LS(id).visible=false;}selLayer=[...SELECTED].find(id=>LM(id))||null;bulkChanged('Added layers deleted; scene layers hidden');refreshSolo();}
function bulkDuplicate(){const ids=selectedRoots().filter(isItem);if(!ids.length)return toast('Only added text, shapes and media can be duplicated');commitHistory();PENDING_MULTI=ids.map(id=>placeItemCopy(mediaItem(id),LS(id),LS(id).start,true));toast(`${ids.length} added layers duplicated`);}
function bulkTimelineDrag(event){
  const ids=selectedRoots(),before=ids.map(id=>({id,start:LS(id).start,end:LS(id).end,offset:layerTimeOffset(id)}));if(!before.length)return;
  const x0=x2s(event.clientX),low=Math.min(...before.map(x=>x.start+x.offset)),high=Math.max(...before.map(x=>Math.min(BASE,x.end+x.offset)));
  dragWith(ev=>{const delta=r2(Math.max(-low,Math.min(BASE-high,snap(x2s(ev.clientX)-x0))));for(const initial of before){LS(initial.id).start=r2(initial.start+delta);LS(initial.id).end=r2(initial.end+delta);}renderLayerRows();changed();},()=>{changed(true);fillInspector();});
}
function bulkCanvasDrag(event,point,hit){const initial=selectedRoots().map(id=>({id,hit:HITS.find(h=>h.id===id),current:transformAt(LS(id),layerRelativeTime(id))})).filter(x=>x.hit);dragging=true;dragWith(ev=>{const next=fxy(ev);let [dx,dy]=snapMove(hit,next[0]-point[0],next[1]-point[1],ev);for(const item of initial){const [x,y]=DXLayerTools.localDelta(item.hit,dx,dy);setTransform(item.id,{x:r2(item.current.x+x),y:r2(item.current.y+y)});}drawOverlay();},()=>{dragging=false;GUIDES=[];changed(true);overlaySoon();});}
function drawBulkOutlines(overlay,scale){for(const id of SELECTED){if(id===selLayer)continue;const hit=HITS.find(h=>h.id===id);if(!hit)continue;const polygon=document.createElementNS('http://www.w3.org/2000/svg','polygon');polygon.setAttribute('points',hit.corners.map(p=>p.join(',')).join(' '));polygon.setAttribute('fill','rgba(80,86,244,.04)');polygon.setAttribute('stroke','#5056F4');polygon.setAttribute('stroke-width',2*scale);overlay.append(polygon);}}
