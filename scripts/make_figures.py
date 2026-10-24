"""Render presentation figures for the heat-water compound-risk products."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .geo_runtime import configure
configure()

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
from osgeo import gdal, ogr

gdal.UseExceptions()

VECTORS = None

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Noto Sans CJK JP", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def read_raster(path: Path) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    dataset = gdal.Open(str(path), gdal.GA_ReadOnly)
    if dataset is None:
        raise RuntimeError(f"Cannot open {path}")
    band = dataset.GetRasterBand(1)
    array = band.ReadAsArray().astype(np.float32)
    nodata = band.GetNoDataValue()
    if nodata is not None:
        array[array == nodata] = np.nan
    gt = dataset.GetGeoTransform()
    extent = (gt[0], gt[0] + dataset.RasterXSize * gt[1], gt[3] + dataset.RasterYSize * gt[5], gt[3])
    return array, extent


def draw_geometry(ax, geometry, color: str, linewidth: float, alpha: float) -> None:
    name = geometry.GetGeometryName().upper()
    if name in {"LINESTRING", "LINEARRING"}:
        points = geometry.GetPoints()
        if points:
            xs, ys = zip(*[(point[0], point[1]) for point in points])
            ax.plot(xs, ys, color=color, linewidth=linewidth, alpha=alpha, zorder=5)
        return
    if name == "POLYGON":
        for index in range(geometry.GetGeometryCount()):
            draw_geometry(ax, geometry.GetGeometryRef(index), color, linewidth, alpha)
        return
    for index in range(geometry.GetGeometryCount()):
        draw_geometry(ax, geometry.GetGeometryRef(index), color, linewidth, alpha)


def draw_context(ax) -> None:
    if VECTORS is None or not VECTORS.exists():
        return
    dataset = ogr.Open(str(VECTORS), 0)
    if dataset is None:
        return
    for layer_name, color, linewidth, alpha in [
        ("city_boundary", "#17324d", 1.0, 0.8),
        ("waterways", "#2d9cdb", 0.6, 0.65),
        ("major_roads", "#666666", 0.25, 0.35),
    ]:
        layer = dataset.GetLayerByName(layer_name)
        if layer is None:
            continue
        layer.ResetReading()
        for feature in layer:
            geometry = feature.GetGeometryRef()
            if geometry is not None:
                draw_geometry(ax, geometry, color, linewidth, alpha)
    dataset = None


def add_map_decor(ax, extent) -> None:
    x_min, x_max, y_min, y_max = extent
    bar_x0 = x_min + 0.05 * (x_max - x_min)
    bar_y = y_min + 0.06 * (y_max - y_min)
    bar_length = min(5000.0, (x_max - x_min) * 0.25)
    ax.plot([bar_x0, bar_x0 + bar_length], [bar_y, bar_y], color="#202020", linewidth=3, solid_capstyle="butt", zorder=8)
    ax.text(bar_x0, bar_y + 0.02 * (y_max - y_min), "0", fontsize=8, color="#202020")
    ax.text(bar_x0 + bar_length, bar_y + 0.02 * (y_max - y_min), f"{bar_length/1000:g} km", fontsize=8, ha="right", color="#202020")
    ax.text(x_max - 0.05 * (x_max - x_min), y_max - 0.07 * (y_max - y_min), "N↑", fontsize=14, ha="right", color="#17324d")
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#17324d")
        spine.set_linewidth(0.8)


def plot_continuous(ax, array, extent, title, cmap, label):
    image = ax.imshow(array, extent=extent, origin="upper", cmap=cmap, vmin=0, vmax=1)
    draw_context(ax)
    add_map_decor(ax, extent)
    ax.set_title(title, fontsize=13, loc="left", color="#17324d", pad=8)
    return image


def plot_compound(ax, array, extent, title):
    colors = ["#e8f5e9", "#ef6c5b", "#42a5f5", "#6a1b9a"]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm([1, 2, 3, 4, 5], cmap.N)
    image = ax.imshow(array, extent=extent, origin="upper", cmap=cmap, norm=norm)
    draw_context(ax)
    add_map_decor(ax, extent)
    ax.set_title(title, fontsize=13, loc="left", color="#17324d", pad=8)
    return image


def plot_priority(ax, array, extent, title):
    colors = ["#ffffff", "#7b1fa2", "#ef6c5b", "#66bb6a"]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)
    image = ax.imshow(array, extent=extent, origin="upper", cmap=cmap, norm=norm)
    draw_context(ax)
    add_map_decor(ax, extent)
    ax.set_title(title, fontsize=13, loc="left", color="#17324d", pad=8)
    return image


def main(config) -> None:
    global OUTPUTS, FIGURES, VECTORS
    OUTPUTS, FIGURES = config.output_dir, config.figure_dir
    VECTORS = config.inputs.get("context_vectors")
    FIGURES.mkdir(parents=True, exist_ok=True)
    heat, extent = read_raster(OUTPUTS / "heat_persistence_risk_30m.tif")
    water, _ = read_raster(OUTPUTS / "water_risk_normalized_30m.tif")
    compound, _ = read_raster(OUTPUTS / "compound_action_zones_30m.tif")
    priority, _ = read_raster(OUTPUTS / "new_impervious_compound_priority_30m.tif")
    human_zones, _ = read_raster(OUTPUTS / "human_exposure_priority_zones_30m.tif")

    fig, axes = plt.subplots(2, 2, figsize=(14, 11), constrained_layout=True)
    fig.get_layout_engine().set(rect=(0, 0.045, 1, 0.95))
    fig.suptitle("SYNTHETIC DEMO — NOT OBSERVATIONS" if config.synthetic else
                 "热水共治：长春四环城市热—涝复合风险诊断", fontsize=20, color="#17324d", weight="bold")
    heat_im = plot_continuous(axes[0, 0], heat, extent, "A  多年夏季持续热风险", "YlOrRd", "热风险")
    water_im = plot_continuous(axes[0, 1], water, extent, "B  水涝风险（研究性代理指标）", "Blues", "水涝风险")
    plot_compound(axes[1, 0], compound, extent, "C  热—涝复合治理分区")
    plot_priority(axes[1, 1], priority, extent, "D  新增不透水面治理优先级")

    fig.colorbar(heat_im, ax=axes[0, 0], fraction=0.035, pad=0.02, label="标准化风险（0—1）")
    fig.colorbar(water_im, ax=axes[0, 1], fraction=0.035, pad=0.02, label="标准化风险（0—1）")
    axes[1, 0].legend(
        handles=[
            Patch(facecolor="#e8f5e9", label="低热低涝—生态协同"),
            Patch(facecolor="#ef6c5b", label="高温治理优先"),
            Patch(facecolor="#42a5f5", label="水涝治理优先"),
            Patch(facecolor="#6a1b9a", label="热涝双高—综合治理"),
        ],
        loc="upper left",
        fontsize=8,
        framealpha=0.9,
    )
    axes[1, 1].legend(
        handles=[
            Patch(facecolor="#7b1fa2", label="新增不透水面+热涝双高"),
            Patch(facecolor="#ef6c5b", label="新增不透水面+单项高风险"),
            Patch(facecolor="#66bb6a", label="新增不透水面+低风险"),
        ],
        loc="upper left",
        fontsize=8,
        framealpha=0.9,
    )
    fig.text(0.02, 0.015, "Synthetic 30 m inputs; demonstration only." if config.synthetic else
             "统一分析网格：30 m；热环境为2013—2015与2021—2023夏季合成；水涝层用于空间筛查，不替代工程内涝预报。",
             fontsize=9, color="#4d6b7a")
    fig.savefig(FIGURES / "01_heat_water_compound_dashboard.png", dpi=260, bbox_inches="tight")
    plt.close(fig)

    single_maps = [
        (heat, "热风险", "heat_persistence_risk_map.png", "YlOrRd", "多年夏季持续热风险"),
        (water, "水涝风险", "water_risk_map.png", "Blues", "水涝风险（研究性代理指标）"),
    ]
    for array, label, filename, cmap, title in single_maps:
        fig, ax = plt.subplots(figsize=(10, 8))
        if config.synthetic:
            fig.suptitle("SYNTHETIC DEMO — NOT OBSERVATIONS", fontsize=12)
        image = plot_continuous(ax, array, extent, title, cmap, label)
        fig.colorbar(image, ax=ax, fraction=0.035, pad=0.02, label="标准化风险（0—1）")
        fig.text(0.01, 0.01, "Synthetic 30 m grid." if config.synthetic else "统一分析网格：30 m；四环范围。", fontsize=9, color="#4d6b7a")
        fig.savefig(FIGURES / filename, dpi=260, bbox_inches="tight")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 8))
    if config.synthetic:
        fig.suptitle("SYNTHETIC DEMO — NOT OBSERVATIONS", fontsize=12)
    human_colors = ["#ffffff", "#7b1fa2", "#ef6c5b", "#43a047", "#cfd8dc"]
    human_cmap = ListedColormap(human_colors)
    human_norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5, 4.5], human_cmap.N)
    ax.imshow(human_zones, extent=extent, origin="upper", cmap=human_cmap, norm=human_norm)
    draw_context(ax)
    add_map_decor(ax, extent)
    ax.set_title("重点人群与公共服务暴露优先级", fontsize=16, loc="left", color="#17324d", pad=10)
    ax.legend(
        handles=[
            Patch(facecolor="#7b1fa2", label="复合高风险+高暴露：重点保护"),
            Patch(facecolor="#ef6c5b", label="复合高风险+低暴露：环境治理"),
            Patch(facecolor="#43a047", label="低复合风险+高暴露：持续监测"),
            Patch(facecolor="#cfd8dc", label="一般关注"),
        ],
        loc="upper left",
        bbox_to_anchor=(0.01, 0.99),
        fontsize=9,
        framealpha=0.92,
    )
    fig.text(0.01, 0.01, "暴露代理由住宅、教育、医疗和公共服务建筑功能构成；不等同于人口普查数量。", fontsize=9, color="#4d6b7a")
    fig.savefig(FIGURES / "02_human_exposure_priority.png", dpi=260, bbox_inches="tight")
    plt.close(fig)

    print(f"Figures written to: {FIGURES}")


if __name__ == "__main__":
    import argparse
    from .project_config import load_project_config
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    main(load_project_config(parser.parse_args().config))
