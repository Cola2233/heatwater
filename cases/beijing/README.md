# 北京中心城区 · Landsat 地表温度

[返回城市案例](../README.md)

北京样例把两景真实 Landsat 温度影像接入 Heatwater。下载后用浏览器打开，切换日期、点击 16 个统计格，即可查看温度范围并导出 CSV。[下载北京离线地图](https://github.com/Cola2233/heatwater/releases/download/v0.1.0/heatwater-beijing-temperature.html)

| 项目 | 内容 |
|---|---|
| 样区 | 116.34–116.48°E、39.87–39.97°N |
| 观测日期 | 2014-08-19、2023-07-19 |
| 坐标系与网格 | EPSG:32650，30 米采样，16 个规则统计格 |
| 实现范围 | 单景地表温度查看、像元统计与导出 |

![北京地表温度图和所选网格统计](../../docs/assets/beijing-temperature.png)

完整场景编号、质量掩膜、USGS 署名和构建命令见[北京样例方法](../../docs/beijing-temperature-demo.md)。

[北京场景清单](scenes.json) · [从公开影像重建该案例](../../docs/rebuild-temperature-case.md)

## 两期夏季合成

v0.2.0 增加 2013–2015 年和 2021–2023 年的并排地表温度合成。分析范围限定在中心城区样区内的 2021 年建成地表。两期分别使用 7 和 9 个有效观测日，建成地表中 99.91% 的像元在两期都达到至少 3 个观测日。

![北京中心样区两期夏季地表温度对照，共用温标并同步选点](../../docs/assets/beijing-summer-built-up.png)

图中浅灰为 2021 年建成地表掩膜外区域。左右两图使用同一温标，选框标记同一像元。

[下载离线对照地图](https://github.com/Cola2233/heatwater/releases/download/v0.2.0/beijing-summer-temperature.html) · [下载 GeoTIFF、掩膜和清单](https://github.com/Cola2233/heatwater/releases/download/v0.2.0/beijing-summer-results.zip) · [合成方法与复算命令](../../docs/beijing-summer-composite.md)
