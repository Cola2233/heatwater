# 北京中心样区的两期夏季地表温度

本案例并排查看北京中心城区样区内、2021 年建成地表上的 2013–2015 年和 2021–2023 年晴空夏季地表温度。每期提供温度中位数和有效观测日数。点选同一位置可同时查看两期结果。

## 影像筛选与合成

外框为 116.34–116.48°E、39.87–39.97°N。Landsat 8/9 Collection 2 Level-2 Tier 1 地表温度数据统一到 EPSG:32650 的 402×373 网格，采样间距为 30 米。影像的有效空间细节仍由热红外传感器决定。

在外框内，以 [ESA WorldCover 2021 v200](https://doi.org/10.5281/zenodo.7254221) 的建成地表类别（代码 50）限定分析范围。用最近邻将分类采样到温度网格，保留像元中心对应类别为 50 的 115,791 个采样像元，占样区 77.22%，约 104.21 km²。两期共用此掩膜。早期图反映 2021 年建成地表位置在早期的温度。这一定义仅涵盖指定的中心城区样区。

对每年 6–8 月按月挑选目录整景云量最低的一景，要求整景云量 ≤65%，场景足迹覆盖样区至少 95%。没有符合条件的月份不补值。通过温度缺值、QA_PIXEL 位 0–5 和 QA_RADSAT 进行像元级过滤。2014-06-16 的候选场景过滤后无有效像元，因此排除。完整场景和排除记录见[合成清单](../cases/beijing/summer-scenes.json)。

同日多个场景先拼接成一次观测。重叠处按场景编号排序，取第一个质控有效的值。每个像元对达到 3 个有效日期的观测取中位数，低于门槛的温度像元标为缺值，同时保留原始有效日数。

| 指标 | 2013–2015 年夏季 | 2021–2023 年夏季 |
|---|---:|---:|
| 有建成地表有效像元的观测日 | 7 | 9 |
| 掩膜内逐像元有效日数的中位数 | 6 | 5 |
| 至少 3 个有效日期的覆盖 | 99.92% | 99.93% |

两期同时达到门槛的有 115,690 个采样像元，占掩膜内 99.91%。两期的晴空日期、月份分布与天气条件不同，合成图适合观察所选影像的空间格局。长期趋势或城市化归因需要另行控制日期、天气与采样差异。

## 复算

从仓库根目录使用已安装 GDAL 的 Python。先下载场景，再将公开土地覆盖分类对齐至第一景温度网格。以下命令以 PowerShell 为例：

```powershell
python -m scripts.prepare_temperature_case --case cases/beijing/summer-scenes.json --rasters-only --output artifacts/beijing-summer-scenes
$reference = (Get-ChildItem artifacts/beijing-summer-scenes/*.tif | Select-Object -First 1).FullName
python -m scripts.build_built_up_mask --reference "$reference" --output artifacts/beijing-built-up-mask.tif
python -m scripts.seasonal_temperature --case cases/beijing/summer-scenes.json --rasters artifacts/beijing-summer-scenes --domain-mask artifacts/beijing-built-up-mask.tif --output artifacts/beijing-summer-composite
```

最后一条命令生成两期温度 GeoTIFF、两期有效观测次数 GeoTIFF、`summary.json` 和 `summer-temperature.html`。观测次数图以 65535 为掩膜外缺值，掩膜内的 0 表示有效观测为零。用浏览器打开 HTML 即可离线查看。WorldCover 网络读取若遇到本机证书问题，可以从 [ESA 数据入口](https://esa-worldcover.org/en/data-access)下载 N39E114 图块，再以 `--worldcover <本地 GeoTIFF>` 指定该文件。

© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium。WorldCover 数据使用 CC BY 4.0，案例附带的衍生掩膜保留该署名。

数据及质控说明见 [USGS Landsat 地表温度](https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-temperature)和 [USGS 质量波段](https://www.usgs.gov/landsat-missions/landsat-collection-2-quality-assessment-bands)。
