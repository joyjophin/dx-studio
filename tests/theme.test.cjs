const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('dx_studio/theme.js','utf8');

// Exercise the shipped controller with media/storage events, without changing OS settings.
function browser({saved=null,dark=false,blocked=false}={}){
  const events={},mediaEvents={},ready={},changes={},writes=[];
  const root={dataset:{},style:{}},picker={value:'',addEventListener:(name,fn)=>changes[name]=fn};
  const system={matches:dark,addEventListener:(name,fn)=>mediaEvents[name]=fn};
  const window={matchMedia:()=>system,localStorage:{getItem:()=>{if(blocked)throw Error('blocked');return saved;},setItem:(...entry)=>{if(blocked)throw Error('blocked');writes.push(entry);}},addEventListener:(name,fn)=>events[name]=fn};
  let mounted=false;
  const document={documentElement:root,readyState:'loading',querySelectorAll:()=>mounted?[picker]:[],addEventListener:(name,fn)=>ready[name]=fn};
  vm.runInNewContext(source,{window,document});
  const initial={...root.dataset};mounted=true;ready.DOMContentLoaded();
  return {root,picker,writes,initial,choose(value){picker.value=value;changes.change();},system(dark){system.matches=dark;mediaEvents.change();},storage(key,value){events.storage({key,newValue:value});}};
}

test('system applies before mount and follows changes; explicit choice survives system changes and reload',()=>{
  const page=browser({dark:true});assert.equal(page.initial.theme,'dark');assert.equal(page.picker.value,'system');
  page.system(false);assert.equal(page.root.dataset.theme,'light');
  page.choose('dark');page.system(true);page.system(false);assert.equal(page.root.dataset.theme,'dark');
  assert.equal(page.root.style.colorScheme,'dark');assert.deepEqual(page.writes.at(-1),['dx-studio:theme:v1','dark']);
  assert.equal(browser({saved:page.writes.at(-1)[1]}).initial.theme,'dark');
  page.choose('system');assert.equal(page.root.dataset.theme,'light');page.system(true);assert.equal(page.root.dataset.theme,'dark');
});

test('other tabs sync preferences; invalid/cleared and blocked storage remain usable',()=>{
  const page=browser({saved:'light',dark:true});page.storage('unrelated','dark');assert.equal(page.root.dataset.theme,'light');
  page.storage('dx-studio:theme:v1','dark');assert.equal(page.picker.value,'dark');
  page.storage('dx-studio:theme:v1','invalid');assert.equal(page.picker.value,'system');assert.equal(page.root.dataset.theme,'dark');
  page.choose('light');page.storage(null,null);assert.equal(page.picker.value,'system');
  const privatePage=browser({blocked:true,dark:true});privatePage.choose('light');assert.equal(privatePage.root.dataset.theme,'light');
  assert.equal(browser({saved:'invalid',dark:true}).initial.theme,'dark');
});
