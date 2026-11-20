(function(){
"use strict";
const $=id=>document.getElementById(id);
const zoneColors=["#cbdcb9","#e39b78","#72abc5","#80579b"];
/* Actual-input chart overlays for the design directions. No simulated trends. */
let chartData=null,chartCache=null;
function svgEl(name,attrs){
 const el=document.createElementNS("http://www.w3.org/2000/svg",name);
 for(const[k,v]of Object.entries(attrs))el.setAttribute(k,v);
 return el;
}
function updatePanels(data,result,state){
 const style=getComputedStyle(document.body),ink=style.getPropertyValue("--muted").trim(),
 accent=style.getPropertyValue("--accent").trim(),line=style.getPropertyValue("--line").trim();
 if(chartData!==data){
  chartData=data;
  const bins=new Uint32Array(400),exposureBins=new Uint32Array(5);
  let n=0,sx=0,sy=0,sxx=0,syy=0,sxy=0;
  for(let i=0;i<data.heat.length;i++){
   if(!result.zones[i])continue;
   const h=data.heat[i],w=data.water[i],e=data.exposure[i];
   bins[Math.min(19,Math.floor(w*20))*20+Math.min(19,Math.floor(h*20))]++;
   exposureBins[Math.min(4,Math.floor(e*5))]++;
   n++;sx+=h;sy+=w;sxx+=h*h;syy+=w*w;sxy+=h*w;
  }
  const denominator=Math.sqrt((n*sxx-sx*sx)*(n*syy-sy*sy));
  chartCache={bins,exposureBins,r:denominator?(n*sxy-sx*sy)/denominator:NaN};
 }
 document.querySelectorAll(".period-label").forEach(el=>el.textContent=data.periods.join(" / "));
 document.querySelectorAll(".current-case").forEach(el=>el.textContent=data.title+(data.synthetic?"模拟":"本地"));
 if($("plot-r"))$("plot-r").textContent=Number.isFinite(chartCache.r)?"像元相关 r = "+chartCache.r.toFixed(2):"相关系数不可计算";
 const plot=$("bivariate");
 if(plot){
  plot.replaceChildren();
  plot.setAttribute("aria-label","真实有效像元的热与水归一化分数联合分布");
  const max=Math.max(...chartCache.bins),unit=8.5,x0=35,y0=15,H=170;
  chartCache.bins.forEach((n,i)=>{
   if(!n)return;
   plot.append(svgEl("rect",{x:x0+i%20*unit,y:y0+H-unit-Math.floor(i/20)*unit,width:unit-.5,height:unit-.5,fill:accent,opacity:.12+.88*Math.log1p(n)/Math.log1p(max)}));
  });
  plot.append(svgEl("path",{d:"M35 15V185H205",fill:"none",stroke:ink,"stroke-width":1}));
  const t=state.threshold;
  plot.append(svgEl("path",{d:"M"+(35+t*170)+" 15V185M35 "+(185-t*170)+"H205",fill:"none",stroke:ink,"stroke-dasharray":"3 4","stroke-width":1}));
  for(const[x,y,s]of [[32,203,"0"],[201,203,"1"],[14,22,"1"],[95,221,"热分数"],[1,105,"水"]]){
   const label=svgEl("text",{x,y,fill:ink,"font-size":16,"font-family":"Segoe UI,Microsoft YaHei,sans-serif"});label.textContent=s;plot.append(label);
  }
 }
 const exposure=$("exposure-bars");
 if(exposure){
  exposure.replaceChildren();
  const max=Math.max(...chartCache.exposureBins);
  chartCache.exposureBins.forEach((n,i)=>{
   const bin=document.createElement("div");bin.className="hist-bin";bin.style.setProperty("--height",Math.round(n/Math.max(max,1)*100)+"%");
   const value=document.createElement("b");value.textContent=(n/Math.max(result.validCount,1)*100).toFixed(1)+"%";
   const bar=document.createElement("i"),caption=document.createElement("small");caption.textContent=["0–0.2","0.2–0.4","0.4–0.6","0.6–0.8","0.8–1"][i];
   bin.append(value,bar,caption);exposure.append(bin);
  });
 }
 $("zone-rows").querySelectorAll(".zone-row").forEach((el,i)=>{
  el.style.setProperty("--share",result.counts[i]/Math.max(result.validCount,1)*100+"%");
  el.style.setProperty("--barcolor",zoneColors[i]);
 });
}

window.HeatwaterCharts={update:updatePanels};
})();
