/* Road-derived block interaction and rendering, independent of raster controls. */
(function(){
 'use strict';
 const fields={zones:'both_share',heat:'heat_mean',water:'water_mean',compound:'compound_mean',exposure:'exposure_mean',expansion:'expansion_share'};
 const labels={both_share:'双高像元占比',heat_mean:'平均热分数',water_mean:'平均水分数',compound_mean:'平均复合分数',exposure_mean:'平均建筑暴露',expansion_share:'新增硬化占比',high_exposure_share:'高分高暴露占比',valid_area_km2:'有效分析面积'};
 const palettes={heat:[[255,242,194],[201,73,51]],water:[[227,241,244],[43,101,151]],
  compound:[[228,237,214],[103,67,135]],exposure:[[238,240,231],[49,115,91]],
  zones:[[228,237,214],[103,67,135]],expansion:[[238,240,231],[49,115,91]]};
 const $=id=>document.getElementById(id);
 const format=(key,n)=>n==null?'—':key.endsWith('_share')?(n*100).toFixed(1)+'%':key==='valid_area_km2'?n.toFixed(3)+' km²':n.toFixed(2);
 function create(callbacks){
  let current=null,rows=[],byId=new Map(),paths=new Map(),selected=null,hovered=null,page=0,settings=null,unit='街区';
  const pageSize=20;
  function filtered(){
   const text=$('block-search').value.trim().toLowerCase(),quality=$('block-quality').value,sort=$('block-sort').value;
   return rows.filter(r=>r.valid_pixels>0&&(!text||r.name.toLowerCase().includes(text))&&
     (quality!=='supported'||(!r.low_support&&!r.partial_coverage)))
    .sort((a,b)=>(b[sort]??-1)-(a[sort]??-1)||a.id-b.id);
  }
  function showDetail(){
   const r=byId.get(selected),target=$('block-detail');target.replaceChildren();
   const heading=document.createElement('h3');heading.textContent=r?r.name:'选择一个'+unit;target.append(heading);
   if(!r){const p=document.createElement('p');p.textContent='点击地图上的色块，或点击右侧列表。分区以道路推导编号，不是官方行政街道。';target.append(p);return;}
   const quality=document.createElement('p');quality.className='block-quality-note';
   quality.textContent=[r.low_support?'有效像元不足9个':null,r.partial_coverage?'有效覆盖不足80%':null,r.boundary_cut?'被分析范围边界截断':null].filter(Boolean).join('；')||'有效像元与覆盖达到当前展示筛选条件';
   target.append(quality);
   const dl=document.createElement('dl');
   for(const [label,value]of [['有效分析面积',format('valid_area_km2',r.valid_area_km2)],['有效像元',r.valid_pixels+' 个'],
    ['有效覆盖',(r.coverage*100).toFixed(1)+'%'],['双高像元占比',format('both_share',r.both_share)],
    ['平均热分数',format('heat_mean',r.heat_mean)],['平均水分数',format('water_mean',r.water_mean)],
    ['平均复合分数',format('compound_mean',r.compound_mean)],['平均建筑暴露',format('exposure_mean',r.exposure_mean)],
    ['高分高暴露占比',format('high_exposure_share',r.high_exposure_share)],['新增硬化占比',format('expansion_share',r.expansion_share)]]){
     const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=value;dl.append(dt,dd);
   }
   target.append(dl);
   const button=document.createElement('button');button.textContent='定位到此街区';button.onclick=()=>callbacks.locate(r);target.append(button);
  }
  function select(id,locate=false){
   selected=byId.has(id)?id:null;showDetail();renderList();callbacks.redraw();
   if(locate&&selected)callbacks.locate(byId.get(selected));
  }
  function renderList(){
   if(!current||!current.blocks)return;
   const list=filtered(),sort=$('block-sort').value,maxPage=Math.max(0,Math.ceil(list.length/pageSize)-1);
   page=Math.min(page,maxPage);
   $('block-result-count').textContent=list.length+' 个符合筛选 / '+rows.filter(r=>r.valid_pixels>0).length+' 个有数据'+unit;
   $('block-page').textContent=(page+1)+' / '+(maxPage+1);$('block-prev').disabled=page===0;$('block-next').disabled=page===maxPage;
   const container=$('block-list');container.replaceChildren();
   list.slice(page*pageSize,(page+1)*pageSize).forEach((r,i)=>{
    const button=document.createElement('button');button.className='block-row';button.dataset.blockId=r.id;
    button.setAttribute('aria-pressed',String(r.id===selected));
    const name=document.createElement('span'),value=document.createElement('b'),note=document.createElement('small');
    name.textContent=(page*pageSize+i+1)+'. '+r.name;value.textContent=format(sort,r[sort]);
    note.textContent=[r.valid_pixels+' 个有效像元',r.low_support?'像元不足':null,r.partial_coverage?'覆盖不足':null,r.boundary_cut?'边缘截断':null].filter(Boolean).join(' / ');
    button.append(name,value,note);button.onclick=()=>{callbacks.mode('blocks');select(r.id,true);};container.append(button);
   });
   if(!list.length){const p=document.createElement('p');p.className='block-empty';p.textContent='没有符合条件的街区，请调整搜索或覆盖筛选。';container.append(p);}
  }
  function update(data,result,state){
   const changed=current!==data;current=data;settings={...state};
   const available=Boolean(data.blocks&&data.blockIds);
   $('view-blocks').disabled=!available;$('blocks-region').hidden=!available;
   if(!available){rows=[];byId.clear();paths.clear();selected=null;return;}
   unit=data.blocks.diagnostics.scale==='overview'?'片区':'街区';
   $('download-blocks').textContent='导出筛选'+unit+'CSV';
   $('block-search').placeholder=unit==='片区'?'例如 P0123':'例如 B0123';
   const mergeArea=data.blocks.diagnostics.min_merge_area_m2;
   $('block-scale-method').textContent=(unit==='片区'?'片区概览不使用住宅路、未分类道路及生活道路单独切分，':'细街区保留住宅等道路线网，')+
    '按公共边合并小单元，目标合并面积'+(mergeArea/1e6).toFixed(4)+'平方公里。';
   if(changed){
    selected=null;hovered=null;page=0;$('block-search').value='';paths.clear();
    for(const f of data.blocks.features){
     const path=new Path2D();
     for(const polygon of f.polygons)for(const ring of polygon){ring.forEach(([x,y],i)=>i?path.lineTo(x,y):path.moveTo(x,y));path.closePath();}
     paths.set(f.id,path);
    }
   }
   rows=window.HeatwaterBlockCore.analyze(data,result);byId=new Map(rows.map(r=>[r.id,r]));
   $('block-overview').textContent=rows.filter(r=>r.valid_pixels>0).length+' 个有数据'+unit+' / '+rows.length+' 个推导单元';
   $('block-source-note').textContent=data.synthetic?'道路、街区和栅格均为模拟，用于演示分析流程。':
    (unit==='片区'?'概览采用较高层级道路线网，不使用住宅路单独细分；':'细街区保留住宅等道路线网；')+'排除步道、服务路、匝道及明确标记的桥隧。编号不代表官方名称。';
   showDetail();renderList();
  }
  function draw(ctx,transform,layer,appearance={}){
   const palette=palettes[layer],key=fields[layer],{x,y,scale}=transform;
   ctx.save();ctx.translate(x,y);ctx.scale(scale,scale);ctx.lineWidth=.55/scale;
   for(const r of appearance.rows||rows){
    const value=r[key];if(value==null)continue;
    const t=Math.max(0,Math.min(1,value)),color=palette[0].map((v,i)=>Math.round(v+(palette[1][i]-v)*t));
    const change=appearance.changes?.get(r.id),delta=change?.delta||0;
    if(appearance.changes){
     ctx.fillStyle=Math.abs(delta)>1e-7?(delta>0?'#ef8548':'#43bfcb'):'#899690';
     ctx.globalAlpha=Math.abs(delta)>1e-7?.35+.6*Math.sqrt(Math.min(1,Math.abs(delta)/(appearance.kind==='weight'?.1:1))):.2;
    }else{ctx.fillStyle='rgb('+color.join(',')+')';ctx.globalAlpha=(r.low_support||r.partial_coverage)? .55 : .95;}
    ctx.fill(paths.get(r.id),'evenodd');ctx.globalAlpha=.65;ctx.strokeStyle='#283c38';ctx.stroke(paths.get(r.id));
   }
   ctx.globalAlpha=1;
   if(hovered&&paths.has(hovered)){ctx.strokeStyle='#f7f3df';ctx.lineWidth=2/scale;ctx.stroke(paths.get(hovered));}
   if(selected&&paths.has(selected)){ctx.strokeStyle='#ffd8a1';ctx.lineWidth=3/scale;ctx.stroke(paths.get(selected));}
   ctx.restore();
  }
  function hit(col,row){
   if(!current||!current.blockIds||col<0||row<0||col>=current.width||row>=current.height)return null;
   return byId.get(current.blockIds[Math.floor(row)*current.width+Math.floor(col)])||null;
  }
  function description(layer){
   return [labels[fields[layer]],'按当前分区内共同有效像元计算'+(fields[layer].endsWith('_share')?'比例':'均值')+'。色块不表示内部处处同值；不足9个有效像元或覆盖不足80%的单元以淡色显示。'];
  }
  function csv(){
   const columns=['id','name','block_scale','valid_pixels','total_pixels','valid_area_km2','geometry_area_km2','coverage','heat_mean','water_mean','compound_mean','exposure_mean',
    'both_pixels','both_share','high_exposure_pixels','high_exposure_share','expansion_share','low_support','partial_coverage','boundary_cut','heat_weight','threshold','synthetic'];
   const values=filtered().map(r=>({...r,block_scale:settings.blockScale,heat_weight:settings.heatWeight,threshold:settings.threshold,synthetic:current.synthetic}));
   const quote=x=>'"'+String(x??'').replaceAll('"','""')+'"';
   callbacks.download(current.id+'-'+settings.blockScale+'-block-summary.csv','\uFEFF'+[columns,...values.map(r=>columns.map(k=>r[k]))].map(r=>r.map(quote).join(',')).join('\r\n'),'text/csv;charset=utf-8');
  }
  $('block-search').addEventListener('input',()=>{page=0;renderList();});
  for(const id of ['block-quality','block-sort'])$(id).addEventListener('change',()=>{page=0;renderList();});
  $('block-prev').onclick=()=>{page--;renderList();};$('block-next').onclick=()=>{page++;renderList();};
  $('download-blocks').onclick=csv;
  function hover(id){if(hovered===id)return;hovered=id;callbacks.redraw();}
  return {update,draw,hit,select,hover,description,get rows(){return rows;},get selected(){return selected;}};
 }
 window.HeatwaterBlocks={create};
})();
