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
// The optional limit patch must be additive, exact, and absent by default.
const bananaPatch=['04208054 38000040','04355664 0000001C','0035564B 0000001C','0035563B 00000014','04355668 00000008','0035564C 00000008','0035563C 00000006'].join('\n');
for(const fixture of fixtures){
  const enabled=generate(fixture.weights,{maximumBananas:true});
  assert.equal(enabled.code,fixture.code+'\n'+bananaPatch);
  assert.equal(enabled.lines,fixture.lines+7);
  assert.equal(enabled.bytes,fixture.bytes);
  assert.deepEqual(enabled.distribution,fixture.distribution);
  assert.equal(generate(fixture.weights,{maximumBananas:false}).code,fixture.code);
  assert.equal(generate(fixture.weights,{maximumBananas:true}).code,enabled.code);
}
assert.throws(()=>generate(ITEMS.map(()=>0),{maximumBananas:true}));
// All supported lap counts combine with every item and the optional banana patch.
let lapCases=0;
for(const fixture of fixtures){
  for(let laps=1;laps<=99;laps++)for(const bananas of [false,true]){
    const output=generate(fixture.weights,{maximumBananas:bananas,babyParkLaps:laps});
    const prefix=generate(fixture.weights,{maximumBananas:bananas}).code;
    assert(output.code.startsWith(prefix+'\n'));
    const extra=output.code.slice(prefix.length+1).split('\n');
    assert.equal(extra.length,laps>9?58:15);
    assert.equal(output.lines,fixture.lines+(bananas?7:0)+extra.length);
    assert.equal(extra[10],`04005348 ${(0x38000000|laps).toString(16).toUpperCase()}`);
    assert.equal(extra[14],'04187BFC 4BE7D724');
    const addresses=output.code.split('\n').map(line=>line.split(' ')[0]);
    assert.equal(new Set(addresses).size,addresses.length,'No overlapping writes');
    assert.deepEqual(output.distribution,fixture.distribution);
    const hookMap=new Map(extra.map(line=>line.split(' ')));
    if(laps>9){
      assert.equal(hookMap.get('04144934'),'4BEC0A24');
      assert.equal(hookMap.get('04189AB4'),'4BE7B8B8');
      assert.equal(hookMap.get('0414F658'),'4BEB5D28');
      assert.equal(hookMap.get('0414F3B0'),'4BEB5FE4');
      assert.equal(hookMap.get('0414F3EC'),'2C1E0009');
      assert(hookMap.has('0414638C'));assert(hookMap.has('04250FB8'));assert(hookMap.has('0414F4CC'));
    }
    for(const [a] of hookMap){
      const address=parseInt(a,16);
      if(address<0x04010000)assert(address>=0x04005320&&address<0x040053e4,'Lap cave bounds');
    }
    lapCases++;
  }
  assert.equal(generate(fixture.weights,{babyParkLaps:null}).code,fixture.code);
}
for(const laps of [0,100,-1,9.5,Infinity,NaN,'99',true])assert.throws(()=>generate(fixtures[0].weights,{babyParkLaps:laps}),/1 to 99/);
console.log(JSON.stringify({status:'passed',lapCases,lapRange:[1,99],shortLapLines:15,longLapLines:58}));
const introPatch=['041CFD50 60000000','041CFE18 60000000','041B0D58 38000003','041B10AC 60000000','0412DBEC 60000000'].join('\n');
let introCases=0;
for(const fixture of fixtures)for(const babyParkLaps of [null,1,9,10,99])for(const maximumBananas of [false,true]){
  const options={babyParkLaps,maximumBananas};
  const base=generate(fixture.weights,options),enabled=generate(fixture.weights,{...options,skipIntro:true});
  assert.equal(enabled.code,base.code+'\n'+introPatch);
  assert.equal(enabled.lines,base.lines+5);
  assert.deepEqual(enabled.distribution,base.distribution);
  assert.equal(generate(fixture.weights,{...options,skipIntro:false}).code,base.code);
  const addresses=enabled.code.split('\n').map(line=>line.split(' ')[0]);
  assert.equal(new Set(addresses).size,addresses.length);
  introCases++;
}
assert.throws(()=>generate(ITEMS.map(()=>0),{skipIntro:true}));
for(const positions of [Array.from({length:8},(_,i)=>i===7?fixtures[0].weights:null),Array.from({length:8},()=>ITEMS.map(()=>1))]){
  for(const fog of [null,0,100])for(const speedCC of [null,150,10000]){
    const options={maximumBananas:true,babyParkLaps:99,fog,speedCC};
    const base=MKDDMixer.generatePositions(positions,options);
    const enabled=MKDDMixer.generatePositions(positions,{...options,skipIntro:true});
    assert.equal(enabled.code,base.code+'\n'+introPatch);
    const addresses=enabled.code.split('\n').map(line=>line.split(' ')[0]);
    assert.equal(new Set(addresses).size,addresses.length);
    const lastBase=generate(fixtures[0].weights,options);
    assert.equal(generate(fixtures[0].weights,{...options,skipIntro:true}).code,lastBase.code+'\n'+introPatch);
    introCases+=2;
  }
}
console.log(JSON.stringify({status:'passed',introCases,introLines:5}));
console.log(JSON.stringify({status:'passed',fixtureCount:fixtures.length,ticketAndFuzzChecks:checks,bananaPatchCases:fixtures.length,invalidInputChecks:12,itemIDs:ITEMS.map(i=>i.id)}));
