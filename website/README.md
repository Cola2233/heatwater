# 城市韧性观测台 · HTML 预览

本目录是无构建步骤、无 CDN、可离线打开的静态网页。

## 设计规范

当前采用用户选定的 C 城市风险图谱，并融合 A 的紧凑分析总览、B 的集中参数操作。
布局为深色主地图与浅色结论区，下方展示分区构成、热水联合分布与建筑暴露。
设计依据与验证见 [融合实现记录](../docs/design-atlas-final.md)。
字体使用本机中英文字体，不请求外部字体或在线地图，单文件可离线使用。

## 单文件分享

把页面、样式、脚本和全部地图数据嵌入一个 HTML：

```sh
python -m scripts.build_single_html --output artifacts/releases/heatwater-demo.html
```

将生成的 HTML 单独发送给朋友即可，不需要附带目录或开启服务器。
对方先保存文件，再用 Edge、Chrome 或其他现代浏览器打开。
以上默认使用公开模拟案例。生成本地长春真实数据文件时，显式使用
`--entry website/local.html --output artifacts/share/changchun.html`。
真实成果单文件包含真实栅格的浏览器数据；它属于本地分享成果，
不会自动纳入公开 Git 仓库。部分聊天软件的内置预览不执行 JavaScript，
这种情况下请下载后在系统浏览器中打开。

## 预览

直接在浏览器中打开 index.html，即为公开模拟案例。或者从项目根目录运行：

```sh
python -m http.server 8765 --bind 127.0.0.1 --directory website
```

浏览器访问 http://127.0.0.1:8765/index.html。

地图支持六个图层、滚轮/按钮缩放、拖动平移、悬停像元查询。
键盘聚焦地图后，可用 +/- 缩放、方向键平移、0 复位。
参数滑块更新面积统计，可下载 PNG、分区 CSV 与探索参数 JSON。
包含街区数据时默认显示道路街区；可切回原始像元。点击色块查看下方详情，
若包含概览尺度，则优先显示片区概览；地图上方“分区粒度”可切回细街区。
支持编号搜索、覆盖筛选、指标排序、分页及街区CSV导出。详见 [街区方法与生成步骤](../docs/blocks.md)。
JSON 标记 exploration_only，不能直接替代 Python 运行配置。

## 使用本地长春成果

先运行完整 Python 流程，再导出：

```sh
python -m scripts.run_pipeline --config config/local.json
python -m scripts.export_web_data --config config/local.json
```

生成 website/data/local.js 和 website/local.html。
本地入口为 http://127.0.0.1:8765/local.html，也可离线打开。
本地入口同时提供长春真实成果和模拟案例切换。

真实数据导出文件和入口均被 Git 忽略。公开入口 index.html 只引用
demo.js，不会尝试请求真实数据。发布时仅使用 Git 跟踪的文件，
不要将本地 website 目录整包上传。

## 更新公开模拟案例

```sh
python -m scripts.synthetic_case --directory artifacts/web-demo
python -m scripts.run_pipeline --config artifacts/web-demo/config.json
python -m scripts.export_web_data --config artifacts/web-demo/config.json
```

模拟数据生成器要求新目录，避免覆盖已有文件。

## 检查

公开贡献和CI默认使用不依赖真实数据的检查：

```sh
npm ci
npx playwright install chromium
npm run test:browser
```

完整检查与环境变量见 [贡献指南](../CONTRIBUTING.md)。下方两项旧浏览器脚本用于本地真实案例检查，
不属于首次克隆仓库后的必需步骤；atlas-check.cjs的视觉采集器仅在本地参考工具存在时启用。

```sh
node --test website/tests/core.test.cjs website/tests/dataset.test.cjs
node --check website/app.js
```

浏览器测试为可选开发工具，需要已安装 Playwright 与可用浏览器：

```sh
node website/tests/browser-check.cjs
node website/tests/atlas-check.cjs
```

默认检查本地入口。HEATWATER_URL 可指定其他已启动的预览地址，
PLAYWRIGHT_MODULE 可指定环境已有的 Playwright 模块。
截图保存到忽略目录 artifacts/frontend/。

浏览器通过 Float32 运算复现当前权重组合，所有分区统计基于原始
30 m 栅格而非缩略图。正式方法修改应通过 Python 配置重跑；
浏览器页面不写入原栅格、不执行投影转换，也不提供工程内涝预测。
