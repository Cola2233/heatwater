/* Explicit map feedback, with actual previous-result comparison and accessible controls. */
(function(){
 'use strict';
 const $=id=>document.getElementById(id),area=n=>n.toFixed(2)+' km²';
 function create(callbacks){
  let snapshot=null,beforeView=false;
  function paintControls(){
   $('compare-map').disabled=!snapshot;$('clear-map-change').disabled=!snapshot;
   $('compare-map').textContent=beforeView?'返回当前地图':'对比上一步';
   $('compare-map').setAttribute('aria-pressed',String(beforeView));
   $('show-map-change').disabled=beforeView;
   $('map-change-legend').hidden=!snapshot||beforeView||!$('show-map-change').checked;
   if(!snapshot)return;
   const f=snapshot.change;
   $('map-feedback-title').textContent=beforeView?'正在查看上一步地图':
    f.kind==='weight'?'权重变化已映射到地图':'阈值变化已映射到地图';
   $('map-feedback-detail').textContent=beforeView?
    '上一步：热权重'+Math.round(snapshot.beforeSettings.heatWeight*100)+'%，阈值'+snapshot.beforeSettings.threshold.toFixed(2)+'。右侧数字仍是当前参数统计。':snapshot.message;
   $('map-change-positive').textContent=f.kind==='weight'?'橙：复合分数增加':'橙：新进入双高';
   $('map-change-negative').textContent=f.kind==='weight'?'青：复合分数减少':'青：退出双高';
   $('map-change-scale').textContent=f.kind==='weight'?'片区按均值差着色，像元按分数差着色':'片区按双高占比差着色，像元按判定变化着色';
  }
  function reset(message){
   snapshot=null;beforeView=false;paintControls();
   $('map-feedback-title').textContent='地图与参数联动';
   $('map-feedback-detail').textContent=message||'拖动滑块：权重看复合分数，阈值看双高判定。可取消跟随，保留原始图层作底图。';
   $('map-feedback').dataset.kind='idle';
  }
  function update(data,before,after,beforeSettings,settings,kind,switched){
   const change=window.HeatwaterFeedbackCore.compare(data,before,after,kind);
   const unit=data.blocks?.diagnostics.scale==='overview'?'片区':'街区';
   const affectedBlocks=[...change.blocks.values()].filter(b=>b.changedPixels>0).length;
   let message=kind==='weight'?
    '热权重 '+Math.round(beforeSettings.heatWeight*100)+'% → '+Math.round(settings.heatWeight*100)+'%；变化范围 '+area(change.affectedArea):
    '阈值 '+beforeSettings.threshold.toFixed(2)+' → '+settings.threshold.toFixed(2)+'；双高新增 '+area(change.enteredArea)+'，退出 '+area(change.exitedArea);
   if(data.blocks)message+='；影响 '+affectedBlocks+' 个'+unit;
   if(!change.affectedPixels)message+='。当前数据在该调整下没有可显示的空间变化。';
   else message+='。与上一步比较，未变化区域以淡色显示。';
   if(switched)message+='已跟随切换图层。';
   else if(!['compound','zones'].includes(settings.layer))message+='底图原始分数保持不变，叠加层表示复合或双高变化。';
   const overlay=document.createElement('canvas');overlay.width=data.width;overlay.height=data.height;
   const context=overlay.getContext('2d'),image=context.createImageData(data.width,data.height);
   change.delta.forEach((v,i)=>{
    if(!v)return;
    const intensity=Math.min(1,Math.abs(v)/(kind==='weight'?.1:1));
    const c=v>0?[239,133,72]:[67,191,203];
    image.data.set([...c,Math.round(95+160*Math.sqrt(intensity))],i*4);
   });context.putImageData(image,0,0);
   snapshot={before,change,overlay,beforeSettings:{...beforeSettings},settings:{...settings},message,
    beforeRows:data.blocks?window.HeatwaterBlockCore.analyze(data,before):null};
   beforeView=false;$('show-map-change').checked=true;$('map-feedback').dataset.kind=kind;paintControls();
   if(!matchMedia('(prefers-reduced-motion: reduce)').matches)$('map-feedback').animate([{boxShadow:'inset 3px 0 #f3bd86'},{boxShadow:'inset 3px 0 transparent'}],{duration:700});
  }
  function appearance(){
   return snapshot?{rows:beforeView?snapshot.beforeRows:null,
    changes:!beforeView&&$('show-map-change').checked?snapshot.change.blocks:null,
    kind:snapshot.change.kind,before:beforeView}:{};
  }
  function hoverText(block){
   if(beforeView)block=snapshot.beforeRows?.find(r=>r.id===block.id)||block;
   const suffix='复合 '+(block.compound_mean==null?'—':block.compound_mean.toFixed(2))+' / 双高 '+(block.both_share==null?'—':(block.both_share*100).toFixed(1)+'%');
   const change=snapshot?.change.blocks.get(block.id);
   if(!change||!$('show-map-change').checked||beforeView)return suffix;
   const value=snapshot.change.kind==='weight'?(change.delta>=0?'+':'')+change.delta.toFixed(3):
    (change.delta>=0?'+':'')+(change.delta*100).toFixed(1)+' 个百分点';
   return suffix+'；本次'+(snapshot.change.kind==='weight'?'复合均值差 ':'双高占比差 ')+value;
  }
  $('compare-map').onclick=()=>{if(!snapshot)return;beforeView=!beforeView;paintControls();callbacks.redraw();};
  $('clear-map-change').onclick=()=>{reset('已收起变化叠加，地图显示当前参数结果。');callbacks.redraw();};
  $('show-map-change').onchange=()=>{paintControls();callbacks.redraw();};
  $('follow-map-parameters').onchange=()=>{
   if(!snapshot)$('map-feedback-detail').textContent=$('follow-map-parameters').checked?
    '调参时自动跟随：权重切至复合分数，阈值切至治理分区。':'已保留当前图层；调参后仍会叠加真实变化，底图原始分数不改写。';
  };
  reset();
  return {reset,update,appearance,hoverText,get before(){return snapshot?.before;},
   get beforeSettings(){return snapshot?.beforeSettings;},get overlay(){return snapshot?.overlay;},
   get active(){return Boolean(snapshot&&!beforeView&&$('show-map-change').checked);},get comparing(){return beforeView;},
   get kind(){return snapshot?.change.kind;},get following(){return $('follow-map-parameters').checked;}};
 }
 window.HeatwaterMapFeedback={create};
})();
