import importlib.util
import unittest
import numpy as np
from scripts.blocks import summarize_blocks, partition_blocks


class BlockStatisticsTests(unittest.TestCase):
    def test_valid_pixel_conservation_and_distinct_denominators(self):
        labels=np.array([[1,1,2],[1,0,2]],dtype=np.uint32)
        heat=np.array([[.8,.2,.9],[.9,-9999,.1]],dtype=np.float32)
        water=np.array([[.8,.9,.2],[.9,-9999,.2]],dtype=np.float32)
        exposure=np.array([[1,0,.7],[.5,-9999,0]],dtype=np.float32)
        transition=np.array([[2,1,2],[1,0,1]])
        rows=summarize_blocks(labels,heat,water,exposure,transition,.55,.67)
        self.assertEqual(sum(r['valid_pixels'] for r in rows),5)
        self.assertEqual(rows[0]['both_pixels'],2)
        self.assertAlmostEqual(rows[0]['both_share'],2/3)
        self.assertEqual(rows[0]['high_exposure_pixels'],1)
        self.assertAlmostEqual(rows[1]['expansion_share'],.5)
        changed=summarize_blocks(labels,heat,water,exposure,transition,.7,.67)
        self.assertEqual([r['both_pixels'] for r in rows],[r['both_pixels'] for r in changed])
        self.assertNotEqual(rows[0]['compound_mean'],changed[0]['compound_mean'])

    def test_missing_ownership_is_rejected(self):
        a=np.ones((2,2),dtype=np.float32)*.5
        with self.assertRaisesRegex(ValueError,'unassigned'):
            summarize_blocks(np.zeros((2,2),dtype=np.uint32),a,a,a,a,.55,.67)

    def test_coverage_uses_all_owned_centers(self):
        a=np.array([[.5,-9999]],dtype=np.float32)
        rows=summarize_blocks(np.ones((1,2),dtype=np.uint32),a,a,a,a,.55,.67)
        self.assertEqual(rows[0]['valid_pixels'],1)
        self.assertEqual(rows[0]['total_pixels'],2)
        self.assertEqual(rows[0]['coverage'],.5)


@unittest.skipUnless(importlib.util.find_spec('shapely'),'Optional Shapely required')
class BlockTopologyTests(unittest.TestCase):
    def test_partition_covers_extent_without_overlap_and_reports_dangle(self):
        from shapely.geometry import LineString, box
        from shapely.ops import unary_union
        polygons,diag=partition_blocks([LineString([(50,0),(50,100)]),
                                       LineString([(20,20),(30,20)])],box(0,0,100,100),min_area=0)
        self.assertEqual(len(polygons),2)
        self.assertAlmostEqual(sum(p.area for p in polygons),10000)
        self.assertAlmostEqual(unary_union(polygons).area,10000)
        self.assertGreater(diag['dangle_segments']+diag['cut_segments'],0)

    def test_sliver_is_merged_by_shared_boundary(self):
        from shapely.geometry import LineString, box
        polygons,diag=partition_blocks([LineString([(1,0),(1,100)])],box(0,0,100,100),min_area=900)
        self.assertEqual(len(polygons),1)
        self.assertAlmostEqual(polygons[0].area,10000)
        self.assertEqual(diag['merged_slivers'],1)

    def test_merging_stops_once_current_groups_reach_target_area(self):
        from shapely.geometry import LineString,box
        lines=[LineString([(x,0),(x,100)]) for x in range(50,400,50)]
        polygons,_=partition_blocks(lines,box(0,0,400,100),min_area=9000)
        self.assertGreaterEqual(len(polygons),3)
        self.assertTrue(all(p.area>=9000 for p in polygons))
        self.assertAlmostEqual(sum(p.area for p in polygons),40000)
