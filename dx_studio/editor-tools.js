/* Shared selection geometry. Canvas coordinates are converted back to parent space. */
(function(root){
  const bounds=h=>{const xs=h.corners.map(p=>p[0]),ys=h.corners.map(p=>p[1]);return [Math.min(...xs),Math.min(...ys),Math.max(...xs),Math.max(...ys)];};
  function roots(ids,metadata){const chosen=new Set(ids),map=new Map(metadata.map(m=>[m.id,m]));return [...chosen].filter(id=>{let parent=map.get(id)?.parent;while(parent){if(chosen.has(parent))return false;parent=map.get(parent)?.parent;}return true;});}
  function localDelta(hit,dx,dy){const [a,b,c,d]=hit.base||[1,0,0,1],det=a*d-c*b;if(Math.abs(det)<1e-8)throw new Error('Cannot arrange a layer with a zero-size parent transform');return [(d*dx-c*dy)/det,(-b*dx+a*dy)/det];}
  function align(hits,mode,target){
    if(!hits.length)return [];const boxes=hits.map(bounds),area=target||[Math.min(...boxes.map(b=>b[0])),Math.min(...boxes.map(b=>b[1])),Math.max(...boxes.map(b=>b[2])),Math.max(...boxes.map(b=>b[3]))];
    if(mode==='space-x'||mode==='space-y'){
      if(hits.length<3)throw new Error('Select at least three visible layers to distribute');
      const axis=mode==='space-x'?0:1,order=boxes.map((b,i)=>({b,i})).sort((a,b)=>a.b[axis]-b.b[axis]);
      const total=order.reduce((sum,x)=>sum+x.b[axis+2]-x.b[axis],0),gap=(area[axis+2]-area[axis]-total)/(hits.length-1);let cursor=area[axis];
      return order.map(({b,i})=>{const delta=cursor-b[axis];cursor+=b[axis+2]-b[axis]+gap;return {id:hits[i].id,dx:axis===0?delta:0,dy:axis===1?delta:0};});
    }
    return hits.map((hit,i)=>{const b=boxes[i];let dx=0,dy=0;
      if(mode==='left')dx=area[0]-b[0];if(mode==='center')dx=(area[0]+area[2]-b[0]-b[2])/2;if(mode==='right')dx=area[2]-b[2];
      if(mode==='top')dy=area[1]-b[1];if(mode==='middle')dy=(area[1]+area[3]-b[1]-b[3])/2;if(mode==='bottom')dy=area[3]-b[3];return {id:hit.id,dx,dy};});
  }
  root.DXLayerTools={bounds,roots,localDelta,align};if(typeof module!=='undefined'&&module.exports)module.exports=root.DXLayerTools;
})(typeof globalThis!=='undefined'?globalThis:this);
