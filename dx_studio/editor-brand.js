/* Palette/type presets change selected public parameters through normal undo and autosave. */
let BRAND_PRESETS=[],BRAND_REVIEW=null;
function brandPanel(){
  BRAND_REVIEW=null;
  const root=el('div');root.append(el('p','note','Reuse your palette and exposed text sizes across projects. Review exactly which fields change, and keep the exceptions you want.'));
  const select=el('select');select.id='brandPreset';select.setAttribute('aria-label','Brand preset');select.onchange=()=>{BRAND_REVIEW=null;$('#brandReview').replaceChildren();};root.append(el('p','sub','Choose a preset to review'),select);
  const row=el('div','kbar');row.append(mediaButton('Review preset',reviewBrand),mediaButton('Export preset',exportBrand),mediaButton('Import preset JSON',importBrand));root.append(row);
  const name=el('input','txt');name.id='brandName';name.placeholder='e.g. My channel palette';name.maxLength=80;name.setAttribute('aria-label','New brand preset name');root.append(name,mediaButton('Save current style',saveBrand));
  const note=el('p','note');note.id='brandStatus';note.setAttribute('role','status');root.append(note);
  const review=el('div');review.id='brandReview';root.append(review);root.append(brandAssetsPanel());setTimeout(loadBrands,0);return root;
}
async function loadBrands(selected){
  try{BRAND_PRESETS=(await api('/api/brands')).presets;const select=$('#brandPreset');if(!select)return;select.replaceChildren();for(const preset of BRAND_PRESETS){const option=el('option');option.value=preset.id;option.textContent=preset.name+(preset.builtin?' · included':'');select.append(option);}if(selected)select.value=selected;$('#brandStatus').textContent='Presets match public colour and *_size parameters. Custom fonts and logos are managed separately.';}
  catch(error){showErr(error.message);}
}
async function reviewBrand(){
  try{const preset=BRAND_PRESETS.find(p=>p.id===$('#brandPreset').value),resolved=await api('/api/brands/resolve',{id:preset.id});if($('#brandPreset').value!==preset.id)return;BRAND_REVIEW=resolved;
    const root=$('#brandReview');root.replaceChildren();root.append(el('h3',null,'Choose fields to apply'));
    for(const [key,value]of Object.entries(resolved.values)){const row=el('label','brand-field'),check=el('input');check.type='checkbox';check.checked=true;check.dataset.brandKey=key;
      const label=el('span');label.textContent=(S(key)?.label||key)+': '+V[key]+' → '+value;row.append(check,label);
      if(S(key)?.type==='color'){const swatch=el('span','brand-swatch');swatch.style.background=value;row.append(swatch);}root.append(row);}
    root.append(mediaButton('Apply selected fields',applyBrand));$('#brandStatus').textContent=`${Object.keys(resolved.values).length} compatible fields. ${resolved.skipped.length} skipped. ${resolved.clamped.length} sizes adjusted to this scene’s limits.`;
  }catch(error){showErr(error.message);}
}
function applyBrand(){
  if(!BRAND_REVIEW)return;const keys=[...document.querySelectorAll('[data-brand-key]:checked')].map(box=>box.dataset.brandKey);
  if(!keys.length)return toast('Choose at least one field');commitHistory();for(const key of keys)V[key]=BRAND_REVIEW.values[key];changed(true);buildPanelsKeepingTab('Brand');toast('Brand style applied; other fields kept');
}
function buildPanelsKeepingTab(name){buildPanels();const tab=[...document.querySelectorAll('.tab')].find(tab=>tab.dataset.p===name);if(tab)tab.click();}
async function saveBrand(){
  try{const keys=BRAND_REVIEW?[...document.querySelectorAll('[data-brand-key]:checked')].map(box=>box.dataset.brandKey):null;
    const result=await api('/api/brands/save',{name:$('#brandName').value,values:clone(V),keys});await loadBrands(result.preset.id);toast('Brand style saved on this computer');}
  catch(error){showErr(error.message);}
}
function exportBrand(){
  const preset=BRAND_PRESETS.find(p=>p.id===$('#brandPreset').value);if(!preset)return;
  const data={format_version:1,name:preset.name,tokens:preset.tokens},url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'})),link=el('a');link.href=url;link.download='dx-studio-brand.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function importBrand(){$('#brandImportText').value='';$('#brandImportMessage').textContent='Paste an exported DX Studio brand preset. It will be saved locally; review it before applying.';$('#brandImportDialog').showModal();}
async function applyBrandImport(){
  try{const preset=JSON.parse($('#brandImportText').value);if(preset.format_version!==1)throw new Error('Use a DX Studio brand preset with format_version 1');const result=await api('/api/brands/import',preset);$('#brandImportDialog').close();await loadBrands(result.preset.id);await reviewBrand();}
  catch(error){$('#brandImportMessage').textContent=error.message;}
}
