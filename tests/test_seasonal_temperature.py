import unittest

import numpy as np

from scripts.seasonal_temperature import composite_by_day


class SeasonalTemperatureTests(unittest.TestCase):
    def test_same_date_scenes_fill_gaps_without_double_weighting(self):
        scenes = [
            ("LC08_L2SP_123033_20140702_02_T1", np.array([[90., 24., np.nan]])),
            ("LC08_L2SP_123032_20140702_02_T1", np.array([[30., -9999., -9999.]])),
            ("LC08_L2SP_123032_20140718_02_T1", np.array([[40., 26., 22.]])),
            ("LC08_L2SP_123032_20140803_02_T1", np.array([[35., np.nan, -9999.]])),
        ]
        temperature, days, dates = composite_by_day(scenes, minimum=2)
        np.testing.assert_array_equal(days, [[3, 2, 1]])
        np.testing.assert_array_equal(temperature, [[35., 25., -9999.]])
        self.assertEqual(dates, ["2014-07-02", "2014-07-18", "2014-08-03"])

    def test_all_masked_dates_do_not_count_as_observed(self):
        temperature, days, dates = composite_by_day([
            ("LC08_L2SP_123032_20140702_02_T1", np.array([[-9999., np.nan]])),
        ])
        np.testing.assert_array_equal(days, [[0, 0]])
        np.testing.assert_array_equal(temperature, [[-9999., -9999.]])
        self.assertEqual(dates, [])
