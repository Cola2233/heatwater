import importlib.util
import unittest
import numpy as np
from scripts.planning_blocks import delineate

@unittest.skipUnless(importlib.util.find_spec('scipy'),'Optional scipy required for planning units')
class PlanningBlockTests(unittest.TestCase):
    def test_roads_cut_real_domain_and_outside_stays_unassigned(self):
        domain=np.zeros((12,12),bool);domain[1:11,1:11]=True
        road=np.zeros_like(domain);road[:,6]=True
        ids,diag=delineate(domain,road,np.zeros_like(domain),min_cells=1,max_blocks=70)
        self.assertEqual(diag['blocks'],2)
        self.assertTrue(np.all(ids[domain]>0));self.assertTrue(np.all(ids[~domain]==0))
        self.assertNotEqual(ids[5,3],ids[5,9])

    def test_slivers_merge_but_not_across_river_and_results_are_deterministic(self):
        domain=np.ones((16,16),bool);road=np.zeros_like(domain);road[:,2]=True;road[:,7]=True
        river=np.zeros_like(domain);river[8,:]=True
        a,diag=delineate(domain,road,river,min_cells=40,max_blocks=4)
        b,_=delineate(domain,road,river,min_cells=40,max_blocks=4)
        np.testing.assert_array_equal(a,b)
        self.assertLessEqual(diag['blocks'],4)
        top=set(a[:8].ravel());bottom=set(a[9:].ravel());self.assertFalse(top&bottom)

    def test_no_open_cells_fails_instead_of_creating_fake_partition(self):
        d=np.ones((4,4),bool)
        with self.assertRaisesRegex(ValueError,'open'):
            delineate(d,d,np.zeros_like(d))
