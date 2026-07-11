#!/usr/bin/env python3
"""Build the coefficient-boundary audit requested for journal revision.

The output is a row-level metadata table for all environmental coefficient
files. It flags whether a coefficient can be summed in the main direct
production account, should be used only as a final-product footprint, or needs
manual review because its boundary can overlap with another process.
"""

from __future__ import annotations

import csv
import os


HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "coefficient_boundary_audit.csv")


FIELDS = [
    "indicator",
    "commodity",
    "casm_code",
    "casm_world_code",
    "region",
    "boundary",
    "direct_or_lifecycle",
    "includes_feed",
    "includes_land_use_change",
    "includes_processing",
    "includes_transport",
    "source_year",
    "source_reference",
    "imputed_flag",
    "imputation_rule",
    "can_sum_with_other_commodity_coefficients",
    "recommended_account",
    "double_counting_risk",
    "audit_note",
]


def low(value: str | None) -> str:
    return (value or "").strip().lower()


def yn(value: bool) -> str:
    return "yes" if value else "no"


def directness(boundary: str, source: str) -> str:
    text = low(boundary + " " + source)
    if "poore" in text or "lca" in text or "cradle-to-retail" in text:
        return "lifecycle"
    if "farm-gate" in text or "on-farm" in text or "fertil" in text or "excretion" in text:
        return "direct"
    return "review"


def flags(boundary: str, source: str, notes: str, commodity: str) -> dict[str, str]:
    text = low(" ".join([boundary, source, notes, commodity]))
    is_lca = directness(boundary, source) == "lifecycle"
    animal = any(
        word in text
        for word in [
            "pig",
            "pork",
            "cattle",
            "beef",
            "sheep",
            "goat",
            "chicken",
            "poultry",
            "egg",
            "milk",
            "fish",
            "animal",
        ]
    )
    return {
        "includes_feed": yn(is_lca and animal or "feed" in text),
        "includes_land_use_change": yn("land-use" in text or "luc" in text),
        "includes_processing": yn(is_lca or "processing" in text or "retail" in text),
        "includes_transport": yn(is_lca or "transport" in text),
    }


def recommendation(indicator: str, boundary: str, source: str, notes: str, commodity: str) -> tuple[str, str, str, str]:
    kind = directness(boundary, source)
    f = flags(boundary, source, notes, commodity)
    if kind == "direct":
        return "yes", "direct_production_account", "low", "Use in global net-effect account if the model quantity is the matching direct production process."
    if kind == "lifecycle":
        if f["includes_feed"] == "yes":
            risk = "high_for_joint_product_sum"
            note = "Final-product footprint only. Do not add to feed-crop lifecycle coefficients in the same production total."
        else:
            risk = "medium_boundary_overlap"
            note = "Final-product footprint sensitivity only unless all intermediate-product overlaps are removed."
        return "no", "final_product_consumption_footprint", risk, note
    if indicator == "nitrogen":
        return "manual_review", "direct_or_supply_chain_nitrogen", "medium_boundary_overlap", "Keep crop fertilizer, livestock excretion and virtual-N factors in separate accounts unless overlaps are removed."
    return "manual_review", "boundary_review_required", "unknown", "Boundary text is insufficient for automatic classification."


def carbon_rows() -> list[dict[str, str]]:
    rows = []
    path = os.path.join(HERE, "carbon_footprint_coefficients.csv")
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            boundary = r.get("system_boundary", "")
            source = r.get("source", "")
            notes = r.get("notes", "")
            rec = recommendation("carbon", boundary, source, notes, r.get("commodity", ""))
            rows.append(
                {
                    "indicator": "carbon",
                    "commodity": r.get("commodity", ""),
                    "casm_code": r.get("casm_code", ""),
                    "casm_world_code": r.get("casm_world_code", ""),
                    "region": r.get("region", ""),
                    "boundary": boundary,
                    "direct_or_lifecycle": directness(boundary, source),
                    **flags(boundary, source, notes, r.get("commodity", "")),
                    "source_year": r.get("year", ""),
                    "source_reference": source,
                    "imputed_flag": yn("proxy" in low(notes) or "aggregate" in low(notes)),
                    "imputation_rule": notes if ("proxy" in low(notes) or "aggregate" in low(notes)) else "",
                    "can_sum_with_other_commodity_coefficients": rec[0],
                    "recommended_account": rec[1],
                    "double_counting_risk": rec[2],
                    "audit_note": rec[3],
                }
            )
    return rows


def water_rows() -> list[dict[str, str]]:
    rows = []
    path = os.path.join(HERE, "water_footprint_coefficients.csv")
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            source = r.get("source", "")
            notes = r.get("notes", "")
            boundary = "farm water footprint: green, blue and grey components"
            rec = recommendation("water", boundary, source, notes, r.get("commodity", ""))
            rows.append(
                {
                    "indicator": "water",
                    "commodity": r.get("commodity", ""),
                    "casm_code": r.get("casm_code", ""),
                    "casm_world_code": r.get("casm_world_code", ""),
                    "region": r.get("region", ""),
                    "boundary": boundary,
                    "direct_or_lifecycle": "direct",
                    **flags(boundary, source, notes, r.get("commodity", "")),
                    "source_year": r.get("year_period", ""),
                    "source_reference": source,
                    "imputed_flag": yn("proxy" in low(notes) or "aggregate" in low(notes)),
                    "imputation_rule": notes if ("proxy" in low(notes) or "aggregate" in low(notes)) else "",
                    "can_sum_with_other_commodity_coefficients": rec[0],
                    "recommended_account": rec[1],
                    "double_counting_risk": rec[2],
                    "audit_note": rec[3],
                }
            )
    return rows


def nitrogen_rows() -> list[dict[str, str]]:
    rows = []
    path = os.path.join(HERE, "nitrogen_coefficients.csv")
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            category = r.get("category", "")
            source = r.get("source", "")
            notes = r.get("notes", "")
            if category == "A_crop_Nfert":
                boundary = "direct crop fertilizer application"
                kind = "direct"
            elif "excretion" in low(category + " " + source + " " + notes):
                boundary = "direct livestock nitrogen excretion"
                kind = "direct"
            else:
                boundary = "supply-chain or virtual nitrogen factor"
                kind = "review"
            rec = recommendation("nitrogen", boundary, source, notes, r.get("commodity_or_animal", ""))
            rows.append(
                {
                    "indicator": "nitrogen",
                    "commodity": r.get("commodity_or_animal", ""),
                    "casm_code": r.get("casm_code", ""),
                    "casm_world_code": "",
                    "region": r.get("region", ""),
                    "boundary": boundary,
                    "direct_or_lifecycle": kind,
                    **flags(boundary, source, notes, r.get("commodity_or_animal", "")),
                    "source_year": r.get("year", ""),
                    "source_reference": source,
                    "imputed_flag": yn("proxy" in low(notes) or "default" in low(notes)),
                    "imputation_rule": notes if ("proxy" in low(notes) or "default" in low(notes)) else "",
                    "can_sum_with_other_commodity_coefficients": rec[0],
                    "recommended_account": rec[1],
                    "double_counting_risk": rec[2],
                    "audit_note": rec[3],
                }
            )
    return rows


def land_rows() -> list[dict[str, str]]:
    rows = []
    path = os.path.join(HERE, "land_coefficients.csv")
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            source = r.get("source", "")
            notes = r.get("notes", "")
            boundary = "lifecycle land occupation equivalent: arable plus pasture"
            rec = recommendation("land", boundary, source, notes, r.get("commodity", ""))
            rows.append(
                {
                    "indicator": "land",
                    "commodity": r.get("commodity", ""),
                    "casm_code": r.get("casm_code", ""),
                    "casm_world_code": r.get("casm_world_code", ""),
                    "region": r.get("region", ""),
                    "boundary": boundary,
                    "direct_or_lifecycle": "lifecycle",
                    **flags(boundary, source, notes, r.get("commodity", "")),
                    "source_year": r.get("year", ""),
                    "source_reference": source,
                    "imputed_flag": yn("proxy" in low(notes) or "aggregate" in low(notes)),
                    "imputation_rule": notes if ("proxy" in low(notes) or "aggregate" in low(notes)) else "",
                    "can_sum_with_other_commodity_coefficients": rec[0],
                    "recommended_account": rec[1],
                    "double_counting_risk": rec[2],
                    "audit_note": rec[3],
                }
            )
    return rows


def main() -> None:
    rows = carbon_rows() + water_rows() + nitrogen_rows() + land_rows()
    with open(OUT, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {OUT} ({len(rows)} rows)")


if __name__ == "__main__":
    main()

