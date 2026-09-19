const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
vm.runInThisContext(fs.readFileSync(path.join(__dirname,'../index.html'),'utf8').match(/<script>\s*([\s\S]*?)<\/script>/)[1]);
const {ITEMS,generate,generatePositions}=MKDDMixer;
const weights=ITEMS.map(i=>i.weight||0),positions=Array.from({length:8},()=>weights);
const fixtures=[];
let combinations=0;
for(const create of [o=>generate(weights,o),o=>generatePositions(positions,o)]){
  assert.equal(create({firstPerson:false}).code,create({}).code);
  for(const firstPerson of [null,1,'true',{},[]])assert.throws(()=>create({firstPerson}),/First-person/);
  for(const kartSize of [null,0,.1,1,10,100])for(const scalePhysics of (kartSize===null?[false]:[false,true]))
  for(const fog of [null,0,100])for(const speedCC of [null,150,10000])for(const babyParkLaps of [null,1,99])
  for(const maximumBananas of [false,true])for(const skipIntro of [false,true]){
    const options={kartSize,scalePhysics,fog,speedCC,babyParkLaps,maximumBananas,skipIntro};
    const base=create(options).code,result=create({...options,firstPerson:true});
    assert(result.code.startsWith(base+'\n'));
    const extra=result.code.slice(base.length+1).split('\n');
    assert.equal(extra.length,50);
    assert.equal(extra.at(-1),'042B7484 4BD4DB1C');
    const addresses=result.code.split('\n').map(l=>l.split(' ')[0]);
    assert.equal(new Set(addresses).size,addresses.length,'All options must use separate addresses');
    const scale=Buffer.from(extra.find(l=>l.startsWith('040050B0 ')).split(' ')[1],'hex').readFloatBE();
    assert.equal(scale,Math.fround(Math.max(.01,kartSize??1)));
    assert.equal(create({...options,firstPerson:false}).code,base);
    combinations++;
  }
}
for(const kartSize of [null,0,.1,1,10,100]){
  const base=generate(weights,{kartSize}).code;
  fixtures.push({kartSize,code:generate(weights,{kartSize,firstPerson:true}).code.slice(base.length+1)});
}
if(process.argv[2])fs.writeFileSync(process.argv[2],JSON.stringify(fixtures));
console.log(`First person: ${combinations} option combinations, off-default parity, invalid input and address isolation passed.`);
