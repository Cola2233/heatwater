# 开源组件接入实验

实验运行于2026-11-04，整理于2026-11-05。目标是在真实长春数据上验证道路简化与地图引擎的接入成本。现有正式单文件和全城分区保留，以下为独立原型。

2026-11-06已在MapLibre预览上加入[片区解释与参数稳定性](explanation-stability.md)。下文启动比较记录的是加入这些功能前的原型，不作为新版本性能数据。

## MapLibre：可离线交互的真实数据原型

使用MapLibre GL JS 6.16.0，复用本项目的热水计算、片区统计与参数差异模块。原型包含528个概览片区和2304个细分单元，共同有效像元仍为436411个。默认双高面积52.8669平方公里，网页显示52.87。

验证项目：离线打开、悬停数值、点击选中、权重调整后的地图变化、阈值调整、上一步对比、两级尺度切换、CSV下载、移动端布局。浏览器检查未发现JavaScript错误，HTTP请求为0。未加载在线底图、字体或瓦片。

原型文件为`artifacts/opensource-pilot/changchun-maplibre.html`，约16.61 MB。坐标从分析网格的完整仿射变换投影至WGS84，保留多面及孔洞；面积和统计仍采用原始分析网格，不以网页显示投影计算面积。

### 启动开销

同机离线、1440×1000、无头Edge软件WebGL环境，两个入口交替运行，各3次：

| 指标 | 现有Canvas单文件 | MapLibre原型 |
|---|---:|---:|
| 文件字节数 | 13,635,410 | 16,608,511 |
| 启动中位数 | 1648 ms | 2152 ms |

两种引擎的就绪条件不同，这只是近似启动比较，不能推断交互帧率或其他机器性能。当前证据支持其交互功能可接入，但不支持“启动更快”的结论。后续整合应权衡引擎开销与维护收益。

## neatnet：减少小面，但需要检查连通性

使用neatnet 0.1.6，在长春中心城区3×3公里样区实验，外围增加600米处理缓冲。两组沿用相同地面道路筛选和核心范围；13528个建筑面作为排除掩膜。比较未经面积合并的原始面，避免后处理阈值掩盖差异。

| 指标 | 原始道路 | neatnet道路 |
|---|---:|---:|
| 原始分割面数量 | 518 | 478 |
| 小于8100平方米的面 | 276 | 230 |
| 面积中位数（平方米） | 7368.06 | 8560.25 |
| 悬挂线段数（dangles） | 52 | 59 |
| cut线段数 | 0 | 0 |
| 分区总面积（平方公里） | 9 | 9 |
| 有效像元覆盖数 | 9990 | 9990 |

小面数量下降约16.7%，有效像元覆盖保持一致，但悬挂线段增加。不能将面数量减少等同于街区划分更准确；边界截断及局部拓扑变化还需核查。因此当前仅保留为可选预处理实验，不自动替换正式全城分区。neatnet调用约17.77秒，不包含数据读取与绘图。

对照图、报告、指标和GeoPackage保存在`artifacts/opensource-pilot/`：`neatnet-comparison.html`、`neatnet-comparison.png`、`neatnet-results.json`、`pilot.gpkg`。

## urban-heat：借鉴工程分层

阅读了[urban-heat](https://github.com/damienallen/urban-heat)的项目配置与[compose.yml](https://github.com/damienallen/urban-heat/blob/main/compose.yml)。其服务、界面、MongoDB分离部署，对本项目的启发是保持计算、数据契约和展示模块独立。这是工程结构判断；本实验没有复制其AGPL代码，也没有引入数据库或在线后端。当前离线交付目标无需完整搬入其服务架构。

## 复现

以下命令从仓库根目录运行。真实数据需要本地`config/local.json`及`website/data/local.js`，不包含在公开仓库中；路径和数据许可见数据说明。道路实验使用独立Python环境，不升级QGIS附带环境。

```powershell
python -m venv artifacts/neatnet-env
artifacts/neatnet-env/Scripts/python -m pip install -r experiments/neatnet-requirements.txt
artifacts/neatnet-env/Scripts/python -m scripts.neatnet_pilot --config config/local.json --output artifacts/opensource-pilot

npm ci --prefix website/maplibre-lab --ignore-scripts
npm run bundle --prefix website/maplibre-lab
python -m scripts.build_maplibre_prototype --data website/data/local.js --vendor website/maplibre-lab --output artifacts/opensource-pilot/changchun-maplibre.html

npm ci
node website/maplibre-lab/check.cjs
node website/maplibre-lab/benchmark.cjs
```

生成MapLibre原型的Python需要GDAL/OSR，可使用本项目Conda环境或QGIS Python；省略`--data`生成公开模拟案例。浏览器检查脚本当前针对真实长春基线，在Windows使用已安装Edge，其他平台需要Playwright Chromium。完整Python依赖冻结记录位于本次本地实验输出`neatnet-requirements.lock.txt`；地图开发依赖由独立package-lock.json锁定。

MapLibre主程序和Worker打包后内嵌HTML，Worker通过本地Blob加载。MapLibre 6的Worker类型识别与实际IIFE经典脚本格式匹配；不需要关闭浏览器安全检查。MapLibre许可证内嵌于原型，并同时输出`MapLibre-LICENSE.txt`。依赖仍分别遵守其上游许可。

## 当前决策

- MapLibre保留为下一阶段整合候选，先评审真实地图交互，再决定正式入口迁移。
- neatnet继续作为可选实验；扩大样区并检查连通性后再决定全城应用。
- 保持自有计算核心与显示引擎分离，保持真实数据和公开模拟数据的交付边界。

原始验证记录：`maplibre-check.json`、`startup-comparison.json`、`neatnet-results.json`。所有真实实验产物位于被Git忽略的`artifacts/`下。
