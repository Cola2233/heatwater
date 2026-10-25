const test = require("node:test");
const assert = require("node:assert/strict");
const core = require("../core.js");

const data = {
  width: 2, height: 2, resolution: 30,
  heat: new Float32Array([0.2, 0.8, 0.8, NaN]),
  water: new Float32Array([0.8, 0.2, 0.8, NaN]),
  exposure: new Float32Array([0.6, 0, 1, NaN]),
  transition: new Uint8Array([2,1,2,0])
};

test("zones, exposure, area and invalid cells follow the Python contracts", () => {
  const r=core.analyze(data,{heatWeight:0.55,threshold:0.67});
  assert.deepEqual(Array.from(r.zones),[3,2,4,0]);
  assert.equal(r.validCount,3);
  assert.ok(Math.abs(r.area-0.0027)<1e-12);
  assert.equal(r.highScoreCount,1);
  assert.equal(r.highExposureCount,1);
  assert.deepEqual(Array.from(r.expansion),[2,0,1,0]);
});

test("changing weights changes scores but never component zones",()=>{
  const a=core.analyze(data,{heatWeight:0.3,threshold:0.67});
  const b=core.analyze(data,{heatWeight:0.7,threshold:0.67});
  assert.deepEqual(a.zones,b.zones);
  assert.notEqual(a.compound[0],b.compound[0]);
});

test("empty or invalid settings are rejected",()=>{
  assert.throws(()=>core.analyze(data,{heatWeight:NaN,threshold:0.67}));
  assert.throws(()=>core.analyze(data,{heatWeight:0.55,threshold:1}));
  assert.throws(()=>core.analyze({...data,width:9},{heatWeight:0.55,threshold:0.67}));
});

test("exported aggregate shares sum to one hundred",()=>{
  const r=core.analyze(data,{heatWeight:0.55,threshold:0.67});
  assert.equal(r.counts.reduce((a,b)=>a+b,0),3);
  assert.equal(Math.round(r.counts.reduce((a,b)=>a+b/r.validCount*100,0)),100);
});
