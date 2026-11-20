const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {analyze}=require('../core.js'),{analyze:blocks}=require('../blocks-core.js');
for(const [file,key,csv]of [['demo.js','demo',null],['local.js','changchun','../../artifacts/reproduced/derived/blocks/block_summary.csv']]){
 test(key+' block summaries conserve raster totals and match Python baseline',{skip:!fs.existsSync(path.join(__dirname,'../data',file))},()=>{
  const scope={window:{}};vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../data',file),'utf8'),scope);
  const raw=scope.window.HEATWATER_DATASETS[key];assert.ok(raw.blocks,'Expected precomputed block sample');
  const data={...raw.meta,blocks:raw.blocks};
  for(const name of ['heat','water','exposure','transition','block_ids']){
   const bytes=Uint8Array.from(Buffer.from(raw.arrays[name],'base64'));
   data[name==='block_ids'?'blockIds':name]=name==='transition'?bytes:name==='block_ids'?new Uint32Array(bytes.buffer):new Float32Array(bytes.buffer);
  }
  const result=analyze(data,{heatWeight:.55,threshold:.67}),rows=blocks(data,result);
  assert.equal(rows.reduce((s,r)=>s+r.valid_pixels,0),result.validCount);
  assert.equal(rows.reduce((s,r)=>s+r.both_pixels,0),result.counts[3]);
  assert.equal(rows.reduce((s,r)=>s+r.high_exposure_pixels,0),result.highExposureCount);
  assert.equal(rows.reduce((s,r)=>s+r.total_pixels,0),data.width*data.height);
  const csvPath=csv&&(raw.blocks.diagnostics.scale==='overview'?csv.replace('/blocks/','/blocks_overview/'):csv);
  if(csvPath&&fs.existsSync(path.join(__dirname,csvPath))){
   const lines=fs.readFileSync(path.join(__dirname,csvPath),'utf8').replace(/^\uFEFF/,'').trim().split(/\r?\n/),header=lines.shift().split(',');
   const expected=lines.map(line=>Object.fromEntries(line.split(',').map((v,i)=>[header[i],v])));
   assert.equal(rows.length,expected.length);
   rows.forEach((r,i)=>{
    for(const field of ['id','valid_pixels','total_pixels','both_pixels','high_exposure_pixels'])assert.equal(r[field],Number(expected[i][field]));
    for(const field of ['heat_mean','water_mean','compound_mean','exposure_mean','both_share','high_exposure_share','expansion_share']){
     if(r[field]==null)assert.equal(expected[i][field],'');else assert.ok(Math.abs(r[field]-Number(expected[i][field]))<1e-7,field+' '+r.id);
    }
   });
  }
  for(const variant of Object.values(raw.block_scales||{})){
   const bytes=Uint8Array.from(Buffer.from(variant.ids,'base64'));
   const other=blocks({...data,blocks:variant.blocks,blockIds:new Uint32Array(bytes.buffer)},result);
   assert.equal(other.reduce((s,r)=>s+r.valid_pixels,0),result.validCount);
   assert.equal(other.reduce((s,r)=>s+r.both_pixels,0),result.counts[3]);
   assert.equal(other.reduce((s,r)=>s+r.high_exposure_pixels,0),result.highExposureCount);
  }
 });
}
