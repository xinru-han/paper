"""Convert the prior China-CASM diet solutions into audited relative shifters."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = Path(__file__).with_name("config.yaml")


def _project_path(value: str) -> Path:
    path = (PROJECT_ROOT / value).resolve()
    path.relative_to(PROJECT_ROOT)
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_paths(config: dict) -> tuple[pd.DataFrame, dict]:
    source_path = _project_path(config["inputs"]["prior_casm_results"])
    source = pd.read_csv(
        source_path,
        usecols=["scenario", "variable", "commodity", "year", "value"],
        encoding="utf-8-sig",
    )
    source = source[source["variable"].eq("food_demand_pc")].copy()
    source["year"] = pd.to_numeric(source["year"], errors="raise").astype(int)
    source["value"] = pd.to_numeric(source["value"], errors="raise").astype(float)
    scenarios = {
        pathway: str(definition["source_scenario"])
        for pathway, definition in config["diet_pathways"].items()
    }
    required_scenarios = set(scenarios.values())
    source = source[source["scenario"].isin(required_scenarios)]
    years = list(range(int(config["benchmark_year"]), int(config["projection_end"]) + 1))
    if not set(years) <= set(source["year"]):
        raise ValueError("Prior China-CASM food paths do not cover every 2023-2050 year")
    source = source[source["year"].isin(years)].copy()
    if source.duplicated(["scenario", "commodity", "year"]).any():
        raise ValueError("Prior China-CASM food paths contain duplicate keys")
    if not np.isfinite(source["value"]).all() or (source["value"] < 0).any():
        raise ValueError("Prior China-CASM food paths contain invalid quantities")

    lookup = source.set_index(["scenario", "commodity", "year"])["value"]
    baseline_scenario = scenarios["BASELINE"]
    rows: list[dict] = []
    for pathway, source_scenario in scenarios.items():
        for world_product, definition in config["product_mapping"].items():
            source_products = [str(value) for value in definition["source_commodities"]]
            for year in years:
                try:
                    baseline = float(
                        sum(lookup.loc[(baseline_scenario, product, year)] for product in source_products)
                    )
                    pathway_value = float(
                        sum(lookup.loc[(source_scenario, product, year)] for product in source_products)
                    )
                except KeyError as exc:
                    raise ValueError(
                        f"Missing China-CASM path for {pathway}/{world_product}/{year}"
                    ) from exc
                if baseline <= 0.0 or pathway_value < 0.0:
                    raise ValueError(
                        f"Invalid mapped food path for {pathway}/{world_product}/{year}"
                    )
                multiplier = pathway_value / baseline
                rows.append(
                    {
                        "diet_pathway": pathway,
                        "source_scenario": source_scenario,
                        "year": year,
                        "world_commodity": world_product,
                        "source_commodities": "+".join(source_products),
                        "baseline_kg_per_capita": baseline,
                        "pathway_kg_per_capita": pathway_value,
                        "preference_multiplier_vs_baseline": multiplier,
                        "mapping_note": str(definition["note"]),
                    }
                )
    result = pd.DataFrame.from_records(rows).sort_values(
        ["diet_pathway", "world_commodity", "year"]
    ).reset_index(drop=True)
    expected = len(scenarios) * len(config["product_mapping"]) * len(years)
    if len(result) != expected or result.duplicated(
        ["diet_pathway", "year", "world_commodity"]
    ).any():
        raise AssertionError("Mapped diet-path grid is incomplete")
    benchmark = result[result["year"].eq(int(config["benchmark_year"]))]
    benchmark_error = float(
        (benchmark["preference_multiplier_vs_baseline"] - 1.0).abs().max()
    )
    if benchmark_error > 1.0e-10:
        raise ValueError(f"Diet pathways do not share the 2023 benchmark: {benchmark_error}")
    if not np.isfinite(result["preference_multiplier_vs_baseline"]).all() or (
        result["preference_multiplier_vs_baseline"] <= 0.0
    ).any():
        raise ValueError("Mapped diet multipliers must be finite and positive")

    report = {
        "status": "passed",
        "source": str(source_path),
        "source_sha256": _sha256(source_path),
        "scenario_type": config["interpretation"]["scenario_type"],
        "pathways": list(scenarios),
        "year_start": min(years),
        "year_end": max(years),
        "mapped_world_commodity_count": len(config["product_mapping"]),
        "mapped_world_commodities": list(config["product_mapping"]),
        "excluded_prior_casm_foods": config["excluded_prior_casm_foods"],
        "benchmark_maximum_absolute_multiplier_error": benchmark_error,
        "mapping_rule": "pathway-to-BS ratio of summed China-CASM kg/person/year",
        "important_scope_limit": (
            "Vegetables, fruit, eggs, aquatic foods, tubers and sheep/goat meat are "
            "outside the CASM-World 31-product equilibrium and receive no market shock."
        ),
    }
    return result, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    paths, report = build_paths(config)
    output_path = _project_path(config["inputs"]["mapped_diet_paths"])
    report_path = _project_path(config["inputs"]["mapped_diet_paths_report"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    paths.to_csv(output_path, index=False, lineterminator="\n")
    report["output"] = str(output_path)
    report["output_sha256"] = _sha256(output_path)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {output_path} ({len(paths)} rows)")
    print(f"wrote {report_path}")


if __name__ == "__main__":
    main()
