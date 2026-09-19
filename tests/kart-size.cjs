const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
vm.runInThisContext(fs.readFileSync(path.join(__dirname,'../index.html'),'utf8').match(/<script>\s*([\s\S]*?)<\/script>/)[1]);
const {ITEMS,generate,generatePositions,raceOptionCodes}=MKDDMixer;
const weights=ITEMS.map(i=>i.weight||0),positions=[...Array(7).fill(null),weights];
const decode=lines=>new Map(lines.map(line=>line.split(' ').map(x=>parseInt(x,16))));
const float=word=>{const b=Buffer.alloc(4);b.writeUInt32BE(word);return b.readFloatBE();};
const fixtures=[];
for(let n=0;n<=1000;n++)for(const scalePhysics of [false,true]){
  const kartSize=n/10,lines=raceOptionCodes(null,null,kartSize,scalePhysics),writes=decode(lines);
  assert.equal(writes.size,lines.length);
  assert.equal(float(writes.get(0x040041d0)),Math.fround(kartSize));
  assert.equal(float(writes.get(0x040041d4)),Math.fround(scalePhysics?Math.max(.01,kartSize):1));
  assert.equal(writes.has(0x0429d6c0),scalePhysics);
  assert.equal(writes.has(0x04353a74),scalePhysics);
  if(scalePhysics){
    assert.equal(float(writes.get(0x04353a74)),Math.fround(75*Math.max(.01,kartSize)));
    assert.equal(float(writes.get(0x043635a0)),Math.fround(130*Math.max(.01,kartSize)));
  }
  fixtures.push({kartSize,scalePhysics,code:lines.join('\n')});
}
for(const value of [-1,100.01,NaN,Infinity,-Infinity,'1',true,{},[]])assert.throws(()=>raceOptionCodes(null,null,value),/Kart size/);
assert.throws(()=>raceOptionCodes(null,null,null,true),/Enable kart size/);
assert.throws(()=>raceOptionCodes(null,null,1,1),/Enable kart size/);
let combinations=0;
for(const create of [o=>generate(weights,o),o=>generatePositions(positions,o)]){
  assert.equal(create({kartSize:null,scalePhysics:false}).code,create({}).code);
  for(const kartSize of [0,.1,.5,1,2,10,100])for(const scalePhysics of [false,true])for(const fog of [null,0,100])for(const speedCC of [null,150,10000])for(const babyParkLaps of [null,1,99])for(const maximumBananas of [false,true])for(const skipIntro of [false,true]){
    const base=create({fog,speedCC,babyParkLaps,maximumBananas});
    const result=create({fog,speedCC,babyParkLaps,maximumBananas,kartSize,scalePhysics,skipIntro});
    assert.equal(result.code,base.code+'\n'+raceOptionCodes(null,null,kartSize,scalePhysics).join('\n')+(skipIntro?'\n041CFD50 60000000\n041CFE18 60000000\n041B0D58 38000003\n041B10AC 60000000\n0412DBEC 60000000':''));
    const lines=result.code.split('\n');assert.equal(lines.length,result.lines);
    assert.equal(decode(lines).size,lines.length,'All option writes must be disjoint');
    combinations++;
  }
}
if(process.argv[2])fs.writeFileSync(process.argv[2],JSON.stringify(fixtures));
console.log(JSON.stringify({status:'passed',sizeValues:1001,physicalModes:2,combinations}));
