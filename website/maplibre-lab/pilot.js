(function(){
 'use strict';
 const $=id=>document.getElementById(id),pilot=window.PILOT,raw=pilot.raw;
 const primary=raw.blocks.diagnostics.scale||'detail';
 const variants={[primary]:{blocks:raw.blocks,ids:raw.arrays.block_ids},...raw.block_scales};
 function decode(text,type){const a=Uint8Array.from(atob(text),c=>c.charCodeAt(0));return type==='u8'?a:type==='u32'?new Uint32Array(a.buffer):new Float32Array(a.buffer);}
 const data={...raw.meta,heat:decode(raw.arrays.heat),water:decode(raw.arrays.water),exposure:decode(raw.arrays.exposure),transition:decode(raw.arrays.transition,'u8')};
 const settings={heatWeight:.55,threshold:.67};
 let scale=primary,result,rows=[],before=null,beforeRows=null,beforeSettings=null,change=null,comparing=false,selected=null,hovered=null,frame=0,ready=false,revision=0;
 const low={compound_mean:'#e4edd6',both_share:'#e4edd6',heat_mean:'#fff2c2',water_mean:'#e3f1f4',exposure_mean:'#eef0e7'};
 const high={compound_mean:'#674387',both_share:'#674387',heat_mean:'#c94933',water_mean:'#2b6597',exposure_mean:'#31735b'};
 $('case-name').textContent=data.title+(data.synthetic?'（模拟案例）':'（本地真实数据）');
 document.title='热水共治 / 片区解释与参数稳定性 / '+(data.synthetic?'模拟案例':data.title);
 $('build-info').textContent='MapLibre '+pilot.version+' / EPSG:'+data.epsg+' → WGS84逐顶点转换 / 资源与数据全部嵌入';$('licenses').textContent=pilot.license;
 for(const [key,variant]of Object.entries(variants)){const option=document.createElement('option');option.value=key;option.textContent=(key==='planning'?'主干路片区':key==='overview'?'片区概览':'细街区')+'（'+variant.blocks.features.length+'）';$('scale').append(option);}
 $('scale').value=scale;
 // The bundle is a classic IIFE worker. MapLibre uses .cjs to select classic workers.
 const worker=URL.createObjectURL(new Blob([pilot.worker],{type:'text/javascript'}));maplibregl.setWorkerUrl(worker+'#worker.cjs');maplibregl.setWorkerCount(1);
 const map=new maplibregl.Map({container:'map',style:{version:8,sources:{},layers:[{id:'background',type:'background',paint:{'background-color':'#202e2c'}}]},center:[125.3,43.88],zoom:10,
  canvasContextAttributes:{preserveDrawingBuffer:true,antialias:true},attributionControl:false});
 map.addControl(new maplibregl.NavigationControl(),'top-right');map.addControl(new maplibregl.ScaleControl({unit:'metric'}),'bottom-right');
 map.on('error',event=>{const message=event.error?.message||String(event.error);$('map-error').hidden=false;$('map-error').textContent='地图引擎错误：'+message;console.error(message);});
 function fit(){const bounds=new maplibregl.LngLatBounds();for(const f of pilot.geo[scale].features){const b=f.properties.bounds;bounds.extend([b[0],b[1]]);bounds.extend([b[2],b[3]]);}map.fitBounds(bounds,{padding:35,duration:0});}
 function recompute(remember=true){
  if(remember&&result){before=result;beforeRows=rows;beforeSettings={...lastSettings};}
  result=window.HeatwaterCore.analyze(data,settings);rows=window.HeatwaterBlockCore.analyze(data,result);
  if(remember&&before){const kind=beforeSettings.threshold!==settings.threshold?'threshold':'weight';change=window.HeatwaterFeedbackCore.compare(data,before,result,kind);$('metric').value=kind==='weight'?'compound_mean':'both_share';}
  lastSettings={...settings};comparing=false;
  $('weight-value').textContent=Math.round(settings.heatWeight*100)+'%';$('threshold-value').textContent=settings.threshold.toFixed(2);$('both').textContent=(result.counts[3]*result.pixelArea).toFixed(2);
  $('compare').disabled=!before;paint();detail();
  if(data.analysis_domain){$('domain-note').hidden=false;$('domain-note').textContent=data.partition_method+'。仅统计真实四环边界内：'+result.validCount.toLocaleString()+' 个共同有效像元 / '+result.area.toFixed(2)+' km²。与旧矩形范围结果不可直接比较。';}
 }
 let lastSettings={...settings};
 function paint(){
  if(!ready)return;
  const metric=$('metric').value,isStability=metric==='selection_frequency',showChange=!isStability&&change&&$('changes').checked&&!comparing,current=comparing?beforeRows:rows;
  for(const row of current){const delta=change?.blocks.get(row.id)?.delta||0,score=isStability?HeatwaterResearch.score(row.id):row[metric];map.setFeatureState({source:'units',id:row.id},{score:score??0,valid:row.valid_pixels>0&&(!isStability||score!==null)&&HeatwaterResearch.matches(row),delta,selected:row.id===selected});}
  map.setPaintProperty('unit-fill','fill-color',showChange?['case',['>', ['feature-state','delta'],.000001],'#ef8548',['<',['feature-state','delta'],-.000001],'#43bfcb','#899690']:
   ['interpolate',['linear'],['number',['feature-state','score'],0],0,low[metric]||'#f1e9d6',1,high[metric]||'#285c4f']);
  map.setPaintProperty('unit-fill','fill-opacity',['case',['boolean',['feature-state','valid'],false],showChange?.9:.88,0]);
  $('compare').textContent=comparing?'返回当前':'查看上一步';
  $('compare').disabled=!before||isStability;
  $('status').textContent=isStability?'参数稳定性 / 72组固定参数 / 入选频率地图':comparing?'上一步地图：热权重 '+Math.round(beforeSettings.heatWeight*100)+'% / 阈值 '+beforeSettings.threshold.toFixed(2)+'（右侧为当前统计）':
   showChange?'本次参数变化 / 影响 '+change.affectedArea.toFixed(2)+' km² / '+(change.kind==='weight'?'复合分数差':'双高判定差'):
   rows.filter(r=>r.valid_pixels>0).length+' 个有数据分区 / MapLibre矢量渲染';
  $('legend').textContent=isStability?'浅色0% → 深绿100%；无填色表示数据不足、计算中或被筛选隐藏。频率不是灾害概率。':showChange?'橙色增加 / 青色减少 / 灰色未变化。片区颜色表示均值或占比变化。':'当前分数或比例：浅色较低，深色较高。筛选条件同步作用于地图。';
  revision++;map.once('idle',()=>{window.heatwaterPilot.renderedRevision=revision;});
 }
 function detail(){
  HeatwaterResearch.refresh();
 }
 function setScale(){
  scale=$('scale').value;data.blocks=variants[scale].blocks;data.blockIds=decode(variants[scale].ids,'u32');
  selected=null;hovered=null;before=null;beforeRows=null;change=null;comparing=false;result=null;
  map.removeFeatureState({source:'units'});map.getSource('units').setData(pilot.geo[scale]);recompute(false);HeatwaterResearch.changeScale(data,scale);paint();detail();fit();
 }
 const popup=new maplibregl.Popup({closeButton:false,closeOnClick:false});
 map.on('load',()=>{
  map.addSource('units',{type:'geojson',data:pilot.geo[scale]});
  map.addLayer({id:'unit-fill',type:'fill',source:'units',paint:{'fill-color':'#cbdcb9','fill-opacity':.9}});
  if(raw.map_context){
   for(const key of ['roads','water','boundary'])map.addSource('context-'+key,{type:'geojson',data:raw.map_context[key]});
   map.addLayer({id:'context-water',type:'fill',source:'context-water',paint:{'fill-color':'#7db5c5','fill-opacity':.95}});
   map.addLayer({id:'context-roads',type:'line',source:'context-roads',filter:['==',['get','level'],1],paint:{'line-color':'#e6e5d6','line-opacity':.8,'line-width':['interpolate',['linear'],['zoom'],10,.8,14,3]}});
   map.addLayer({id:'context-expressways',type:'line',source:'context-roads',filter:['==',['get','level'],2],paint:{'line-color':'#f4dca5','line-opacity':.95,'line-width':['interpolate',['linear'],['zoom'],10,1.5,14,5]}});
   map.addLayer({id:'context-boundary',type:'line',source:'context-boundary',paint:{'line-color':'#d1d6c3','line-width':1.5}});
   $('context-tools').hidden=false;$('context-toggle').onchange=()=>{for(const id of ['context-water','context-roads','context-expressways'])map.setLayoutProperty(id,'visibility',$('context-toggle').checked?'visible':'none');};
  }
  map.addLayer({id:'unit-line',type:'line',source:'units',paint:{'line-color':['case',['boolean',['feature-state','selected'],false],'#ffd8a1',['boolean',['feature-state','hover'],false],'#fff4dc','#344e45'],
   'line-width':['case',['boolean',['feature-state','selected'],false],3,['boolean',['feature-state','hover'],false],2,.65]}});
  ready=true;setScale();
  map.on('mousemove','unit-fill',event=>{
   if(hovered!=null)map.setFeatureState({source:'units',id:hovered},{hover:false});
   hovered=event.features[0].id;map.setFeatureState({source:'units',id:hovered},{hover:true});map.getCanvas().style.cursor='pointer';
   const row=(comparing?beforeRows:rows).find(r=>r.id===hovered);if(!row)return;
   const container=document.createElement('div'),h=document.createElement('strong'),p=document.createElement('p');h.textContent=row.name;
   p.textContent='复合 '+(row.compound_mean?.toFixed(2)??'—')+' / 双高 '+(row.both_share==null?'—':(row.both_share*100).toFixed(1)+'%')+' / 参数入选频率 '+(HeatwaterResearch.score(row.id)==null?'未计算':(HeatwaterResearch.score(row.id)*100).toFixed(1)+'%');container.append(h,p);
   popup.setLngLat(event.lngLat).setDOMContent(container).addTo(map);
  });
  map.on('mouseleave','unit-fill',()=>{if(hovered!=null)map.setFeatureState({source:'units',id:hovered},{hover:false});hovered=null;popup.remove();map.getCanvas().style.cursor='';});
  map.on('click','unit-fill',event=>{selected=event.features[0].id;paint();detail();});
  map.once('idle',()=>{window.heatwaterPilot.ready=true;});
 });
 for(const id of ['weight','threshold'])$(id).oninput=()=>{
  settings.heatWeight=Number($('weight').value)/100;settings.threshold=Number($('threshold').value)/100;
  cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>recompute());
 };
 $('scale').onchange=setScale;$('metric').onchange=()=>{change=null;comparing=false;paint();};$('changes').onchange=paint;
 $('fit').onclick=fit;$('compare').onclick=()=>{comparing=!comparing;paint();detail();};
 $('reset').onclick=()=>{settings.heatWeight=.55;settings.threshold=.67;$('weight').value=55;$('threshold').value=67;recompute();};
 $('export').onclick=()=>{
  const columns=['id','name','valid_pixels','valid_area_km2','heat_mean','water_mean','compound_mean','both_share','exposure_mean'];
  const quote=v=>'"'+String(v??'').replaceAll('"','""')+'"';
  const content='\uFEFF'+[columns,...rows.map(r=>columns.map(k=>r[k]))].map(r=>r.map(quote).join(',')).join('\r\n');
  const url=URL.createObjectURL(new Blob([content],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download=data.id+'-'+scale+'-maplibre.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 };
 window.heatwaterPilot={map,ready:false,renderedRevision:0,get revision(){return revision;},get rows(){return rows;},get selected(){return selected;},get comparing(){return comparing;},get scale(){return scale;}};
 HeatwaterResearch.init({data,rows:()=>rows,selected:()=>selected,comparing:()=>comparing,settings:()=>({...settings}),paint,
  clearCompare:()=>{comparing=false;change=null;detail();},
  focus:id=>{selected=id;paint();detail();const f=pilot.geo[scale].features.find(f=>f.id===id),b=f.properties.bounds;map.fitBounds([[b[0],b[1]],[b[2],b[3]]],{padding:65,maxZoom:15,duration:500});$('map').scrollIntoView({behavior:'smooth',block:'center'});}
 });
})();
