/* Navigation and progressive disclosure only; project values stay in the editor. */
const SHELL_ICONS={
 media:'<rect x="3" y="5" width="18" height="15" rx="2"/><path d="m3 15 5-5 5 5 3-3 5 5"/><circle cx="16.5" cy="9" r="1"/>',
 text:'<path d="M4 5h16M12 5v15M8 20h8"/>',
 elements:'<rect x="3" y="3" width="8" height="8" rx="2"/><circle cx="17" cy="17" r="5"/><path d="m16 4 4 4m0-4-4 4M4 16v4h4"/>',
 audio:'<path d="M5 9v6M9 5v14M13 8v8M17 3v18M21 10v4"/>',
 captions:'<rect x="2" y="5" width="20" height="14" rx="3"/><path d="M10 10H8a2 2 0 0 0 0 4h2m8-4h-2a2 2 0 0 0 0 4h2"/>',
 design:'<circle cx="12" cy="12" r="9"/><path d="M12 3v18M3 12h18M5.6 5.6l12.8 12.8M5.6 18.4 18.4 5.6"/>',
 more:'<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
 back:'<path d="m14 6-6 6 6 6"/>',
 view:'<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M8 4v16M8 15h13"/>',
 layers:'<path d="m3 8 9-5 9 5-9 5zM3 12l9 5 9-5M3 16l9 5 9-5"/>',
 close:'<path d="m6 6 12 12M18 6 6 18"/>',
};
const SHELL_GROUPS=[
 {id:'media',label:'Media',panels:[['Media','Library'],['Layers','Layers']]},
 {id:'text',label:'Text',panels:[['Text','Scene text']]},
 {id:'elements',label:'Elements',panels:[['Blocks','Blocks & templates']]},
 {id:'audio',label:'Audio',panels:[['Narration','Voice'],['Audio','Mix']]},
 {id:'captions',label:'Captions',panels:[['Captions','Captions'],['Transcript','Transcript']]},
 {id:'design',label:'Design',panels:[['Brand','Brand'],['Colours','Colours'],['Composition','Layout'],['Presenter','Presenter']]},
];
let SHELL_CANVAS_GESTURE=false,SHELL_TRACKS=false,SHELL_HELP=new Set(),SHELL_SECTIONS=new Set();
function canvasRatio(width,height){let a=width,b=height;while(b){const r=a%b;a=b;b=r;}return(width/a)+':'+(height/a);}
function shellIcon(name){return '<svg aria-hidden="true" viewBox="0 0 24 24">'+(SHELL_ICONS[name]||SHELL_ICONS.more)+'</svg>';}
function openTool(panel){
 if(window.innerWidth<=1050&&selLayer){SELECTED.clear();selLayer=null;fillInspector();}
 if(!VIEW.inspector){VIEW.inspector=true;applyView();}
 document.querySelector('.tab[data-p="'+panel+'"]')?.click();
 $('#moreTools').open=false;
}
function shellPanelChanged(panel){
 const group=SHELL_GROUPS.find(g=>g.panels.some(([name])=>name===panel));
 for(const button of document.querySelectorAll('[data-tool]')){const active=button.dataset.tool===group?.id;button.classList.toggle('on',active);button.setAttribute('aria-pressed',String(active));}
 $('#toolTitle').textContent=group?.label||panel;$('#moreTools summary').classList.toggle('on',!group);
 const subnav=$('#toolSubnav');subnav.replaceChildren();
 for(const [name,label]of group?.panels||[]){if(!document.querySelector('.tab[data-p="'+name+'"]'))continue;const b=el('button','tool-subtab'+(name===panel?' on':''));b.textContent=label;b.setAttribute('aria-pressed',String(name===panel));b.onclick=()=>openTool(name);subnav.append(b);}
 subnav.hidden=subnav.childElementCount<2;
 const quick=$('#toolQuick');quick.replaceChildren();
 if(panel==='Text')quick.append(mediaButton('+ Add text',()=>$('#bText').click()));
 if(panel==='Blocks'){const button=mediaButton('+ Add shape',()=>openShapes(button));quick.append(button);}
 if(panel==='Composition'){const guides=mediaButton('Toggle safe-zone guides',()=>$('#bSafe').click());quick.append(guides);}
 const pane=document.querySelector('.pane.on');if(pane){shellHelp(pane,panel);if(panel==='Text')shellTextFocus(pane);}
 document.querySelector('.app').classList.toggle('timing-tool',panel==='Timing');
}
function shellHelp(pane,panel){
 for(const note of [...pane.querySelectorAll(':scope > div > .note,:scope > .note')]){
  if(note.parentElement.tagName==='DETAILS')continue;
  const details=el('details','tool-help'),summary=el('summary');summary.textContent='About this tool';details.open=SHELL_HELP.has(panel);details.ontoggle=()=>details.open?SHELL_HELP.add(panel):SHELL_HELP.delete(panel);note.before(details);details.append(summary,note);
 }
}
function shellTextFocus(pane){
 const timed=SCH.filter(entry=>entry.type==='text'&&entry.at!=null);if(!timed.length)return;
 const scene=V.__story.find(scene=>scene.start<=ST()&&ST()<scene.end);if(!scene)return;
 const fields=[...pane.querySelectorAll('[id]')].filter(node=>node.id.startsWith('f-')&&SCH.some(entry=>entry.type==='text'&&'f-'+entry.key===node.id));
 let extra=pane.querySelector('.text-extra');if(!extra){extra=el('details','inspector-section text-extra');const title=el('summary');title.textContent='More project text';extra.append(title);pane.append(extra);}
 let caption=pane.querySelector('.text-scene-label');if(!caption){caption=el('p','text-scene-label');pane.insertBefore(caption,extra);}caption.textContent=scene.name+' · scene text';
 for(const field of fields){const entry=SCH.find(entry=>'f-'+entry.key===field.id);if(entry.at!=null&&scene.start<=entry.at&&entry.at<scene.end)pane.insertBefore(field,extra);else extra.append(field);}
 pane.dataset.textScene=scene.id;
}
function shellSeek(){const pane=document.querySelector('.pane.on');if(!pane||pane.dataset.p!=='Text'||['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName))return;const scene=V.__story.find(scene=>scene.start<=ST()&&ST()<scene.end);if(scene&&pane.dataset.textScene!==scene.id)shellTextFocus(pane);}
function shellInspectorChanged(){if(SHELL_CANVAS_GESTURE)return;document.querySelector('.app').classList.toggle('has-selection',!!selLayer);}
function shellInspectorSections(root){
 const nodes=[...root.children],groups=[];let group={title:'',nodes:[]};
 for(const node of nodes){if(node.tagName==='H3'){groups.push(group);group={title:node.textContent,nodes:[]};}else group.nodes.push(node);}groups.push(group);root.replaceChildren();
 const header=groups.shift();for(const node of header.nodes){if(node.classList.contains('sub'))continue;root.append(node);}
 const priority=['Content','Text','Transform','Shape'];groups.sort((a,b)=>(priority.includes(a.title)?priority.indexOf(a.title):100)-(priority.includes(b.title)?priority.indexOf(b.title):100));
 for(const group of groups){if(!group.nodes.length)continue;
  // The words stay directly editable; typography and motion are secondary.
  if(group.title==='Text'&&group.nodes[0]?.querySelector('textarea')){root.append(group.nodes.shift());group.title='Typography';}
  const details=el('details','inspector-section'),summary=el('summary');summary.textContent=group.title==='On screen'?'Timing & visibility':group.title;details.open=group.title==='Content'||group.title==='Transform'||SHELL_SECTIONS.has(group.title);details.ontoggle=()=>details.open?SHELL_SECTIONS.add(group.title):SHELL_SECTIONS.delete(group.title);details.append(summary,...group.nodes);root.append(details);
 }
}
function toggleTimelineLayers(){SHELL_TRACKS=!SHELL_TRACKS;document.querySelector('.app').classList.toggle('tracks-expanded',SHELL_TRACKS);$('#bTimelineLayers').setAttribute('aria-expanded',String(SHELL_TRACKS));$('#bTimelineLayers').classList.toggle('on',SHELL_TRACKS);requestAnimationFrame(()=>{placePlayhead();overlaySoon();requestFrame();});}
function setupShell(){
 const rail=$('#toolRail');for(const group of SHELL_GROUPS){if(!group.panels.some(([name])=>document.querySelector('.tab[data-p="'+name+'"]')))continue;const b=el('button','tool-button');b.dataset.tool=group.id;b.setAttribute('aria-label',group.label);b.title=group.label;b.innerHTML=shellIcon(group.id);b.append(document.createTextNode(group.label));b.onclick=()=>openTool(group.panels.find(([name])=>document.querySelector('.tab[data-p="'+name+'"]'))[0]);rail.insertBefore(b,$('#moreTools'));}
 const menu=$('#moreToolsMenu'),primaryPanels=new Set(SHELL_GROUPS.flatMap(group=>group.panels.map(([name])=>name)));for(const name of panels()){if(primaryPanels.has(name))continue;const b=el('button');b.textContent=name==='Revisions'?'Revision handoff':name;b.onclick=()=>openTool(name);menu.append(b);}
 $('#moreTools summary').innerHTML=shellIcon('more')+'<span>More</span>';
 $('#bHome').innerHTML=shellIcon('back');$('#bHome').setAttribute('aria-label','Back to projects');
 $('#bView').innerHTML=shellIcon('view');$('#bView').setAttribute('aria-label','View options');
 $('#bTimelineLayers').innerHTML=shellIcon('layers')+'<span>Layers</span>';
 $('#bCloseInspector').innerHTML=shellIcon('close');$('#bCloseInspector').onclick=()=>{SELECTED.clear();selLayer=null;selectionRefresh();};
 $('#bExport').onclick=()=>openTool('Export');$('#bCollapseTools').onclick=()=>{VIEW.inspector=false;applyView();};
 $('#bTimelineLayers').onclick=toggleTimelineLayers;
 $('#canvasFormat').textContent=canvasRatio(PJ.width,PJ.height)+' · '+PJ.width+' × '+PJ.height;
 $('#duration').textContent='/ '+DUR.toFixed(2)+' s';
 $('#bUndo').textContent='↶';$('#bRedo').textContent='↷';$('#bUndo').setAttribute('aria-label','Undo');$('#bRedo').setAttribute('aria-label','Redo');
 $('#bPrev').textContent='‹';$('#bNext').textContent='›';$('#bPrev').setAttribute('aria-label','Previous frame');$('#bNext').setAttribute('aria-label','Next frame');
 document.addEventListener('click',event=>{for(const menu of document.querySelectorAll('.shell-menu[open]'))if(!menu.contains(event.target))menu.open=false;});
 for(const button of document.querySelectorAll('#projectMenu button'))button.addEventListener('click',()=>{$('#projectMenu').open=false;});
 (document.querySelector('.tab[data-p="Media"]')||document.querySelector('.tab'))?.click();shellInspectorChanged();setGuides(false);
}
