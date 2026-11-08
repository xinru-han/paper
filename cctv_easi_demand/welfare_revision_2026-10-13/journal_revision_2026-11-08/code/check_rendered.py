#!/usr/bin/env python3
"""Check PDF exports and make compact contact sheets for visual inspection."""

import json
from pathlib import Path
import re

import fitz
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CHECKS = ROOT / "checks"
CHECKS.mkdir(exist_ok=True)
reports = []
for name in ["manuscript_en", "猪肉降价_食品篮子成本_中文修订稿", "supplementary_material_en"]:
    doc = fitz.open(ROOT / f"{name}.pdf")
    texts = [page.get_text() for page in doc]
    full_text = "\n".join(texts)
    assert "家庭食品购买的价格响应与成本暴露" not in full_text
    assert "¿" not in full_text and "�" not in full_text
    if name.endswith("_en"):
        assert not re.search(r"[\u4e00-\u9fff]", full_text)
    outside = []
    for number, page in enumerate(doc, 1):
        assert len(texts[number - 1].strip()) > 60, (name, number)
        for block in page.get_text("blocks"):
            if block[0] < -1 or block[1] < -1 or block[2] > page.rect.width + 1 or block[3] > page.rect.height + 1:
                outside.append(number)
    assert not outside, (name, outside)
    if name == "manuscript_en":
        assert "Cheaper Pork, Costlier Food Baskets" in texts[0]
        assert all(f"Table {i}." in full_text for i in range(1, 9))
        assert all(f"Figure {i}." in full_text for i in range(1, 4))
    width, height, columns = 250, 370, 4
    sheet = Image.new("RGB", (width * columns, height * ((len(doc) + columns - 1) // columns)), "#e9e9e9")
    draw = ImageDraw.Draw(sheet)
    for index, page in enumerate(doc):
        pixmap = page.get_pixmap(matrix=fitz.Matrix(.42, .42), alpha=False)
        picture = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
        picture.thumbnail((width - 10, height - 25))
        x, y = index % columns * width, index // columns * height
        sheet.paste(picture, (x + 5, y + 20))
        draw.text((x + 7, y + 4), f"Page {index + 1}", fill="black")
    target = CHECKS / f"{name}_contact.png"
    sheet.save(target)
    reports.append({"file": f"{name}.pdf", "pages": len(doc), "text_within_page": True,
                    "no_unknown_math_glyph": True, "contact_sheet": str(target.relative_to(ROOT))})
    if name == "manuscript_en":
        for phrase, output in [("Cheaper Pork, Costlier Food Baskets", "english_title"),
                               ("Figure 2.", "english_offsets"), ("Table 4.", "english_elasticities")]:
            number = next(i for i, text in enumerate(texts) if phrase in text)
            doc[number].get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False).save(CHECKS / f"{output}.png")
    doc.close()
(CHECKS / "pdf_validation.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(reports, ensure_ascii=False, indent=2))
