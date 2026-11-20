# 道路推导街区

街区功能将同一套原始栅格汇总到道路围合的分析单元。它是可复现的道路推导结果，
不是官方街道、社区或地籍边界。界面沿用已选定的城市图谱布局。

## 片区概览与细街区

当前真实案例默认使用528个概览单元，其中526个含有效观测。地图上方“分区粒度”可切回
保留的2304个细街区；原始像元视图继续可用。概览不使用residential、unclassified、living_street
单独细分，采用motorway、trunk、primary、secondary、tertiary道路线网与0.2平方公里目标合并面积。
邻接小单元合并时根据当前组面积判断，已达到目标的组不会再主动按原始小面大小继续串联合并。
目标面积是合并启发式，不是每个单元面积的硬下限。外围道路缺失、断线或稀疏仍可形成大范围单元。

| 尺度 | 单元数 | 几何面积中位数 | 小于0.05平方公里 |
|---|---:|---:|---:|
| 保留的细街区 | 2304 | 0.0398 km² | 1297 |
| 当前概览 | 528 | 0.2837 km² | 32 |

概览生成到derived_dir/blocks_overview/，不会覆盖原来的blocks/。
公开模拟案例目前只包含细街区示例；粒度选择仅在至少两种尺度存在时显示。

```sh
python -m scripts.blocks --config config/local.json --scale overview
python -m scripts.export_web_data --config config/local.json
```

网页导出器优先选择概览，并将其他尺度的轮廓和像元归属一并嵌入，复用相同的热、水与暴露数组。
尺度切换不改变全域统计，CSV包含block_scale字段。保留的2304细街区是前一合并算法的历史结果；
用新版组面积约束重新生成细街区时，单元数和编号可能改变，应以相应诊断文件为准。

## 生成与更新

先完成模拟处理流程，再生成公开示例：

```sh
python -m scripts.blocks --config demo/config.json
python -m scripts.export_web_data --config demo/config.json
```

模拟案例的四条道路线与九个街区均为程序生成，并不表示真实城区。
真实案例显式提供本地道路库；下面路径由使用者替换：

```sh
python -m scripts.blocks --config config/local.json --roads data/external/roads.gpkg --road-layer roads
python -m scripts.export_web_data --config config/local.json
python -m scripts.build_single_html --entry website/local.html --output artifacts/share/changchun.html
```

也可在本地配置的inputs中设置block_roads路径。安装包命令为heatwater-blocks。
处理需要Shapely 2和GDAL；Conda环境已列入依赖。街区是可选步骤，原处理链不要求道路。
网页导出发现街区输入网格或热、水、暴露栅格指纹已变化时会报错，要求重新生成街区。

## 输入约定

- 道路库须声明CRS，可转换到参考EPSG:32651；默认图层名roads。
- highway字段为必需，使用OSM风格道路分类；other_tags为可选的桥隧/层级标签。
- 采用motorway、trunk、primary、secondary、tertiary、residential、unclassified、living_street。
- 排除其他道路类型，包括步道、服务路与匝道；明确标记为桥、隧道或非零layer的线不参与面化。
- 缺少桥隧标签不等于道路必在地面。数据完整性与断头路会影响划分粒度，不能从道路自动得到官方街区名称。

## 划分方法

道路转换、裁剪至分析栅格矩形范围，与范围边界一起建立平面线网。
先将坐标相对参考网格原点平移，再使用0.5米精度网格节点化、面化。
Shapely的[union_all](https://shapely.readthedocs.io/en/latest/reference/shapely.unary_union.html)
提供精度网格合并；[polygonize_full](https://shapely.readthedocs.io/en/stable/reference/shapely.polygonize_full.html)
同时返回多边形及未成面的线段诊断。

默认将小于8100平方米的面按最长公共边归并，减少双线道路中线和匝道残留形成的碎片。
可用--min-area调整，但这会改变划分和编号；8100平方米不是自然街区面积标准。
每次生成均验证多边形合并面积与分析范围一致、没有正面积重叠。
未闭合线、断头线与非法环数量写入诊断文件，不能声称所有路口均已恢复。

编号按几何中心由北向南、由西向东排序。同一输入版本可复现，更新道路或参数后编号可能变化。
边界处单元会被分析范围截断，另有boundary_cut标记。较大单元可能源自稀疏或未闭合道路，
不能据此认定其内部不存在更小的实际街区。

## 统计口径

使用未简化几何，将每个原始30米像元中心分配给一个街区。共同有效像元的定义与core.js及Python原流程一致。

| 字段 | 定义 |
|---|---|
| total_pixels | 几何包含的栅格中心数，包括无效观测 |
| valid_pixels | 热、水、暴露均在0–1的有限值像元数 |
| coverage | valid_pixels / total_pixels |
| valid_area_km2 | valid_pixels × 900 / 1000000 |
| geometry_area_km2 | 街区多边形面积；与像元统计面积不同 |
| heat_mean / water_mean / compound_mean / exposure_mean | 共同有效像元的对应分数均值 |
| both_share | 热、水分别达到当前阈值的像元数 / valid_pixels |
| high_exposure_share | 复合分数达到当前阈值且暴露≥0.6的像元数 / valid_pixels |
| expansion_share | 转换编码为2的有效像元数 / valid_pixels |

不采用ALL_TOUCHED或按几何相交面积分摊。同一像元不会被多个街区重复计数。
没有有效像元的单元均值为null，不能伪装成低风险零值。
阈值比较和复合运算使用Float32口径，与既有浏览器分析一致。

有效像元不足9个、有效覆盖不足80%会分别标记。默认列表隐藏这些单元，选择“所有有数据街区”可查看。
这些规则用于展示筛选，不是估计精度或街区真实性保证。地图轮廓简化2米，仅用于显示；统计不使用简化轮廓。

## 输出与界面

生成到配置derived_dir下的blocks/目录：

- road_blocks.gpkg：街区矢量及基础统计字段。
- block_ids_30m.tif：像元归属编号，UInt32，与原始网格一致。
- block_summary.csv：当前配置基线的完整统计。
- diagnostics.json：源道路指纹、筛选/面化诊断、参数和有效像元总数。
- blocks_browser.json：供网页导出器嵌入的轮廓和归属数组。

网页支持街区/原始像元切换；现有六个图层在街区模式下分别显示均值或占比。
点击色块可看下方详情；点击列表或定位按钮会缩放并回到地图。
搜索、覆盖筛选、指标降序、分页与CSV导出均在本地执行。CSV导出当前筛选下的全部街区，
不局限于当前页；均值与比例随权重、阈值重新计算。

## 初版细街区验证（2026-11-02，历史保留）

17712条源道路要素中，3293条符合筛选且与研究范围相交。
4045个初始面合并1741个小碎片后，得到2304个推导单元，全部有有效像元。
34个单元有效像元不足9个，83个单元被研究范围边界截断。
仍有24条cut segments与1312条dangle segments，已保留诊断，不作为已修复路口报告。

全部436411个共同有效像元恰好归属一个单元；双高像元和高分高暴露像元加总与原成果一致。
Python与浏览器逐街区的计数完全一致，均值/占比误差小于1e-7。
真实与模拟数据分开导出，真实道路衍生成果仍保留在本地，不进入公开模拟案例。
