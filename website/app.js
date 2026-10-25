/* Offline UI: no analytics, network map services, or build dependencies. */
(function(){
"use strict";
const $=id=>document.getElementById(id);
const datasets=window.HEATWATER_DATASETS||{};
const zoneNames=["低热低涝 · 生态协同","高温分量优先","水涝分量优先","热涝双高 · 综合核查"];
const zoneColors=["#cbdcb9","#e39b78","#72abc5","#80579b"];
const descriptions={
 zones:["热涝治理分区","分别判断热、水分量是否达到阈值。四类分区提供不同的空间核查视角；改变权重不会改变这一分区。"],
 heat:["持续热分数","两期夏季 LST 经 P5–P95 归一化后的均值。分数较高代表共同有效区内相对偏热，并非摄氏温度。"],
 water:["水涝代理分数","已有水涝空间代理对齐、归一化后的相对分数。用于研究筛查，不能据此预测积水深度或发生时间。"],
 compound:["加权复合分数","用当前热、水权重组合连续分数。分数达到当前阈值的像元计入“复合高分区域”。"],
 exposure:["建筑功能暴露","住宅、教育、医疗、公共服务建筑的功能存在代理。权重叠加后截断至 1，不代表人口数量。"],
 expansion:["新增不透水面","转换编码 2 与四类分区叠加。紫色为双高区，橙色为单项高值，绿色为未达到分量阈值；空白为未选中。"]
};
const state={layer:"zones",heatWeight:.55,threshold:.67,zoom:1,panX:0,panY:0};
let data,result,raster=document.createElement("canvas"),transform,frame=0;
const canvas=$("map"),ctx=canvas.getContext("2d");
function decode(encoded,type){
 const binary=atob(encoded),bytes=new Uint8Array(binary.length);
 for(let i=0;i<binary.length;i++)bytes[i]=binary.charCodeAt(i);
 return type==="u8"?bytes:new Float32Array(bytes.buffer);
}
function loadDataset(id){
 const raw=datasets[id];if(!raw)throw new Error("数据文件不存在");
 data={...raw.meta,heat:decode(raw.arrays.heat),water:decode(raw.arrays.water),
       exposure:decode(raw.arrays.exposure),transition:decode(raw.arrays.transition,"u8")};
 state.zoom=1;state.panX=state.panY=0;
 $("dataset-tag").textContent=data.synthetic?"模拟案例 · 非观测":"真实成果 · 仅本地";
 $("dataset-tag").classList.toggle("synthetic",data.synthetic);
 $("dataset-description").textContent=data.synthetic?"自动生成的模拟栅格与建筑；演示算法及交互。":"本地长春成果；未上传在线服务。";
 $("map-caption").textContent=data.title+" / "+descriptions[state.layer][0];
 $("map-extent").textContent=data.width+" × "+data.height+" px · EPSG:"+data.epsg;
 $("source-detail").textContent="当前案例："+data.title+"；"+
   (data.synthetic?"所有数值与建筑均为模拟。":"热环境窗口："+data.periods.join(" 与 ")+"。")+
   " 原始分析分辨率 "+data.resolution+" m。界面加载 Python 流程导出的热、水、建筑暴露与土地转换栅格，不执行重新投影。";
 compute();
}
const number=n=>n.toLocaleString("zh-CN",{minimumFractionDigits:2,maximumFractionDigits:2});
function compute(){
 result=window.HeatwaterCore.analyze(data,state);
 $("metric-area").textContent=number(result.area);
 $("metric-pixels").textContent=result.validCount.toLocaleString("zh-CN")+" 个共同有效像元";
 $("metric-both").textContent=number(result.counts[3]*result.pixelArea);
 $("metric-both-share").textContent="占有效区 "+(result.validCount?result.counts[3]/result.validCount*100:0).toFixed(2)+"%";
 $("metric-score").textContent=number(result.highScoreCount*result.pixelArea);
 $("metric-exposure").textContent=number(result.highExposureCount*result.pixelArea);
 $("weight-output").textContent=Math.round(state.heatWeight*100)+"%";
 $("threshold-output").textContent=state.threshold.toFixed(2);
 $("weight-heat").textContent=state.heatWeight.toFixed(2);
 $("weight-water").textContent=(1-state.heatWeight).toFixed(2);
 $("stacked-bar").replaceChildren();$("zone-rows").replaceChildren();
 for(let i=0;i<4;i++){
   const share=result.validCount?result.counts[i]/result.validCount*100:0;
   const bar=document.createElement("span");bar.style.width=share+"%";bar.style.background=zoneColors[i];$("stacked-bar").append(bar);
   const row=document.createElement("div");row.className="zone-row";
   const label=document.createElement("span"),dot=document.createElement("i");dot.style.background=zoneColors[i];
   label.append(dot,document.createTextNode(zoneNames[i]));
   const value=document.createElement("b");value.textContent=number(result.counts[i]*result.pixelArea)+" km²";
   const count=document.createElement("small");count.textContent=result.counts[i].toLocaleString("zh-CN")+" 个像元";
   const pct=document.createElement("em");pct.textContent=share.toFixed(2)+"%";
   row.append(label,value,count,pct);$("zone-rows").append(row);
 }
 $("stacked-bar").setAttribute("aria-label",zoneNames.map((n,i)=>n+" "+(result.validCount?result.counts[i]/result.validCount*100:0).toFixed(2)+"%").join("；"));
 $("insight-text").textContent="当前阈值 "+state.threshold.toFixed(2)+" 下，热涝分量双高区域为 "+
   number(result.counts[3]*result.pixelArea)+" km²。按复合分数与建筑暴露联合筛查，候选区域为 "+
   number(result.highExposureCount*result.pixelArea)+" km²。两种判定口径不同，不表示包含关系。"+
   (data.synthetic?" 这是模拟案例的交互结果。":"");
 rasterize();updateLegend();draw();
}
function continuous(v,low,high){
 const t=Math.max(0,Math.min(1,v));return low.map((x,i)=>Math.round(x+(high[i]-x)*t));
}
function colorAt(i){
 if(!result.zones[i])return null;
 const layer=state.layer;
 if(layer==="zones")return zoneColors[result.zones[i]-1];
 if(layer==="expansion")return result.expansion[i]?[null,"#80579b","#e39b78","#9fbc89"][result.expansion[i]]:null;
 if(layer==="heat")return continuous(data.heat[i],[255,242,194],[201,73,51]);
 if(layer==="water")return continuous(data.water[i],[227,241,244],[43,101,151]);
 if(layer==="compound")return continuous(result.compound[i],[228,237,214],[103,67,135]);
 return continuous(data.exposure[i],[238,240,231],[49,115,91]);
}
function hex(hex){return [1,3,5].map(p=>parseInt(hex.slice(p,p+2),16));}
function rasterize(){
 raster.width=data.width;raster.height=data.height;
 const rc=raster.getContext("2d"),image=rc.createImageData(data.width,data.height);
 for(let i=0;i<result.zones.length;i++){
   let c=colorAt(i);if(!c)continue;if(typeof c==="string")c=hex(c);
   image.data.set([c[0],c[1],c[2],255],i*4);
 }
 rc.putImageData(image,0,0);
}
function updateLegend(){
 $("legend").replaceChildren();
 if(state.layer==="zones"||state.layer==="expansion"){
   const names=state.layer==="zones"?["低热低涝","高温优先","水涝优先","热涝双高"]:["双高 · 优先核查","单项高值","未达高值"];
   const colors=state.layer==="zones"?zoneColors:["#80579b","#e39b78","#9fbc89"];
   names.forEach((name,i)=>{const el=document.createElement("span"),dot=document.createElement("i");dot.style.background=colors[i];el.append(dot,document.createTextNode(name));$("legend").append(el);});
 }else{
   const palettes={heat:["#fff2c2","#c94933"],water:["#e3f1f4","#2b6597"],compound:["#e4edd6","#674387"],exposure:["#eef0e7","#31735b"]};
   const colors=palettes[state.layer],span=document.createElement("span"),gradient=document.createElement("i");
   gradient.className="gradient";gradient.style.background="linear-gradient(90deg,"+colors.join(",")+")";
   span.append(document.createTextNode("低 0 "),gradient,document.createTextNode(" 1 高"));
   $("legend").append(span);
 }
 $("layer-title").textContent=descriptions[state.layer][0];$("layer-note").textContent=descriptions[state.layer][1];
 $("map-caption").textContent=data.title+" / "+descriptions[state.layer][0];
}
function draw(){
 if(!data)return;
 const rect=canvas.getBoundingClientRect(),dpr=window.devicePixelRatio||1,W=rect.width,H=rect.height;
 if(W<1||H<1)return;
 canvas.width=Math.round(W*dpr);canvas.height=Math.round(H*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);
 ctx.fillStyle="#eef1eb";ctx.fillRect(0,0,W,H);ctx.strokeStyle="#dde4d7";ctx.lineWidth=.5;
 for(let x=0;x<W;x+=36){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();}
 for(let y=0;y<H;y+=36){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}
 const scale=Math.min((W-70)/data.width,(H-75)/data.height)*state.zoom;
 const x=(W-data.width*scale)/2+state.panX,y=(H-data.height*scale)/2-5+state.panY;
 transform={x,y,scale,W,H};ctx.imageSmoothingEnabled=false;
 ctx.drawImage(raster,x,y,data.width*scale,data.height*scale);
 // This is a pixel-grid extent, not a cadastral or administrative boundary.
 ctx.strokeStyle="#9eb29e";ctx.lineWidth=.7;ctx.strokeRect(x,y,data.width*scale,data.height*scale);
 ctx.font="8px system-ui";ctx.fillStyle="#84977e";
 ctx.fillText("E "+Math.round(data.geotransform[0]).toLocaleString("en-US")+" m",Math.max(10,x),Math.max(12,y-8));
 const desired=data.resolution*90/scale,power=10**Math.floor(Math.log10(desired));
 const distance=[1,2,5,10].map(n=>n*power).find(n=>n>=desired)||power*10;
 const length=distance/data.resolution*scale,barX=W-25-length,barY=H-27;
 ctx.fillStyle="#fff";ctx.fillRect(barX-7,barY-19,length+14,30);
 ctx.fillStyle="#506d58";ctx.fillRect(barX,barY,length,2);
 ctx.font="9px system-ui";ctx.fillText(distance>=1000?(distance/1000)+" km":distance+" m",barX,barY-5);
 if(data.synthetic){ctx.fillStyle="#6d785f";ctx.font="8px system-ui";ctx.fillText("SYNTHETIC · 非观测",12,H-49);}
}
function scheduleCompute(){cancelAnimationFrame(frame);frame=requestAnimationFrame(compute);}
function zoom(factor){state.zoom=Math.max(.6,Math.min(8,state.zoom*factor));draw();}
function inspect(event){
 if(!transform)return;
 const rect=canvas.getBoundingClientRect(),col=Math.floor((event.clientX-rect.left-transform.x)/transform.scale),
 row=Math.floor((event.clientY-rect.top-transform.y)/transform.scale);
 const i=row*data.width+col;
 if(col<0||col>=data.width||row<0||row>=data.height||!result.zones[i]){
   $("pixel-inspector").textContent="范围外或无有效观测 · 拖动地图可平移";return;
 }
 $("pixel-inspector").textContent="像元 "+col+", "+row+"  ·  热 "+data.heat[i].toFixed(2)+"  /  水 "+
  data.water[i].toFixed(2)+"  /  暴露 "+data.exposure[i].toFixed(2)+"  ·  "+zoneNames[result.zones[i]-1];
}
function download(name,content,type){
 const url=URL.createObjectURL(new Blob([content],{type})),a=document.createElement("a");
 a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function exportCsv(){
 const rows=[["dataset","synthetic","heat_weight","water_weight","threshold","zone","pixel_count","area_km2","share_percent"]];
 result.counts.forEach((n,i)=>rows.push([data.title,data.synthetic,state.heatWeight,1-state.heatWeight,state.threshold,zoneNames[i],n,(n*result.pixelArea).toFixed(4),(n/result.validCount*100).toFixed(2)]));
 const escape=v=>'"'+String(v).replaceAll('"','""')+'"';
 download(data.id+"-zone-summary.csv","\uFEFF"+rows.map(r=>r.map(escape).join(",")).join("\r\n"),"text/csv;charset=utf-8");
}
function initialize(){
 if(!window.HeatwaterCore||!Object.keys(datasets).length)throw new Error("未找到网页数据，请先执行 export_web_data。");
 for(const[id,payload]of Object.entries(datasets)){const option=document.createElement("option");option.value=id;option.textContent=payload.meta.title+(payload.meta.synthetic?" · 模拟":" · 本地真实成果");$("dataset").append(option);}
 $("dataset").value=datasets.changchun?"changchun":"demo";loadDataset($("dataset").value);
 $("dataset").addEventListener("change",e=>loadDataset(e.target.value));
 document.querySelectorAll("[data-layer]").forEach(button=>button.addEventListener("click",()=>{
   state.layer=button.dataset.layer;
   document.querySelectorAll("[data-layer]").forEach(b=>{const selected=b===button;b.classList.toggle("selected",selected);b.setAttribute("aria-pressed",String(selected));});
   rasterize();updateLegend();draw();
 }));
 $("heat-weight").addEventListener("input",e=>{state.heatWeight=Number(e.target.value)/100;scheduleCompute();});
 $("threshold").addEventListener("input",e=>{state.threshold=Number(e.target.value)/100;scheduleCompute();});
 $("reset-parameters").addEventListener("click",()=>{state.heatWeight=.55;state.threshold=.67;$("heat-weight").value=55;$("threshold").value=67;compute();});
 $("zoom-in").onclick=()=>zoom(1.3);$("zoom-out").onclick=()=>zoom(1/1.3);
 $("zoom-reset").onclick=()=>{state.zoom=1;state.panX=state.panY=0;draw();};
 canvas.addEventListener("wheel",e=>{e.preventDefault();zoom(e.deltaY<0?1.12:1/1.12);},{passive:false});
 let drag=null;
 canvas.addEventListener("pointerdown",e=>{drag={x:e.clientX,y:e.clientY,px:state.panX,py:state.panY};canvas.setPointerCapture(e.pointerId);});
 canvas.addEventListener("pointermove",e=>{if(drag){state.panX=drag.px+e.clientX-drag.x;state.panY=drag.py+e.clientY-drag.y;draw();}inspect(e);});
 const endDrag=()=>{drag=null;};canvas.addEventListener("pointerup",endDrag);canvas.addEventListener("pointercancel",endDrag);
 canvas.addEventListener("keydown",e=>{
   if(["+","=","-","0","ArrowLeft","ArrowRight","ArrowUp","ArrowDown"].includes(e.key))e.preventDefault();
   if(e.key==="+"||e.key==="=")zoom(1.2);if(e.key==="-")zoom(1/1.2);
   if(e.key==="0")$("zoom-reset").click();
   if(e.key==="ArrowLeft")state.panX-=25;if(e.key==="ArrowRight")state.panX+=25;
   if(e.key==="ArrowUp")state.panY-=25;if(e.key==="ArrowDown")state.panY+=25;draw();
 });
 new ResizeObserver(draw).observe(canvas.parentElement);
 $("download-csv").onclick=exportCsv;
 $("download-settings").onclick=()=>download(data.id+"-exploration.json",JSON.stringify({dataset:data.id,synthetic:data.synthetic,exploration_only:true,parameters:{heat_weight:state.heatWeight,water_weight:1-state.heatWeight,zone_threshold:state.threshold,compound_threshold:state.threshold,exposure_threshold:.6},source_hashes:data.source_hashes},null,2),"application/json");
 $("download-map").onclick=()=>{
   const out=document.createElement("canvas");out.width=canvas.width;out.height=canvas.height+130;
   const c=out.getContext("2d");c.fillStyle="#f6f7f2";c.fillRect(0,0,out.width,out.height);c.drawImage(canvas,0,70);
   c.fillStyle="#173b38";c.font="18px sans-serif";c.fillText(data.title+" · "+descriptions[state.layer][0],20,27);
   c.font="12px sans-serif";c.fillText((data.synthetic?"模拟数据 · 非观测 | ":"本地真实成果 · 研究性空间筛查 | ")+"热权重 "+state.heatWeight.toFixed(2)+" / 阈值 "+state.threshold.toFixed(2),20,51);
   c.fillText("N ↑",out.width-48,27);
   const legendY=canvas.height+91;
   c.font="11px sans-serif";
   if(state.layer==="zones"||state.layer==="expansion"){
     const labels=state.layer==="zones"?["低热低涝","高温优先","水涝优先","热涝双高"]:["双高区","单项高值","未达高值"];
     const colors=state.layer==="zones"?zoneColors:["#80579b","#e39b78","#9fbc89"];
     labels.forEach((label,i)=>{c.fillStyle=colors[i];c.fillRect(20+i*110,legendY-9,9,9);c.fillStyle="#173b38";c.fillText(label,35+i*110,legendY);});
   }else{
     c.fillStyle="#173b38";c.fillText("相对分数：0 低 → 1 高；色阶与页面当前图层一致",20,legendY);
   }
   c.fillStyle="#74847c";c.fillText("研究性空间筛查 / 浏览器参数探索",20,legendY+22);
   out.toBlob(blob=>{if(blob)download(data.id+"-"+state.layer+".png",blob,"image/png");});
 };
}
try{initialize();}catch(error){$("error-message").hidden=false;$("error-message").textContent="页面加载失败："+error.message;console.error(error);}
})();
