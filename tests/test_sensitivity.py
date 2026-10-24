import unittest
import numpy as np
from scripts.sensitivity_analysis import sweep
from scripts.risk_logic import combine_risk, classify_compound_risk

class SensitivityTests(unittest.TestCase):
    def test_baseline_and_independent_weight_threshold_effects(self):
        h = np.array([[0.2, 0.8], [0.4, np.nan]], dtype=np.float32)
        w = np.array([[0.8, 0.2], [0.9, 0.5]], dtype=np.float32)
        valid = np.isfinite(h)
        results = sweep(h, w, valid)
        baseline = next(r for r in results if r["heat_weight"] == 0.55 and r["threshold"] == 0.67)
        np.testing.assert_array_equal(baseline["zones"], classify_compound_risk(h,w,valid))
        np.testing.assert_allclose(baseline["compound"], combine_risk(h,w,valid), equal_nan=True)
        for r in results:
            self.assertEqual(r["zones"][1,1], 0)
            self.assertTrue(np.isnan(r["compound"][1,1]))
        same_threshold = [r for r in results if r["threshold"] == 0.67]
        self.assertTrue(all(np.array_equal(r["zones"], baseline["zones"]) for r in same_threshold))
        self.assertFalse(np.allclose(same_threshold[0]["compound"], same_threshold[-1]["compound"],equal_nan=True))
