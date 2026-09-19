const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
vm.runInThisContext(fs.readFileSync(path.join(__dirname,'../index.html'),'utf8').match(/<script>\s*([\s\S]*?)<\/script>/)[1]);
const {ITEMS,generate,generatePositions,raceOptionCodes}=MKDDMixer;
const weights=ITEMS.map(i=>i.weight||0),positions=Array.from({length:8},(_,i)=>i%2?weights:null);
const decode=lines=>new Map(lines.map(line=>line.split(' ').map(x=>parseInt(x,16))));
const float=word=>{const b=Buffer.alloc(4);b.writeUInt32BE(word);return b.readFloatBE();};
const fixtures=[];
let previousEnd=Infinity,previousStart=Infinity;
for(let fog=0;fog<=100;fog++){
  const lines=raceOptionCodes(fog),writes=decode(lines);
  assert.equal(lines.length,24);assert.equal(writes.size,24);
  assert.equal(writes.get(0x04182490),0x4be82c50);
  assert(!writes.has(0x041A1E64),'Never intercept HUD drawing or add a screen overlay');
  for(const address of writes.keys())assert(address===0x04182490 || (address>=0x040050cc && address<=0x04005128));
  const start=float(writes.get(0x040050d0)),end=float(writes.get(0x040050d4));
  assert(start>=1200,'Keep nearby characters outside the fog');
  assert(start<=previousStart && end<=previousEnd && start<end);
  assert.equal(writes.get(0x040050cc),fog===0?0:2);
  const blendAt=z=>fog===0?0:Math.max(0,Math.min(1,(z-start)/(end-start)));
  for(const z of [0,500,680,1000,1200])assert.equal(blendAt(z),0);
  if(fog===100){assert.equal(start,1200);assert.equal(end,3200);assert.equal(blendAt(2200),0.5);assert.equal(blendAt(3200),1);}
  assert.equal(writes.get(0x040050d8),0xf0f2f4ff);
  previousEnd=end;previousStart=start;
  fixtures.push({fog,code:lines.join('\n')});
}
let previousMultiplier=0;
for(let speedCC=150;speedCC<=500;speedCC++){
  const lines=raceOptionCodes(null,speedCC),writes=decode(lines);
  assert.equal(lines.length,4);
  const multiplier=float(writes.get(0x04361d4c));assert(multiplier>previousMultiplier);
  assert.equal(multiplier,Math.fround(1.15*speedCC/150));
  assert.equal(writes.get(0x04361d44),writes.get(0x04361d48));assert.equal(writes.get(0x04361d48),writes.get(0x04361d4c));
  assert.equal(float(writes.get(0x043d1894)),Math.fround(200*speedCC/150));
  previousMultiplier=multiplier;fixtures.push({speedCC,code:lines.join('\n')});
}
for(const value of [-1,101,NaN,Infinity,1.5,'50',true,{},[]])assert.throws(()=>raceOptionCodes(value,null),/Fog/);
for(const value of [0,149,501,NaN,Infinity,200.5,'200',true,{},[]])assert.throws(()=>raceOptionCodes(null,value),/Speed/);
assert.deepEqual(raceOptionCodes(),[]);
for(const create of [options=>generate(weights,options),options=>generatePositions(positions,options)]){
  assert.equal(create({fog:null,speedCC:null}).code,create({}).code);
  for(const fog of [null,0,1,50,99,100])for(const speedCC of [null,150,200,350,500])for(const babyParkLaps of [null,1,9,10,99])for(const maximumBananas of [false,true]){
    const base=create({babyParkLaps,maximumBananas}),result=create({fog,speedCC,babyParkLaps,maximumBananas}),extra=raceOptionCodes(fog,speedCC);
    assert.equal(result.code,base.code+(extra.length?'\n'+extra.join('\n'):''));
    const lines=result.code.split('\n');assert.equal(lines.length,result.lines);
    assert.equal(decode(lines).size,lines.length,'Item, lap, banana, fog and speed writes must be disjoint');
  }
  assert.throws(()=>create({fog:101}));assert.throws(()=>create({speedCC:149}));
}
if(process.argv[2])fs.writeFileSync(process.argv[2],JSON.stringify(fixtures));
console.log(JSON.stringify({status:'passed',fogValues:101,speedValues:351,combinedConfigurations:600}));
