# 参考Laisen-geo的主干路片区

2026-11-06：MapLibre真实案例预览改为51个主干路片区。此前528个概览分区将矩形分析外框一起围合，外围出现大面，不适合作为直观的城市片区。此次重做空间单元与真实边界裁切；原始30米科学分析成果和Canvas正式入口仍保留。

## 参考与实现

参考[Laisen-geo BRIEF.md](https://github.com/BillyAshlet/Laisen-geo/blob/main/BRIEF.md)的200米网格、快速路/主干路/河流围合、小块合并思路。该项目说明中的长春案例约51块。使用本地同一份four_ring_200m_handoff道路、WorldCover和study_area数据，使用SciPy连通域、距离变换及GDAL栅格化实现，没有复制上游应用源码。仓库核验时未见LICENSE；本地真实数据不随公开源码分发。

快速路和主干路排除匝道；ALL_TOUCHED栅格化形成200米道路屏障，河流与真实城区外部也是屏障。四邻域连通区内按开放格数统计面积，小于30格（1.2平方公里）的小块合并至相邻较大块，最多70块为合并目标；河流屏障不被合并跨越。阈值是分区尺度设定，不是热水风险参数。

此次得到76个原始连通区，合并25次后为51块；使用890条道路，排除730条匝道。不是为了固定凑成51块而改变结果。

道路、水体像元通过最近片区确定唯一统计归属，地图另画实际道路与水体。分区格网200米，热/水/暴露统计仍采用30米像元；不能解释为精确到地籍的街区边界。形状与尺度用于规划片区探索，不代表行政街道。

## 分析范围变化

先生成200米片区，再映射至30米统计网格，以真实四环边界像元中心掩膜裁切，边界外不参加统计，也不生成外围矩形街区。

| 项目 | 旧矩形范围 | 新真实四环范围 |
|---|---:|---:|
| 共同有效像元 | 436411 | 325978 |
| 有效分析面积（平方公里） | 392.7699 | 293.3802 |
| 默认分量双高像元 | 58741 | 48818 |
| 默认分量双高面积（平方公里） | 52.8669 | 43.9362 |

新版分区总范围299.3661平方公里，部分像元输入无效，因此有效面积较小。排除原矩形范围中四环外110433个共同有效像元。此次数值变化来自真实范围裁切，不能直接将前后面积差解释为环境变化。

新范围内51块均满足数据支持要求，默认候选32块，其中14块在至少80%的72组参数组合下入选。这些是探索性筛查结果，入选频率不是灾害概率。

## 复现与检查

需要GDAL、NumPy和SciPy环境；QGIS附带Python可用时直接使用。handoff路径由本地提供：

```powershell
python -m scripts.planning_blocks --handoff <four_ring_200m_handoff目录>
python -m scripts.build_maplibre_prototype --data artifacts/planning-blocks/planning-browser.js --output artifacts/opensource-pilot/changchun-maplibre.html
python -m unittest tests.test_planning_blocks
node website/maplibre-lab/check.cjs
node website/maplibre-lab/research-check.cjs
```

MapLibre依赖安装及--vendor参数见[接入实验](open-source-pilot.md)。规划单元生成器只用于这个本地真实案例，不改变公开模拟案例的九个单元。

生成目录含30米唯一归属栅格、浏览器载荷和来源SHA-256记录。检查覆盖外部不分配、道路分隔、小块合并、河流阻隔、确定性、无开放格报错，以及浏览器道路显隐、点击、调参、解释、稳定性筛选和CSV。
