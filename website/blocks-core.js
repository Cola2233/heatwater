/* Same raster-center denominators as scripts/blocks.py; no browser dependencies. */
(function(root){
 'use strict';
 function analyze(data,result){
  if(!data.blocks||!data.blockIds)return [];
  if(data.blockIds.length!==result.zones.length)throw new Error('Block grid mismatch');
  const rows=data.blocks.features.map(f=>({...f,total_pixels:0,valid_pixels:0,heat_mean:0,water_mean:0,
   compound_mean:0,exposure_mean:0,both_pixels:0,high_exposure_pixels:0,expansion_share:0}));
  const map=new Map(rows.map(r=>[r.id,r]));
  for(let i=0;i<data.blockIds.length;i++){
   const r=map.get(data.blockIds[i]);
   if(!r){if(result.zones[i])throw new Error('Valid pixel unassigned to block');continue;}
   r.total_pixels++;
   if(!result.zones[i])continue;
   r.valid_pixels++;r.heat_mean+=data.heat[i];r.water_mean+=data.water[i];
   r.compound_mean+=result.compound[i];r.exposure_mean+=data.exposure[i];
   if(result.zones[i]===4)r.both_pixels++;
   // Derive the high-exposure count from the same threshold rule as core.js.
   if(result.compound[i]>=Math.fround(result.threshold)&&data.exposure[i]>=Math.fround(.6))r.high_exposure_pixels++;
   if(data.transition[i]===2)r.expansion_share++;
  }
  for(const r of rows){
   const n=r.valid_pixels;
   for(const field of ['heat_mean','water_mean','compound_mean','exposure_mean','expansion_share'])r[field]=n?r[field]/n:null;
   r.both_share=n?r.both_pixels/n:null;r.high_exposure_share=n?r.high_exposure_pixels/n:null;
   r.coverage=r.total_pixels?n/r.total_pixels:0;r.valid_area_km2=n*result.pixelArea;
   r.low_support=n<9;r.partial_coverage=r.coverage<.8;
  }
  return rows;
 }
 const api={analyze};
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.HeatwaterBlockCore=api;
})(typeof window!=='undefined'?window:globalThis);
