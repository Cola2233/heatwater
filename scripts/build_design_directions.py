"""Produce three actual-data design directions without overwriting the current UI."""
from __future__ import annotations
import argparse
import base64
import json
import re
import struct
import zlib
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"design-demos"/"2026-11-02"
LAB=ROOT/"website"/"design-lab"
NAMES=("空间观测大屏","地图研究工作台","城市风险图谱")

def metric(key,label,foot=""):
    foot_id={"area":"metric-pixels","both":"metric-both-share"}.get(key)
    small=f'<small id="{foot_id}">{foot}</small>' if foot_id else f"<small>{foot}</small>"
    return f'<div class="metric"><span class="metric-label">{label}</span><div class="metric-number"><strong id="metric-{key}">—</strong><span class="unit">km²</span></div>{small}</div>'

def metrics(keys=("area","both","score","exposure")):
    meta={"area":("有效分析范围","共同有效像元"),"both":("热涝分量双高","占有效区"),
          "score":("复合高分区域","复合分数达到阈值"),
          "exposure":("高分高建筑暴露","建筑功能暴露不代表人口")}
    return '<section class="metrics" aria-label="当前分区统计" aria-live="polite">'+"".join(metric(k,*meta[k]) for k in keys)+"</section>"

def controls():
    return """<section class="panel panel-pad controls-card" id="lab">
<div class="panel-head"><h2>参数探索</h2><span>基线 0.55 / 0.67</span></div>
<div class="control-head"><label for="heat-weight">热分量权重</label><output id="weight-output" for="heat-weight">55%</output></div>
<input id="heat-weight" type="range" min="30" max="70" step="5" value="55">
<div class="range-labels"><span>热30% / 水70%</span><span>热70% / 水30%</span></div>
<div class="weight-equation"><span>热 <b id="weight-heat">0.55</b></span><span>+</span><span>水 <b id="weight-water">0.45</b></span><span>复合分数</span></div>
<div class="control-head threshold-head"><label for="threshold">高值判定阈值</label><output id="threshold-output" for="threshold">0.67</output></div>
<input id="threshold" type="range" min="50" max="80" step="1" value="67">
<div class="range-labels"><span>0.50 更宽筛查</span><span>0.80 更集中</span></div>
<p class="control-note">权重改变复合分数；四类治理分区由热、水各自的阈值决定。</p>
<button id="reset-parameters" class="text-button">恢复基线参数</button></section>"""

def zones():
    return """<section class="panel panel-pad zones-panel">
<div class="panel-head"><h2>治理分区构成</h2><span>当前阈值</span></div>
<div id="stacked-bar" class="stacked-bar" role="img"></div><div id="zone-rows"></div>
<p class="zone-footnote">四类面积基于同一共同有效像元口径。</p></section>"""

def scatter():
    return """<section class="panel panel-pad chart-panel">
<div class="panel-head"><h2>热与水的空间关系</h2></div>
<div class="chart-wrap"><svg id="bivariate" viewBox="0 0 240 230" role="img"></svg></div>
<p class="chart-caption" id="plot-r"></p><p class="chart-caption">每格表示真实像元数量；虚线为当前阈值。相关不表示因果。</p></section>"""

def exposure():
    return """<section class="panel panel-pad exposure-panel">
<div class="panel-head"><h2>建筑暴露分布</h2><span>有效像元比例</span></div>
<div id="exposure-bars" class="exposure-bars" role="img" aria-label="建筑功能暴露分数分布"></div>
<p class="chart-caption">功能存在代理，不等于人口普查。</p></section>"""

def interpretation():
    return """<section class="panel panel-pad interpret-panel">
<div class="panel-head"><h2>如何读这张图</h2></div><p class="interpret" id="insight-text"></p>
<div class="footer-exports"><button id="download-csv">分区统计CSV</button><button id="download-settings">探索参数JSON</button></div>
</section>"""

def map_panel():
    labels=(("zones","治理分区"),("heat","热分数"),("water","水分数"),("compound","复合分数"),("exposure","建筑暴露"),("expansion","新增硬化"))
    buttons="".join(f'<button data-layer="{key}" aria-pressed="{str(key=="compound").lower()}" class="{"selected" if key=="compound" else ""}">{label}</button>' for key,label in labels)
    return f"""<section class="panel map-panel" id="explorer">
<div class="map-heading"><div><h2 id="map-caption">长春空间分布</h2><span class="period-label">两期夏季合成</span></div><span class="map-extent" id="map-extent"></span></div>
<div class="map-tools" role="group" aria-label="观察图层">{buttons}</div>
<div class="canvas-wrap"><canvas id="map" tabindex="0" aria-label="地图，加减键缩放，方向键平移，零键复位"></canvas>
<div class="map-controls"><button id="zoom-in" aria-label="放大">+</button><button id="zoom-out" aria-label="缩小">−</button><button id="zoom-reset" aria-label="复位">⌂</button></div>
<div class="north" aria-hidden="true">N<span>↑</span></div>
<div class="pixel-inspector" id="pixel-inspector">悬停像元，查看热水与暴露分数</div></div>
<div class="map-footer"><div class="legend" id="legend"></div><div class="toolbar-actions"><button id="focus-toggle">纯净地图</button><button id="download-map">导出地图PNG</button></div></div>
<div class="panel-note"><h4 id="layer-title"></h4><p id="layer-note"></p></div></section>"""

def header(subtitle,letter):
    return f"""<header class="topbar"><div class="project-name"><span class="project-mark" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
<h1>热水共治<span>{subtitle}</span></h1></div>
<div class="dataset-control"><select id="dataset" aria-label="选择案例"></select><span id="dataset-tag" class="dataset-tag"></span></div></header>"""

def method():
    return """<section id="method" class="method-box">
<details><summary>查看方法与应用边界</summary><div class="method-content">
<p>两期LST在共同有效区内分别进行P5–P95归一化，取均值作为持续热分数。已有水涝代理对齐至30米网格后归一化。转换编码2表示新增不透水面。</p>
<p><code>Compound = w × Heat + (1 − w) × Water</code><br><code>Exposure = clip(0.60R + 0.90E + 1.00H + 0.70P, 0, 1)</code></p>
<p id="source-detail"></p><p>水涝层未用独立积水观测校准；不是工程内涝预测。LST不等于气温，建筑功能不等于人口。</p>
</div></details></section>
<footer class="bottom-source"><p id="dataset-description"></p><p>Huashu设计方向初稿 / 参考sc-datav地图与图表联动结构<br>未使用四川地形，未添加虚构实时数据。</p></footer>
<div id="error-message" role="alert" hidden></div>"""

def body(variant):
    if variant==0:
        return header("城市复合风险观测","A")+metrics()+f"""<main class="board-grid">
<aside class="left-col">{zones()}{scatter()}</aside>
<div class="center-col">{map_panel()}</div>
<aside class="right-col">{controls()}{exposure()}</aside></main>{interpretation()}{method()}"""
    if variant==1:
        return header("地图研究工作台","B")+f"""<main class="workspace"><section>{map_panel()}</section>
<aside class="right-col">{controls()}{interpretation()}</aside></main>
<div class="analysis-row">{zones()}{scatter()}{exposure()}</div>{method()}"""
    return header("长春城市风险图谱","C")+f"""<main class="story-layout">
<section class="story-map"><p class="muted">30米的像元尺度，观察同一座城市。</p>{map_panel()}</section>
<aside class="story-copy"><h2 class="story-title">城市的热与水，<br>需要一起被看见。</h2>
<div class="statement">{metric("both","热涝分量双高区域","占有效区")}</div>
{metrics(("area","score","exposure"))}<p class="interpret" id="insight-text"></p>{controls()}
<div class="footer-exports"><button id="download-csv">分区统计CSV</button><button id="download-settings">探索参数JSON</button></div>
</aside></main><div class="analysis-row">{zones()}{scatter()}{exposure()}</div>{method()}"""

def app_source(variant):
    script=(ROOT/"website/app.js").read_text(encoding="utf-8")
    script=re.sub(r"const zoneNames=.*?;", 'const zoneNames=["低热低涝","高温优先","水涝优先","热涝双高"];', script, count=1)
    script=script.replace("真实成果 · 仅本地","本地真实成果").replace("模拟案例 · 非观测","模拟案例（非观测）")
    script=script.replace('data.width+" × "+data.height+" px · EPSG:"+data.epsg',
                          '"网格 "+data.width+"×"+data.height+" / EPSG:"+data.epsg')
    script=script.replace('"use strict";','"use strict";\n'+(LAB/"charts.js").read_text(encoding="utf-8"),1)
    script=script.replace('const state={layer:"zones"','const state={layer:"compound"',1)
    script=script.replace('rasterize();updateLegend();draw();','updatePanels();rasterize();updateLegend();draw();',1)
    colors=[("#0a1c1d","#24413f","#789b8c","#c4d8ca","#132a2a"),("#f1f3ec","#dce4d9","#80968b","#435d50","#fff"),("#222c2d","#33413f","#70867b","#d5ded4","#263b35")][variant]
    script=script.replace('ctx.fillStyle="#f4f4f4"',f'ctx.fillStyle="{colors[0]}"')
    script=script.replace('ctx.strokeStyle="#e0e0e0"',f'ctx.strokeStyle="{colors[1]}"')
    script=script.replace('ctx.strokeStyle="#8d8d8d"',f'ctx.strokeStyle="{colors[2]}"')
    script=script.replace('ctx.fillStyle="#525252"',f'ctx.fillStyle="{colors[3]}"')
    script=script.replace('ctx.fillStyle="#161616"',f'ctx.fillStyle="{colors[3]}"')
    script=script.replace('ctx.fillStyle="#fff"',f'ctx.fillStyle="{colors[4]}"')
    return script

def render_full(variant):
    css=(LAB/"board.css").read_text(encoding="utf-8")
    content=body(variant)
    if variant==1:
        content=content.replace(map_panel(),map_panel().replace('<div class="map-tools"',metrics()+'<div class="map-tools"',1),1)
    javascript="\n".join((ROOT/"website"/p).read_text(encoding="utf-8") for p in ("data/demo.js","data/local.js","core.js"))
    javascript+="\n"+app_source(variant)
    javascript=re.sub(r"</script",lambda _:r"<\/script",javascript,flags=re.I)
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="{'dark' if variant==0 else 'light'}"><title>{NAMES[variant]} / 热水共治初稿</title>
<style>{css}</style></head>
<!-- Assumptions: same real Changchun data, desktop research/demo audience, standalone offline delivery.
No invented live metrics, terrain heights, administrative locations or testimonials.
Direction preview only; current production HTML is retained until user selects a direction. -->
<body class="board-{'abc'[variant]}"><div class="shell">{content}</div><script>{javascript}</script></body></html>"""

def png_raster():
    text=(ROOT/"website/data/local.js").read_text(encoding="utf-8")
    payload=json.loads(text.split('window.HEATWATER_DATASETS["changchun"]=',1)[1].strip().rstrip(";"))
    h=np.frombuffer(base64.b64decode(payload["arrays"]["heat"]),dtype="<f4")
    w=np.frombuffer(base64.b64decode(payload["arrays"]["water"]),dtype="<f4")
    score=np.clip(.55*h+.45*w,0,1)
    valid=np.isfinite(score)&(h>=0)&(w>=0)
    low=np.array([228,237,214]);high=np.array([103,67,135])
    rgb=np.nan_to_num(low+(high-low)*score[:,None]).astype("u1")
    rgba=np.concatenate((rgb,(valid.astype("u1")*255)[:,None]),axis=1)
    W,H=payload["meta"]["width"],payload["meta"]["height"]
    raw=b"".join(b"\0"+rgba.reshape(H,W,4)[y].tobytes() for y in range(H))
    def chunk(name,data):
        return struct.pack(">I",len(data))+name+data+struct.pack(">I",zlib.crc32(name+data)&0xffffffff)
    png=b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",W,H,8,6,0,0,0))+chunk(b"IDAT",zlib.compress(raw))+chunk(b"IEND",b"")
    return base64.b64encode(png).decode("ascii")

def thumbs():
    image="data:image/png;base64,"+png_raster()
    names=(*NAMES,"浅金汇报屏","四象限数据构成","中文图谱展板")
    previews=[]
    for i,name in enumerate(names):
        preview=f'<img src="{image}" alt="长春真实复合分数栅格">'
        bars='<div class="bars" aria-label="四类分区面积，相对最大类归一化">'+''.join(f'<i style="width:{n}%"></i>' for n in (100,31.4,62.2,30.1))+"</div>"
        title='<strong>热水共治</strong><small>长春城市复合风险</small>'
        if i==0: inside=f'<div class="minihead">{title}</div><div class="tiny-cols">{bars}{preview}{bars}</div>'
        elif i==1: inside=f'<div class="minihead">{title}</div><div class="tiny-studio">{preview}<div>{bars}<p>热权重 55%</p><p>阈值 0.67</p></div></div>'
        elif i==2: inside=f'<div class="tiny-story">{preview}<div>{title}<b>52.87</b><p>平方公里双高区域</p></div></div>'
        elif i==3: inside=f'<div class="minihead">{title}</div><div class="tiny-cols">{bars}{preview}{bars}</div>'
        elif i==4: inside=f'<div class="tiny-quad"><div class="quad"><i>44.70%</i><i>14.04%</i><i>27.80%</i><i>13.46%</i></div><div>{title}{preview}</div></div>'
        else: inside=f'<div class="tiny-book">{preview}<div><strong>城市<br>热水图谱</strong><p>长春四环<br>30米研究尺度</p></div></div>'
        previews.append(f'<article><div class="mini mini-{i}">{inside}</div><h2>{chr(65+i)} / {name}</h2><p>{"完整稿候选" if i<3 else "备选构图"}</p></article>')
    return """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>六个设计候选</title><style>
*{box-sizing:border-box}body{margin:0;background:#dfe2dc;color:#273a32;font:14px/1.6 "Segoe UI","Microsoft YaHei",sans-serif}main{padding:28px;max-width:1500px;margin:auto}header{margin-bottom:24px}h1{font-size:28px;font-weight:500}h2{font-size:18px;margin:12px 0 0}p{margin:0;color:#53645c}.grid{display:grid;grid-template-columns:1fr 1fr;gap:28px}.mini{height:300px;overflow:hidden;padding:20px;background:#fff;border:1px solid #bec8bd}.mini strong{font-size:24px}.mini small{font-size:12px;display:block}.mini img{display:block;object-fit:contain;max-width:100%;height:210px}.minihead{height:50px;display:flex;align-items:center;gap:18px;border-bottom:1px solid #ffffff35}.minihead small{font-size:12px}.tiny-cols{display:grid;grid-template-columns:1fr 2fr 1fr;gap:18px;align-items:center}.bars{display:flex;flex-direction:column;gap:22px;padding:18px 0}.bars i{display:block;height:8px;background:currentColor;opacity:.6}.mini-0{background:#102627;color:#b7d6c5}.mini-1{background:#edf1ed}.tiny-studio{display:grid;grid-template-columns:2.5fr 1fr;gap:15px}.tiny-studio>div{padding:0 15px;background:white}.tiny-story{display:grid;grid-template-columns:1.3fr 1fr;gap:25px;align-items:center;height:100%}.tiny-story img{background:#263638;height:260px}.tiny-story b{font:54px Georgia;display:block;color:#ac472f;margin-top:15px}.mini-2{background:#f1eee6}.mini-3{background:#fff4e2;color:#99511f}.mini-4{background:#f2f0d9}.tiny-quad{display:grid;grid-template-columns:1fr 1fr;gap:20px}.tiny-quad img{height:200px}.quad{display:grid;grid-template-columns:1.3fr 1fr;grid-template-rows:1.2fr 1fr;gap:4px;height:255px}.quad i{font-style:normal;display:flex;align-items:center;justify-content:center;background:#cbdcb9;color:#253e31}.quad i:nth-child(2){background:#e39b78}.quad i:nth-child(3){background:#72abc5}.quad i:nth-child(4){background:#80579b;color:white}.mini-5{background:#f6f3e9}.tiny-book{display:grid;grid-template-columns:2fr 1fr;gap:24px;align-items:center}.tiny-book img{height:260px}.tiny-book strong{font-family:Georgia,"SimSun",serif;font-size:36px}.tiny-book p{margin-top:18px;font-size:14px}@media(max-width:750px){.grid{grid-template-columns:1fr}main{padding:16px}}
</style><main><header><h1>同一组长春数据，六种观察方式</h1><p>先比较骨架、密度与阅读顺序，再选择最终方向。没有虚构实时或高程信息。</p></header><div class="grid">"""+"".join(previews)+"</div></main></html>"

def gallery():
    summaries=(
        ("A","空间观测大屏","深色地图居中，分区、热水关系和建筑暴露围绕主图联动。","适合答辩投屏和同屏概览。"),
        ("B","地图研究工作台","地图与工具放在第一屏，参数抽屉在右侧，详细分析排在下方。","适合自己操作研究、反复试参数。"),
        ("C","城市风险图谱","左侧大地图，右侧以真实结论带出解释和参数，再展开数据图。","适合向朋友或评委讲清研究逻辑。")
    )
    cards=[]
    for i,(letter,name,description,use) in enumerate(summaries,1):
        screenshot=base64.b64encode((OUT/f"dir-{i}-screen.png").read_bytes()).decode("ascii")
        cards.append(f'<article><a class="preview" href="dir-{i}.html"><img src="data:image/png;base64,{screenshot}" alt="{name}真实初稿截图"></a><div class="card-body"><h2><span>{letter}</span>{name}</h2><p>{description}</p><p class="use">{use}</p><a class="open" href="dir-{i}.html">打开{letter}版完整交互稿</a></div></article>')
    six=base64.b64encode((OUT/"thumbs.png").read_bytes()).decode("ascii")
    return """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>热水共治 / 三版设计对比</title><style>
*{box-sizing:border-box}body{margin:0;background:#ecefe9;color:#26372f;font:16px/1.75 "Segoe UI","Microsoft YaHei",sans-serif}main{max-width:1580px;margin:auto;padding:40px 32px}header{display:flex;align-items:flex-end;justify-content:space-between;gap:32px;margin-bottom:32px}h1{font-size:36px;line-height:1.4;font-weight:500;margin:0 0 16px}header p{margin:0;max-width:48em;color:#52685a}header aside{font-size:14px;color:#64756a;max-width:25em}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}article{border:1px solid #cbd5ca;background:#fff;display:flex;flex-direction:column}.preview{display:block;background:#dfe5dc;border-bottom:1px solid #cbd5ca}.preview img{display:block;width:100%;height:auto}.card-body{padding:24px;display:flex;flex-direction:column;flex:1}h2{font-size:23px;font-weight:500;line-height:1.4;margin:0 0 16px;display:flex;gap:12px;align-items:center}h2 span{font:20px Georgia;color:#6c806d;border:1px solid #cbd5ca;display:grid;place-content:center;width:38px;height:38px;flex-shrink:0}article p{font-size:16px;line-height:1.8;color:#52685a;margin:0 0 16px}.use{font-size:14px;color:#5d7162;margin-top:auto}.open{display:block;text-align:center;min-height:48px;background:#244b3e;color:#fff;text-decoration:none;padding:10px 16px;margin-top:10px}.open:hover{background:#153c30}a:focus-visible,summary:focus-visible{outline:3px solid #af5a32;outline-offset:4px}details{margin-top:32px;border:1px solid #cbd5ca;background:#f8faf6}summary{cursor:pointer;min-height:56px;padding:16px 24px;font-size:16px}details img{display:block;width:100%;height:auto}.bottom{margin:28px 0 0;font-size:14px;color:#64756a;max-width:90em}.bottom a{color:#244b3e}footer{border-top:1px solid #cbd5ca;padding-top:24px;margin-top:32px;font-size:14px;color:#64756a}@media(max-width:1000px){.grid{grid-template-columns:1fr}header{display:block}header aside{max-width:50em;margin-top:20px}.preview img{max-height:none}main{padding:28px 20px}}@media(max-width:500px){h1{font-size:28px}.card-body{padding:20px}h2{font-size:22px}}
</style></head><body><main><header><div><h1>这次，先让你看见选择。</h1><p>把Huashu的设计探索与sc-datav的地图联动结合，三版共用同一组长春真实数据与分析口径，区别在于布局和阅读顺序。</p></div><aside>点击任一截图或按钮，即可打开能操作的完整初稿。<br>原来的单文件HTML尚未覆盖。</aside></header><section class="grid">"""+"".join(cards)+f"""</section><details><summary>展开六个候选缩略图与另外三个备选</summary><img src="data:image/png;base64,{six}" alt="六个设计候选缩略图"></details><p class="bottom">三版均可离线打开，支持图层切换、缩放、参数调整和导出。深度来自真实栅格与图表，没有四川地形、虚构实时指标或假造3D高程。你可以选A/B/C，也可以指定混合，例如「A的布局+B的颜色」。</p><footer>按照<a href="https://github.com/alchaincyf/huashu-design/blob/master/SKILL.md">Huashu Design</a>的三方向流程，等你选择后，再合成最终可分享单文件。</footer></main></body></html>"""

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage",choices=("thumbs","full","gallery"),default="full")
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if args.stage=="gallery":
        (OUT/"index.html").write_text(gallery(),encoding="utf-8")
        print("Comparison gallery:",OUT/"index.html")
        return
    (OUT/"thumbs.html").write_text(thumbs(),encoding="utf-8")
    if args.stage=="full":
        for variant in range(3):
            (OUT/f"dir-{variant+1}.html").write_text(render_full(variant),encoding="utf-8")
    print("Design directions:",OUT)

if __name__=="__main__":
    main()
