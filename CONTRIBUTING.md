# 参与贡献

欢迎可复现的问题、数据契约改进、文档修正和小范围代码贡献。首次贡献可以先修复文档链接、
改进错误提示，或报告一次能用公开模拟案例重现的运行失败。

## 准备环境

仅修改网页时无需Python或GDAL，直接打开website/index.html。
Python核心开发使用Python 3.11+：

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
```

GIS变更使用environment.yml或匹配的QGIS Python，运行完整模拟流程：

```sh
python -m scripts.synthetic_case --directory demo
python -m scripts.run_pipeline --config demo/config.json
python -m scripts.validate_outputs --config demo/config.json
```

使用新目录生成输入；生成器会拒绝覆盖已有配置。GDAL缺失时跳过的测试不代表GIS检查通过。

## 网页检查

网页运行没有npm依赖。Node 20+与Playwright仅用于开发检查：

```sh
npm ci
npx playwright install chromium
npm test
npm run check
python -m scripts.build_single_html --output artifacts/releases/heatwater-demo.html
npm run test:browser
npm run test:blocks
```

Linux首次安装浏览器系统依赖可使用npx playwright install --with-deps chromium。
默认测试公开源码入口；同时检查单文件，在运行test:browser前设置：

```sh
# POSIX shell
export HEATWATER_PUBLIC_BUNDLE=artifacts/releases/heatwater-demo.html
```

```powershell
$env:HEATWATER_PUBLIC_BUNDLE='artifacts/releases/heatwater-demo.html'
```

Windows已安装Edge时，可设置HEATWATER_BROWSER_CHANNEL=msedge使用Edge，免下载Chromium。
PLAYWRIGHT_MODULE可指定已有Playwright模块位置。测试离线验证模拟案例、六图层、
参数、阈值线、纯净地图、三种下载以及桌面/平板/手机宽度。截图写入忽略目录artifacts/frontend/public/。

## 提交改动

1. 问题描述应包含期望与实际结果、复现命令、软件版本以及脱敏的最小配置。
2. 每次PR聚焦一个问题；说明行为变化与已执行的检查。
3. 改动计算公式时，同步更新methods.md、数据字典与有意义的回归测试。
4. 核心公式位于scripts/risk_logic.py；配置契约位于scripts/project_config.py。
5. Python和浏览器实现须遵守同一统计口径。不要用截图外观代替数值验证。

文档、排版等低影响修正不要求额外添加镜像测试。网页交互改动运行公开浏览器检查；
GIS改动运行GDAL集成与完整模拟链。提交前执行git diff --check。

## 数据与许可

不要提交本地配置、私人影像、真实建筑数据或生成成果。新增数据必须记录来源版本、许可与署名要求。
公开样例应保持可再生成、明确标注模拟。方法问题使用普通Issue；安全问题见SECURITY.md。
