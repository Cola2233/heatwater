# Heatwater 城市案例

每个城市有一个案例页，记录研究区、数据日期、分析能力和交付状态。遥感处理和地图组件统一维护在主项目中。案例可以单独增加数据、图层和下载附件。

| 城市 | 当前成果 | 获取方式 |
|---|---|---|
| [长春四环](changchun/README.md) | 51 个主干路片区，热水联合筛查与参数稳定性 | 公开方法和结果说明，交互地图本地运行 |
| [北京中心样区](beijing/README.md) | 2 景 Landsat 地表温度，16 个统计格 | [离线 HTML](https://github.com/Cola2233/heatwater/releases/download/v0.1.0/heatwater-beijing-temperature.html) |
| [天津中心样区](tianjin/README.md) | 1 景 Landsat 地表温度，16 个统计格 | [离线 HTML](https://github.com/Cola2233/heatwater/releases/download/v0.1.0/heatwater-tianjin-temperature.html) |
| [上海](shanghai/README.md) | Landsat 数据初筛 | 场景统计与准备说明 |
| [广州中心样区](guangzhou/README.md) | 1 景 Landsat 地表温度，16 个统计格 | [离线 HTML](https://github.com/Cola2233/heatwater/releases/download/v0.1.0/heatwater-guangzhou-temperature.html) |
| [深圳中心样区](shenzhen/README.md) | 1 景 Landsat 地表温度，16 个统计格 | [离线 HTML](https://github.com/Cola2233/heatwater/releases/download/v0.1.0/heatwater-shenzhen-temperature.html) |
| [香港](hong-kong/README.md) | Landsat 数据初筛 | 场景统计与准备说明 |
| [台北](taipei/README.md) | Landsat 数据初筛 | 场景统计与准备说明 |

想体验完整交互流程，可以从[模拟案例教程](../docs/quickstart-zh.md)开始。[其余城市的准备计划](../docs/china-city-cases.md)

## 添加或更新城市

1. 在 `cases/<city>/README.md` 写明研究范围、观测日期、坐标系与采样网格、分析单元、数据来源和许可。
2. 记录当前支持的图层、统计和筛查功能。已有构建命令或案例配置放在该目录链接中，处理逻辑由主项目维护。
3. 验证该案例的地图、导出和数据覆盖。若改动共用算法，同时用长春和模拟案例检查既有结果。
4. 将验证后的离线文件作为案例附件发布，在案例页记录对应版本和更新内容，再从本页加入入口。城市所需的原始输入可按其许可从上游获取。

各城市可以按各自进度交付。相同指标在城市之间对比时，应核对时期、分辨率、归一化和空间单元。
