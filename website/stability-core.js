/* Parameter sensitivity only: frequency is not an event probability. */
(function(root){
 'use strict';
 const rule={minPixels:9,minCoverage:.8,minShare:.2,exposureThreshold:.6};
 function supported(r){return r.valid_pixels>=rule.minPixels&&r.coverage>=rule.minCoverage;}
 function analyze(data,core,blocks,options={},progress=()=>{}){
  const weights=options.weights??[.30,.35,.40,.45,.50,.55,.60,.65,.70];
  const thresholds=options.thresholds??[.50,.55,.60,.65,.67,.70,.75,.80];
  if(!weights.length||!thresholds.length||weights.some(w=>!Number.isFinite(w)||w<0||w>1)||thresholds.some(t=>!Number.isFinite(t)||t<=0||t>=1))throw new Error('Invalid sweep parameters');
  const settings=weights.flatMap(heatWeight=>thresholds.map(threshold=>({heatWeight,threshold}))),out=new Map();
  settings.forEach((s,index)=>{
   // Reuse the scientific implementation, including Float32 threshold semantics.
   const rows=blocks.analyze(data,core.analyze(data,s));
   const sorted=rows.filter(supported).sort((a,b)=>b.high_exposure_share-a.high_exposure_share);
   const ranks=new Map();let rank=0,previous=null;
   sorted.forEach((r,i)=>{if(r.high_exposure_share!==previous)rank=i+1;ranks.set(r.id,rank);previous=r.high_exposure_share;});
   for(const r of rows){
    if(!out.has(r.id))out.set(r.id,{id:r.id,eligible:supported(r),selected_count:0,frequency:null,rank_min:null,rank_max:null,cases:[]});
    const target=out.get(r.id),selected=supported(r)&&r.high_exposure_share>=rule.minShare,position=ranks.get(r.id)??null;
    target.cases.push({share:r.high_exposure_share,rank:position,selected});
    if(selected)target.selected_count++;
    if(position!==null){target.rank_min=target.rank_min===null?position:Math.min(position,target.rank_min);target.rank_max=target.rank_max===null?position:Math.max(position,target.rank_max);}
   }
   progress(index+1,settings.length);
  });
  for(const r of out.values())if(r.eligible)r.frequency=r.selected_count/settings.length;
  return {rule:{...rule},settings,rows:[...out.values()]};
 }
 const api={analyze,supported,rule};
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.HeatwaterStability=api;
})(typeof window!=='undefined'?window:globalThis);
