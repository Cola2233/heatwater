import unittest
from scripts.build_maplibre_prototype import project_features

class ProjectionTests(unittest.TestCase):
    def test_pixel_rings_use_full_affine_transform_and_keep_holes(self):
        meta={'geotransform':[100,30,2,200,3,-30]}
        source=[{'id':7,'name':'test','polygons':[[[[0,0],[2,0],[2,2],[0,0]],[[.5,.5],[1,.5],[.5,1],[.5,.5]]]]}]
        out=project_features(meta,source,lambda x,y:(x/100,y/100))
        feature=out['features'][0]
        self.assertEqual(feature['id'],7)
        self.assertEqual(feature['geometry']['type'],'MultiPolygon')
        self.assertEqual(len(feature['geometry']['coordinates'][0]),2)
        self.assertEqual(feature['geometry']['coordinates'][0][0][1],[1.6,2.06])
        self.assertEqual(source[0]['polygons'][0][0][1],[2,0])
