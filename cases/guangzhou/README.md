# 广州中心样区 · Landsat 地表温度

[返回城市案例](../README.md)

离线地图展示公开 Landsat 的单景地表温度。用浏览器打开后可点击 16 个规则网格，查看均值、温度范围与有效像元数，并下载 CSV。
[下载广州离线地图](https://github.com/Cola2233/heatwater/releases/download/v0.1.0/heatwater-guangzhou-temperature.html)

样区为 113.24–113.36°E、23.09–23.18°N。影像对齐至 EPSG:32649 的 30 米采样网格。

| 观测日期 | USGS 场景 | 掩膜后有效覆盖 |
|---|---|---:|
| 2023-06-02 | LC08_L2SP_122044_20230602_02_T1 | 82.62% |

这是中心城区样区的初步温度案例。天气和观测日期会影响单景值。质控方法沿用[温度样例流程](../../docs/beijing-temperature-demo.md)。[场景清单](scenes.json) · [USGS 产品说明与引用](https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-temperature)
