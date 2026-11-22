# 从公开 Landsat 场景重建城市温度地图

七个已发布的城市温度样例都带有 `cases/<city>/scenes.json`。清单记录固定的 USGS 场景、研究范围、投影、采样间距和已验证的有效像元数。使用已安装 GDAL 的项目环境，从仓库根目录运行：

```sh
python -m scripts.prepare_temperature_case --case cases/beijing/scenes.json --output artifacts/temperature-rebuild/beijing
```

把 `beijing` 换成 `tianjin`、`shanghai`、`guangzhou`、`shenzhen`、`hong-kong` 或 `taipei` 可以重建对应案例。重建时需要网络访问 Microsoft Planetary Computer。命令读取温度和质量波段的样区窗口，剔除缺值、云及云影等像元，再生成摄氏度 GeoTIFF、`verification.json` 和独立的离线 HTML。若尺寸或有效像元数与清单不符，命令会报出实际值供复核，避免把变化后的结果当成原样例交付。每次重建使用新的输出目录。

更新城市时，可以在清单中加入已核实的新场景。新场景至少填 `scene`，第一次重建后从 `verification.json` 把实际宽高和有效像元数写回该场景记录。页面按清单顺序显示各观测日。样例展示的是逐景温度，共用显示色带，取样日期和天气条件会影响城市间比较。

下载完成后，用浏览器直接打开 HTML。查看温度图、选择统计格、下载 CSV 均可离线进行。已有对齐且完成质控的 GeoTIFF 时，可以沿用[本地 HTML 打包方法](beijing-temperature-demo.md)跳过网络读取。

Windows 上如 GDAL 无法使用系统信任根，可传入 `--ca-bundle` 指向受信任的证书包。保留 HTTPS 证书验证。

波段语义和温度换算见 [USGS 质量波段](https://www.usgs.gov/landsat-missions/landsat-collection-2-quality-assessment-bands)和 [Collection 2 比例系数](https://www.usgs.gov/faqs/how-do-i-use-a-scale-factor-landsat-level-2-science-products)。
