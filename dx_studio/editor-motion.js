/* Reusable motion and a curve editor; project changes use normal undo/autosave. */
const DXMotion = (() => {
  function bezier(u, points) {
    if(u<=0)return 0;if(u>=1)return 1;
    const [x1,y1,x2,y2]=points,cubic=(t,a,b)=>3*(1-t)**2*t*a+3*(1-t)*t*t*b+t**3;
    let low=0,high=1;for(let i=0;i<32;i++){const mid=(low+high)/2;if(cubic(mid,x1,x2)<u)low=mid;else high=mid;}
    return cubic((low+high)/2,y1,y2);
  }
  function ease(key,u){return key.ease==='custom'?bezier(u,key.bezier):(EASE[key.ease||'ease']||EASE.ease)(u);}
  return {bezier,ease};
})();
const MOTION_OPTIONS={id:'rise',duration:.6,stagger:0,calm:false};

function motionCurveEditor(key,onChange) {
  const root=el('div','motion-curve'),select=el('select');select.setAttribute('aria-label','Keyframe easing');
  for(const value of [...Object.keys(EASE),'custom']){const option=el('option');option.value=value;option.textContent=value==='custom'?'Custom Bézier':value;select.append(option);}
  select.value=key.ease||'ease';root.append(select);
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 240 180');svg.setAttribute('role','group');svg.setAttribute('aria-label','Keyframe easing curve');root.append(svg);
  const controls=el('div','motion-curve-fields');root.append(controls);
  const hint=el('p','sub','Horizontal: time. Vertical: progress. Drag handles or enter values; Y outside 0–1 creates overshoot.');root.append(hint);
  let frozen=null;
  function render(){
    svg.replaceChildren();controls.replaceChildren();
    const custom=key.ease==='custom',points=key.bezier||[.25,.1,.25,1];controls.hidden=!custom;hint.textContent=custom?'Horizontal: time. Vertical: progress. Drag handles or enter values; Y outside 0–1 creates overshoot.':'Horizontal: time. Vertical: progress. Choose Custom Bézier to edit the handles.';
    const samples=Array.from({length:61},(_,i)=>DXMotion.ease(key,i/60));
    const low=frozen?.[0]??Math.min(-.12,...samples,...(custom?[points[1],points[3]]:[]))-.08;
    const high=frozen?.[1]??Math.max(1.12,...samples,...(custom?[points[1],points[3]]:[]))+.08;
    const X=u=>24+192*u,Y=u=>156-132*(u-low)/(high-low);
    const shape=(tag,attributes)=>{const node=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v]of Object.entries(attributes))node.setAttribute(k,v);svg.append(node);return node;};
    shape('path',{d:`M24 ${Y(0)}H216M24 ${Y(1)}H216M24 ${Y(0)}L216 ${Y(1)}`,class:'curve-grid'});
    shape('path',{d:samples.map((v,i)=>(i?'L':'M')+X(i/60)+' '+Y(v)).join(' '),class:'curve-path'});
    if(!custom)return;
    for(const i of [0,2]){
      const endpoint=i===0?[X(0),Y(0)]:[X(1),Y(1)];shape('line',{x1:endpoint[0],y1:endpoint[1],x2:X(points[i]),y2:Y(points[i+1]),class:'curve-tangent'});
      const handle=shape('circle',{cx:X(points[i]),cy:Y(points[i+1]),r:6,class:'curve-handle',tabindex:0,role:'button','aria-label':`${i?'Second':'First'} curve handle. Use arrow keys to move, Shift for larger steps.`});
      handle.onkeydown=event=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key))return;event.preventDefault();event.stopPropagation();const step=event.shiftKey?.1:.01,axis=['ArrowLeft','ArrowRight'].includes(event.key)?i:i+1;points[axis]=Math.max(axis===i?0:-2,Math.min(axis===i?1:3,points[axis]+(['ArrowLeft','ArrowDown'].includes(event.key)?-step:step)));key.bezier=points;onChange();render();svg.querySelectorAll('.curve-handle')[i/2]?.focus();};
      handle.onpointerdown=event=>{
        event.preventDefault();event.stopPropagation();commitHistory();frozen=[low,high];
        const box=svg.getBoundingClientRect();
        dragWith(next=>{points[i]=Math.max(0,Math.min(1,((next.clientX-box.left)/box.width*240-24)/192));points[i+1]=Math.max(-2,Math.min(3,low+(156-(next.clientY-box.top)/box.height*180)/132*(high-low)));key.bezier=points;render();onChange();},()=>{frozen=null;render();});
      };
    }
    for(const [index,label]of ['X1','Y1','X2','Y2'].entries()){
      const wrap=el('label'),input=el('input','num');input.type='number';input.step=.01;input.min=index%2?-2:0;input.max=index%2?3:1;input.value=+(points[index].toFixed(3));input.setAttribute('aria-label','Easing '+label);
      input.onchange=()=>{const value=+input.value;if(input.value===''||!Number.isFinite(value)||value<+input.min||value>+input.max){input.value=points[index];return;}commitHistory();points[index]=value;key.bezier=points;onChange();render();};wrap.append(document.createTextNode(label),input);controls.append(wrap);
    }
  }
  select.onchange=()=>{commitHistory();key.ease=select.value;if(key.ease==='custom'&&!key.bezier)key.bezier=[.25,.1,.25,1];onChange();render();};render();return root;
}

function motionStylesPanel(parent){
  parent.append(el('h3',null,'Motion styles'));
  const root=el('div','motion-styles'),select=el('select');select.setAttribute('aria-label','Motion style');root.append(select);
  const duration=el('input','num'),stagger=el('input','num');
  for(const [input,label,key,min,max]of[[duration,'Motion duration','duration',.01,86400],[stagger,'Motion stagger','stagger',0,60]]){input.type='number';input.step=.05;input.min=min;input.max=max;input.value=MOTION_OPTIONS[key];input.setAttribute('aria-label',label);input.oninput=()=>{if(input.value!==''&&Number.isFinite(+input.value)&&+input.value>=min&&+input.value<=max)MOTION_OPTIONS[key]=+input.value;};const row=el('label','field');row.append(document.createTextNode(label+' (s)'),input);root.append(row);}
  const calm=el('input');calm.type='checkbox';calm.checked=MOTION_OPTIONS.calm;calm.onchange=()=>MOTION_OPTIONS.calm=calm.checked;const calmLabel=el('label','kbar');calmLabel.append(calm,document.createTextNode('Reduced motion: keep fades only'));root.append(calmLabel);
  root.append(el('p','sub','Replaces selected layers’ keyframes and entrances/exits. Keeps their static placement, size, content and on-screen timing. Stagger follows selection order. Undo restores the previous motion.'));
  const apply=mediaButton('Apply to selection',async()=>{
    try{
      const snapshot=JSON.stringify(V),ids=selectedRoots(false),selection=JSON.stringify(ids);MOTION_OPTIONS.duration=+duration.value;MOTION_OPTIONS.stagger=+stagger.value;apply.disabled=true;
      const result=await api('/api/creator/motion-prepare',{values:JSON.parse(snapshot),ids,id:select.value,duration:+duration.value,stagger:+stagger.value,calm:calm.checked});
      if(JSON.stringify(V)!==snapshot||JSON.stringify(selectedRoots(false))!==selection)throw new Error('Project or selection changed while preparing motion; apply again to the current selection');
      const count=Object.keys(result.states).length;if(!count)return toast('Unlock a layer before applying motion');
      commitHistory();Object.assign(V.__layers,result.states);bulkChanged(`Motion applied to ${count} layer${count===1?'':'s'}${result.skipped.length?' · locked layers skipped':''}`);
    }catch(error){showErr(error.message);}finally{apply.disabled=false;}
  });root.append(apply);
  const advanced=el('details','tool-help'),title=el('summary');title.textContent='Save and share styles';advanced.append(title);
  const name=el('input','txt');name.placeholder='e.g. My channel reveal';name.maxLength=80;name.setAttribute('aria-label','Motion style name');advanced.append(name);
  let styles=[];
  async function load(id){try{styles=(await api('/api/creator/motion')).styles;if(!root.isConnected)return;select.replaceChildren();for(const style of styles){const option=el('option');option.value=style.id;option.textContent=style.name+(style.builtin?' · included':'');select.append(option);}select.value=styles.some(s=>s.id===(id||MOTION_OPTIONS.id))?(id||MOTION_OPTIONS.id):styles[0].id;MOTION_OPTIONS.id=select.value;}catch(error){showErr(error.message);}}
  select.onchange=()=>{MOTION_OPTIONS.id=select.value;const style=styles.find(s=>s.id===select.value);if(style){duration.value=Math.round(style.duration*1000)/1000;MOTION_OPTIONS.duration=+duration.value;}};
  advanced.append(mediaButton('Save selected layer’s motion',async()=>{try{if(SELECTED.size!==1)throw new Error('Select exactly one layer to capture its motion');const result=await api('/api/creator/motion-save',{values:clone(V),layer_id:[...SELECTED][0],name:name.value});await load(result.style.id);toast('Motion saved on this computer');}catch(error){showErr(error.message);}}));
  const row=el('div','kbar');row.append(mediaButton('Export JSON',()=>{const style=styles.find(s=>s.id===select.value);if(!style)return;const {id,builtin,...data}=style,url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'})),link=el('a');link.href=url;link.download='dx-motion.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}),
    mediaButton('Import JSON',()=>creatorJSON('Import motion style','Paste an exported DX motion style. This adds it to your local library without changing project layers.',async text=>{const result=await api('/api/creator/motion-import',{style:JSON.parse(text)});await load(result.style.id);})),
    mediaButton('Remove saved style',async()=>{try{await api('/api/creator/motion-delete',{id:select.value});await load();toast('Style removed from the library; applied motion stays in projects');}catch(error){showErr(error.message);}}));
  advanced.append(row);root.append(advanced);parent.append(root);setTimeout(()=>load(),0);
}
