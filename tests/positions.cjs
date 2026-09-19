const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
vm.runInThisContext(fs.readFileSync(path.join(__dirname,'../index.html'),'utf8').match(/<script>\s*([\s\S]*?)<\/script>/)[1]);
const {ITEMS,generatePositions,validatePositions}=MKDDMixer;
const defaults=()=>ITEMS.map(i=>i.weight||0);
const fixtures=[];
function add(name,positions){fixtures.push({name,positions,...generatePositions(positions)});}
add('distinct',Array.from({length:8},(_,rank)=>ITEMS.map((_,i)=>i===rank?1:0)));
add('mixed',Array.from({length:8},(_,rank)=>rank%2?defaults():null));
add('catchup',Array.from({length:8},defaults));
add('equal',Array.from({length:8},()=>ITEMS.map(()=>1)));
add('maximum',Array.from({length:8},()=>ITEMS.map(()=>1000)));
add('uneven',Array.from({length:8},(_,rank)=>ITEMS.map((_,i)=>(i*71+rank*93+3)%1001)));
for(let rank=0;rank<8;rank++)add('only-position-'+rank,Array.from({length:8},(_,i)=>rank===i?defaults():null));
for(let item=0;item<ITEMS.length;item++)add('only-item-'+item,Array.from({length:8},()=>ITEMS.map((_,i)=>i===item?1:0)));
let checks=0;
for(const fixture of fixtures){
  const writes=fixture.code.split('\n').map(line=>line.split(' ').map(x=>parseInt(x,16)));
  assert.equal(writes.length,194);assert.equal(fixture.lines,writes.length);assert.equal(fixture.bytes,772);
  const memory=new Map(writes.map(([address,word])=>[0x80000000+(address&0x1ffffff),word]));
  assert.equal(memory.size,writes.length);assert.equal(memory.get(0x8020cbc8),0x4bdf8858);
  for(const address of memory.keys())assert(address===0x8020cbc8||(address>=0x80005420&&address<0x800054a4)||(address>=0x80004d20&&address<0x80004fa0));
  fixture.positions.forEach((weights,rank)=>{
    const base=0x80004d20+rank*80,total=memory.get(base)>>>16;
    const records=Array.from({length:19},(_,i)=>memory.get(base+4+i*4));
    assert.equal(total,fixture.totals[rank]);
    if(weights===null){assert.equal(total,0);assert(records.every(word=>word===0));return;}
    const expected=[];weights.forEach((weight,i)=>{for(let j=0;j<weight;j++)expected.push(ITEMS[i].id);});
    assert.equal(total,expected.length);
    for(let ticket=0;ticket<total;ticket++){
      assert.equal((records.find(word=>ticket<(word>>>16))>>>8)&255,expected[ticket]);checks++;
    }
    assert.equal(records.filter(Boolean).at(-1)>>>16,total);
  });
  const bananas=generatePositions(fixture.positions,{maximumBananas:true});
  assert.equal(bananas.lines,201);assert.equal(bananas.bytes,fixture.bytes);
  assert.equal(bananas.code,fixture.code+'\n04208054 38000040\n04355664 0000001C\n0035564B 0000001C\n0035563B 00000014\n04355668 00000008\n0035564C 00000008\n0035563C 00000006');
}
for(const invalid of [null,[],Array(8),Array(8).fill(null),Array(7).fill(null),Array(9).fill(null)])assert.throws(()=>generatePositions(invalid));
for(const invalid of [-1,1.5,1001,Infinity,NaN,'1',null,undefined]){
  for(let rank=0;rank<8;rank++){
    const positions=Array.from({length:8},defaults);positions[rank][0]=invalid;
    assert.throws(()=>generatePositions(positions),new RegExp(`${rank===0?'1st':rank===1?'2nd':rank===2?'3rd':(rank+1)+'th'} place:`));
  }
}
for(const weights of [ITEMS.map(()=>0),Array(19),[]])assert.throws(()=>generatePositions([weights,...Array(7).fill(null)]));
assert.deepEqual(validatePositions([defaults(),...Array(7).fill(null)]),[30,0,0,0,0,0,0,0]);
// Deterministic fuzz checks ensure every position's final threshold and padding
// remain independent even when profiles have different enabled item counts.
let seed=123;
for(let trial=0;trial<500;trial++){
  const profiles=Array.from({length:8},()=>ITEMS.map(()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed%1001;}));
  const result=generatePositions(profiles);
  result.distributions.forEach((d,rank)=>assert.equal(d.reduce((s,i)=>s+i.weight,0),result.totals[rank]));
}
if(process.argv[2])fs.writeFileSync(process.argv[2],JSON.stringify(fixtures));
console.log(JSON.stringify({status:'passed',positionFixtures:fixtures.length,exhaustiveTickets:checks,fuzzConfigurations:500}));
