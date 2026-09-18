const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const html=fs.readFileSync(path.join(__dirname,'..','index.html'),'utf8');
const core=html.match(/<script>\s*([\s\S]*?)<\/script>/);
assert(core,'Generator script is present');
vm.runInThisContext(core[1],{filename:'index.html:generator'});
const {ITEMS,generate,validate}=globalThis.MKDDMixer;
const fixture=(name,weights)=>({name,weights,...generate(weights)});
const fixtures=[fixture('catchup',ITEMS.map(i=>i.weight||0)),fixture('equal',ITEMS.map(()=>1)),fixture('maximum',ITEMS.map(()=>1000)),fixture('uneven',ITEMS.map((_,i)=>(i*71+3)%1001))];
ITEMS.forEach((item,i)=>fixtures.push(fixture('only-'+item.id,ITEMS.map((_,j)=>i===j?1:0))));
let checks=0;
for(const f of fixtures){
  assert.equal(f.distribution.reduce((s,i)=>s+i.weight,0),f.total);
  assert.equal(f.code.split('\n').length,f.lines);
  assert.equal(f.lines,29+f.distribution.length);
  assert(f.bytes<=188);
  const writes=f.code.split('\n').map(line=>line.split(' ').map(x=>parseInt(x,16)));
  assert.equal(writes.at(-1)[0],0x0420cbc8);assert.equal(writes.at(-1)[1],0x4bdf8858);
  assert.equal(writes[16][1],0x38800000+f.total-1);
  writes.slice(0,-1).forEach(([address,word],i)=>{
    assert.equal(address,0x04005420+4*i);assert(address<0x040054e4);assert(Number.isInteger(word));
  });
  const records=writes.slice(28,-1).map(([,word])=>({threshold:word>>>16,id:(word>>>8)&255}));
  for(let ticket=0;ticket<f.total;ticket++){
    const selected=records.find(r=>ticket<r.threshold).id;
    let remainder=ticket,index=0;
    while(remainder>=f.weights[index]){remainder-=f.weights[index];index++;}
    assert.equal(selected,ITEMS[index].id);checks++;
  }
}
for(const bad of [-1,1.5,1001,Infinity,NaN,'1',null,undefined]){
  const weights=ITEMS.map(()=>1);weights[0]=bad;assert.throws(()=>generate(weights));
}
assert.throws(()=>generate(ITEMS.map(()=>0)));
assert.throws(()=>generate([]));assert.throws(()=>generate(null));
// Exercise a broad set of weight combinations and verify bounds and exact final threshold.
let state=0x12345678;
for(let n=0;n<1000;n++){
  const weights=ITEMS.map(()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state%1001;});
  const result=generate(weights),lines=result.code.split('\n');
  assert(result.bytes<=188);assert.equal(parseInt(lines.at(-2).split(' ')[1],16)>>>16,result.total);
  checks++;
}
console.log(JSON.stringify({status:'passed',fixtureCount:fixtures.length,ticketAndFuzzChecks:checks,invalidInputChecks:11,itemIDs:ITEMS.map(i=>i.id)}));
