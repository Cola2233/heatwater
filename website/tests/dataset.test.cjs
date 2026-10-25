const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const {analyze}=require("../core.js");
function load(name,id){
 const context={window:{}};
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,"../data",name),"utf8"),context);
 const raw=context.window.HEATWATER_DATASETS[id],data={...raw.meta};
 for(const role of ["heat","water","exposure","transition"]){
  const bytes=Uint8Array.from(Buffer.from(raw.arrays[role],"base64"));
  data[role]=role==="transition"?bytes:new Float32Array(bytes.buffer);
 }
 return analyze(data,{heatWeight:.55,threshold:.67});
}
test("public demo reproduces its Python component summary",()=>{
 const r=load("demo.js","demo");
 assert.equal(r.validCount,1872);
 assert.deepEqual(r.counts,[803,433,432,204]);
 assert.equal(r.highScoreCount,438);
 assert.equal(r.highExposureCount,108);
});
test("local Changchun raster export reproduces its Python baseline",
 {skip:!fs.existsSync(path.join(__dirname,"../data/local.js"))},()=>{
 const r=load("local.js","changchun");
 assert.equal(r.validCount,436411);
 assert.deepEqual(r.counts,[195094,61258,121318,58741]);
 assert.equal(r.highScoreCount,133002);
 assert.equal(r.highExposureCount,77991);
});
