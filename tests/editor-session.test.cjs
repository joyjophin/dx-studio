const test = require('node:test');
const assert = require('node:assert/strict');
const EditorSession = require('../dx_studio/editor-session.js');
const clone = x => JSON.parse(JSON.stringify(x));
function storage() {
  const records = new Map();
  return {get length(){return records.size;},key:i=>[...records.keys()][i],getItem:k=>records.get(k),setItem:(k,v)=>records.set(k,v),removeItem:k=>records.delete(k)};
}
function fixture(t, options={}) {
  const calls=[], statuses=[];
  const session = new EditorSession({projectId:'project-a',sourceRevision:'scene-a',revision:'initial',values:{title:'Original'},storage:storage(),delay:100000,retryDelay:100000,
    onStatus:s=>statuses.push(s),api:async (path,body)=>{calls.push(clone(body));return {revision:'revision-'+calls.length,values:body.values};},...options});
  t.after(()=>session.dispose());return {session,calls,statuses};
}
function deferred() {let resolve; const promise=new Promise(r=>{resolve=r;});return {promise,resolve};}

test('no-op edits do not write; successful autosave clears its recovery copy',async t=>{
 const {session,calls}=fixture(t);session.changed({title:'Original'});await session.flush();assert.equal(calls.length,0);
 session.changed({title:'Changed'});assert.equal(session.storage.length,1);await session.flush();
 assert.equal(session.storage.length,0);assert.equal(session.dirty,false);assert.equal(calls[0].revision,'initial');assert.equal(calls[0].autosave,true);
});
test('new edits during an in-flight save are sent in order with the new revision',async t=>{
 const first=deferred(),calls=[];
 const {session}=fixture(t,{api:async (path,body)=>{calls.push(clone(body));if(calls.length===1)await first.promise;return {revision:'r'+calls.length,values:body.values};}});
 session.changed({title:'First'});const pending=session.flush();session.changed({title:'Second'});first.resolve();await pending;
 assert.deepEqual(calls.map(c=>[c.values.title,c.revision]),[['First','initial'],['Second','r1']]);assert.equal(session.saved.title,'Second');assert.equal(session.dirty,false);
});
test('changing back to the original during a save is still persisted',async t=>{
 const first=deferred(),calls=[];
 const {session}=fixture(t,{api:async(path,body)=>{calls.push(clone(body));if(calls.length===1)await first.promise;return {revision:'r'+calls.length,values:body.values};}});
 session.changed({title:'Temporary'});const pending=session.flush();session.changed({title:'Original'});first.resolve();await pending;
 assert.equal(calls.length,2);assert.equal(session.saved.title,'Original');
});
test('offline failure keeps a browser draft and can retry without losing changes',async t=>{
 let offline=true;const {session}=fixture(t,{api:async(path,body)=>{if(offline)throw new Error('Offline');return {revision:'reconnected',values:body.values};}});
 session.changed({title:'Keep me'});await assert.rejects(session.flush(),/Offline/);assert.equal(session.dirty,true);assert.equal(session.storage.length,1);
 offline=false;await session.flush();assert.equal(session.saved.title,'Keep me');assert.equal(session.storage.length,0);
});
test('conflicts pause further writes and retain the current browser draft',async t=>{
 let calls=0;const {session,statuses}=fixture(t,{api:async()=>{calls++;const error=new Error('Conflict');error.status=409;throw error;}});
 session.changed({title:'My cut'});await assert.rejects(session.flush());session.changed({title:'My newer cut'});await assert.rejects(session.flush());
 assert.equal(calls,1);assert.equal(session.blocked,true);assert.equal(statuses.at(-1).kind,'conflict');assert.equal(JSON.parse(session.storage.getItem(session.key)).values.title,'My newer cut');
});
test('reopening finds pending drafts for this project without applying them',t=>{
 const shared=storage();const original=fixture(t,{storage:shared}).session;original.changed({title:'Recovered cut'});original.dispose();
 const reopened=fixture(t,{storage:shared}).session;assert.equal(reopened.saved.title,'Original');assert.equal(reopened.drafts()[0].values.title,'Recovered cut');
 const other=fixture(t,{storage:shared,projectId:'other-project'}).session;assert.equal(other.drafts().length,0);
 reopened.discard(reopened.drafts()[0].key);assert.equal(reopened.drafts().length,0);
});
test('each tab keeps an independent recovery draft',t=>{
 const shared=storage();const first=fixture(t,{storage:shared}).session;const second=fixture(t,{storage:shared}).session;
 first.changed({title:'One'});second.changed({title:'Two'});assert.equal(shared.length,2);assert.notEqual(first.key,second.key);
});
test('blocked browser storage does not prevent a successful disk save',async t=>{
 const {session,statuses}=fixture(t,{storage:{setItem(){throw new Error('Quota');},removeItem(){throw new Error('Quota');}}});
 session.changed({title:'On disk'});await session.flush();assert.equal(session.saved.title,'On disk');assert.equal(statuses.at(-1).recoveryAvailable,false);
});
test('restoring a saved version adopts its revision and clears only this tab draft',async t=>{
 const {session,calls}=fixture(t);session.changed({title:'Pending'});session.adopt({title:'Restored'},'restored-revision');
 await session.flush();assert.equal(calls.length,0);session.changed({title:'Next'});await session.flush();assert.equal(calls[0].revision,'restored-revision');
});
test('debounce automatically saves without a manual flush',async t=>{
 const done=deferred();const {session}=fixture(t,{delay:10,onStatus:s=>{if(s.kind==='saved')done.resolve();}});
 session.changed({title:'Automatic'});await done.promise;assert.equal(session.saved.title,'Automatic');
});
