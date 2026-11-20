const test=require('node:test'),assert=require('node:assert/strict');
const core=require('../core.js'),blocks=require('../blocks-core.js'),stability=require('../stability-core.js');
function fixture(){
 const n=40;
 return {width:n,height:1,resolution:30,heat:Float32Array.from({length:n},(_,i)=>i<12?.9:i<24?.4:i<36?.9:NaN),
 water:Float32Array.from({length:n},(_,i)=>i<12?.4:i<24?.9:i<36?.9:NaN),exposure:Float32Array.from({length:n},()=>.8),
 transition:new Uint8Array(n),blockIds:Uint32Array.from({length:n},(_,i)=>Math.floor(i/12)+1),
 blocks:{features:[1,2,3,4,5].map(id=>({id,name:'B'+id}))}};
}
test('72 default cases include the baseline and exclude unsupported units from ranks and frequencies',()=>{
 const d=fixture(),out=stability.analyze(d,core,blocks);
 assert.equal(out.settings.length,72);assert.ok(out.settings.some(s=>s.heatWeight===.55&&s.threshold===.67));
 assert.equal(out.rows.find(r=>r.id===3).frequency,1);
 for(const id of [4,5]){const r=out.rows.find(r=>r.id===id);assert.equal(r.frequency,null);assert.equal(r.rank_min,null);}
});
test('sweep shares, selections and tied ranks reproduce the authoritative pixel and block cores',()=>{
 const d=fixture(),out=stability.analyze(d,core,blocks);
 out.settings.forEach((s,j)=>{
  const direct=blocks.analyze(d,core.analyze(d,s)),eligible=direct.filter(stability.supported);
  for(const r of direct){const a=out.rows.find(x=>x.id===r.id),c=a.cases[j];
   assert.equal(c.share,r.high_exposure_share);
   assert.equal(c.selected,stability.supported(r)&&r.high_exposure_share>=.2);
   assert.equal(c.rank,stability.supported(r)?1+eligible.filter(x=>x.high_exposure_share>r.high_exposure_share).length:null);
  }
 });
 assert.deepEqual(Array.from(d.heat.slice(0,2)),[Math.fround(.9),Math.fround(.9)]);
});
test('coverage and exact cutoff boundaries do not silently admit low quality blocks',()=>{
 assert.equal(stability.supported({valid_pixels:9,coverage:.8}),true);
 assert.equal(stability.supported({valid_pixels:8,coverage:1}),false);
 assert.equal(stability.supported({valid_pixels:20,coverage:.79}),false);
 const d=fixture();d.exposure.fill(0);d.exposure.fill(.8,0,3);
 const out=stability.analyze(d,core,blocks,{weights:[.5],thresholds:[.5]});
 assert.equal(out.rows[0].frequency,1);assert.equal(out.rows[1].frequency,0);
 assert.throws(()=>stability.analyze(d,core,blocks,{weights:[],thresholds:[.5]}),/parameters/);
});
test('exactly 20 percent high-score high-exposure pixels qualifies, the remainder do not',()=>{
 const d={width:20,height:1,resolution:30,heat:new Float32Array(20).fill(.9),water:new Float32Array(20).fill(.9),
 exposure:new Float32Array(20),transition:new Uint8Array(20),blockIds:Uint32Array.from({length:20},(_,i)=>i<10?1:2),
 blocks:{features:[{id:1,name:'cutoff'},{id:2,name:'below'}]}};
 d.exposure[0]=d.exposure[1]=d.exposure[10]=.8;
 const out=stability.analyze(d,core,blocks,{weights:[.55],thresholds:[.67]});
 assert.equal(out.rows[0].cases[0].share,.2);assert.equal(out.rows[0].frequency,1);
 assert.equal(out.rows[1].frequency,0);
});
