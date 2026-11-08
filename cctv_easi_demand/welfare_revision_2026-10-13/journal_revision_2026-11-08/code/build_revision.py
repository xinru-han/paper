#!/usr/bin/env python3
"""Build bilingual Word manuscripts from the supplied draft and Stata outputs.

This script formats and validates reported results; it does not estimate models.
"""

import argparse
import csv
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from lxml import etree
from PIL import Image

from revision_text import (
    CN, EN, CN_TITLE, CN_SUBTITLE, EN_TITLE, EN_SUBTITLE,
    EN_TABLE_HEADERS, EN_CELL_LABELS, REFERENCE_INDICES, REMOVE,
)

OUT = Path(__file__).resolve().parents[1]
MATH_TAGS = {qn("m:oMath"), qn("m:oMathPara")}
FOOD_EN = ["Staples", "Oils", "Vegetables", "Fruit", "Pork", "Other meat", "Seafood", "Dairy"]
NUMBER = re.compile(r"[-+]?\d+(?:\.\d+)?")


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def markdown_rows(value):
    rows = [[c.strip() for c in line.strip().strip("|").split("|")]
            for line in value.splitlines() if line.startswith("|")]
    return rows[:1] + rows[2:]


def numeric_tokens(value):
    value = value.replace("−", "-").replace("\u2060", "").replace(",", "")
    return NUMBER.findall(value)


def verify_original_tables(doc, tables):
    keys = ["table_descriptives", "table_main", "table_frequency", "table_aggregation",
            "table_robustness", "table_regularity", "table_historical", "table_scenarios"]
    counts = []
    for number, (table, key) in enumerate(zip(doc.tables, keys), 1):
        expected = markdown_rows(tables[key])[1:]
        assert len(table.rows) - 1 == len(expected), (number, key)
        checked = 0
        for row, values in zip(table.rows[1:], expected):
            for col, cell in enumerate(row.cells[1:], 1):
                actual_n = numeric_tokens(cell.text)
                expected_n = numeric_tokens(values[col])
                assert len(actual_n) == len(expected_n), (number, col, cell.text, values[col])
                assert [float(x) for x in actual_n] == [float(x) for x in expected_n], (
                    number, col, cell.text, values[col])
                checked += len(actual_n)
        counts.append({"original_table": number, "source_key": key, "numeric_values_checked": checked})
    return counts


def replace_paragraph(paragraph, value):
    math = [deepcopy(node) for node in paragraph._p if node.tag in MATH_TAGS]
    placeholders = [int(x) for x in re.findall(r"\{\{M(\d+)\}\}", value)]
    assert sorted(placeholders) == list(range(len(math))), (paragraph.text, value, len(math))
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)
    for token in re.split(r"(\{\{M\d+\}\})", value):
        match = re.fullmatch(r"\{\{M(\d+)\}\}", token)
        if match:
            paragraph._p.append(math[int(match.group(1))])
        elif token:
            paragraph.add_run(token)


def font_for(run, size=None):
    run.font.name = "Times New Roman"
    if size:
        run.font.size = Pt(size)
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), "Noto Serif CJK SC")


def normalize_math(doc):
    # LibreOffice treats an unsplit "it" math token as a formatting command.
    # Two runs preserve the same italic indices in both Word and PDF exports.
    for text in list(doc.element.iter(qn("m:t"))):
        if text.text != "it":
            continue
        run = text.getparent()
        assert run.tag == qn("m:r")
        for letter in "it":
            clone = deepcopy(run)
            clone.find(qn("m:t")).text = letter
            run.addprevious(clone)
        run.getparent().remove(run)


def math_signatures(doc):
    return Counter("".join(node.text or "" for node in math.iter(qn("m:t")))
                   for math in doc.element.xpath(".//m:oMath"))


def page_numbers(doc):
    for section in doc.sections:
        paragraph = section.footer.paragraphs[0]
        paragraph.clear()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        field = OxmlElement("w:fldSimple")
        field.set(qn("w:instr"), "PAGE")
        run = OxmlElement("w:r")
        text = OxmlElement("w:t")
        text.text = "1"
        run.append(text)
        field.append(run)
        paragraph._p.append(field)


def style_document(doc, language):
    for section in doc.sections:
        header = section.header.paragraphs[0]
        header.clear()
        header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = header.add_run(CN_TITLE if language == "cn" else EN_TITLE)
        font_for(run, 8)
    for name in ["Normal", "Body Text", "First Paragraph"]:
        if name not in doc.styles:
            continue
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        style.font.size = Pt(11)
        style._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), "Noto Serif CJK SC")
        style.paragraph_format.line_spacing = 1.15
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.widow_control = True
    for name, size in [("Title", 19), ("Subtitle", 12), ("Heading 1", 13), ("Heading 2", 11.5)]:
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), "Noto Serif CJK SC")
        style.paragraph_format.keep_with_next = True
    in_references = False
    for paragraph in doc.paragraphs:
        if paragraph.text in {"References", "参考文献"}:
            in_references = True
        elif paragraph.style.name == "Title":
            in_references = False
        paragraph.paragraph_format.widow_control = True
        if paragraph.style.name in {"Normal", "Body Text", "First Paragraph"}:
            paragraph.paragraph_format.keep_with_next = False
        if paragraph._p.xpath(".//w:drawing"):
            paragraph.paragraph_format.keep_with_next = True
        for run in paragraph.runs:
            font_for(run)
        if re.match(r"^(Table \d+\.|表\d+\s|Figure \d+\.|图\d+\s)", paragraph.text):
            paragraph.paragraph_format.keep_with_next = True
            paragraph.paragraph_format.space_before = Pt(8)
            for run in paragraph.runs:
                run.bold = True
                font_for(run, 10)
        if paragraph.text.startswith(("Notes:", "注：")):
            paragraph.paragraph_format.keep_with_next = False
            for run in paragraph.runs:
                font_for(run, 9)
        if in_references and paragraph.text not in {"References", "参考文献"}:
            paragraph.paragraph_format.line_spacing = 1.02
            paragraph.paragraph_format.space_after = Pt(3)
            paragraph.paragraph_format.left_indent = Inches(.18)
            paragraph.paragraph_format.first_line_indent = Inches(-.18)
            for run in paragraph.runs:
                font_for(run, 9.5)
    for table in doc.tables:
        style_table(table, language)
    page_numbers(doc)


def style_table(table, language="en"):
    table.autofit = False
    table_width = 6.50
    if len(table.columns) == 7:
        proportions = [1.05, .82, .50, 1.32, .82, .50, 1.32]
    elif len(table.columns) == 6:
        proportions = [1.1, .85, 1.1, 1.12, 1.12, 1.21]
    else:
        proportions = [1.35] + [(table_width - 1.35) / (len(table.columns) - 1)] * (len(table.columns) - 1)
    total = sum(proportions)
    for col, width in zip(table.columns, proportions):
        col.width = Inches(table_width * width / total)
    for row_number, row in enumerate(table.rows):
        trpr = row._tr.get_or_add_trPr()
        if trpr.find(qn("w:cantSplit")) is None:
            trpr.append(OxmlElement("w:cantSplit"))
        if row_number == 0:
            header = OxmlElement("w:tblHeader")
            trpr.append(header)
        for col_number, cell in enumerate(row.cells):
            cell.width = Inches(table_width * proportions[col_number] / total)
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(3)
                paragraph.paragraph_format.space_before = Pt(3)
                paragraph.paragraph_format.line_spacing = 1.05
                paragraph.paragraph_format.first_line_indent = Inches(0)
                paragraph.paragraph_format.left_indent = Inches(0)
                paragraph.paragraph_format.right_indent = Inches(0)
                paragraph.paragraph_format.keep_with_next = row_number < len(table.rows) - 1
                paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT if col_number == 0 else WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    font_for(run, 9 if language == "en" else 9.5)
                    run.bold = row_number == 0


def add_figure_before(doc, anchor, language):
    picture = doc.add_paragraph()
    picture.alignment = WD_ALIGN_PARAGRAPH.CENTER
    picture.add_run().add_picture(str(OUT / "outputs/price_offset.png"), width=Inches(5.9))
    picture.paragraph_format.keep_with_next = True
    caption = doc.add_paragraph(
        "Figure 2. Price contributions to the cost of the 2020 food basket" if language == "en"
        else "图2　猪肉降价与其他品类涨价的篮子成本贡献")
    note = doc.add_paragraph(
        "Notes: Same 2020 baseline as Table 2. Bars are percentage-point contributions; non-meat includes six food groups. Net cost is the sum of all three category contributions."
        if language == "en" else
        "注：与表2采用同一2020年基准样本；柱高为对八类食品预算的成本贡献。非肉类合计六组，净成本为前三项之和。")
    for element in [picture._p, caption._p, note._p]:
        anchor.addprevious(element)


def build_main(source, language, scalars):
    doc = Document(source)
    paragraphs = list(doc.paragraphs)
    texts = CN if language == "cn" else EN
    for i, value in texts.items():
        for key, replacement in scalars.items():
            value = value.replace(key, replacement)
        replace_paragraph(paragraphs[i], value)
    for number, i in enumerate([31, 48, 50, 54, 57, 63, 65, 74, 117], 1):
        replace_paragraph(paragraphs[i], f"\t{{{{M0}}}}\t({number})")
        paragraph_format = paragraphs[i].paragraph_format
        paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        paragraph_format.tab_stops.clear_all()
        paragraph_format.tab_stops.add_tab_stop(Inches(3.25), WD_TAB_ALIGNMENT.CENTER)
        paragraph_format.tab_stops.add_tab_stop(Inches(6.48), WD_TAB_ALIGNMENT.RIGHT)
    for i in sorted(REMOVE | (set(range(144, 180)) - REFERENCE_INDICES), reverse=True):
        paragraphs[i]._p.getparent().remove(paragraphs[i]._p)
    if language == "en":
        for i in range(180, 184):
            paragraphs[i]._p.getparent().remove(paragraphs[i]._p)
    else:
        for i in [180, 181]:
            paragraphs[i].style = doc.styles["Title" if i == 180 else "Subtitle"]
        paragraphs[180].paragraph_format.page_break_before = True

    # Move the complete cost section, including its tables, ahead of purchase results.
    body = doc.element.body
    children = list(body)
    start = children.index(paragraphs[114]._p)
    end = children.index(paragraphs[133]._p)
    for element in children[start:end]:
        paragraphs[76]._p.addprevious(element)
    add_figure_before(doc, paragraphs[124]._p, language)

    image_part = doc.part.related_parts["rId8"]
    image_part._blob = (OUT / "outputs/price_paths.png").read_bytes()
    with Image.open(OUT / "outputs/price_paths.png") as graphic:
        width, height = graphic.size
        doc.inline_shapes[0].height = int(doc.inline_shapes[0].width * height / width)
    if language == "en":
        for table, headers in zip(doc.tables, [EN_TABLE_HEADERS[i] for i in [0, 6, 7, 1, 2, 3, 4, 5]]):
            for cell, value in zip(table.rows[0].cells, headers):
                cell.text = value
            for row in table.rows[1:]:
                row.cells[0].text = EN_CELL_LABELS.get(row.cells[0].text, row.cells[0].text)
    style_document(doc, language)
    normalize_math(doc)
    # The larger replacement price graphic keeps the original image's display box.
    doc.core_properties.title = f"{CN_TITLE}: {CN_SUBTITLE}" if language == "cn" else f"{EN_TITLE}: {EN_SUBTITLE}"
    doc.core_properties.subject = "Household food purchases and fixed-basket price offsets"
    doc.core_properties.comments = "Revised from the user-supplied November 8 manuscript; estimation results retained."
    name = "猪肉降价_食品篮子成本_中文修订稿" if language == "cn" else "manuscript_en"
    target = OUT / f"{name}.docx"
    doc.save(target)
    return target


def add_table(doc, title, content, note):
    doc.add_paragraph(title, style="Heading 2")
    rows = markdown_rows(content) if isinstance(content, str) else content
    table = doc.add_table(rows=0, cols=len(rows[0]))
    table.style = "Table Grid"
    for values in rows:
        for cell, value in zip(table.add_row().cells, values):
            cell.text = str(value).replace("\u2060", "")
    style_table(table)
    paragraph = doc.add_paragraph("Notes: " + note)
    for run in paragraph.runs:
        font_for(run, 9)


def make_supplement(tables, upstream):
    doc = Document()
    for section in doc.sections:
        section.page_width = Inches(8.2677)
        section.page_height = Inches(11.6929)
        section.left_margin = section.right_margin = Inches(.85)
    doc.add_paragraph("Supplementary Material", style="Title")
    doc.add_paragraph(f"{EN_TITLE}: {EN_SUBTITLE}", style="Subtitle")
    doc.add_paragraph("S1. Data and Price Measurement", style="Heading 1")
    doc.add_paragraph(
        "The analysis uses active household-months. Prices are fixed-weight geometric indices of independently priced categories. Priced coverage is an expenditure-accounting measure rather than a complete match of product quality or purchasing channels. Income brackets retain the source categories and do not imply a monthly or annual reporting period.")
    add_table(doc, "Table S1. Priced coverage and residual log-price variation", tables["table_prices"],
              "Coverage uses 2021 expenditure. Residual columns show residual variance as a percentage of original variance after province/calendar-month/year or province/full-year-month controls. These are descriptive regressions, not the main demand specification.")
    add_table(doc, "Table S2. Sample and expenditure by reported income bracket", tables["table_sample_income"],
              "Household-months are mutually exclusive by bracket; distinct households may appear in several brackets. Per-member amounts use the size proxy.")

    doc.add_paragraph("S2. Exact Demand Systems", style="Heading 1")
    old_doc = Document(OUT / "sources/upstream_manuscript_en.docx")
    # Preserve the archived, editable formulas rather than transcribing them as images.
    for i in range(62, 72):
        element = deepcopy(old_doc.paragraphs[i]._p)
        doc.element.body.insert(len(doc.element.body) - 1, element)
        for text in element.iter():
            if text.tag not in {qn("w:t"), qn("m:t")}:
                continue
            if text.text:
                text.text = text.text.replace("equation (8)", "equation (S2)")
                for old, new in [("(7)", "(S1)"), ("(8)", "(S2)"), ("(9)", "(S3)"), ("(10)", "(S4)")]:
                    text.text = text.text.replace(old, new)
    for number, key, title, note in [
        (3, "table_fits", "Exact-system estimation", "All systems use 583,668 household-months. GMM criteria describe fixed-weight objectives, not overidentification tests."),
        (4, "table_exact_own", "Own-price point estimates across systems", "Exact systems use common support of 579,066 observations; the main model uses 574,172. Differences also involve participation, household means, and price interactions."),
        (5, "table_exact_exp", "Food-expenditure point estimates across systems", "Budget elasticities refer to the eight-group food sub-budget, not household income."),
        (6, "table_engel", "Exact-system quadratic Engel tests", "Seven restrictions, with approximate F(7,23) reference. These are within-model nested tests."),
        (7, "table_spec_tests", "Main-model parameter-block score tests", "Maximum absolute-t province-score tests; 999 multiplier draws, conditional on generated weights and evaluation support."),
    ]:
        add_table(doc, f"Table S{number}. {title}", tables[key], note)

    doc.add_paragraph("S3. Inference and Prediction Support", style="Heading 1")
    add_table(doc, "Table S8. Simultaneous 95% bands for sixteen main elasticities", tables["table_simultaneous"],
              "The family comprises eight expenditure and eight own-price elasticities. Province two-step influence functions and 999 studentized Webb score multipliers are used.")
    inf = read_csv(upstream / "outputs/inference/elasticity_inference_paper_main.csv")
    raw = [["Food group", "Raw expend.", "Raw own price", "Positive expend.", "Positive own price"]]
    for good, name in enumerate(FOOD_EN, 1):
        values = []
        for sample in ["raw_all", "common_positive"]:
            for typ in ["expenditure", "own_price"]:
                matches = [r for r in inf if r["sample"] == sample and int(r["good"]) == good and r["type"] == typ]
                assert len(matches) == 1
                values.append(f"{float(matches[0]['estimate']):.4f}")
        raw.append([name] + values)
    add_table(doc, "Table S9. Raw and positive-prediction evaluation samples", raw,
              "The fitted parameters are unchanged. Raw sample N = 583,668; positive sample N = 574,172. Estimates use quantity-equivalent weights.")
    add_table(doc, "Table S10. Responses by purchasing margin", tables["table_main_margins"],
              "The source label unconditional denotes overall participation-adjusted purchasing conditional on the food budget. Latent responses remove the fitted participation transformation and use their own support.")
    add_table(doc, "Table S11. Negative predictions and observed purchase incidence", tables["table_support"],
              "Negative predictions use the raw sample. Latent functions retain main-model parameters and are not a re-estimated no-correction model.")
    add_table(doc, "Table S12a. Main-model uncompensated price-elasticity matrix", tables["table_main_cross"],
              "Rows are demand groups and columns are prices. Uncompensated cross-price signs do not by themselves classify compensated substitutes or complements.")
    add_table(doc, "Table S12b. Exact-EASI uncompensated price-elasticity matrix", tables["table_easi_cross"],
              "The three exact systems' common support is used. These are point estimates.")
    add_table(doc, "Table S13. Main-model elasticities in the lowest and highest income brackets", tables["table_income"],
              "The same full-sample parameters are evaluated by current reported bracket; models are not re-estimated by bracket. Cross-bracket differences are not jointly tested.")
    robust = read_csv(upstream / "outputs/paper/robustness_all_points.csv")
    variants = [("main", "Baseline"), ("order1", "Linear Engel"), ("order3", "Cubic Engel"),
                ("nosy", "No participation"), ("nopcyc", "No history"), ("omit5", "Pork omitted")]
    for typ, label, suffix in [("own_price", "Own-price", "a"), ("expenditure", "Expenditure", "b")]:
        rows = [["Food group"] + [label for _, label in variants]]
        for good, food in enumerate(FOOD_EN, 1):
            values = []
            for variant, _ in variants:
                matches = [r for r in robust if r["variant"] == variant and int(r["good"]) == good]
                assert len(matches) == 1
                values.append(f"{float(matches[0][typ]):.3f}")
            rows.append([food] + values)
        add_table(doc, f"Table S14{suffix}. {label} point estimates by specification", rows,
                  "Each specification is re-estimated on the full estimation sample and evaluated on its own positive-prediction support.")

    doc.add_paragraph("S4. Sample Map and Basket Contributions", style="Heading 1")
    add_table(doc, "Table S15. Observation and evaluation units", [
        ["Use", "N", "Unit / selection"],
        ["Estimation", "583,668", "Active household-month; all observed group zeros retained"],
        ["Main elasticities", "574,172", "All eight fitted shares above 10⁻⁸"],
        ["Exact-system comparison", "579,066", "Common positive predictions and valid utility inversion"],
        ["Old/new grouping evaluation", "569,808", "Intersection of six exact systems"],
        ["Historical basket costs", "182,676", "2020 active household-months"],
        ["10% basket scenarios", "583,668", "All active household-months"],
        ["Quarterly incidence", "203,337", "Active household-quarter"],
        ["Annual incidence", "58,150", "Active household-year"],
    ], "The sample is not a population-weighted estimate of Chinese households. Active windows have at least one positive purchase in the eight groups.")
    components = read_csv(OUT / "outputs/historical_components.csv")
    add_table(doc, "Table S16. Complete historical category-cost decomposition", [
        ["Food group", "Contribution (percentage points)"]
    ] + [[FOOD_EN[int(r["good"]) - 1], f"{float(r['contribution_pp']):.4f}"] for r in components],
        "The supplied historical fixed-basket Stata definition is applied to the same 182,676 baseline observations. Contributions sum to 2.9734 percentage points. Pork is negative; other meat is positive. No demand substitution or curvature-constrained welfare estimates enter this accounting.")
    style_document(doc, "en")
    normalize_math(doc)
    target = OUT / "supplementary_material_en.docx"
    doc.save(target)
    return target


def snapshot(project, base, source):
    inputs = OUT / "sources"
    inputs.mkdir(exist_ok=True)
    shutil.copy2(source, inputs / "input_manuscript.docx")
    shutil.copy2(base / "manuscript/manuscript_food_policy_eight_groups_en.docx", inputs / "upstream_manuscript_en.docx")
    shutil.copy2(project / "manuscript/baseline_table_formatting.py", inputs / "baseline_table_formatting.py")
    shutil.copy2(project / "outputs/exact/basket_weights_2021.csv", inputs / "basket_weights_2021.csv")
    for origin, destination in [(project / "code", inputs / "welfare_stata/code"),
                                (project / "ado", inputs / "welfare_stata/ado"),
                                (base / "code", inputs / "upstream/code"),
                                (base / "ado", inputs / "upstream/ado")]:
        shutil.copytree(origin, destination, dirs_exist_ok=True)
    # Only tables used by the manuscripts are copied, never household-level data.
    source_csvs = [
        "paper/descriptives.csv", "exact/model_fit_full.csv", "exact/elasticities_common_full.csv",
        "inference/elasticity_inference_paper_main.csv", "demand/elasticities_main.csv",
        "paper/main_regularity.csv", "exact/regularity_common_full.csv", "paper/purchase_frequency.csv",
        "paper/robustness_summary.csv", "paper/robustness_all_points.csv", "paper/price_variation.csv",
        "welfare/policy_exposure_historical.csv", "welfare/policy_exposure.csv",
        "paper/sample_statistics.csv", "exact/engel_nested_tests.csv", "paper/main_specification_tests.csv",
        "comparison/meat_before_after.csv", "comparison/exact_matched_sample.csv",
        "regularity/prediction_support_main.csv", "exact/cross_price_common_full.csv",
        "paper/income_descriptives.csv", "welfare/price_shocks_2020_2022.csv",
    ]
    for relative in source_csvs:
        destination = inputs / "upstream/outputs" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(base / "outputs" / relative, destination)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=OUT.parent)
    parser.add_argument("--snapshot", action="store_true", help="Refresh copied source documents and aggregate Stata tables")
    args = parser.parse_args()
    project = args.project.resolve()
    base = project.parent / "meat_merge_trial_2026-10-11"
    source = project / "家庭食品购买的价格响应与成本暴露_英文期刊导向修订稿.docx"
    if args.snapshot or not (OUT / "sources/input_manuscript.docx").exists():
        snapshot(project, base, source)
    source = OUT / "sources/input_manuscript.docx"
    upstream = OUT / "sources/upstream"
    spec = importlib.util.spec_from_file_location("original_formatter", OUT / "sources/baseline_table_formatting.py")
    formatter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(formatter)
    formatter.P = upstream
    tables = formatter.build(False)
    original = Document(source)
    assert len(original.paragraphs) == 184 and len(original.tables) == 8
    table_checks = verify_original_tables(original, tables)
    summary = {r["statistic"]: float(r["value"]) for r in read_csv(OUT / "outputs/price_offset_summary.csv")}
    assert abs(summary["historical_mean"] - 2.973402578372977) < 1e-9
    assert summary["pork_mean"] < 0 < summary["other_meat_mean"]
    remaining = sum(float(r["contribution_pp"]) for r in read_csv(OUT / "outputs/historical_components.csv")
                    if int(r["good"]) in [3, 4, 7])
    scalars = {"@NONMEAT@": f"{summary['nonmeat_mean']:.2f}", "@OFFSET@": f"{summary['offset_pct']:.1f}",
               "@REMAINING@": f"{remaining:.2f}"}
    targets = [build_main(source, language, scalars) for language in ["cn", "en"]]
    targets.append(make_supplement(tables, upstream))
    validation = {"built_utc": datetime.now(timezone.utc).isoformat(),
                  "source_sha256": sha256(source), "table_checks": table_checks,
                  "stata_log": "logs/06_price_offset_check.log", "full_demand_reestimated": False,
                  "summary": summary, "documents": []}
    for target in targets[:2]:
        doc = Document(target)
        full_text = "\n".join(p.text for p in doc.paragraphs)
        assert len(doc.tables) == 8 and len(doc.inline_shapes) == 3
        assert len(doc.element.xpath(".//m:oMath")) == len(original.element.xpath(".//m:oMath"))
        assert math_signatures(doc) == math_signatures(original)
        for table, original_index in zip(doc.tables, [0, 6, 7, 1, 2, 3, 4, 5]):
            original_table = original.tables[original_index]
            actual_values = [[numeric_tokens(c.text) for c in row.cells[1:]] for row in table.rows[1:]]
            original_values = [[numeric_tokens(c.text) for c in row.cells[1:]] for row in original_table.rows[1:]]
            assert actual_values == original_values
        assert not re.search(r"\{\{M\d|@[A-Z]+@", full_text)
        assert "附录A" not in full_text and "Table A" not in full_text
        if target.stem == "manuscript_en":
            text_nodes = [str(x) for x in doc.element.xpath(".//w:t/text()")]
            text_nodes.extend(p.text for s in doc.sections for p in s.header.paragraphs)
            assert not re.search(r"[\u4e00-\u9fff]", " ".join(text_nodes))
        caption_pairs = re.findall(r"^(?:Table (\d+)\.|表(\d+)　)", full_text, flags=re.M)
        captions = [a or b for a, b in caption_pairs]
        assert captions == [str(x) for x in range(1, 9)], captions
        validation["documents"].append({"file": target.name, "sha256": sha256(target),
            "paragraphs": len(doc.paragraphs), "tables": len(doc.tables),
            "figures": len(doc.inline_shapes), "editable_math_objects": len(doc.element.xpath(".//m:oMath"))})
    (OUT / "outputs/document_validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = [{"file": str(p.relative_to(OUT)), "bytes": p.stat().st_size, "sha256": sha256(p)}
                for p in sorted((OUT / "sources").rglob("*")) if p.is_file() and "__pycache__" not in p.parts]
    (OUT / "outputs/source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(validation["documents"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
