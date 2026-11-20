/* Research workflow; MapLibre remains the rendering engine. */
(function(root){
 'use strict';
 const $=id=>document.getElementById(id),supported=HeatwaterStability.supported,cache=new Map();
 let context,output=null,lookup=new Map(),worker=null,scale=null,error=null;
 const pct=x=>x==null?'—':(x*100).toFixed(1)+'%',num=x=>x==null?'—':x.toFixed(3);
 const candidate=r=>supported(r)&&r.high_exposure_share>=HeatwaterStability.rule.minShare;
 function node(tag,text,cls){const el=document.createElement(tag);el.textContent=text;if(cls)el.className=cls;return el;}
 function csv(name,columns,records){
  const quote=v=>'"'+String(v??'').replaceAll('"','""')+'"';
  const text='\uFEFF'+[columns,...records.map(r=>columns.map(k=>r[k]))].map(row=>row.map(quote).join(',')).join('\r\n');
  const url=URL.createObjectURL(new Blob([text],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }
 function quality(r){return [r.low_support?'少于9个有效像元':null,r.partial_coverage?'有效覆盖不足80%':null,r.boundary_cut?'范围边界截断':null].filter(Boolean).join('；')||'支持充分';}
 function matches(r){
  const search=$('shortlist-search').value.trim().toLowerCase(),filter=$('shortlist-filter').value,s=lookup.get(r.id);
  if(!r.valid_pixels||search&&!String(r.name+' '+r.id).toLowerCase().includes(search))return false;
  return filter==='all'||filter==='current'&&candidate(r)||filter==='stable'&&s?.frequency>=.8||filter==='sensitive'&&s?.frequency>0&&s.frequency<.8;
 }
 function filtered(){return context.rows().filter(matches).sort((a,b)=>(lookup.get(b.id)?.frequency??-1)-(lookup.get(a.id)?.frequency??-1)||b.high_exposure_share-a.high_exposure_share||a.id-b.id);}
 function exportRows(){
  const settings=context.settings(),records=filtered().map(r=>{
   const s=lookup.get(r.id);return {id:r.id,name:r.name,scale,heat_weight:settings.heatWeight,threshold:settings.threshold,
    current_selected:candidate(r),eligible:supported(r),valid_pixels:r.valid_pixels,coverage:r.coverage,boundary_cut:!!r.boundary_cut,
    heat_mean:r.heat_mean,water_mean:r.water_mean,compound_mean:r.compound_mean,both_share:r.both_share,exposure_mean:r.exposure_mean,
    high_exposure_share:r.high_exposure_share,selection_frequency:s?.frequency,selected_cases:s?.selected_count,scenario_count:output.settings.length,
    rank_min:s?.rank_min,rank_max:s?.rank_max,min_valid_pixels:9,min_coverage:.8,min_selected_share:.2,exposure_threshold:.6,
    sweep_weights:JSON.stringify([...new Set(output.settings.map(x=>x.heatWeight))]),sweep_thresholds:JSON.stringify([...new Set(output.settings.map(x=>x.threshold))]),
    frequency_meaning:'parameter_selection_frequency_not_event_probability',quality:quality(r)};
  });
  const columns=['id','name','scale','heat_weight','threshold','current_selected','eligible','valid_pixels','coverage','boundary_cut','heat_mean','water_mean','compound_mean','both_share','exposure_mean','high_exposure_share','selection_frequency','selected_cases','scenario_count','rank_min','rank_max','min_valid_pixels','min_coverage','min_selected_share','exposure_threshold','sweep_weights','sweep_thresholds','frequency_meaning','quality'];
  csv(context.data.id+'-'+scale+'-screening.csv',columns,records);
 }
 function renderList(){
  const rows=filtered(),body=$('shortlist-rows');body.replaceChildren();
  $('export-shortlist').disabled=!output||!rows.length;
  $('shortlist-count').textContent='匹配 '+rows.length+' 个片区 / 当前入选 '+context.rows().filter(candidate).length+' 个 / '+(output?'72组参数已完成':'稳定性计算中');
  for(const r of rows.slice(0,20)){
   const s=lookup.get(r.id),tr=document.createElement('tr'),td=document.createElement('td'),button=node('button',r.name);button.onclick=()=>context.focus(r.id);td.append(button);tr.append(td);
   for(const text of [supported(r)?candidate(r)?'入选':'未入选':'数据不足',pct(r.high_exposure_share),s?pct(s.frequency):'计算中',s?.rank_min==null?'—':s.rank_min+'–'+s.rank_max,quality(r)])tr.append(node('td',text));
   body.append(tr);
  }
  if(!rows.length){const td=node('td','没有匹配片区。可调整筛选条件或搜索词。');td.colSpan=6;const tr=document.createElement('tr');tr.append(td);body.append(tr);}
 }
 function renderDetail(){
  const panel=$('selection'),row=context.rows().find(r=>r.id===context.selected());panel.replaceChildren();
  panel.append(node('h3',row?row.name:'选择一个片区'));
  if(!row){panel.append(node('p','在地图或核查清单中点击片区，查看筛选依据、指标排名和72组参数明细。'));return;}
  if(context.comparing())panel.append(node('p','地图正在显示上一步；本卡片和清单始终解释当前参数。','notice'));
  panel.append(node('p',supported(row)?candidate(row)?'当前进入优先核查候选':'当前未进入优先核查候选':'数据支持不足，暂不参与候选筛选与排名','decision'));
  panel.append(node('p','高分高暴露像元占比 '+pct(row.high_exposure_share)+' / 入选门槛20%'));
  panel.append(node('p','有效面积 '+row.valid_area_km2.toFixed(3)+' km² / '+row.valid_pixels+' 像元 / 覆盖 '+pct(row.coverage)));
  panel.append(node('p','质量提示：'+quality(row)));
  const eligible=context.rows().filter(supported),all=context.rows(),total=all.reduce((a,r)=>a+r.valid_pixels,0);
  const table=document.createElement('table'),head=node('tr','');for(const t of ['指标','片区','全域均值','排名'])head.append(node('th',t));table.append(head);
  for(const [key,label,format]of [['heat_mean','热分数',num],['water_mean','水分数',num],['compound_mean','复合分数',num],['both_share','双高占比',pct],['exposure_mean','建筑暴露',num]]){
   const mean=total?all.reduce((a,r)=>a+(r[key]??0)*r.valid_pixels,0)/total:null;
   const rank=supported(row)?1+eligible.filter(r=>r[key]>row[key]).length:null,tr=document.createElement('tr');
   for(const t of [label,format(row[key]),format(mean),rank==null?'—':rank+'/'+eligible.length])tr.append(node('td',t));table.append(tr);
  }
  panel.append(table,node('p','全域均值按有效像元加权；排名在支持充分的片区中按指标降序，并列同名次。指标对比描述空间差异，不作因果解释。','scope'));
  const s=lookup.get(row.id);
  if(!s){panel.append(node('p',error?'稳定性计算失败：'+error:'正在后台计算参数稳定性…'));return;}
  panel.append(node('h4','入选频率 '+pct(s.frequency)),node('p',s.eligible?s.selected_count+'/'+output.settings.length+' 组入选 / 排名范围 '+s.rank_min+'–'+s.rank_max:'数据支持不足，入选频率与排名不计算。'));
  if(s.eligible)panel.append(node('p',s.frequency>=.8?'在至少80%的所测试参数组合下入选，建议优先核查。':s.frequency>0?'入选随参数改变，应结合具体参数与现场资料复核。':'在所测试参数组合下均未入选；这不代表没有风险。'));
  const details=document.createElement('details');details.append(node('summary','查看72组参数依据'));
  const scroll=node('div','','scenario-scroll'),cases=document.createElement('table'),h=document.createElement('tr');for(const t of ['热权重','阈值','高分高暴露','排名','入选'])h.append(node('th',t));cases.append(h);
  s.cases.forEach((c,i)=>{const p=output.settings[i],tr=document.createElement('tr');for(const text of [pct(p.heatWeight),p.threshold.toFixed(2),pct(c.share),c.rank??'—',s.eligible?(c.selected?'是':'否'):'不参与'])tr.append(node('td',text));cases.append(tr);});
  scroll.append(cases);details.append(scroll);panel.append(details);
 }
 function refresh(){if(!context)return;renderDetail();renderList();}
 function changeScale(data,key){
  if(worker){worker.terminate();worker=null;}scale=key;output=null;error=null;lookup=new Map();
  $('show-stability').disabled=true;$('export-shortlist').disabled=true;$('shortlist-filter').value='all';
  function accept(value){output=value;lookup=new Map(value.rows.map(r=>[r.id,r]));$('stability-progress').textContent='72 / 72 组已完成 · 支持充分 '+value.rows.filter(r=>r.eligible).length+' 个片区';$('show-stability').disabled=false;$('export-shortlist').disabled=false;refresh();context.paint();}
  if(cache.has(key)){accept(cache.get(key));return;}
  $('stability-progress').textContent='后台计算 0 / 72 组，地图仍可操作';
  const url=URL.createObjectURL(new Blob([PILOT.analysisWorker],{type:'text/javascript'}));worker=new Worker(url);URL.revokeObjectURL(url);
  function fail(message){error=message;$('stability-progress').textContent='稳定性计算失败：'+message;worker?.terminate();worker=null;refresh();}
  worker.onerror=event=>fail(event.message);
  worker.onmessage=event=>{
   const message=event.data;if(message.error){fail(message.error);return;}
   if(message.output){cache.set(key,message.output);worker.terminate();worker=null;accept(message.output);}
   else $('stability-progress').textContent='后台计算 '+message.progress+' / '+message.total+' 组，地图仍可操作';
  };
  worker.postMessage(data);
 }
 function init(value){context=value;
  const option=node('option','入选频率（72组参数）');option.value='selection_frequency';$('metric').append(option);
  $('show-stability').onclick=()=>{$('metric').value='selection_frequency';context.clearCompare();context.paint();$('map').scrollIntoView({behavior:'smooth',block:'center'});};
  $('shortlist-filter').onchange=()=>{refresh();context.paint();};$('shortlist-search').oninput=()=>{renderList();context.paint();};
  $('export-shortlist').onclick=exportRows;
 }
 root.HeatwaterResearch={init,refresh,changeScale,matches,score:id=>lookup.get(id)?.frequency??null,get output(){return output;},get loading(){return !output&&!error;}};
})(window);
