# 热水共治 · Heatwater

Heatwater 是一个基于遥感的城市片区筛查项目。它把地表热环境、水涝代理和建筑功能暴露放在同一张地图上，帮助研究者判断哪些片区值得优先核查，以及这个判断对权重和阈值有多敏感。

**Heatwater is a reproducible remote-sensing workflow for screening urban heat, waterlogging proxies, and building-use exposure.** It connects raster processing, road-based spatial units, and interactive sensitivity analysis in an offline map.

## 项目维护与协助

Rin（[Cola2233](https://github.com/Cola2233)）负责研究选题、数据与方法判断，并维护项目。[OpenAI Codex](https://github.com/codex) 作为 AI 编程助手，协助实现离线地图与城市演示、核对测试、整理文档和打包发布。

## 城市案例

| 案例 | 可以看到什么 |
|---|---|
| [长春四环研究案例](cases/changchun/README.md) | 51 个主干路片区和 30 米采样网格，支持片区解释、72 组权重与阈值的敏感性分析、核查清单导出。真实数据在本地运行。 |
| [北京真实温度样例](cases/beijing/README.md) | 两景公开 Landsat 地表温度，经过质量掩膜和网格对齐。可切换日期、点击 16 个统计格和导出 CSV。 |
| 公开模拟体验 | 9 个模拟片区，可离线走完选区、调参、检查入选频率和导出清单。[图文教程与视频说明](docs/quickstart-zh.md) |

从[城市案例目录](cases/README.md)查看各城市的进度、方法和附件。每个案例有独立入口，可以随数据和分析进度更新。

![北京公开 Landsat 温度样例，右侧显示所选网格的统计](docs/assets/beijing-temperature.png)

**体验入口**。在 [v0.1.0 发布页](https://github.com/Cola2233/heatwater/releases/tag/v0.1.0) 下载 `heatwater-quickstart-zh.zip`。解压后用 Edge 或 Chrome 打开 `heatwater-research-demo.html`，包内还有图文教程和 70 秒中文字幕演示。各城市案例页列出可下载的真实温度样例。代码与模拟数据采用 MIT 许可。

项目包含遥感栅格处理、道路分区、片区汇总、筛查条件解释及交互导出。地图展示使用 MapLibre，分区方法借鉴 Laisen-geo。[方法与适用范围](docs/methods.md) · [开源组件用法](docs/open-source-pilot.md) · [八城扩展计划](docs/china-city-cases.md)

## 先试用，再决定是否安装

| 你想做什么 | 从这里开始 | 需要什么 |
|---|---|---|
| 看地图、调整权重和阈值 | 下载仓库，双击 [website/index.html](website/index.html) | 支持 JavaScript 的桌面浏览器 |
| 分享一个离线演示文件 | 运行下方打包命令，发送生成的 HTML | Python 3.11+，无需 GDAL |
| 运行栅格处理链 | [完整复现指南](docs/reproducibility.md) | Python、GDAL、NumPy、Matplotlib |
| 修复问题或贡献功能 | [贡献指南](CONTRIBUTING.md) | 对应 Python 或 Node 开发环境 |

下载仓库ZIP后请先解压；GitHub的源码预览不会直接执行HTML。
Node/Playwright仅用于开发检查，使用网页不需要npm install。

### 生成可分享的公开演示

从仓库根目录执行：

```sh
python -m scripts.build_single_html --output artifacts/releases/heatwater-demo.html
```

默认仅嵌入公开模拟案例。把生成的HTML发给别人，对方用浏览器打开即可。
长春真实数据版本需要显式选择本地入口，见 [网页说明](website/README.md)。

### 运行完整模拟工作流

```sh
conda env create -f environment.yml
conda activate heatwater
python -m scripts.synthetic_case --directory demo
python -m scripts.run_pipeline --config demo/config.json
python -m scripts.validate_outputs --config demo/config.json
```

生成器要求使用新目录。完整流程输出20项必需成果及校验清单。
安装包同时提供heatwater-demo、heatwater、heatwater-validate命令；
GDAL需要单独通过Conda或QGIS环境提供。

## 它能做什么

- 将两期LST与水涝代理对齐到参考网格，在共同有效区域计算相对分数。
- 分别判断热、水分量是否偏高，输出四类治理分区与连续复合分数。
- 叠加新增不透水面及建筑功能，查看候选核查区域。
- 输出GeoTIFF、CSV、图件、参数敏感性结果与SHA-256清单。
- 在离线地图中查看原始分析网格，切换图层、探索参数并导出结果。
- 可选道路围合街区，汇总均值、双高占比与建筑暴露，保留像元不足和边界截断标记。

默认热/水权重为0.55/0.45，分量和复合高分阈值为0.67。
改变权重会改变连续复合分数；四类分区由热、水分量各自的阈值决定。
网页操作不会改写Python成果或原始栅格。

## 使用自己的数据

复制config/example.json为config/local.json，填写输入路径、单位、建筑字段与输出目录。
输入契约见 [data/README.md](data/README.md)。当前实现沿用长春案例的30米、EPSG:32651网格约束，
时间窗口、输出命名和地图文案仍有案例特征，尚不是任意城市的通用适配器。

```sh
python -m scripts.run_pipeline --config config/local.json
```

真实数据及其衍生图表按来源许可管理，不随公开模拟演示分发。
数据获取状态与许可见 [DATA_LICENSE.md](DATA_LICENSE.md)。

## 适用范围

本工具用于研究性空间筛查。水涝层是代理指标，尚未用独立积水观测校准；
LST不等于气温，建筑功能暴露不等于人口。长春的两期夏季合成窗口也不是逐年温度序列。
目前不提供工程内涝预报或干预效果预测。详见 [方法](docs/methods.md) 与 [解释边界](docs/limitations.md)。

## 开发与检查

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
node --test website/tests/core.test.cjs website/tests/dataset.test.cjs
```

没有GDAL时集成测试会跳过，纯算法与打包测试仍能运行。
可选端到端浏览器检查不依赖真实数据：

```sh
npm ci
npx playwright install chromium
python -m scripts.build_single_html --output artifacts/releases/heatwater-demo.html
npm run test:browser
```

设置HEATWATER_PUBLIC_BUNDLE=artifacts/releases/heatwater-demo.html可同时检查单文件。
环境变量写法、已有Edge的使用方式与贡献流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 项目导航

| 位置 | 内容 |
|---|---|
| scripts/ | 配置、算法、GIS处理、制图、校验、模拟数据和网页打包 |
| website/ | 无构建依赖的离线地图、公开模拟栅格及前端测试 |
| tests/ | Python单元与GDAL集成测试 |
| config/example.json | 可移植的配置模板 |
| docs/ | 方法、数据字典、架构、复现与维护文档 |
| .github/ | CI与问题模板 |

- [架构](docs/architecture.md) / [数据字典](docs/data_dictionary.md) / [路线图](docs/roadmap.md)
- [版本变更](CHANGELOG.md) / [发布流程](docs/publishing.md) / [贡献指南](CONTRIBUTING.md)
- [代码许可](LICENSE) / [数据许可](DATA_LICENSE.md) / [引用信息](CITATION.cff)

在线演示地址、GitHub CI结果、正式Release和DOI仅在实际创建后补充。
