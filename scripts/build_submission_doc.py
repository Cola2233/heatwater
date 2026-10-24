"""Create the competition process document for the Changchun submission package."""

from __future__ import annotations

import csv
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

PROJECT = Path(__file__).resolve().parents[1]
FIGURES = PROJECT / "figures"
OUTPUTS = PROJECT / "outputs"
DOC_OUT = PROJECT / "submission_package" / "05_过程文档" / "热水共治_作品制作过程文档.docx"


def set_cell_shading(cell, fill: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)


def set_cell_border(cell, color: str = "D9D9D9", size: str = "4") -> None:
    properties = cell._tc.get_or_add_tcPr()
    borders = properties.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        properties.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def set_cell_text(cell, text: str, *, bold: bool = False, color: str = "000000", size: int = 9) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = paragraph.add_run(str(text))
    run.bold = bold
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def style_document(document: Document) -> None:
    section = document.sections[0]
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)
    normal = document.styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    normal.font.size = Pt(10.5)
    normal.paragraph_format.line_spacing = 1.25
    normal.paragraph_format.space_after = Pt(5)
    for style_name, size in [("Title", 22), ("Heading 1", 16), ("Heading 2", 12)]:
        style = document.styles[style_name]
        style.font.name = "Microsoft YaHei"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)


def add_heading(document: Document, text: str, level: int = 1) -> None:
    paragraph = document.add_heading(text, level=level)
    paragraph.paragraph_format.space_before = Pt(10 if level == 1 else 6)
    paragraph.paragraph_format.space_after = Pt(5)


def add_body(document: Document, text: str) -> None:
    paragraph = document.add_paragraph(text)
    paragraph.paragraph_format.first_line_indent = Cm(0.7)


def add_bullet(document: Document, text: str) -> None:
    paragraph = document.add_paragraph(style="List Bullet")
    paragraph.add_run(text)


def add_figure(document: Document, path: Path, caption: str, width: float = 15.8) -> None:
    if not path.exists():
        return
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run().add_picture(str(path), width=Cm(width))
    caption_paragraph = document.add_paragraph(caption)
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_paragraph.runs[0].font.size = Pt(9)
    caption_paragraph.runs[0].font.color.rgb = RGBColor(77, 107, 122)


def add_table(document: Document, headers: list[str], rows: list[list[str]], widths: list[float] | None = None) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.autofit = False
    for index, header in enumerate(headers):
        cell = table.rows[0].cells[index]
        set_cell_text(cell, header, bold=True, color="FFFFFF", size=9)
        set_cell_shading(cell, "1F4E78")
        set_cell_border(cell)
    for row_index, row in enumerate(rows):
        cells = table.add_row().cells
        for index, value in enumerate(row):
            set_cell_text(cells[index], value, size=9)
            set_cell_shading(cells[index], "F3F6F8" if row_index % 2 else "FFFFFF")
            set_cell_border(cells[index])
    if widths:
        for row in table.rows:
            for index, width in enumerate(widths):
                row.cells[index].width = Cm(width)
    document.add_paragraph()


def load_summary() -> tuple[list[list[str]], list[list[str]]]:
    compound = []
    with (OUTPUTS / "compound_action_zone_summary.csv").open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            compound.append([row["zone_label"], row["area_km2"], row["share_percent"] + "%"])
    exposure = []
    with (OUTPUTS / "human_exposure_priority_summary.csv").open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            exposure.append([row["zone_label"], row["area_km2"], row["share_percent"] + "%"])
    return compound, exposure


def build() -> None:
    compound_rows, exposure_rows = load_summary()
    DOC_OUT.parent.mkdir(parents=True, exist_ok=True)
    document = Document()
    style_document(document)

    title = document.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("热水共治 长春城市热涝复合风险与更新优先区识别")
    subtitle = document.add_paragraph("遥感应用组作品制作过程文档")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.runs[0].font.size = Pt(12)
    subtitle.runs[0].font.color.rgb = RGBColor(77, 107, 122)
    document.add_paragraph()

    add_heading(document, "一 作品概述")
    add_body(document, "本作品面向长春城市扩张、高温和水涝风险并存的问题，融合多年夏季地表温度、土地覆盖转换、地形、地表硬化、水系和建筑功能数据，构建30 m城市热涝复合风险诊断流程。作品的最终目标不是只绘制一张热岛图，而是识别应该优先改造和保护的空间单元。")
    add_body(document, "作品最终回答三个应用问题：哪些地方持续偏热，哪些地方具有较高水涝空间风险，新增不透水面中哪些区域同时涉及住宅、教育、医疗和公共服务建筑。")

    add_heading(document, "二 数据与软件")
    add_table(document, ["数据或软件", "内容", "用途"], [
        ["Landsat夏季LST合成", "2013—2015与2021—2023，30 m", "持续热风险"],
        ["GLC_FCS30D转换", "2013—2022土地覆盖转换，30 m", "新增不透水面"],
        ["DEM与地表环境数据", "高程、坡度、硬化和水涝空间代理指标", "水涝风险筛查"],
        ["SinoBF-1建筑功能", "住宅、教育、医疗和公共服务建筑", "暴露代理"],
        ["QGIS与GDAL NumPy", "栅格对齐、计算、制图和批处理", "可复现处理链"],
    ], widths=[4.0, 7.0, 5.0])

    add_heading(document, "三 处理流程")
    add_body(document, "首先将早期和近期夏季LST裁剪到相同的四环范围，并统一为30 m栅格。然后在共同有效区内分别采用5%和95%分位数进行稳健归一化，以减少不同天气条件对两期LST直接比较的影响。")
    add_body(document, "水涝层来自已有的地形、地表硬化和土地覆盖空间筛查结果。该层被对齐到热环境参考网格后，与持续热风险共同构建热涝复合风险。最后，利用2013—2022土地覆盖转换和建筑功能数据，分别识别新增不透水面优先区以及重点人群与公共服务保护区。")
    add_bullet(document, "持续热风险等于2013—2015与2021—2023标准化热风险的平均值。")
    add_bullet(document, "热涝复合风险等于0.55乘以持续热风险加0.45乘以水涝风险。")
    add_bullet(document, "复合风险阈值为0.67，建筑功能暴露阈值为0.60。")

    add_heading(document, "四 作品成果图")
    add_figure(document, FIGURES / "01_heat_water_compound_dashboard.png", "图1 热风险 水涝风险 热涝复合分区与新增不透水面治理优先级")
    add_figure(document, FIGURES / "02_human_exposure_priority.png", "图2 重点人群与公共服务暴露优先级")

    add_heading(document, "五 热涝复合分区结果")
    add_table(document, ["分区", "面积 km2", "占有效区"], compound_rows, widths=[9.0, 3.5, 3.5])
    add_body(document, "热涝双高区是本作品的核心治理对象。该区域同时具有较高持续热风险和较高水涝空间风险，应优先配置蓝绿基础设施、透水铺装、雨水花园、树冠遮阴和公共避暑空间。")

    add_heading(document, "六 重点人群与公共服务保护结果")
    add_table(document, ["分区", "面积 km2", "占有效区"], exposure_rows, widths=[9.0, 3.5, 3.5])
    add_body(document, "建筑功能暴露层由住宅、教育、医疗和公共服务建筑构成。它是空间暴露代理，不等同于人口普查数量。重点保护区应作为后续实地核查、学校医院周边降温和社区更新排序的候选区域。")

    add_heading(document, "七 文件与复现方式")
    add_table(document, ["提交内容", "对应文件"], [
        ["成果图", "01_heat_water_compound_dashboard.png；02_human_exposure_priority.png"],
        ["成果数据", "outputs目录下GeoTIFF与CSV统计表"],
        ["辅助公式", "auxiliary/formulas.md"],
        ["分区编码", "auxiliary/zone_codes.csv；exposure_zone_codes.csv"],
        ["源代码", "scripts目录和run_pipeline.ps1"],
        ["数据来源", "outputs/data_manifest.csv"],
        ["处理说明", "docs/processing_flow.md"],
    ], widths=[4.0, 12.0])
    add_body(document, "在QGIS 4.0.3自带Python环境中运行run_pipeline.ps1，可重新生成栅格成果、统计表和制图结果。热环境原始文件和建筑功能文件较大，提交包保留必要源数据、数据清单和可复现脚本；无关的大型中间文件不纳入提交。")

    add_heading(document, "八 应用边界")
    add_body(document, "水涝层用于城市空间筛查，不替代工程排水模型、暴雨情景模拟或内涝预报。热风险表达的是统一空间范围内的相对风险，不将两期合成结果直接解释为长期气温趋势。建筑功能暴露用于定位需要优先核查的区域，正式治理仍需结合人口、道路、排水管网和现场调查。")

    footer = document.sections[0].footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("热水共治 长春城市热涝复合风险与更新优先区识别").font.size = Pt(8)
    document.save(DOC_OUT)
    print(DOC_OUT)


if __name__ == "__main__":
    build()
