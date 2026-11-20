"""Road-derived analysis units, raster-center ownership and reproducible summaries."""
from __future__ import annotations
import argparse
import base64
import csv
import json
import re
from pathlib import Path
import numpy as np

SURFACE_CLASSES={'motorway','trunk','primary','secondary','tertiary',
                 'residential','unclassified','living_street'}
OVERVIEW_CLASSES={'motorway','trunk','primary','secondary','tertiary'}


def summarize_blocks(labels,heat,water,exposure,transition,weight=.55,threshold=.67):
    arrays=[np.asarray(a).ravel() for a in (labels,heat,water,exposure,transition)]
    ids,h,w,e,tr=arrays
    if len({a.size for a in arrays})!=1:
        raise ValueError('Block arrays must share a grid')
    valid=np.isfinite(h)&np.isfinite(w)&np.isfinite(e)&(h>=0)&(h<=1)&(w>=0)&(w<=1)&(e>=0)&(e<=1)
    if np.any(ids[valid]==0):
        raise ValueError('Valid pixels are unassigned to a block')
    count=int(ids.max())+1
    total=np.bincount(ids.astype(int),minlength=count)
    owned=ids[valid].astype(int)
    n=np.bincount(owned,minlength=count)
    h,w,e=h[valid].astype('f4'),w[valid].astype('f4'),e[valid].astype('f4')
    score=np.float32(weight)*h+np.float32(1-weight)*w
    t=np.float32(threshold)
    sums={k:np.bincount(owned,weights=v,minlength=count) for k,v in
          [('heat',h),('water',w),('compound',score),('exposure',e)]}
    both=np.bincount(owned,weights=(h>=t)&(w>=t),minlength=count)
    high=np.bincount(owned,weights=(score>=t)&(e>=np.float32(.6)),minlength=count)
    expansion=np.bincount(owned,weights=tr[valid]==2,minlength=count)
    return [dict(id=i,total_pixels=int(total[i]),valid_pixels=int(n[i]),
                 coverage=float(n[i]/total[i]) if total[i] else 0,
                 **{k+'_mean':float(v[i]/n[i]) if n[i] else None for k,v in sums.items()},
                 both_pixels=int(both[i]),both_share=float(both[i]/n[i]) if n[i] else None,
                 high_exposure_pixels=int(high[i]),high_exposure_share=float(high[i]/n[i]) if n[i] else None,
                 expansion_share=float(expansion[i]/n[i]) if n[i] else None)
            for i in range(1,count)]


def partition_blocks(lines,extent,min_area=900,precision=.5):
    from shapely import unary_union, polygonize_full, get_parts, STRtree
    from shapely.affinity import translate
    # Work relative to the raster origin so precision does not move its extent.
    x0,y0=extent.bounds[:2]
    shifted=[translate(line,xoff=-x0,yoff=-y0) for line in lines]
    shifted.append(translate(extent.boundary,xoff=-x0,yoff=-y0))
    noded=unary_union(shifted,grid_size=precision)
    faces,cuts,dangles,invalid=polygonize_full(get_parts(noded))
    polygons=[translate(p,xoff=x0,yoff=y0) for p in get_parts(faces)]
    polygons=[p for p in polygons if extent.covers(p.representative_point())]
    tree=STRtree(polygons)
    parent=list(range(len(polygons)))
    group_area=[p.area for p in polygons]
    def find(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    merged=0
    for i in sorted(range(len(polygons)),key=lambda i:polygons[i].area):
        if group_area[find(i)]>=min_area:continue
        neighbors=[int(j) for j in tree.query(polygons[i],predicate='intersects') if j!=i and find(int(j))!=find(i)]
        lengths=[(group_area[find(j)]<min_area,polygons[i].boundary.intersection(polygons[j].boundary).length,j) for j in neighbors]
        if lengths:
            _,length,j=max(lengths)
            if length>0:
                a,b=find(i),find(j);parent[a]=b;group_area[b]+=group_area[a];merged+=1
    groups={}
    for i,p in enumerate(polygons):groups.setdefault(find(i),[]).append(p)
    output=[unary_union(group) for group in groups.values()]
    output.sort(key=lambda p:(-round(p.centroid.y,3),round(p.centroid.x,3)))
    union=unary_union(output)
    tolerance=max(1e-6,extent.area*1e-9)
    if abs(union.area-extent.area)>tolerance or abs(sum(p.area for p in output)-union.area)>tolerance:
        raise ValueError('Block partition fails extent coverage/non-overlap check')
    return output,dict(raw_faces=len(polygons),blocks=len(output),merged_slivers=merged,
                       cut_segments=len(get_parts(cuts)),dangle_segments=len(get_parts(dangles)),
                       invalid_rings=len(get_parts(invalid)),extent_area_m2=extent.area,
                       partition_area_m2=union.area,precision_m=precision,min_merge_area_m2=min_area)


def build(config,roads=None,road_layer='roads',min_area=None,scale='detail'):
    from .geo_runtime import configure
    configure()
    from osgeo import gdal,ogr,osr
    from shapely import from_wkb
    from shapely.geometry import box,LineString
    from .build_heat_water_resilience import read_band
    from .provenance import sha256
    gdal.UseExceptions();ogr.UseExceptions()
    reference,heat,_=read_band(config.output_dir/'heat_persistence_risk_30m.tif')
    _,water,_=read_band(config.output_dir/'water_risk_normalized_30m.tif')
    _,exposure,_=read_band(config.output_dir/'building_function_exposure_30m.tif')
    _,transition,_=read_band(config.input_path('transition'))
    gt=reference.GetGeoTransform();width,height=reference.RasterXSize,reference.RasterYSize
    extent=box(gt[0],gt[3]+height*gt[5],gt[0]+width*gt[1],gt[3])
    if scale not in {'detail','overview'}:raise ValueError('Unknown block scale')
    if min_area is None:min_area=200000 if scale=='overview' else 8100
    classes=OVERVIEW_CLASSES if scale=='overview' else SURFACE_CLASSES
    dest=config.derived_dir/('blocks_overview' if scale=='overview' else 'blocks');dest.mkdir(parents=True,exist_ok=True)
    lines=[];excluded=0;outside=0;source_count=0
    roads=Path(roads).resolve() if roads else config.inputs.get('block_roads')
    if config.synthetic and not roads:
        for col in (13,31):
            x=gt[0]+col*gt[1];lines.append(LineString([(x,extent.bounds[1]),(x,extent.bounds[3])]))
        for row in (14,27):
            y=gt[3]+row*gt[5];lines.append(LineString([(extent.bounds[0],y),(extent.bounds[2],y)]))
        source_count=len(lines)
    else:
        if not roads:raise ValueError('Real blocks require --roads or inputs.block_roads')
        dataset=ogr.Open(str(roads));layer=dataset.GetLayerByName(road_layer) if dataset else None
        if layer is None:raise ValueError('Road layer not found: '+road_layer)
        if layer.GetLayerDefn().GetFieldIndex('highway')<0:
            raise ValueError('Road layer requires a highway classification field')
        source_srs=layer.GetSpatialRef()
        if source_srs is None:raise ValueError('Road CRS is required')
        target=osr.SpatialReference();target.ImportFromEPSG(config.grid['epsg'])
        source_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        target.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        transform=osr.CoordinateTransformation(source_srs,target)
        for feature in layer:
            source_count+=1
            tags=dict(re.findall(r'"([^"\s]+)"=>"([^"]*)"',feature.GetField('other_tags') or '')) if feature.GetFieldIndex('other_tags')>=0 else {}
            highway=feature.GetField('highway') if feature.GetFieldIndex('highway')>=0 else None
            grade=any(tags.get(k,'no') not in {'no','false','0',''} for k in ('bridge','tunnel')) or tags.get('layer','0') not in {'0',''}
            if highway not in classes or grade:excluded+=1;continue
            geom=feature.GetGeometryRef()
            if geom is None:excluded+=1;continue
            geom=geom.Clone();geom.Transform(transform)
            line=from_wkb(bytes(geom.ExportToWkb())).intersection(extent)
            if not line.is_empty:lines.append(line)
            else:outside+=1
        dataset=None
    if not lines:raise ValueError('No eligible surface roads intersect the reference extent')
    polygons,diag=partition_blocks(lines,extent,min_area)
    srs=osr.SpatialReference();srs.ImportFromEPSG(config.grid['epsg'])
    memory=ogr.GetDriverByName('Memory').CreateDataSource('blocks')
    layer=memory.CreateLayer('blocks',srs,ogr.wkbUnknown)
    layer.CreateField(ogr.FieldDefn('block_id',ogr.OFTInteger))
    for i,p in enumerate(polygons,1):
        feature=ogr.Feature(layer.GetLayerDefn());feature.SetField('block_id',i)
        feature.SetGeometry(ogr.CreateGeometryFromWkb(p.wkb));layer.CreateFeature(feature)
    raster=gdal.GetDriverByName('MEM').Create('',width,height,1,gdal.GDT_UInt32)
    raster.SetGeoTransform(gt);raster.SetProjection(reference.GetProjection())
    raster.GetRasterBand(1).SetNoDataValue(0)
    gdal.RasterizeLayer(raster,[1],layer,options=['ATTRIBUTE=block_id'])
    ids=raster.ReadAsArray()
    if np.any(ids==0):raise ValueError('Partition leaves raster centers unassigned')
    gdal.GetDriverByName('GTiff').CreateCopy(str(dest/'block_ids_30m.tif'),raster,options=['COMPRESS=DEFLATE'])
    rows=summarize_blocks(ids,heat,water,exposure,transition,
                          config.parameters['heat_weight'],config.parameters['zone_threshold'])
    # Some geometric slivers may contain no raster center; retain them explicitly.
    by_id={r['id']:r for r in rows}
    for i in range(1,len(polygons)+1):
        if i not in by_id:
            blank=summarize_blocks(np.array([i],dtype='u4'),np.array([-9999.]),np.array([-9999.]),np.array([-9999.]),np.array([0]))[-1]
            blank['total_pixels']=0;rows.append(blank)
    rows.sort(key=lambda r:r['id'])
    features=[]
    gpkg=dest/'road_blocks.gpkg'
    if gpkg.exists():ogr.GetDriverByName('GPKG').DeleteDataSource(str(gpkg))
    output=ogr.GetDriverByName('GPKG').CreateDataSource(str(gpkg))
    out_layer=output.CreateLayer('road_blocks',srs,ogr.wkbUnknown)
    for name,kind in [('block_id',ogr.OFTInteger),('label',ogr.OFTString),('valid_px',ogr.OFTInteger),('both_share',ogr.OFTReal),('area_km2',ogr.OFTReal)]:
        out_layer.CreateField(ogr.FieldDefn(name,kind))
    for p,row in zip(polygons,rows):
        i=row['id'];name=f'片区 P{i:04d}' if scale=='overview' else f'街区 B{i:04d}'
        edge=p.boundary.intersection(extent.boundary).length>0
        row.update(name=name,geometry_area_km2=p.area/1e6,valid_area_km2=row['valid_pixels']*gt[1]**2/1e6,
                   boundary_cut=edge,low_support=row['valid_pixels']<9,partial_coverage=row['coverage']<.8)
        f=ogr.Feature(out_layer.GetLayerDefn());f.SetField('block_id',i);f.SetField('label',name)
        f.SetField('valid_px',row['valid_pixels']);f.SetField('area_km2',p.area/1e6)
        if row['both_share'] is not None:f.SetField('both_share',row['both_share'])
        f.SetGeometry(ogr.CreateGeometryFromWkb(p.wkb));out_layer.CreateFeature(f)
        simple=p.simplify(2,preserve_topology=True)
        pieces=list(simple.geoms) if simple.geom_type=='MultiPolygon' else [simple]
        rings=[[[[round((x-gt[0])/gt[1],3),round((y-gt[3])/gt[5],3)] for x,y in ring.coords]
                for ring in [piece.exterior,*piece.interiors]] for piece in pieces]
        bounds=[(p.bounds[0]-gt[0])/gt[1],(p.bounds[3]-gt[3])/gt[5],
                (p.bounds[2]-gt[0])/gt[1],(p.bounds[1]-gt[3])/gt[5]]
        features.append(dict(id=i,name=name,polygons=rings,bounds=bounds,
                             geometry_area_km2=row['geometry_area_km2'],boundary_cut=edge))
    output=None
    with (dest/'block_summary.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    diag.update(synthetic=config.synthetic,scale=scale,merge_strategy='current-group-area-aware',source_features=source_count,used_road_features=len(lines),
                excluded_features=excluded,outside_extent_features=outside,source_file=roads.name if roads else 'generated synthetic road lines',
                source_sha256=sha256(roads) if roads else None,road_layer=road_layer,
                included_highway_classes=sorted(classes),grade_separated_excluded=True,
                grade_filter_scope='explicit bridge/tunnel/nonzero layer tags; untagged crossings may remain',
                assigned_valid_pixels=sum(r['valid_pixels'] for r in rows),
                low_support_blocks=sum(r['low_support'] for r in rows),
                edge_blocks=sum(r['boundary_cut'] for r in rows),
                valid_blocks=sum(r['valid_pixels']>0 for r in rows),
                sampling='one owner per raster center; not fractional polygon area',
                geometry_simplification_m=2,low_support_pixel_threshold=9,
                width=width,height=height,geotransform=gt,
                raster_hashes={key:sha256(config.output_dir/name) for key,name in
                               [('heat','heat_persistence_risk_30m.tif'),('water','water_risk_normalized_30m.tif'),
                                ('exposure','building_function_exposure_30m.tif')]})
    (dest/'diagnostics.json').write_text(json.dumps(diag,ensure_ascii=False,indent=2),encoding='utf-8')
    browser=dict(version=1,features=features,diagnostics=diag,
                 ids=base64.b64encode(ids.astype('<u4').tobytes()).decode('ascii'))
    (dest/'blocks_browser.json').write_text(json.dumps(browser,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(json.dumps(diag,ensure_ascii=True))
    return dest


def main():
    from .project_config import load_project_config
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--roads',type=Path)
    parser.add_argument('--road-layer',default='roads')
    parser.add_argument('--min-area',type=float,default=None)
    parser.add_argument('--scale',choices=('detail','overview'),default='detail',
                        help='Overview excludes residential/unclassified roads and targets 0.2 km² merging; detail targets 8100 m²')
    args=parser.parse_args()
    if args.min_area is not None and args.min_area<0:parser.error('--min-area must not be negative')
    build(load_project_config(args.config),args.roads,args.road_layer,args.min_area,args.scale)


if __name__=='__main__':main()
