const test=require('node:test'),assert=require('node:assert/strict');
const {analyze}=require('../core.js');
const {compare}=require('../feedback-core.js');
const data={width:4,height:1,resolution:30,heat:Float32Array.from([.9,.1,.5,-9999]),
 water:Float32Array.from([.1,.9,.5,-9999]),exposure:Float32Array.from([1,1,1,-9999]),transition:new Uint8Array(4),blockIds:Uint32Array.from([1,2,2,0])};
test('weight feedback shows opposite local score changes without altering raw water',()=>{
 const before=analyze(data,{heatWeight:.3,threshold:.6}),after=analyze(data,{heatWeight:.7,threshold:.6});
 const water=Array.from(data.water),f=compare(data,before,after,'weight');
 assert.equal(f.affectedPixels,2);assert.ok(f.delta[0]>0);assert.ok(f.delta[1]<0);assert.equal(f.delta[2],0);
 assert.equal(f.enteredPixels,1);assert.equal(f.exitedPixels,1);
 assert.ok(f.blocks.get(1).delta>0);assert.ok(f.blocks.get(2).delta<0);
 assert.deepEqual(Array.from(data.water),water);
});
test('threshold feedback marks actual double-high entries and exits, not fixed water colors',()=>{
 const d={...data,heat:Float32Array.from([.7,.9,.4,-9999]),water:Float32Array.from([.7,.8,.3,-9999])};
 const before=analyze(d,{heatWeight:.55,threshold:.67}),after=analyze(d,{heatWeight:.55,threshold:.75});
 const f=compare(d,before,after,'threshold');
 assert.equal(f.enteredPixels,0);assert.equal(f.exitedPixels,1);assert.equal(f.delta[0],-1);assert.equal(f.delta[1],0);
 assert.equal(f.blocks.get(1).delta,-1);assert.equal(f.affectedArea,.0009);
 const reverse=compare(d,after,before,'threshold');assert.equal(reverse.enteredPixels,1);assert.equal(reverse.exitedPixels,0);
});
test('identical results have zero feedback instead of manufactured change',()=>{
 const r=analyze(data,{heatWeight:.55,threshold:.67}),f=compare(data,r,r,'weight');
 assert.equal(f.affectedPixels,0);assert.equal(f.affectedArea,0);assert.ok([...f.blocks.values()].every(b=>b.delta===0));
});
