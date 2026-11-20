const test=require('node:test');
const assert=require('node:assert/strict');
const {analyze:pixelAnalyze}=require('../core.js');
const {analyze}=require('../blocks-core.js');
const data={width:3,height:2,resolution:30,heat:Float32Array.from([.8,.2,.9,.9,-9999,.1]),
 water:Float32Array.from([.8,.9,.2,.9,-9999,.2]),exposure:Float32Array.from([1,0,.7,.5,-9999,0]),
 transition:Uint8Array.from([2,1,2,1,0,1]),blockIds:Uint32Array.from([1,1,2,1,0,2]),
 blocks:{features:[{id:1,name:'街区 B0001',boundary_cut:true},{id:2,name:'街区 B0002',boundary_cut:false}]}};
test('block summaries conserve the common valid population and component counts',()=>{
 const result=pixelAnalyze(data,{heatWeight:.55,threshold:.67});
 const rows=analyze(data,result);
 assert.equal(rows.reduce((s,r)=>s+r.valid_pixels,0),result.validCount);
 assert.equal(rows.reduce((s,r)=>s+r.both_pixels,0),result.counts[3]);
 assert.equal(rows[0].both_share,2/3);
 assert.equal(rows[0].high_exposure_pixels,1);
 assert.equal(rows[1].expansion_share,.5);
 assert.equal(rows[0].low_support,true);
 const changed=analyze(data,pixelAnalyze(data,{heatWeight:.7,threshold:.67}));
 assert.equal(rows[0].both_pixels,changed[0].both_pixels);
 assert.notEqual(rows[0].compound_mean,changed[0].compound_mean);
});
test('unsupported units have null means instead of fake zero risks',()=>{
 const d={...data,blocks:{features:[...data.blocks.features,{id:3,name:'empty'}]}};
 const row=analyze(d,pixelAnalyze(d,{heatWeight:.55,threshold:.67}))[2];
 assert.equal(row.valid_pixels,0);assert.equal(row.compound_mean,null);
});
test('missing ownership is an error, not silently dropped area',()=>{
 assert.throws(()=>analyze({...data,blockIds:new Uint32Array(6)},pixelAnalyze(data,{heatWeight:.55,threshold:.67})),/unassigned/);
});
