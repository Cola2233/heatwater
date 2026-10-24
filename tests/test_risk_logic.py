import unittest

import numpy as np

from scripts.risk_logic import (
    classify_exposure_priority,
    classify_compound_risk,
    combine_risk,
    robust_minmax,
)


class RiskLogicTests(unittest.TestCase):
    def test_robust_minmax_ignores_nodata(self):
        values = np.array([[1.0, 2.0], [3.0, -9999.0]], dtype=np.float32)
        valid = values != -9999.0

        result = robust_minmax(values, valid, low_percentile=0, high_percentile=100)

        np.testing.assert_allclose(result[valid], [0.0, 0.5, 1.0])
        self.assertTrue(np.isnan(result[~valid]).all())

    def test_combine_risk_preserves_invalid_cells(self):
        heat = np.array([[0.0, 1.0], [0.5, 0.5]], dtype=np.float32)
        water = np.array([[1.0, 0.0], [0.5, 0.5]], dtype=np.float32)
        valid = np.array([[True, True], [True, False]])

        result = combine_risk(heat, water, valid, heat_weight=0.6, water_weight=0.4)

        np.testing.assert_allclose(result[0, :], [0.4, 0.6])
        self.assertTrue(np.isnan(result[1, 1]))

    def test_compound_risk_has_four_action_zones(self):
        heat = np.array([[0.2, 0.8], [0.2, 0.8]], dtype=np.float32)
        water = np.array([[0.2, 0.2], [0.8, 0.8]], dtype=np.float32)
        valid = np.ones_like(heat, dtype=bool)

        result = classify_compound_risk(heat, water, valid, threshold=0.6)

        np.testing.assert_array_equal(result, [[1, 2], [3, 4]])

    def test_exposure_priority_separates_high_risk_and_high_exposure(self):
        compound = np.array([[0.8, 0.8], [0.2, 0.2]], dtype=np.float32)
        exposure = np.array([[0.8, 0.2], [0.8, 0.2]], dtype=np.float32)
        valid = np.ones_like(compound, dtype=bool)

        result = classify_exposure_priority(compound, exposure, valid, compound_threshold=0.6, exposure_threshold=0.6)

        np.testing.assert_array_equal(result, [[1, 2], [3, 4]])


if __name__ == "__main__":
    unittest.main()
