"""Compare original and neatnet roads in a buffered real-data sample; no production writes."""
from __future__ import annotations
import argparse,base64,json,re,time,platform,importlib.metadata
from pathlib import Path
import numpy as np


def run(config_path,output):
    import geopandas as gpd
    import neatnet
    import shapely
    from shapely.geometry import box
    from .blocks import SURFACE_CLASSES,partition_blocks
    from .project_config import load_project_config
    config=load_project_config(config_path);output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    web=config.project_root/'website/data/local.js'
    raw=json.loads(web.read_text(encoding='utf-8').split('window.HEATWATER_DATASETS["changchun"]=',1)[1].strip().rstrip(';'))
    meta=raw['meta'];gt=meta['geotransform'];w,h=meta['width'],meta['height']
    cx=gt[0]+(w//2)*30;cy=gt[3]-(h//2)*30
    core=box(cx-1500,cy-1500,cx+1500,cy+1500);buffer=core.buffer(600).envelope
    roads=gpd.read_file(config.input_path('block_roads'),layer='roads',bbox=buffer.bounds).to_crs(meta['epsg'])
    def eligible(row):
        text=row.get('other_tags');text=text if isinstance(text,str) else ''
        tags=dict(re.findall(r'"([^"\s]+)"=>"([^"]*)"',text))
        return row.highway in SURFACE_CLASSES and not any(tags.get(k,'no') not in {'no','false','0',''} for k in ('bridge','tunnel')) and tags.get('layer','0') in {'0',''}
    roads=roads[roads.apply(eligible,axis=1)].copy().explode(ignore_index=True)
    roads.geometry=shapely.force_2d(roads.geometry.intersection(buffer));roads=roads[~roads.geometry.is_empty].reset_index(drop=True)
    buildings=gpd.read_file(config.input_path('building_functions'),bbox=buffer.bounds).to_crs(meta['epsg'])
    buildings=buildings[buildings.intersects(buffer)]
    print('Input roads:',len(roads),'building exclusion polygons:',len(buildings),flush=True)
    start=time.perf_counter()
    simplified=neatnet.neatify(roads,exclusion_mask=buildings.geometry)
    seconds=time.perf_counter()-start
    roads.to_file(output/'pilot.gpkg',layer='original_roads',driver='GPKG')
    simplified.to_file(output/'pilot.gpkg',layer='neatnet_roads',driver='GPKG')
    cols=np.arange(round((core.bounds[0]-gt[0])/30),round((core.bounds[2]-gt[0])/30))
    rows=np.arange(round((gt[3]-core.bounds[3])/30),round((gt[3]-core.bounds[1])/30))
    xx,yy=np.meshgrid(gt[0]+(cols+.5)*30,gt[3]-(rows+.5)*30)
    points=shapely.points(xx.ravel(),yy.ravel())
    valid=np.ones((h,w),dtype=bool)
    for key in ['heat','water','exposure']:
        a=np.frombuffer(base64.b64decode(raw['arrays'][key]),dtype='<f4').reshape(h,w)
        valid&=np.isfinite(a)&(a>=0)&(a<=1)
    sample_valid=valid[np.ix_(rows,cols)].ravel()
    metrics={};partitions={}
    for key,frame in [('original',roads),('neatnet',simplified)]:
        lines=[g.intersection(core) for g in frame.geometry if g.intersects(core)]
        lines=[g for g in lines if not g.is_empty]
        polygons,diag=partition_blocks(lines,core,min_area=0)
        areas=np.array([p.area for p in polygons])
        pair=shapely.STRtree(polygons).query(points,predicate='intersects')
        owned=np.zeros(len(points),dtype=bool);owned[pair[0]]=True
        metrics[key]={'road_features':len(frame),'road_length_m':float(frame.length.sum()),'raw_faces':len(polygons),
                      'faces_under_8100m2':int((areas<8100).sum()),'median_face_m2':float(np.median(areas)),
                      'cut_segments':diag['cut_segments'],'dangle_segments':diag['dangle_segments'],
                      'partition_area_km2':float(sum(p.area for p in polygons)/1e6),
                      'valid_pixels_covered':int((owned&sample_valid).sum()),'expected_valid_pixels':int(sample_valid.sum())}
        if not np.all(owned[sample_valid]):raise ValueError(key+' leaves valid sample pixels uncovered')
        partitions[key]=polygons
        gpd.GeoDataFrame({'block_id':range(1,len(polygons)+1)},geometry=polygons,crs=meta['epsg']).to_file(output/'pilot.gpkg',layer=key+'_faces',driver='GPKG')
    result={'core_bounds_utm':list(core.bounds),'core_area_km2':core.area/1e6,'context_buffer_m':600,
            'building_exclusions':len(buildings),'neatnet_seconds':seconds,
            'versions':{k:importlib.metadata.version(k) for k in ['neatnet','geopandas','shapely','momepy']},
            'python':platform.python_version(),'metrics':metrics,
            'scope':'One central 3x3 km sample. Geometry comparison only; fewer faces does not establish scientific accuracy.'}
    (output/'neatnet-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(12,12),facecolor='#f1eee6')
    for j,(key,frame) in enumerate([('original',roads),('neatnet',simplified)]):
        frame.plot(ax=axes[0,j],color='#356968' if j==0 else '#ac472f',linewidth=.8)
        gpd.GeoSeries(partitions[key]).plot(ax=axes[1,j],facecolor='#d7dfce',edgecolor='#3d6055',linewidth=.6)
        axes[0,j].set_title(key+' road network');axes[1,j].set_title(f'{key}: {metrics[key]["raw_faces"]} faces / {metrics[key]["faces_under_8100m2"]} small faces')
        for ax in axes[:,j]:ax.set_xlim(core.bounds[0],core.bounds[2]);ax.set_ylim(core.bounds[1],core.bounds[3]);ax.set_aspect('equal');ax.set_axis_off()
    fig.suptitle('Changchun real roads / neatnet pilot (same 3 km × 3 km extent)',fontsize=16)
    fig.tight_layout();fig.savefig(output/'neatnet-comparison.png',dpi=150);plt.close(fig)
    image=base64.b64encode((output/'neatnet-comparison.png').read_bytes()).decode()
    body='<h1>长春道路清理对照实验</h1><p>同一个3×3公里真实样区，外围600米用于减轻裁切影响；建筑轮廓作为保护掩膜。</p><table><tr><th>指标</th><th>原道路</th><th>neatnet</th></tr>'
    for label,key in [('面化单元','raw_faces'),('小于8100平方米','faces_under_8100m2'),('断头线段','dangle_segments'),('覆盖有效像元','valid_pixels_covered')]:
        body+=f'<tr><td>{label}</td><td>{metrics["original"][key]}</td><td>{metrics["neatnet"][key]}</td></tr>'
    body+='</table><p>这是局部几何验证，单元更少不等于边界更准确；正式长春分区尚未替换。</p>'
    body+=f'<img alt="道路与分区对照" src="data:image/png;base64,{image}"><details><summary>运行记录</summary><pre>'+json.dumps(result,ensure_ascii=False,indent=2)+'</pre></details>'
    (output/'neatnet-comparison.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>neatnet道路对照</title><style>body{max-width:1200px;margin:32px auto;padding:0 20px;background:#f1eee6;color:#263c35;font:16px/1.8 "Microsoft YaHei",sans-serif}h1{font-size:30px}table{border-collapse:collapse;width:100%}td,th{padding:12px;border:1px solid #c9cabb;text-align:left}img{width:100%;margin-top:24px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}</style>'+body+'</html>',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=True),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,default=Path('artifacts/opensource-pilot'))
    a=p.parse_args();run(a.config,a.output)


if __name__=='__main__':main()
