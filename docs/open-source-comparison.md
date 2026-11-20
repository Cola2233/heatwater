# 相关开源项目筛选

核验日期：2026-11-04。检查范围为GitHub仓库元数据、README及必要的许可/配置文件；未安装运行这些项目。
后续已完成neatnet样区实验和MapLibre真实数据原型，见[接入实验结果](open-source-pilot.md)；下文保留初次筛选时的范围与判断。
以下接入优先级为针对本项目的工程判断，不表示性能或模型精度已验证。

| 项目 | 可复用能力 | 仓库标注许可 | 对当前项目的用途 |
|---|---|---|---|
| [damienallen/urban-heat](https://github.com/damienallen/urban-heat) | 欧洲城市热岛交互展示，带前后端结构 | AGPL-3.0 | 最接近完整应用的参照；研究界面、数据组织与部署，不能只换城市名称 |
| [uscuni/neatnet](https://github.com/uscuni/neatnet) | 道路几何简化，处理双线道路、环岛等交通几何 | BSD-3-Clause | 优先做街区质量对照实验，比较与现有道路面化/合并方法的差异 |
| [pysal/momepy](https://github.com/pysal/momepy) | 城市形态、建筑与街网指标 | BSD-3-Clause | 后续补建筑密度、形状、空间关系等片区解释指标 |
| [maplibre/maplibre-gl-js](https://github.com/maplibre/maplibre-gl-js) | GPU加速的网页地图引擎 | BSD-3-Clause，已核对LICENSE.txt | 作为地图交互底层的候选；仍需处理坐标、离线资源与现有统计联动 |
| [opengeos/leafmap](https://github.com/opengeos/leafmap) | Python交互地图、矢量/栅格加载、分屏与联动地图 | MIT | 适合快速研究原型、Notebook工具；不能直接等同于现有单文件离线网页 |
| [UMEP-dev/UMEP](https://github.com/UMEP-dev/UMEP) | QGIS城市气候敏感规划工具集 | GPL-3.0 | 未来物理过程与规划情景扩展的参照，需要对应模型输入 |
| [Deltares/SFINCS](https://github.com/Deltares/SFINCS) | 动态复合洪水建模 | 源码GPL-3.0；官方预编译程序另有条款 | 水涝物理模拟的长期候选，不是直接替换当前代理分数的现成模块 |

## 推荐次序

1. 用neatnet在一小块长春道路上做对照，检查碎片数、面积分布、闭合性和像元覆盖；通过后再接入正式处理。
2. 用MapLibre做同一批片区数据的地图原型，比较悬停、选中、视图切换、离线打包和性能，保留当前单文件作为回退。
3. 阅读urban-heat的完整工程组织，借鉴应用结构与数据管线。它的pyproject.toml包含Python后端，仓库也有app、Dockerfile和compose.yml，迁移成本高于地图库。
4. 将本项目自有价值集中在热水复合规则、建筑暴露、片区汇总、参数对比、验证及复现。

没有在本次筛选中发现经过核验、能够直接复现本项目“长春热水复合筛查＋建筑暴露＋多尺度片区＋离线单文件”的完整替代项目。
这是本轮检索结论，不代表GitHub不存在其他相近项目。

## 核验记录

- neatnet、momepy、leafmap、UMEP、urban-heat和MapLibre查询时均未归档；已读取GitHub公开仓库元数据。
- MapLibre的API许可识别为NOASSERTION，因此另读[LICENSE.txt](https://github.com/maplibre/maplibre-gl-js/blob/main/LICENSE.txt)，确认为主项目BSD三条款文本。
- urban-heat的README仅简短介绍交互展示；技术判断额外依据[pyproject.toml](https://github.com/damienallen/urban-heat/blob/main/pyproject.toml)与根目录文件。
- SFINCS依据[README.rst](https://github.com/Deltares/SFINCS/blob/main/README.rst)，源码和官方预编译程序的许可条件分别说明。
- 复用时保留各组件的许可、版权和引用信息，按实际选用版本检查；不将不同上游代码统一标记成本项目MIT。
