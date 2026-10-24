"""Pure NumPy logic for the Changchun heat-water compound-risk workflow."""

from __future__ import annotations

import numpy as np


def robust_minmax(
    values: np.ndarray,
    valid: np.ndarray,
    *,
    low_percentile: float = 5.0,
    high_percentile: float = 95.0,
) -> np.ndarray:
    """Scale valid finite cells to 0-1 using robust percentile limits."""
    values = np.asarray(values, dtype=np.float32)
    valid = np.asarray(valid, dtype=bool) & np.isfinite(values)
    if not (0 <= low_percentile < high_percentile <= 100):
        raise ValueError("percentiles must satisfy 0 <= low < high <= 100")
    if not np.any(valid):
        raise ValueError("valid mask contains no finite cells")

    result = np.full(values.shape, np.nan, dtype=np.float32)
    sample = values[valid]
    low = float(np.percentile(sample, low_percentile))
    high = float(np.percentile(sample, high_percentile))
    if high <= low:
        result[valid] = 0.0
        return result

    result[valid] = np.clip((values[valid] - low) / (high - low), 0.0, 1.0)
    return result


def combine_risk(
    heat_risk: np.ndarray,
    water_risk: np.ndarray,
    valid: np.ndarray,
    *,
    heat_weight: float = 0.55,
    water_weight: float = 0.45,
) -> np.ndarray:
    """Combine normalized heat and water risks, preserving invalid cells."""
    if heat_weight < 0 or water_weight < 0 or heat_weight + water_weight <= 0:
        raise ValueError("risk weights must be non-negative and not both zero")
    total = heat_weight + water_weight
    heat_weight /= total
    water_weight /= total

    heat_risk = np.asarray(heat_risk, dtype=np.float32)
    water_risk = np.asarray(water_risk, dtype=np.float32)
    valid = (
        np.asarray(valid, dtype=bool)
        & np.isfinite(heat_risk)
        & np.isfinite(water_risk)
    )
    result = np.full(heat_risk.shape, np.nan, dtype=np.float32)
    result[valid] = heat_weight * heat_risk[valid] + water_weight * water_risk[valid]
    return result


def classify_compound_risk(
    heat_risk: np.ndarray,
    water_risk: np.ndarray,
    valid: np.ndarray,
    *,
    threshold: float = 0.67,
) -> np.ndarray:
    """Return action-zone codes: 1 low-low, 2 heat, 3 water, 4 heat-water."""
    if not 0 < threshold < 1:
        raise ValueError("threshold must be between 0 and 1")
    heat_risk = np.asarray(heat_risk, dtype=np.float32)
    water_risk = np.asarray(water_risk, dtype=np.float32)
    valid = (
        np.asarray(valid, dtype=bool)
        & np.isfinite(heat_risk)
        & np.isfinite(water_risk)
    )
    result = np.zeros(heat_risk.shape, dtype=np.uint8)
    heat_high = heat_risk >= threshold
    water_high = water_risk >= threshold
    result[valid] = 1 + heat_high[valid].astype(np.uint8) + 2 * water_high[valid].astype(np.uint8)
    return result


def classify_exposure_priority(
    compound_risk: np.ndarray,
    exposure_risk: np.ndarray,
    valid: np.ndarray,
    *,
    compound_threshold: float = 0.67,
    exposure_threshold: float = 0.6,
) -> np.ndarray:
    """Classify compound-risk cells by public-service/building exposure.

    Codes: 1 high-risk/high-exposure, 2 high-risk/low-exposure,
    3 low-risk/high-exposure, 4 low-risk/low-exposure, 0 invalid.
    """
    if not 0 < compound_threshold < 1 or not 0 < exposure_threshold < 1:
        raise ValueError("classification thresholds must be between 0 and 1")
    compound_risk = np.asarray(compound_risk, dtype=np.float32)
    exposure_risk = np.asarray(exposure_risk, dtype=np.float32)
    valid = (
        np.asarray(valid, dtype=bool)
        & np.isfinite(compound_risk)
        & np.isfinite(exposure_risk)
    )
    result = np.zeros(compound_risk.shape, dtype=np.uint8)
    compound_high = compound_risk >= compound_threshold
    exposure_high = exposure_risk >= exposure_threshold
    result[valid & compound_high & exposure_high] = 1
    result[valid & compound_high & ~exposure_high] = 2
    result[valid & ~compound_high & exposure_high] = 3
    result[valid & ~compound_high & ~exposure_high] = 4
    return result


ZONE_LABELS = {
    0: "无效区",
    1: "低热低涝—生态协同区",
    2: "高温治理优先区",
    3: "水涝治理优先区",
    4: "热涝双高—综合治理区",
}

EXPOSURE_ZONE_LABELS = {
    0: "无效区",
    1: "重点人群与公共服务保护区",
    2: "环境治理优先区",
    3: "公共服务暴露监测区",
    4: "一般关注区",
}
