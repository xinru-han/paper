"""Streaming extraction of the unbalanced 2023 FAOSTAT benchmark.

This module deliberately stops before statistical balancing.  It converts
source observations to stable physical units and records source roles; a
later balancing stage must reconcile them under commodity and processing
identities without silently replacing missing observations by zero.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Iterable
import zipfile

import pandas as pd

from casm_world.concordance import load_concordance
from casm_world.geography import (
    EXPECTED_TERRITORIES,
    aggregate_additive_values,
    load_territory_config,
)
from casm_world.paths import load_source_catalog, verify_source


NORMALIZED_COLUMNS = [
    "Area Code (M49)",
    "Area",
    "Item Code",
    "Element Code",
    "Element",
    "Year",
    "Unit",
    "Value",
    "Flag",
]

ELEMENT_ACCOUNT = {
    5301: "domestic_supply",
    5510: "production",
    5511: "production",
    5610: "imports",
    5611: "imports",
    5910: "exports",
    5911: "exports",
    5071: "stock_change",
    5072: "stock_change",
    5141: "food",
    5142: "food",
    5520: "feed",
    5521: "feed",
    5023: "processing",
    5131: "processing",
    5165: "other_use",
    5154: "other_use",
    5525: "seed",
    5527: "seed",
    5016: "loss",
    5123: "loss",
    5166: "residual",
    5170: "residual",
    5312: "area",
    5412: "yield",
    5851: "energy_consumption",
    5852: "energy_production",
}


def _m49(value: object) -> str | None:
    text = str(value).strip().lstrip("'")
    if not text.isdigit():
        return None
    return text.zfill(3)


def normalized_quantity(value: float, unit: str, commodity: str) -> tuple[float, str]:
    """Convert a FAOSTAT physical observation to a model unit.

    Quantities use Mt, areas Mha, yields t/ha.  Bioenergy is converted from
    TJ using a lower-heating-value convention, recorded here rather than
    hidden in the benchmark builder.
    """

    unit = str(unit).strip()
    if unit in {"t", "tonnes"}:
        return float(value) / 1_000_000.0, "Mt"
    if unit == "1000 t":
        return float(value) / 1_000.0, "Mt"
    if unit == "ha":
        return float(value) / 1_000_000.0, "Mha"
    if unit == "100 mg/ha":
        return float(value) * 1.0e-4, "t/ha"
    if unit == "kg/ha":
        return float(value) / 1_000.0, "t/ha"
    if unit == "TJ":
        lower_heating_value_gj_per_t = {"ETH": 26.8, "BDI": 37.0}
        if commodity not in lower_heating_value_gj_per_t:
            raise ValueError(f"No TJ-to-mass conversion for {commodity}")
        # 1 TJ = 1,000 GJ; divide by GJ/t and then by 1,000,000 t/Mt.
        factor = 0.001 / lower_heating_value_gj_per_t[commodity]
        return float(value) * factor, "Mt"
    raise ValueError(f"Unsupported FAOSTAT unit {unit!r} for {commodity}")


def _normalized_member(zipped: zipfile.ZipFile) -> str:
    names = [
        name
        for name in zipped.namelist()
        if name.endswith("All_Data_(Normalized).csv")
    ]
    if len(names) != 1:
        raise ValueError("Expected one normalized all-data member")
    return names[0]


def read_normalized_rows(
    archive: Path,
    *,
    year: int,
    item_codes: Iterable[int],
    allowed_m49: set[str] | None = None,
    chunksize: int = 250_000,
) -> pd.DataFrame:
    """Read only selected year/items from a normalized FAOSTAT archive."""

    wanted = {int(code) for code in item_codes}
    frames: list[pd.DataFrame] = []
    with zipfile.ZipFile(archive) as zipped:
        member = _normalized_member(zipped)
        with zipped.open(member) as stream:
            for chunk in pd.read_csv(
                stream,
                usecols=lambda name: name in NORMALIZED_COLUMNS,
                chunksize=chunksize,
                low_memory=False,
            ):
                item = pd.to_numeric(chunk["Item Code"], errors="coerce")
                years = pd.to_numeric(chunk["Year"], errors="coerce")
                keep = item.isin(wanted) & years.eq(year)
                if not keep.any():
                    continue
                selected = chunk.loc[keep].copy()
                selected["m49"] = selected["Area Code (M49)"].map(_m49)
                selected = selected[selected["m49"].notna()]
                if allowed_m49 is not None:
                    selected = selected[selected["m49"].isin(allowed_m49)]
                frames.append(selected)
    if not frames:
        return pd.DataFrame(columns=NORMALIZED_COLUMNS + ["m49"])
    return pd.concat(frames, ignore_index=True)


def _domain_mappings(config: dict, domain: str) -> tuple[dict[int, list[tuple[str, str]]], set[int]]:
    reverse: dict[int, list[tuple[str, str]]] = defaultdict(list)
    codes: set[int] = set()
    for commodity, definition in config["commodities"].items():
        for role in ("balance", "activity", "validation"):
            mapping = definition.get(role)
            if not mapping or mapping.get("domain") != domain:
                continue
            for code in mapping.get("items", []):
                reverse[int(code)].append((commodity, role))
                codes.add(int(code))
    return reverse, codes


def extract_domain_benchmark(
    archive: Path,
    *,
    domain: str,
    config: dict,
    year: int = 2023,
    allowed_m49: set[str] | None = None,
) -> pd.DataFrame:
    """Return source-labelled, unit-normalized benchmark observations."""

    reverse, item_codes = _domain_mappings(config, domain)
    if not item_codes:
        return pd.DataFrame()
    rows = read_normalized_rows(
        archive,
        year=year,
        item_codes=item_codes,
        allowed_m49=allowed_m49,
    )
    records: list[dict] = []
    for row in rows.to_dict(orient="records"):
        item_code = int(row["Item Code"])
        element_code = int(row["Element Code"])
        account = ELEMENT_ACCOUNT.get(element_code)
        if account is None:
            continue
        for commodity, role in reverse[item_code]:
            # A mapping may request one explicit element (e.g. fluid-milk food).
            mapping = config["commodities"][commodity][role]
            requested = mapping.get("element")
            if requested and account != requested:
                continue
            value, model_unit = normalized_quantity(
                float(row["Value"]), str(row["Unit"]), commodity
            )
            records.append(
                {
                    "m49": row["m49"],
                    "area_name": row["Area"],
                    "commodity": commodity,
                    "role": role,
                    "account": account,
                    "value": value,
                    "unit": model_unit,
                    "source_domain": domain,
                    "source_item_code": item_code,
                    "source_element_code": element_code,
                    "source_flag": row.get("Flag"),
                    "year": year,
                }
            )
    if not records:
        return pd.DataFrame()
    result = pd.DataFrame.from_records(records)
    keys = [
        "m49",
        "area_name",
        "commodity",
        "role",
        "account",
        "unit",
        "source_domain",
        "year",
    ]
    # Keep source-code lineage as deterministic comma-separated strings while
    # summing multi-item aggregates such as OCG and OTO.
    grouped = result.groupby(keys, as_index=False, dropna=False).agg(
        value=("value", "sum"),
        source_item_codes=(
            "source_item_code",
            lambda values: ",".join(str(value) for value in sorted(set(values))),
        ),
        source_element_codes=(
            "source_element_code",
            lambda values: ",".join(str(value) for value in sorted(set(values))),
        ),
        source_flags=(
            "source_flag",
            lambda values: ",".join(
                str(value) for value in sorted(set(values.dropna().astype(str)))
            ),
        ),
    )
    return grouped.sort_values(keys).reset_index(drop=True)


def country_codebook(un_m49_html: Path) -> pd.DataFrame:
    """Rebuild the canonical M49-to-model identifier bridge from raw UN data."""

    tables = pd.read_html(un_m49_html)
    candidates = [
        table
        for table in tables
        if {"M49 Code", "ISO-alpha3 Code", "Country or Area"} <= set(table.columns)
    ]
    if not candidates:
        raise ValueError("No UN M49 country table found")
    official = candidates[0].copy()
    official = official[[
        "M49 Code",
        "ISO-alpha3 Code",
        "Country or Area",
        "Region Code",
        "Region Name",
        "Sub-region Code",
        "Sub-region Name",
    ]]
    official.columns = [
        "m49",
        "economy_id",
        "economy_name",
        "region_code",
        "region_name",
        "subregion_code",
        "subregion_name",
    ]
    official["m49"] = pd.to_numeric(official["m49"], errors="raise").astype(int).astype(str).str.zfill(3)
    official["economy_id"] = official["economy_id"].astype(str).str.upper()
    if len(official) != 248 or not official["m49"].is_unique:
        raise ValueError("UN M49 canonical table must contain 248 unique rows")
    supplemental = pd.DataFrame.from_records(
        [
            {
                "m49": "158",
                "economy_id": "TWN",
                "economy_name": "China; Taiwan Province of",
                "region_code": "142",
                "region_name": "Asia",
                "subregion_code": "030",
                "subregion_name": "Eastern Asia",
            },
            {
                "m49": "412",
                "economy_id": "XKX",
                "economy_name": "Kosovo",
                "region_code": "150",
                "region_name": "Europe",
                "subregion_code": "039",
                "subregion_name": "Southern Europe",
            },
        ]
    )
    result = pd.concat([official, supplemental], ignore_index=True)
    if len(result) != 250 or not result["m49"].is_unique:
        raise ValueError("Canonical codebook must contain 248 M49 rows plus TWN and XKX")
    return result.sort_values("economy_id").reset_index(drop=True)


def build_unbalanced_benchmark(project_root: Path) -> dict:
    """Extract and aggregate the source-labelled 2023 observations.

    This creates an *unbalanced* audit table, not a calibrated model input.
    Its coverage report is intentionally allowed to list missing products and
    accounts; the balancing gate remains closed until those are resolved.
    """

    catalog = load_source_catalog(project_root / "config/data_sources.yaml")
    source_keys = {
        "CB": "fao_nonfood_balances",
        "FBS": "fao_fbs",
        "QCL": "fao_qcl",
        "SUA": "fao_sua",
        "BIO": "fao_bioenergy",
    }
    for key in [*source_keys.values(), "un_m49"]:
        verify_source(catalog.source(key))

    concordance = load_concordance(project_root / "config/commodities.yaml")
    codebook = country_codebook(catalog.source("un_m49").path)
    allowed_m49 = set(codebook["m49"])
    observations: list[pd.DataFrame] = []
    for domain, source_key in source_keys.items():
        frame = extract_domain_benchmark(
            catalog.source(source_key).path,
            domain=domain,
            config=concordance,
            year=2023,
            allowed_m49=allowed_m49,
        )
        if not frame.empty:
            observations.append(frame)
    if not observations:
        raise ValueError("No benchmark observations were extracted")
    source = pd.concat(observations, ignore_index=True)
    source = source.merge(
        codebook[["m49", "economy_id", "region_code", "subregion_code"]],
        on="m49",
        how="left",
        validate="many_to_one",
    )
    if source["economy_id"].isna().any():
        raise ValueError("Benchmark contains unmapped M49 country codes")

    numeric_dimensions = [
        "year",
        "commodity",
        "role",
        "account",
        "unit",
        "source_domain",
    ]
    territory_config = load_territory_config(
        project_root / "config/territory_aggregation.yaml"
    )
    model = aggregate_additive_values(
        source,
        territory_config,
        value_columns=["value"],
        dimension_columns=numeric_dimensions,
        require_all_territories=False,
    )
    if set(model["economy_id"]) & EXPECTED_TERRITORIES:
        raise AssertionError("Excluded territory survived in model benchmark")

    interim = project_root / "data/interim"
    processed = project_root / "data/processed"
    interim.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)
    source_path = interim / "benchmark_source_observations_2023.csv"
    model_path = processed / "benchmark_unbalanced_2023.csv"
    source.to_csv(source_path, index=False)
    model.to_csv(model_path, index=False)

    expected = set(concordance["commodities"])
    observed = set(model["commodity"])
    balance = model[model["role"].eq("balance")]
    report = {
        "benchmark_year": 2023,
        "status": "unbalanced_not_simulation_ready",
        "source_observation_rows": int(len(source)),
        "model_observation_rows": int(len(model)),
        "source_economies_observed": int(source["economy_id"].nunique()),
        "model_accounts_observed": int(model["economy_id"].nunique()),
        "commodities_expected": len(expected),
        "commodities_observed": len(observed),
        "missing_commodity_observations": sorted(expected - observed),
        "commodities_with_balance_rows": int(balance["commodity"].nunique()),
        "excluded_territories_present_in_model": sorted(
            set(model["economy_id"]) & EXPECTED_TERRITORIES
        ),
        "source_output": str(source_path),
        "model_output": str(model_path),
        "next_gate": "statistical_balancing_and_complete_account_coverage",
    }
    report_path = processed / "benchmark_unbalanced_report_2023.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    args = parser.parse_args()
    report = build_unbalanced_benchmark(args.project_root.resolve())
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
