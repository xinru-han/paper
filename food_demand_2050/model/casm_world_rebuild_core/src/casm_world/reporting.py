"""Build reporting groups without confusing source geography and model accounts.

There are two deliberately separate membership layers:

* model-account membership generates World, focus-economy, EU27 and World
  Bank income results from solved model accounts;
* source-geography membership generates UN geographic results from the
  original M49 source contributions before territory aggregation.

Consequently, an overseas source can enter its parent's accounting target
without moving its reporting geography to the parent's UN region.
"""

from __future__ import annotations

from math import isfinite
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd
import yaml

from casm_world.geography import territory_crosswalk, validate_territory_config


EU27 = frozenset(
    {
        "AUT",
        "BEL",
        "BGR",
        "HRV",
        "CYP",
        "CZE",
        "DNK",
        "EST",
        "FIN",
        "FRA",
        "DEU",
        "GRC",
        "HUN",
        "IRL",
        "ITA",
        "LVA",
        "LTU",
        "LUX",
        "MLT",
        "NLD",
        "POL",
        "PRT",
        "ROU",
        "SVK",
        "SVN",
        "ESP",
        "SWE",
    }
)

ACCOUNT_GROUP_SYSTEMS = frozenset({"GLOBAL", "FOCUS", "ECONOMIC", "WB_INCOME_FY25"})
SOURCE_GROUP_SYSTEMS = frozenset(
    {"UN_REGION", "UN_SUBREGION", "UN_REPORTING_AREA"}
)
EXCLUSIVE_GROUP_SYSTEMS = frozenset(
    {"GLOBAL", "WB_INCOME_FY25", *SOURCE_GROUP_SYSTEMS}
)
FORBIDDEN_MODEL_ACCOUNT_CODES = frozenset({"WORLD", "WLD", "EU27", "ROW"})


def load_reporting_config(path: str | Path) -> dict[str, Any]:
    """Load and validate the reporting-group configuration."""

    config_path = Path(path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError(f"Reporting configuration must be a mapping: {config_path}")
    validate_reporting_config(config)
    return config


def validate_reporting_config(config: Mapping[str, Any]) -> None:
    """Validate fixed group definitions and membership-layer separation."""

    required = {
        "membership_layers",
        "unassigned_m49_geography",
        "global_group",
        "focus_groups",
        "economic_groups",
        "supplemental_source_geographies",
        "world_bank_income",
        "coverage_gate",
    }
    missing = required - set(config)
    if missing:
        raise ValueError(f"Reporting configuration is missing: {sorted(missing)}")

    global_group = config["global_group"]
    if (
        global_group.get("group_system") != "GLOBAL"
        or global_group.get("group_code") != "WORLD"
    ):
        raise ValueError("World must be GLOBAL/WORLD")

    focus = config["focus_groups"]
    if focus.get("CHINA_MAINLAND", {}).get("model_accounts") != ["CHN"]:
        raise ValueError("China-mainland focus must contain CHN only")
    if focus.get("USA", {}).get("model_accounts") != ["USA"]:
        raise ValueError("USA focus must contain USA only")

    configured_eu = set(
        config.get("economic_groups", {}).get("EU27", {}).get("model_accounts", [])
    )
    if configured_eu != EU27 or len(configured_eu) != 27:
        raise ValueError("EU27 must contain the fixed 27 member-state accounts")

    layers = config["membership_layers"]
    account_systems = set(layers.get("model_account", {}).get("group_systems", []))
    source_systems = set(layers.get("source_geography", {}).get("group_systems", []))
    if account_systems != ACCOUNT_GROUP_SYSTEMS:
        raise ValueError("Unexpected model-account group systems")
    if source_systems != SOURCE_GROUP_SYSTEMS:
        raise ValueError("Unexpected source-geography group systems")
    if account_systems & source_systems:
        raise ValueError("Account and source-geography systems must be disjoint")

    unassigned = config["unassigned_m49_geography"]
    if (
        str(unassigned.get("group_code")).zfill(3) != "000"
        or unassigned.get("source_economies") != ["ATA"]
    ):
        raise ValueError("ATA must be the sole explicit unassigned M49 geography")

    supplements = config["supplemental_source_geographies"]
    if set(supplements) != {"TWN", "XKX"}:
        raise ValueError("M49 supplements must be exactly TWN and XKX")
    if str(supplements["TWN"].get("m49")).zfill(3) != "158":
        raise ValueError("TWN must use statistical M49 code 158")
    if str(supplements["XKX"].get("m49")).zfill(3) != "412":
        raise ValueError("XKX must use statistical M49 code 412")

    income = config["world_bank_income"]
    expected_income_map = {"L": "LIC", "LM": "LMC", "UM": "UMC", "H": "HIC"}
    if income.get("raw_code_to_group") != expected_income_map:
        raise ValueError("Unexpected World Bank income-code mapping")
    if set(income.get("groups", {})) != {"LIC", "LMC", "UMC", "HIC", "NCL"}:
        raise ValueError("World Bank income groups must include LIC/LMC/UMC/HIC/NCL")
    if income.get("synthetic_account_proxies", {}).get("OTHER_EASTERN_ASIA") != "TWN":
        raise ValueError("OTHER_EASTERN_ASIA must use TWN as its income proxy")

    if int(config["coverage_gate"].get("expected_interim_benchmark_accounts", -1)) != 193:
        raise ValueError("Interim benchmark coverage gate must be 193 accounts")


def _required_m49_table(path: Path) -> pd.DataFrame:
    required = {
        "Region Code",
        "Region Name",
        "Sub-region Code",
        "Sub-region Name",
        "Intermediate Region Code",
        "Intermediate Region Name",
        "Country or Area",
        "M49 Code",
        "ISO-alpha3 Code",
    }
    candidates = [table for table in pd.read_html(path) if required <= set(table.columns)]
    if not candidates:
        raise ValueError(f"No UN M49 country/area table found in {path}")
    # The saved UN page contains the same coded table in several languages.
    # Select the English labels explicitly and require all language variants
    # to agree on the complete geographic code structure.
    english = [
        table
        for table in candidates
        if "Africa" in set(table["Region Name"].dropna().astype(str))
        and "Eastern Asia" in set(table["Sub-region Name"].dropna().astype(str))
    ]
    if len(english) != 1:
        raise ValueError(f"Expected one English UN M49 table in {path}")
    comparison_columns = [
        "M49 Code",
        "ISO-alpha3 Code",
        "Region Code",
        "Sub-region Code",
        "Intermediate Region Code",
    ]
    reference_table = english[0][comparison_columns].reset_index(drop=True)
    if any(
        not table[comparison_columns].reset_index(drop=True).equals(reference_table)
        for table in candidates[1:]
    ):
        raise ValueError(f"Conflicting UN M49 tables found in {path}")
    return english[0].copy()


def _required_code(series: pd.Series, label: str) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.isna().any():
        raise ValueError(f"Missing or invalid {label}")
    return numeric.astype(int).astype(str).str.zfill(3)


def _nullable_code(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.map(lambda value: pd.NA if pd.isna(value) else f"{int(value):03d}")


def load_un_m49_geography(
    un_m49_html: str | Path,
    reporting_config: Mapping[str, Any],
) -> pd.DataFrame:
    """Rebuild the 248-row M49 table and append explicit TWN/XKX geography."""

    validate_reporting_config(reporting_config)
    raw = _required_m49_table(Path(un_m49_html))
    raw = raw.rename(
        columns={
            "ISO-alpha3 Code": "source_economy_id",
            "Country or Area": "source_name",
            "M49 Code": "m49",
            "Region Code": "region_code",
            "Region Name": "region_name",
            "Sub-region Code": "subregion_code",
            "Sub-region Name": "subregion_name",
            "Intermediate Region Code": "intermediate_region_code",
            "Intermediate Region Name": "intermediate_region_name",
        }
    )
    columns = [
        "source_economy_id",
        "source_name",
        "m49",
        "region_code",
        "region_name",
        "subregion_code",
        "subregion_name",
        "intermediate_region_code",
        "intermediate_region_name",
    ]
    geography = raw[columns].copy()
    geography["source_economy_id"] = (
        geography["source_economy_id"].astype(str).str.strip().str.upper()
    )
    if not geography["source_economy_id"].str.fullmatch(r"[A-Z]{3}").all():
        raise ValueError("UN M49 ISO-alpha3 identifiers are invalid")
    geography["m49"] = _required_code(geography["m49"], "M49 country code")
    geography["region_code"] = _nullable_code(geography["region_code"])
    geography["subregion_code"] = _nullable_code(geography["subregion_code"])
    geography["intermediate_region_code"] = _nullable_code(
        geography["intermediate_region_code"]
    )
    geography["intermediate_region_name"] = geography[
        "intermediate_region_name"
    ].where(geography["intermediate_region_code"].notna(), pd.NA)
    if len(geography) != 248:
        raise ValueError("Raw UN M49 table must contain exactly 248 country/area rows")

    unassigned = reporting_config["unassigned_m49_geography"]
    missing_region = set(
        geography.loc[
            geography["region_code"].isna() | geography["subregion_code"].isna(),
            "source_economy_id",
        ]
    )
    if missing_region != set(unassigned["source_economies"]):
        raise ValueError(
            f"Unexpected blank UN M49 geography: {sorted(missing_region)}"
        )
    missing_mask = geography["source_economy_id"].isin(missing_region)
    geography.loc[missing_mask, "region_code"] = str(
        unassigned["group_code"]
    ).zfill(3)
    geography.loc[missing_mask, "region_name"] = unassigned["group_name"]
    geography.loc[missing_mask, "subregion_code"] = str(
        unassigned["group_code"]
    ).zfill(3)
    geography.loc[missing_mask, "subregion_name"] = unassigned["group_name"]

    supplements = []
    for economy_id, record in reporting_config[
        "supplemental_source_geographies"
    ].items():
        supplements.append(
            {
                "source_economy_id": economy_id,
                "source_name": record["source_name"],
                "m49": str(record["m49"]).zfill(3),
                "region_code": str(record["region_code"]).zfill(3),
                "region_name": record["region_name"],
                "subregion_code": str(record["subregion_code"]).zfill(3),
                "subregion_name": record["subregion_name"],
                "intermediate_region_code": record.get("intermediate_region_code"),
                "intermediate_region_name": record.get("intermediate_region_name"),
            }
        )
    geography = pd.concat([geography, pd.DataFrame(supplements)], ignore_index=True)
    if (
        len(geography) != 250
        or geography["source_economy_id"].duplicated().any()
        or geography["m49"].duplicated().any()
    ):
        raise ValueError("Canonical source geography must contain 250 unique rows")

    use_intermediate = geography["intermediate_region_code"].notna()
    geography["reporting_area_code"] = geography["subregion_code"]
    geography["reporting_area_name"] = geography["subregion_name"]
    geography.loc[use_intermediate, "reporting_area_code"] = geography.loc[
        use_intermediate, "intermediate_region_code"
    ]
    geography.loc[use_intermediate, "reporting_area_name"] = geography.loc[
        use_intermediate, "intermediate_region_name"
    ]
    return geography.sort_values("source_economy_id").reset_index(drop=True)


def build_source_geography(
    un_m49_html: str | Path,
    reporting_config: Mapping[str, Any],
    territory_config: Mapping[str, Any],
) -> pd.DataFrame:
    """Join original M49 reporting geography to accounting destinations."""

    validate_territory_config(territory_config)
    geography = load_un_m49_geography(un_m49_html, reporting_config)
    crosswalk = territory_crosswalk(territory_config).set_index("source_economy_id")
    source = geography["source_economy_id"]
    geography["territory_aggregation_source"] = source.isin(crosswalk.index)
    geography["accounting_target"] = source.map(crosswalk["accounting_target"]).fillna(
        source
    )
    # Only the 25 explicit exclusions are decided at the source-geography
    # layer. Whether any other source is an observed model account is decided
    # separately from the concrete benchmark account universe.
    geography["source_model_entity"] = source.map(crosswalk["model_entity"]).astype(
        "boolean"
    )
    geography["accounting_target_type"] = source.map(
        crosswalk["accounting_target_type"]
    ).fillna("own_economy_account")

    mapped = geography[geography["territory_aggregation_source"]].set_index(
        "source_economy_id"
    )
    expected_region = crosswalk["reporting_region_target"]
    expected_area = crosswalk["reporting_subregion_target"]
    bad_region = mapped.index[mapped["region_code"].ne(expected_region)].tolist()
    bad_area = mapped.index[mapped["reporting_area_code"].ne(expected_area)].tolist()
    if bad_region or bad_area:
        raise ValueError(
            "Territory reporting geography disagrees with raw M49: "
            f"region={sorted(bad_region)}, reporting_area={sorted(bad_area)}"
        )
    return geography


def build_source_geography_membership(source_geography: pd.DataFrame) -> pd.DataFrame:
    """Build exclusive UN memberships keyed by original source economy."""

    required = {
        "source_economy_id",
        "accounting_target",
        "region_code",
        "region_name",
        "subregion_code",
        "subregion_name",
        "reporting_area_code",
        "reporting_area_name",
    }
    if not required <= set(source_geography.columns):
        raise ValueError(
            f"Source geography is missing: {sorted(required-set(source_geography.columns))}"
        )
    if source_geography["source_economy_id"].duplicated().any():
        raise ValueError("Source geography identifiers must be unique")

    rows: list[dict[str, Any]] = []
    definitions = (
        ("UN_REGION", "region_code", "region_name"),
        ("UN_SUBREGION", "subregion_code", "subregion_name"),
        ("UN_REPORTING_AREA", "reporting_area_code", "reporting_area_name"),
    )
    for record in source_geography.to_dict("records"):
        for system, code_column, name_column in definitions:
            if pd.isna(record[code_column]) or pd.isna(record[name_column]):
                raise ValueError(
                    f"{record['source_economy_id']} lacks a {system} assignment"
                )
            rows.append(
                {
                    "membership_layer": "source_geography",
                    "group_system": system,
                    "group_code": str(record[code_column]).zfill(3),
                    "group_name": record[name_column],
                    "source_economy_id": record["source_economy_id"],
                    "accounting_target": record["accounting_target"],
                }
            )
    membership = pd.DataFrame(rows)
    if membership.duplicated(["group_system", "source_economy_id"]).any():
        raise AssertionError("A source economy was assigned twice within a UN system")
    expected = set(source_geography["source_economy_id"])
    for system in SOURCE_GROUP_SYSTEMS:
        actual = set(
            membership.loc[membership["group_system"].eq(system), "source_economy_id"]
        )
        if actual != expected:
            raise AssertionError(f"Incomplete {system} source membership")
    if membership["group_code"].eq("WORLD").any():
        raise AssertionError("World must not be generated from source-geography membership")
    return membership.sort_values(
        ["group_system", "group_code", "source_economy_id"]
    ).reset_index(drop=True)


def load_world_bank_income_groups(
    workbook: str | Path,
    reporting_config: Mapping[str, Any],
) -> pd.DataFrame:
    """Load the configured World Bank fiscal-year income interface."""

    validate_reporting_config(reporting_config)
    income = reporting_config["world_bank_income"]
    table = pd.read_excel(
        workbook,
        sheet_name=income["source_sheet"],
        header=int(income["header_row_zero_based"]),
        dtype=object,
    )
    required = {
        income["source_code_column"],
        income["source_name_column"],
        income["fiscal_year_column"],
    }
    if not required <= set(table.columns):
        raise ValueError(f"World Bank workbook is missing: {sorted(required-set(table.columns))}")
    result = table[
        [
            income["source_code_column"],
            income["source_name_column"],
            income["fiscal_year_column"],
        ]
    ].copy()
    result.columns = ["economy_id", "economy_name", "raw_income_code"]
    result["economy_id"] = result["economy_id"].astype("string").str.strip().str.upper()
    result = result[result["economy_id"].str.fullmatch(r"[A-Z]{3}", na=False)].copy()
    if result["economy_id"].duplicated().any():
        raise ValueError("World Bank income codes must be unique")
    result["raw_income_code"] = result["raw_income_code"].astype("string").str.strip()
    result["group_code"] = result["raw_income_code"].map(income["raw_code_to_group"])
    result["group_code"] = result["group_code"].fillna("NCL")
    result["group_name"] = result["group_code"].map(income["groups"])
    result["group_system"] = income["group_system"]
    result["classification_period"] = income["fiscal_year_column"]
    result["represented_calendar_year"] = int(income["represented_calendar_year"])
    return result.sort_values("economy_id").reset_index(drop=True)


def _model_accounts(
    values: pd.DataFrame | Iterable[str], entity_column: str = "economy_id"
) -> list[str]:
    if isinstance(values, pd.DataFrame):
        if entity_column not in values.columns:
            raise ValueError(f"Missing model-account column: {entity_column}")
        raw = values[entity_column]
    else:
        raw = pd.Series(list(values), dtype="object")
    accounts = sorted(set(raw.astype(str).str.strip().str.upper()))
    if not accounts or "" in accounts:
        raise ValueError("Model-account list must be non-empty and contain no blanks")
    forbidden = set(accounts) & FORBIDDEN_MODEL_ACCOUNT_CODES
    if forbidden:
        raise ValueError(f"Reporting aggregates cannot be model accounts: {sorted(forbidden)}")
    return accounts


def build_model_account_membership(
    model_accounts: pd.DataFrame | Iterable[str],
    reporting_config: Mapping[str, Any],
    *,
    income_groups: pd.DataFrame | None = None,
    territory_config: Mapping[str, Any] | None = None,
    entity_column: str = "economy_id",
) -> pd.DataFrame:
    """Build World/focus/EU27/WB membership with one World row per account."""

    validate_reporting_config(reporting_config)
    accounts = _model_accounts(model_accounts, entity_column)
    if territory_config is not None:
        validate_territory_config(territory_config)
        territory_sources = set(territory_crosswalk(territory_config)["source_economy_id"])
        surviving = set(accounts) & territory_sources
        if surviving:
            raise ValueError(
                f"Territory sources cannot be model accounts: {sorted(surviving)}"
            )

    rows: list[dict[str, Any]] = []

    def add(system: str, code: str, name: str, members: Iterable[str]) -> None:
        for account in sorted(set(members) & set(accounts)):
            rows.append(
                {
                    "membership_layer": "model_account",
                    "group_system": system,
                    "group_code": code,
                    "group_name": name,
                    "model_account_id": account,
                }
            )

    world = reporting_config["global_group"]
    add(world["group_system"], world["group_code"], world["group_name"], accounts)
    for code, definition in reporting_config["focus_groups"].items():
        add("FOCUS", code, definition["group_name"], definition["model_accounts"])
    for code, definition in reporting_config["economic_groups"].items():
        add("ECONOMIC", code, definition["group_name"], definition["model_accounts"])

    if income_groups is not None:
        required_income = {"economy_id", "group_code", "group_name"}
        if not required_income <= set(income_groups.columns):
            raise ValueError(
                f"Income interface is missing: {sorted(required_income-set(income_groups.columns))}"
            )
        if income_groups["economy_id"].duplicated().any():
            raise ValueError("Income interface economy identifiers must be unique")
        keyed_income = income_groups.set_index("economy_id")
        income_config = reporting_config["world_bank_income"]
        proxies = income_config.get("synthetic_account_proxies", {})
        for account in accounts:
            lookup = proxies.get(account, account)
            if lookup in keyed_income.index:
                group_code = keyed_income.at[lookup, "group_code"]
                group_name = keyed_income.at[lookup, "group_name"]
            else:
                group_code = "NCL"
                group_name = income_config["groups"]["NCL"]
            rows.append(
                {
                    "membership_layer": "model_account",
                    "group_system": income_config["group_system"],
                    "group_code": group_code,
                    "group_name": group_name,
                    "model_account_id": account,
                }
            )

    membership = pd.DataFrame(rows)
    if membership.duplicated(
        ["group_system", "group_code", "model_account_id"]
    ).any():
        raise AssertionError("Duplicate model-account reporting membership")
    world_rows = membership[membership["group_system"].eq("GLOBAL")]
    if len(world_rows) != len(accounts) or set(world_rows["model_account_id"]) != set(
        accounts
    ):
        raise AssertionError("Every model account must enter World exactly once")
    return membership.sort_values(
        ["group_system", "group_code", "model_account_id"]
    ).reset_index(drop=True)


def account_coverage_report(
    model_accounts: pd.DataFrame | Iterable[str],
    membership: pd.DataFrame,
    reporting_config: Mapping[str, Any],
    *,
    territory_config: Mapping[str, Any] | None = None,
    entity_column: str = "economy_id",
) -> dict[str, Any]:
    """Audit World and WB coverage for a concrete model-account universe."""

    validate_reporting_config(reporting_config)
    accounts = set(_model_accounts(model_accounts, entity_column))
    world = membership[membership["group_system"].eq("GLOBAL")]
    world_counts = world["model_account_id"].value_counts()
    missing_world = sorted(accounts - set(world["model_account_id"]))
    duplicate_world = sorted(world_counts[world_counts.ne(1)].index.tolist())

    wb_system = reporting_config["world_bank_income"]["group_system"]
    wb = membership[membership["group_system"].eq(wb_system)]
    wb_counts = wb["model_account_id"].value_counts()
    missing_wb = sorted(accounts - set(wb["model_account_id"]))
    duplicate_wb = sorted(wb_counts[wb_counts.ne(1)].index.tolist())

    surviving_territories: list[str] = []
    if territory_config is not None:
        territory_sources = set(territory_crosswalk(territory_config)["source_economy_id"])
        surviving_territories = sorted(accounts & territory_sources)

    expected = int(
        reporting_config["coverage_gate"]["expected_interim_benchmark_accounts"]
    )
    passed = (
        len(accounts) == expected
        and not missing_world
        and not duplicate_world
        and len(world) == len(accounts)
        and not missing_wb
        and not duplicate_wb
        and len(wb) == len(accounts)
        and not surviving_territories
    )
    return {
        "model_account_count": len(accounts),
        "expected_model_account_count": expected,
        "world_membership_rows": int(len(world)),
        "world_unique_accounts": int(world["model_account_id"].nunique()),
        "world_missing_accounts": missing_world,
        "world_duplicate_accounts": duplicate_world,
        "wb_income_membership_rows": int(len(wb)),
        "wb_income_missing_accounts": missing_wb,
        "wb_income_duplicate_accounts": duplicate_wb,
        "territory_sources_surviving_as_accounts": surviving_territories,
        "status": "passed" if passed else "blocked",
    }


def _aggregate_values(
    frame: pd.DataFrame,
    membership: pd.DataFrame,
    *,
    entity_column: str,
    member_column: str,
    value_columns: Sequence[str],
    dimension_columns: Sequence[str],
    group_systems: Iterable[str] | None,
) -> pd.DataFrame:
    values = list(value_columns)
    dimensions = list(dimension_columns)
    if not values or len(values) != len(set(values)):
        raise ValueError("value_columns must be non-empty and unique")
    if len(dimensions) != len(set(dimensions)):
        raise ValueError("dimension_columns must be unique")
    required = {entity_column, *values, *dimensions}
    if not required <= set(frame.columns):
        raise ValueError(f"Reporting input is missing: {sorted(required-set(frame.columns))}")
    membership_required = {
        member_column,
        "group_system",
        "group_code",
        "group_name",
    }
    if not membership_required <= set(membership.columns):
        raise ValueError(
            f"Reporting membership is missing: {sorted(membership_required-set(membership.columns))}"
        )

    data = frame[[entity_column, *dimensions, *values]].copy()
    data[entity_column] = data[entity_column].astype(str).str.strip().str.upper()
    key = [*dimensions, entity_column]
    if data.duplicated(key).any():
        raise ValueError("Duplicate entity rows within a reporting slice")
    for column in values:
        numeric = pd.to_numeric(data[column], errors="coerce")
        if numeric.isna().any() or not numeric.map(lambda value: isfinite(float(value))).all():
            raise ValueError(f"Reporting values must be finite and non-null: {column}")
        data[column] = numeric

    selected = membership.copy()
    if group_systems is not None:
        requested = set(group_systems)
        selected = selected[selected["group_system"].isin(requested)]
        missing_systems = requested - set(selected["group_system"])
        if missing_systems:
            raise ValueError(f"Unknown or empty reporting systems: {sorted(missing_systems)}")
    selected = selected.rename(columns={member_column: entity_column})
    observed = set(data[entity_column])
    for system in set(selected["group_system"]) & EXCLUSIVE_GROUP_SYSTEMS:
        system_membership = selected[selected["group_system"].eq(system)]
        counts = system_membership[entity_column].value_counts()
        missing_members = observed - set(system_membership[entity_column])
        duplicate_members = set(counts[counts.ne(1)].index) & observed
        if missing_members or duplicate_members:
            raise ValueError(
                f"Invalid exclusive {system} coverage: "
                f"missing={sorted(missing_members)}, "
                f"duplicate={sorted(duplicate_members)}"
            )
    merged = data.merge(
        selected[[entity_column, "group_system", "group_code", "group_name"]],
        on=entity_column,
        how="inner",
        validate="many_to_many",
    )
    keys = ["group_system", "group_code", "group_name", *dimensions]
    return (
        merged.groupby(keys, as_index=False, dropna=False)[values]
        .sum(min_count=1)
        .sort_values(keys)
        .reset_index(drop=True)
    )


def aggregate_model_account_values(
    frame: pd.DataFrame,
    membership: pd.DataFrame,
    *,
    value_columns: Sequence[str],
    dimension_columns: Sequence[str],
    entity_column: str = "economy_id",
    group_systems: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Aggregate solved account values to account-basis reporting groups."""

    return _aggregate_values(
        frame,
        membership,
        entity_column=entity_column,
        member_column="model_account_id",
        value_columns=value_columns,
        dimension_columns=dimension_columns,
        group_systems=group_systems,
    )


def aggregate_source_geography_values(
    frame: pd.DataFrame,
    membership: pd.DataFrame,
    *,
    value_columns: Sequence[str],
    dimension_columns: Sequence[str],
    entity_column: str = "economy_id",
    group_systems: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Aggregate original source contributions to their original UN geography."""

    return _aggregate_values(
        frame,
        membership,
        entity_column=entity_column,
        member_column="source_economy_id",
        value_columns=value_columns,
        dimension_columns=dimension_columns,
        group_systems=group_systems,
    )
