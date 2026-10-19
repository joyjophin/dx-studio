/* A small, optional first-project guide. No project data leaves this computer. */
const GUIDE_STEPS=[
 ['Make it yours','Select a headline on the canvas, then change its words in the inspector. Use Text for the scene’s exposed text controls.','Text'],
 ['Bring your sources','Add footage and images in Media. Add a voice recording in Audio → Voice. Imports are copied into the project.','Media'],
 ['Leave room for your presenter','Choose a presenter reservation in Design → Layout. Toggle safe-zone guides above the canvas; guides stay out of the exported video.','Composition'],
 ['Fix the captions','Open Captions to correct words and timings. Changing caption text does not change the recording.','Captions'],
 ['Keep your work','Watch for “All changes saved”. The project menu has Version history and browser draft recovery. Versions keep settings; a portable ZIP also carries source files and the matching engine.',null],
 ['Finish and share','Open Export, check source files, choose resolution and caption mode, then Build this export. Review the finished MP4 before publishing.','Export']
];
let GUIDE_INDEX=0;
function showGuide(index=0){GUIDE_INDEX=index;const [title,note,panel]=GUIDE_STEPS[index];$('#guideStep').textContent='Step '+(index+1)+' of '+GUIDE_STEPS.length;$('#guideTitle').textContent=title;$('#guideText').textContent=note;$('#guideOpen').hidden=!panel;$('#guideOpen').onclick=()=>{$('#guideDialog').close();openTool(document.querySelector('.tab[data-p="'+panel+'"]')?panel:'Layers');};$('#guidePrev').disabled=index===0;$('#guideNext').textContent=index===GUIDE_STEPS.length-1?'Finish guide':'Next';if(!$('#guideDialog').open)$('#guideDialog').showModal();}
function finishGuide(){try{localStorage.setItem('dx-studio:guide:v1','done');}catch(_){}$('#welcomeBar').hidden=true;$('#guideDialog').close();}
async function downloadProjectBundle(){
 const button=$('#bundleDownload');button.disabled=true;
 try{await session.flush();$('#bundleMessage').textContent='Preparing your portable project…';const result=await api('/api/bundle/prepare',{include_history:$('#bundleHistory').checked}),link=el('a');link.href=projectURL(result.url);link.download='dx-project.zip';link.click();$('#bundleDialog').close();toast('Portable project ready');}catch(error){$('#bundleMessage').textContent=error.message;}finally{button.disabled=false;}
}
async function showDiagnostics(){
 $('#diagnosticsDialog').showModal();$('#diagnosticsText').textContent='Checking this installation…';$('#diagnosticsDownload').disabled=true;
 try{const report=await api('/api/system');$('#diagnosticsText').textContent=JSON.stringify(report,null,2);$('#diagnosticsDownload').disabled=false;$('#diagnosticsDownload').onclick=()=>creatorDownload('dx-studio-diagnostics.json',report);}catch(error){$('#diagnosticsText').textContent=error.message;}
}
function setupGuide(){
 $('#bGuide').onclick=()=>showGuide();$('#guideStart').onclick=()=>showGuide();$('#guideDismiss').onclick=finishGuide;$('#guideClose').onclick=()=>$('#guideDialog').close();$('#guidePrev').onclick=()=>showGuide(Math.max(0,GUIDE_INDEX-1));$('#guideNext').onclick=()=>GUIDE_INDEX===GUIDE_STEPS.length-1?finishGuide():showGuide(GUIDE_INDEX+1);
 $('#bBundle').onclick=()=>{$('#bundleMessage').textContent='Includes source files, current saved edits, fonts and the matching engine. Output videos and caches are excluded. Review your source assets and licences before sharing.';$('#bundleDialog').showModal();};$('#bundleDownload').onclick=downloadProjectBundle;$('#bundleClose').onclick=()=>$('#bundleDialog').close();$('#bDiagnostics').onclick=showDiagnostics;$('#diagnosticsClose').onclick=()=>$('#diagnosticsDialog').close();
 try{$('#welcomeBar').hidden=localStorage.getItem('dx-studio:guide:v1')==='done';}catch(_){}if(new URLSearchParams(location.search).has('tour'))showGuide();
}
