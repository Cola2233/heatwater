"""Arterial-scale planning units: labelled components, adjacency merge and exact-domain masking.

Method reference: Laisen-geo BRIEF.md. This implementation uses scipy/GDAL;
no upstream application code or datasets are incorporated into public assets.
"""
from pathlib import Path
import argparse
import base64
import json
import re
import numpy as np


def delineate(domain,roads,river,min_cells=30,max_blocks=70):
    from scipy import ndimage
    domain=np.asarray(domain,dtype=bool);roads=np.asarray(roads,dtype=bool);river=np.asarray(river,dtype=bool)
    if domain.shape!=roads.shape or domain.shape!=river.shape:raise ValueError('Mask grids differ')
    labels,n=ndimage.label(domain&~roads&~river)
    if not n:raise ValueError('No open cells for planning units')
    # Nearest ownership gives road/water pixels explicit ownership for aggregation.
    nearest=ndimage.distance_transform_edt(labels==0,return_distances=False,return_indices=True)
    filled=labels[tuple(nearest)];filled[~domain]=0
    size=np.bincount(labels.ravel(),minlength=n+1).astype(int)
    edges=set()
    for axis in (0,1):
        sl1=[slice(None),slice(None)];sl2=sl1.copy();sl1[axis]=slice(None,-1);sl2[axis]=slice(1,None)
        a,b=filled[tuple(sl1)],filled[tuple(sl2)]
        keep=(a>0)&(b>0)&(a!=b)&~river[tuple(sl1)]&~river[tuple(sl2)]
        edges.update((min(int(x),int(y)),max(int(x),int(y))) for x,y in zip(a[keep],b[keep]))
    parent=np.arange(n+1)
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=int(parent[i])
        return i
    count=n;merged=0
    while True:
        adjacency={i:set() for i in range(1,n+1) if find(i)==i}
        for a,b in edges:
            x,y=find(a),find(b)
            if x!=y:adjacency[x].add(y);adjacency[y].add(x)
        choices=[i for i,neighbors in adjacency.items() if neighbors and (size[i]<min_cells or count>max_blocks)]
        if not choices:break
        small=min(choices,key=lambda i:(size[i],i))
        large=max(adjacency[small],key=lambda i:(size[i],-i))
        parent[small]=large;size[large]+=size[small];count-=1;merged+=1
    lut=np.zeros(n+1,dtype=np.uint32);roots={}
    # Scan order provides stable ids from north to south.
    for value in filled.ravel():
        if value:
            r=find(int(value))
            if r not in roots:roots[r]=len(roots)+1
            lut[value]=roots[r]
    ids=lut[filled]
    return ids,{'raw_components':n,'blocks':len(roots),'merged':merged,'min_open_cells':min_cells,
                'target_max_blocks':max_blocks,'domain_cells':int(domain.sum()),'road_cells':int((domain&roads).sum()),
                'river_cells':int((domain&river).sum()),'barrier_ownership':'nearest component; river pixels included in statistics but drawn separately'}


def build(data_file,handoff,output):
    from .geo_runtime import configure
    configure()
    from osgeo import gdal,ogr,osr
    from scipy import ndimage
    from shapely import from_wkb
    from .provenance import sha256
    from .blocks import summarize_blocks
    gdal.UseExceptions();ogr.UseExceptions();osr.UseExceptions()
    text=Path(data_file).read_text(encoding='utf-8');raw=json.loads(re.search(r'=\s*(\{.*\});',text,re.S)[1])
    handoff=Path(handoff);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    wc_ds=gdal.Open(str(handoff/'rasters/WorldCover_2021_200m.tif'));wc=wc_ds.ReadAsArray();gt=wc_ds.GetGeoTransform()
    epsg=osr.SpatialReference();epsg.ImportFromEPSG(32651);epsg.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    wgs=osr.SpatialReference();wgs.ImportFromEPSG(4326);wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    to_utm=osr.CoordinateTransformation(wgs,epsg);to_wgs=osr.CoordinateTransformation(epsg,wgs)
    roads_ds=gdal.GetDriverByName('MEM').Create('',wc_ds.RasterXSize,wc_ds.RasterYSize,1,gdal.GDT_Byte)
    roads_ds.SetGeoTransform(gt);roads_ds.SetProjection(wc_ds.GetProjection())
    memory=ogr.GetDriverByName('Memory').CreateDataSource('roads');layer=memory.CreateLayer('roads',epsg,ogr.wkbUnknown)
    road_geo=[];excluded_links=0
    for filename,level in [('arterials.geojson',1),('expressways.geojson',2)]:
        features=json.loads((handoff/'vectors'/filename).read_text(encoding='utf-8'))['features']
        for f in features:
            properties=f.get('properties',{})
            if str(properties.get('is_link','')).lower()=='true' or str(properties.get('highway','')).endswith('_link'):
                excluded_links+=1;continue
            geom=ogr.CreateGeometryFromJson(json.dumps(f['geometry']));geom.Transform(to_utm)
            feature=ogr.Feature(layer.GetLayerDefn());feature.SetGeometry(geom);layer.CreateFeature(feature)
            road_geo.append({'type':'Feature','properties':{'level':level},'geometry':f['geometry']})
    # The supplied handoff roads were sampled every ~50 m in Laisen-geo;
    # GDAL all-touched rasterization gives connected barriers without that custom sampler.
    gdal.RasterizeLayer(roads_ds,[1],layer,burn_values=[1],options=['ALL_TOUCHED=TRUE'])
    coarse,diag=delineate(wc>0,roads_ds.ReadAsArray()>0,wc==80)
    meta=raw['meta'];h,w=meta['height'],meta['width'];rgt=meta['geotransform']
    if meta['epsg']!=32651:raise ValueError('This handoff requires EPSG:32651 input')
    yy,xx=np.indices((h,w));x=rgt[0]+(xx+.5)*rgt[1];y=rgt[3]+(yy+.5)*rgt[5]
    col=np.floor((x-gt[0])/gt[1]).astype(int);row=np.floor((y-gt[3])/gt[5]).astype(int)
    if np.any(col<0) or np.any(col>=wc.shape[1]) or np.any(row<0) or np.any(row>=wc.shape[0]):raise ValueError('Analysis grid exceeds handoff')
    nearest=ndimage.distance_transform_edt(coarse==0,return_distances=False,return_indices=True)
    full=coarse[tuple(nearest)];ids=full[row,col].astype('u4')
    boundary_path=handoff/'vectors/study_area.geojson';boundary_ds=ogr.Open(str(boundary_path));boundary_layer=boundary_ds.GetLayer(0)
    def raster(values,dtype=gdal.GDT_UInt32):
        ds=gdal.GetDriverByName('MEM').Create('',w,h,1,dtype);ds.SetGeoTransform(rgt);ds.SetProjection(epsg.ExportToWkt());ds.GetRasterBand(1).WriteArray(values);return ds
    mask_ds=raster(np.zeros((h,w),dtype='u1'),gdal.GDT_Byte);gdal.RasterizeLayer(mask_ds,[1],boundary_layer,burn_values=[1])
    inside=mask_ds.ReadAsArray()>0;ids[~inside]=0
    arrays={k:np.frombuffer(base64.b64decode(raw['arrays'][k]),dtype='<f4').copy().reshape(h,w) for k in ['heat','water','exposure']}
    original_valid=np.logical_and.reduce([np.isfinite(a)&(a>=0)&(a<=1) for a in arrays.values()])
    for key,a in arrays.items():a[~inside]=np.nan;raw['arrays'][key]=base64.b64encode(a.astype('<f4').tobytes()).decode()
    transition=np.frombuffer(base64.b64decode(raw['arrays']['transition']),dtype='u1').copy().reshape(h,w);transition[~inside]=0
    raw['arrays']['transition']=base64.b64encode(transition.tobytes()).decode()
    raster_ds=raster(ids);gdal.GetDriverByName('GTiff').CreateCopy(str(output/'planning_ids_30m.tif'),raster_ds,options=['COMPRESS=DEFLATE'])
    vector=ogr.GetDriverByName('Memory').CreateDataSource('units');polygons=vector.CreateLayer('units',epsg,ogr.wkbPolygon)
    polygons.CreateField(ogr.FieldDefn('id',ogr.OFTInteger));gdal.Polygonize(raster_ds.GetRasterBand(1),None,polygons,0)
    geometries={}
    for f in polygons:
        i=f.GetField('id')
        if i:geometries.setdefault(i,[]).append(from_wkb(bytes(f.GetGeometryRef().ExportToWkb())))
    from shapely import unary_union
    features=[]
    for i,parts in sorted(geometries.items()):
        p=unary_union(parts).simplify(10,preserve_topology=True);pieces=list(p.geoms) if p.geom_type=='MultiPolygon' else [p]
        rings=[[[[round((x-rgt[0])/30,4),round((y-rgt[3])/-30,4)] for x,y in ring.coords] for ring in [piece.exterior,*piece.interiors]] for piece in pieces]
        features.append({'id':i,'name':f'主干路片区 U{i:02d}','polygons':rings,
                         'bounds':[(p.bounds[0]-rgt[0])/30,(p.bounds[3]-rgt[3])/-30,(p.bounds[2]-rgt[0])/30,(p.bounds[1]-rgt[3])/-30],
                         'geometry_area_km2':p.area/1e6,'boundary_cut':False})
    stats=summarize_blocks(ids,*[arrays[k] for k in ['heat','water','exposure']],transition)
    # Actual study boundary contacts are reported rather than treated as complete administrative units.
    edge=inside&~ndimage.binary_erosion(inside)
    edge_ids=set(ids[edge].tolist())
    for f in features:f['boundary_cut']=f['id'] in edge_ids
    diag.update(scale='planning',method='arterial barriers on 200m grid; scipy connected components and adjacency merge',
                reference='https://github.com/BillyAshlet/Laisen-geo/blob/main/BRIEF.md',
                geometry_resolution_m=200,statistics_resolution_m=30,used_roads=len(road_geo),excluded_links=excluded_links,
                old_valid_pixels=int(original_valid.sum()),assigned_valid_pixels=sum(r['valid_pixels'] for r in stats),
                excluded_outside_study_pixels=int((original_valid&~inside).sum()),domain_area_km2=float(inside.sum()*.0009),
                source_hashes={p.name:sha256(p) for p in [boundary_path,handoff/'rasters/WorldCover_2021_200m.tif',handoff/'vectors/arterials.geojson',handoff/'vectors/expressways.geojson']})
    raw['meta'].update(id='changchun-planning',title='长春四环 · 主干路片区',analysis_domain='真实四环边界；30米像元中心采样',partition_method='主干路、快速路、河流围合；200米分区，30米统计',previous_valid_pixels=diag['old_valid_pixels'])
    raw['blocks']={'version':1,'features':features,'diagnostics':diag};raw.pop('block_scales',None)
    raw['arrays']['block_ids']=base64.b64encode(ids.astype('<u4').tobytes()).decode()
    # Context overlays are geographic vectors; they do not enter the statistical rule.
    water_ids=raster((wc==80)[row,col].astype('u4')*inside);water_vector=ogr.GetDriverByName('Memory').CreateDataSource('water');wl=water_vector.CreateLayer('water',epsg,ogr.wkbPolygon);wl.CreateField(ogr.FieldDefn('id',ogr.OFTInteger))
    gdal.Polygonize(water_ids.GetRasterBand(1),None,wl,0);water_geo=[]
    for f in wl:
        if f.GetField('id')==1:
            g=f.GetGeometryRef().Clone();g.Transform(to_wgs);water_geo.append({'type':'Feature','properties':{},'geometry':json.loads(g.ExportToJson())})
    boundary_geo=[];boundary_layer.ResetReading()
    for f in boundary_layer:
        g=f.GetGeometryRef().Clone();s=boundary_layer.GetSpatialRef();s.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER);g.Transform(osr.CoordinateTransformation(s,wgs));boundary_geo.append({'type':'Feature','properties':{},'geometry':json.loads(g.ExportToJson())})
    raw['map_context']={key:{'type':'FeatureCollection','features':value} for key,value in [('roads',road_geo),('water',water_geo),('boundary',boundary_geo)]}
    (output/'planning-browser.js').write_text('window.HEATWATER_DATASETS=window.HEATWATER_DATASETS||{};\nwindow.HEATWATER_DATASETS["changchun-planning"]='+json.dumps(raw,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
    (output/'diagnostics.json').write_text(json.dumps(diag,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(diag,ensure_ascii=True));return diag


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',type=Path,default=Path('website/data/local.js'));p.add_argument('--handoff',type=Path,required=True);p.add_argument('--output',type=Path,default=Path('artifacts/planning-blocks'))
    a=p.parse_args();build(a.data,a.handoff,a.output)

if __name__=='__main__':main()
