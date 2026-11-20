# 北京中心城区地表温度样例

这个离线样例展示真实卫星影像如何进入 Heatwater。两景覆盖同一北京中心样区，每景可单独查看。切换日期后点击 4×4 显示网格，可读取该统计单元的有效像元数、均值和温度范围。CSV 包含两景的全部 32 条网格记录。

## 数据与处理

| 观测日 | Landsat Collection 2 Level-2 场景 | 质控后覆盖 |
|---|---|---:|
| 2014-08-19 | LC08_L2SP_123032_20140819_02_T1 | 99.87% |
| 2023-07-19 | LC09_L2SP_123032_20230719_02_T1 | 99.89% |

样区为 116.34–116.48°E、39.87–39.97°N，输出对齐至 EPSG:32650 的 30 米采样网格。使用 QA_PIXEL 位 0–5、QA_RADSAT 和温度 NoData 过滤像元，按 Landsat 产品比例系数和偏移量换算摄氏度。色带共享 30–55 °C 显示范围，范围外显示端点颜色，CSV 保留实际统计值。页面内嵌温度保留到 0.01 °C，该位数是存储精度。

天气、季节内日期和观测条件都可能影响两景温度。样例的统计单元是规则网格。热水联合筛查、建筑用途暴露与 72 组参数分析可通过长春方法说明和公开模拟体验查看。

温度来源为 USGS Landsat Collection 2 Level-2 Surface Temperature，影像目录使用 Microsoft Planetary Computer。请引用 USGS 的 Landsat 8/9 Collection 2 Level-2 数据集。[数据来源、比例系数说明与引用](https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-temperature)

## 本地构建

先准备同一网格的质控后摄氏度 GeoTIFF 与场景清单。清单的 `scenes` 中逐景记录 `scene`、`file` 和 `valid_count`。在有 GDAL 的 Python 环境中运行：

```sh
python -m scripts.build_temperature_demo --report artifacts/china-city-pilot/beijing/verification.json --output artifacts/releases/v0.1.0-candidate/heatwater-beijing-temperature.html
```

生成的单文件 HTML 可以直接用浏览器打开。数据目录保留在本地工作区，首版候选发布附件内嵌本样区的温度值。
