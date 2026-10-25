/* Pure numerical logic shared by browser and dependency-free Node tests. */
(function(root){
  "use strict";
  function analyze(data,settings){
    const {heatWeight,threshold}=settings;
    if(!Number.isFinite(heatWeight)||heatWeight<0||heatWeight>1||
       !Number.isFinite(threshold)||threshold<=0||threshold>=1)
      throw new Error("Invalid parameters");
    const n=data.width*data.height;
    if(!Number.isInteger(n)||n<1||["heat","water","exposure","transition"].some(k=>data[k].length!==n))
      throw new Error("Raster dimensions do not match");
    const zones=new Uint8Array(n),expansion=new Uint8Array(n),compound=new Float32Array(n);
    const counts=[0,0,0,0],pixelArea=data.resolution**2/1e6;
    let validCount=0,highScoreCount=0,highExposureCount=0;
    const hw=Math.fround(heatWeight),ww=Math.fround(1-heatWeight),t=Math.fround(threshold);
    for(let i=0;i<n;i++){
      const h=data.heat[i],w=data.water[i],e=data.exposure[i];
      if(!Number.isFinite(h)||!Number.isFinite(w)||!Number.isFinite(e)||
         h<0||h>1||w<0||w>1||e<0||e>1){compound[i]=NaN;continue;}
      const z=1+Number(h>=t)+2*Number(w>=t);
      zones[i]=z;counts[z-1]++;validCount++;
      const c=Math.fround(Math.fround(hw*h)+Math.fround(ww*w));
      compound[i]=c;
      if(c>=t){highScoreCount++;if(e>=Math.fround(.6))highExposureCount++;}
      if(data.transition[i]===2)expansion[i]=z===4?1:(z===1?3:2);
    }
    return {zones,expansion,compound,counts,validCount,area:validCount*pixelArea,
            highScoreCount,highExposureCount,pixelArea};
  }
  const api={analyze};
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  else root.HeatwaterCore=api;
})(typeof window!=="undefined"?window:globalThis);
