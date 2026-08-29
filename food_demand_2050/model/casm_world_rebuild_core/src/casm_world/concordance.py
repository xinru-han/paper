"""Commodity-concordance validation against frozen FAOSTAT code tables."""

from __future__ import annotations

import csv
import io
from pathlib import Path
import zipfile

import yaml


DOMAIN_ARCHIVES = {
    "CB": "CommodityBalances_(non-food)_(2010-)_E_All_Data_(Normalized).zip",
    "FBS": "FoodBalanceSheets_E_All_Data_Normalized.zip",
    "QCL": "Production_Crops_Livestock_E_All_Data_Normalized.zip",
    "SUA": "SUA_Crops_Livestock_E_All_Data_Normalized.zip",
    "BIO": "Environment_Bioenergy_E_All_Data_(Normalized).zip",
}


def load_concordance(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    commodities = config.get("commodities", {})
    if len(commodities) != 31:
        raise ValueError(f"Expected 31 commodities, found {len(commodities)}")
    if len(set(commodities)) != len(commodities):
        raise ValueError("Commodity codes must be unique")
    return config


def _item_codes(archive: Path) -> set[int]:
    with zipfile.ZipFile(archive) as zipped:
        names = [name for name in zipped.namelist() if name.endswith("ItemCodes.csv")]
        if len(names) != 1:
            raise ValueError(f"Expected one ItemCodes table in {archive}")
        with zipped.open(names[0]) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
            reader = csv.DictReader(text, skipinitialspace=True)
            code_column = next(
                (column for column in reader.fieldnames or [] if column.strip() == "Item Code"),
                None,
            )
            if code_column is None:
                raise ValueError(f"No Item Code column in {archive}")
            codes: set[int] = set()
            for row in reader:
                try:
                    codes.add(int(row[code_column]))
                except (TypeError, ValueError):
                    continue
        if codes:
            return codes

        # The current FBS bulk archive ships an empty ItemCodes table.  In
        # that case validate against the Item Code column in the normalized
        # data itself rather than silently accepting an empty catalogue.
        data_names = [
            name
            for name in zipped.namelist()
            if name.endswith("All_Data_(Normalized).csv")
        ]
        if len(data_names) != 1:
            raise ValueError(f"Cannot locate normalized data in {archive}")
        with zipped.open(data_names[0]) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
            reader = csv.DictReader(text)
            for row in reader:
                try:
                    codes.add(int(row["Item Code"]))
                except (TypeError, ValueError):
                    continue
        if not codes:
            raise ValueError(f"No numeric item codes found in {archive}")
        return codes


def validate_concordance(config: dict, faostat_root: Path) -> dict:
    available = {
        domain: _item_codes(faostat_root / filename)
        for domain, filename in DOMAIN_ARCHIVES.items()
    }
    checked: list[tuple[str, str, str, int]] = []
    missing: list[tuple[str, str, str, int]] = []
    for commodity, definition in config["commodities"].items():
        for role in ("balance", "activity", "validation"):
            mapping = definition.get(role)
            if not mapping or mapping.get("domain") == "DERIVED":
                continue
            domain = mapping["domain"]
            if domain not in available:
                raise ValueError(f"Unsupported domain {domain} for {commodity}/{role}")
            for item in mapping.get("items", []):
                record = (commodity, role, domain, int(item))
                checked.append(record)
                if int(item) not in available[domain]:
                    missing.append(record)
    if missing:
        raise ValueError(f"Unknown FAOSTAT item mappings: {missing}")

    systems = config.get("processing_systems", {})
    for name in ("soybean_crush", "sunflower_crush", "rapeseed_crush"):
        system = systems[name]
        total = sum(float(value) for value in system["outputs"].values())
        total += float(system["residual"])
        if abs(total - 1.0) > 1e-10:
            raise ValueError(f"{name} mass coefficients sum to {total}")
    cotton = systems["cotton_ginning"]
    cotton_total = sum(float(value) for value in cotton["outputs"].values())
    cotton_total += float(cotton["residual"])
    if abs(cotton_total - 1.0) > 1e-10:
        raise ValueError(f"cotton_ginning mass coefficients sum to {cotton_total}")

    return {
        "commodity_count": len(config["commodities"]),
        "mapping_records_checked": len(checked),
        "processing_system_count": len(systems),
        "status": "passed",
    }
