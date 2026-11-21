const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
vm.runInThisContext(fs.readFileSync(path.join(__dirname, '../index.html'), 'utf8').match(/<script>\s*([\s\S]*?)<\/script>/)[1]);
const {ITEMS, generate, generatePositions} = MKDDMixer;
const weights = ITEMS.map(i => i.weight || 0);
const positions = Array(8).fill(weights);
const normalOdds = Array(8).fill(null);
const floats = (code, address) => Buffer.from(code.match(new RegExp('^' + address + ' ([0-9A-F]{8})$', 'm'))[1], 'hex').readFloatBE();

for (const create of [options => generate(weights, options), options => generatePositions(positions, options)]) {
  const stock = create({}).code;
  assert.equal(create({respawnMask: 0, cameraBack: 100, driftIndicator: true}).code, stock);
  for (const mask of [-1, 256, null, false, 1.2, '1']) assert.throws(() => create({respawnMask: mask}));
  for (const offset of [-1, 201, 1.5, '0', null]) assert.throws(() => create({cameraBack: offset}));
  for (const height of [-1, 161, 0.5, '90', null]) assert.throws(() => create({cameraHeight: height}));
  for (let height = 0; height <= 160; height++) {
    assert.equal(floats(create({firstPerson: true, cameraHeight: height}).code, '040052D8'), height);
  }
  for (const tilt of [-1, 31, 0.5, '10', null]) assert.throws(() => create({cameraTilt: tilt}));
  for (let tilt = 1; tilt <= 30; tilt++) {
    assert.equal(floats(create({firstPerson: true, cameraTilt: tilt}).code, '04004C68'), Math.fround(-1000*Math.tan(tilt*Math.PI/180)));
  }
  assert.throws(() => create({driftIndicator: 1}));
  for (let back = 0; back <= 200; back++) {
    const {code} = create({firstPerson: true, cameraBack: back});
    assert.equal(floats(code, '040052DC'), 120 - back);
    assert.match(code, /^04145DC8 /m);
  }
  assert.doesNotMatch(create({firstPerson: true, driftIndicator: false}).code, /^04145DC8 /m);
  for (let mask = 1; mask <= 255; mask++) {
    const {code, lines} = create({respawnMask: mask, firstPerson: true, cameraTilt: 12, fog: 100,
      maximumBananas: true, babyParkLaps: 99, skipIntro: true, kartSize: 2, scalePhysics: true, speedCC: 999});
    assert.match(code, new RegExp('^040042DC ' + mask.toString(16).padStart(8, '0').toUpperCase() + '$', 'm'));
    assert.equal(new Set(code.split('\n').map(line => line.slice(0,8))).size, lines);
  }
}
const rescue = generatePositions(normalOdds, {respawnMask: 0xa5});
assert(!rescue.code.includes('0420CBC8') && rescue.bytes === 0);
assert.throws(() => generatePositions(normalOdds, {}));
assert.deepEqual(rescue.distributions, Array(8).fill([]));
const camera = generate(weights, {firstPerson: true}).code;
const hud = camera.slice(generate(weights, {firstPerson: true, driftIndicator: false}).code.length + 1);
if (process.argv[2]) fs.writeFileSync(process.argv[2], JSON.stringify({rescue: rescue.code, hud,
  live: generate(weights, {firstPerson:true, cameraBack:90, respawnMask:255, skipIntro:true}).code}));
console.log('All 256 rank masks, 201 setbacks, 161 heights, 31 angles, HUD toggles, native item odds and combined patch addresses passed.');
