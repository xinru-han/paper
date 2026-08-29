import csv
from pathlib import Path
import zipfile

import pandas as pd

from casm_world.benchmark import (
    country_codebook,
    extract_domain_benchmark,
    normalized_quantity,
    read_normalized_rows,
)


def _archive(path: Path) -> None:
    columns = [
        "Area Code (M49)", "Area", "Item Code", "Element Code", "Element",
        "Year", "Unit", "Value", "Flag",
    ]
    rows = [
        ["'156", "China", 2513, 5511, "Production", 2023, "1000 t", 10, "A"],
        ["'156", "China", 2515, 5511, "Production", 2023, "1000 t", 5, "E"],
        ["'156", "China", 2513, 5611, "Import quantity", 2023, "1000 t", 2, "A"],
        ["'156", "China", 2513, 5511, "Production", 2022, "1000 t", 99, "A"],
        ["'001", "World", 2513, 5511, "Production", 2023, "1000 t", 999, "A"],
    ]
    import io

    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(columns)
    writer.writerows(rows)
    with zipfile.ZipFile(path, "w") as zipped:
        zipped.writestr("Synthetic_All_Data_(Normalized).csv", stream.getvalue())


def test_unit_normalization():
    assert normalized_quantity(1000, "1000 t", "WHE") == (1.0, "Mt")
    assert normalized_quantity(1_000_000, "t", "WHE") == (1.0, "Mt")
    assert normalized_quantity(10_000, "100 mg/ha", "WHE") == (1.0, "t/ha")


def test_stream_filter_and_multi_item_aggregation(tmp_path):
    archive = tmp_path / "fbs.zip"
    _archive(archive)
    raw = read_normalized_rows(
        archive, year=2023, item_codes=[2513, 2515], allowed_m49={"156"}
    )
    assert len(raw) == 3
    config = {
        "commodities": {
            "OCG": {"balance": {"domain": "FBS", "items": [2513, 2515]}}
        }
    }
    result = extract_domain_benchmark(
        archive, domain="FBS", config=config, year=2023, allowed_m49={"156"}
    )
    production = result[result["account"].eq("production")].iloc[0]
    assert production["value"] == 0.015
    assert production["source_item_codes"] == "2513,2515"
    assert set(result["m49"]) == {"156"}


def test_country_codebook_is_rebuilt_from_raw_un_snapshot():
    raw = Path(
        "/root/data/CASM/casm_world_2050/data/raw/un/"
        "un_m49_overview_2026-08-29.html"
    )
    codebook = country_codebook(raw)
    assert len(codebook) == 250
    assert codebook["m49"].is_unique
    assert codebook.loc[codebook["economy_id"].eq("CHN"), "m49"].item() == "156"
    assert codebook.loc[codebook["economy_id"].eq("TWN"), "m49"].item() == "158"
    assert codebook.loc[codebook["economy_id"].eq("XKX"), "m49"].item() == "412"
