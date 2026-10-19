const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

test('continuous pointer or slider input renders before release and keeps its latest value', () => {
  const html = fs.readFileSync(require('node:path').join(__dirname, '../dx_studio/editor.html'), 'utf8');
  const source = html.match(/function queuePreview\(immediate=false\) \{[\s\S]*?\n\}/)[0];
  let now = 0, sequence = 0, value = 0;
  const tasks = new Map(), rendered = [];
  const scope = {pushTimer:null,
    setTimeout(fn, delay) { const id = ++sequence; tasks.set(id, {fn, at:now+delay}); return id; },
    clearTimeout(id) { tasks.delete(id); },
    pushNow() { scope.clearTimeout(scope.pushTimer); scope.pushTimer=null; rendered.push({at:now,value}); }
  };
  vm.createContext(scope);vm.runInContext(source,scope);
  function advance(time) { while(true) {const next=[...tasks].sort((a,b)=>a[1].at-b[1].at)[0];if(!next||next[1].at>time)break;tasks.delete(next[0]);now=next[1].at;next[1].fn();}now=time; }
  for(let time=0;time<200;time+=8){advance(time);value=time;scope.queuePreview();}
  assert.ok(rendered.length>=5,'input must not starve preview until pointer-up');
  assert.ok(rendered[0].at<=40,'the first visible update must occur during the gesture');
  value=200;scope.queuePreview(true);advance(240);
  assert.equal(rendered.at(-1).value,200,'release must flush the final transform');
  assert.equal(tasks.size,0);
});
