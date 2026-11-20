"""Build a standalone offline MapLibre pilot; public demo is the default."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def project_features(meta,features,transform):
    gt=meta['geotransform'];out=[]
    for f in features:
        polygons=[];coords=[]
        for polygon in f['polygons']:
            rings=[]
            for ring in polygon:
                points=[]
                for x,y in ring:
                    lng,lat=transform(gt[0]+x*gt[1]+y*gt[2],gt[3]+x*gt[4]+y*gt[5])[:2]
                    point=[round(lng,8),round(lat,8)];points.append(point);coords.append(point)
                rings.append(points)
            polygons.append(rings)
        xs,ys=zip(*coords)
        out.append({'type':'Feature','id':f['id'],'properties':{'name':f['name'],'bounds':[min(xs),min(ys),max(xs),max(ys)]},
                    'geometry':{'type':'MultiPolygon','coordinates':polygons}})
    return {'type':'FeatureCollection','features':out}

def build(data_file,output,vendor):
    from .geo_runtime import configure
    configure()
    from osgeo import osr
    source=Path(data_file).read_text(encoding='utf-8')
    match=re.search(r'window\.HEATWATER_DATASETS\["([^"]+)"\]\s*=\s*(\{.*\});',source,re.S)
    if not match:raise ValueError('Expected a project browser dataset')
    raw=json.loads(match[2]);meta=raw['meta']
    if not raw.get('blocks'):raise ValueError('Dataset must contain block data')
    utm=osr.SpatialReference();utm.ImportFromEPSG(meta['epsg']);utm.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    wgs=osr.SpatialReference();wgs.ImportFromEPSG(4326);wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    transformer=osr.CoordinateTransformation(utm,wgs)
    variants={raw['blocks']['diagnostics'].get('scale','detail'):{'blocks':raw['blocks'],'ids':raw['arrays']['block_ids']},**raw.get('block_scales',{})}
    geo={key:project_features(meta,v['blocks']['features'],transformer.TransformPoint) for key,v in variants.items()}
    root=Path(vendor);library=root/'node_modules/maplibre-gl'
    version=json.loads((library/'package.json').read_text())['version']
    license=(library/'LICENSE.txt').read_text(encoding='utf-8')
    lab=ROOT/'website/maplibre-lab'
    values={'VENDOR_CSS':(library/'dist/maplibre-gl.css').read_text(encoding='utf-8'),
            'PILOT_CSS':(lab/'pilot.css').read_text(encoding='utf-8'),
            'VENDOR_JS':(root/'bundle/maplibre.js').read_text(encoding='utf-8'),
            'CORE_JS':(ROOT/'website/core.js').read_text(encoding='utf-8'),
            'BLOCK_CORE_JS':(ROOT/'website/blocks-core.js').read_text(encoding='utf-8'),
            'FEEDBACK_CORE_JS':(ROOT/'website/feedback-core.js').read_text(encoding='utf-8'),
            'STABILITY_JS':(ROOT/'website/stability-core.js').read_text(encoding='utf-8'),
            'RESEARCH_JS':(lab/'explanation.js').read_text(encoding='utf-8'),
            'PAYLOAD_JS':'window.PILOT='+json.dumps({'raw':raw,'geo':geo,'worker':(root/'bundle/worker.js').read_text(encoding='utf-8'),
               'version':version,'license':license,
               'analysisWorker':'\n'.join((ROOT/p).read_text(encoding='utf-8') for p in ['website/core.js','website/blocks-core.js','website/stability-core.js'])+'''\nself.onmessage=function(event){try{const output=HeatwaterStability.analyze(event.data,HeatwaterCore,HeatwaterBlockCore,{},function(done,total){self.postMessage({progress:done,total:total});});self.postMessage({output:output});}catch(error){self.postMessage({error:error.message});}};'''
               },ensure_ascii=False,separators=(',',':'))+';',
            'PILOT_JS':(lab/'pilot.js').read_text(encoding='utf-8')}
    html=(lab/'pilot.html').read_text(encoding='utf-8')
    for key,value in values.items():
        if key.endswith('JS'):value=re.sub('</script',lambda _:r'<\/script',value,flags=re.I)
        html=html.replace('/* '+key+' */',value)
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(html,encoding='utf-8')
    (output.parent/'MapLibre-LICENSE.txt').write_text(license,encoding='utf-8')
    print(json.dumps({'output':str(output),'maplibre':version,'synthetic':meta['synthetic'],'scales':{k:len(v['features']) for k,v in geo.items()},'bytes':output.stat().st_size}))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',type=Path,default=ROOT/'website/data/demo.js');p.add_argument('--output',type=Path,default=ROOT/'artifacts/opensource-pilot/maplibre-demo.html');p.add_argument('--vendor',type=Path,default=ROOT/'artifacts/maplibre-runtime')
    a=p.parse_args();build(a.data,a.output,a.vendor)

if __name__=='__main__':main()
