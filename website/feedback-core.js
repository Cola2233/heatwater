/* Compare actual analyses. The feedback never changes source data or model rules. */
(function(root){
 'use strict';
 function compare(data,before,after,kind){
  if(!['weight','threshold'].includes(kind))throw new Error('Unknown feedback kind');
  if(before.zones.length!==after.zones.length)throw new Error('Feedback grid mismatch');
  const delta=new Float32Array(after.zones.length),blocks=new Map();
  let affectedPixels=0,enteredPixels=0,exitedPixels=0;
  for(let i=0;i<delta.length;i++){
   if(!after.zones[i]||!before.zones[i])continue;
   const previous=kind==='threshold'?Number(before.zones[i]===4):before.compound[i];
   const current=kind==='threshold'?Number(after.zones[i]===4):after.compound[i];
   const change=current-previous;
   delta[i]=kind==='threshold'||Math.abs(change)>1e-6?change:0;
   if(delta[i])affectedPixels++;
   const wasHigh=kind==='threshold'?before.zones[i]===4:before.compound[i]>=Math.fround(before.threshold);
   const isHigh=kind==='threshold'?after.zones[i]===4:after.compound[i]>=Math.fround(after.threshold);
   if(isHigh&&!wasHigh)enteredPixels++;
   if(wasHigh&&!isHigh)exitedPixels++;
   const id=data.blockIds?.[i];
   if(id){
    if(!blocks.has(id))blocks.set(id,{sum:0,validPixels:0,changedPixels:0,delta:0});
    const block=blocks.get(id);block.sum+=delta[i];block.validPixels++;if(delta[i])block.changedPixels++;
   }
  }
  for(const block of blocks.values())block.delta=block.sum/block.validPixels;
  return {kind,delta,blocks,affectedPixels,affectedArea:affectedPixels*after.pixelArea,
   enteredPixels,exitedPixels,enteredArea:enteredPixels*after.pixelArea,exitedArea:exitedPixels*after.pixelArea};
 }
 const api={compare};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.HeatwaterFeedbackCore=api;
})(typeof window!=='undefined'?window:globalThis);
