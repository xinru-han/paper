from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

import run_maidads_pipeline as pipe


ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "ProvinceMAIDADS"
RESULTS = PROJECT / "Results"
DATA_OUT = PROJECT / "Data" / "output"
OUT_DIR = RESULTS / "GDP_Food_Nutrition"

GROUP_LABEL_CN = {
    "grain": "主粮",
    "oil": "食用油",
    "vegfruit": "蔬菜水果",
    "pork": "猪肉",
    "meatother": "非猪肉肉类及水产品",
    "meatsea": "肉类水产",
    "dairyegg": "奶类蛋类",
    "all_food": "覆盖食品合计",
}

ITEM_LABEL_CN = {
    "grain": "主粮",
    "oil": "食用油",
    "vegetable": "蔬菜",
    "fruit": "水果",
    "pork": "猪肉",
    "beef": "牛肉",
    "mutton": "羊肉",
    "poultry": "禽肉",
    "aquatic": "水产品",
    "egg": "蛋类",
    "milk": "奶类",
}


def md_table(df: pd.DataFrame, digits: int = 2) -> str:
    tmp = df.copy()
    for col in tmp.select_dtypes(include=[np.number]).columns:
        tmp[col] = tmp[col].map(lambda x: "" if pd.isna(x) else f"{x:.{digits}f}")
    tmp = tmp.fillna("").astype(str)
    lines = [
        "| " + " | ".join(map(str, tmp.columns)) + " |",
        "| " + " | ".join(["---"] * len(tmp.columns)) + " |",
    ]
    for row in tmp.itertuples(index=False):
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cdf = np.cumsum(weights) / np.sum(weights)
    return float(values[np.searchsorted(cdf, q)])


def weighted_loglog_slope(df: pd.DataFrame) -> tuple[float, float]:
    x = np.log(df["pgdp_real_2023"].to_numpy(float))
    y = np.log(df["m"].to_numpy(float))
    w = df["population_10k"].to_numpy(float)
    xmat = np.column_stack([np.ones(len(x)), x])
    sw = np.sqrt(w / w.sum())
    coef = np.linalg.lstsq(xmat * sw[:, None], y * sw, rcond=None)[0]
    return float(coef[0]), float(coef[1])


def load_params(group_names: list[str]) -> dict[str, np.ndarray | float]:
    params = pd.read_csv(RESULTS / "parameter_estimates.csv")
    maidads = params[params["model"].eq("MAIDADS_sat")].copy()
    maidads = maidads.set_index("group").loc[group_names].reset_index()
    return {
        "alpha": maidads["alpha"].to_numpy(float),
        "beta": maidads["beta"].to_numpy(float),
        "delta": maidads["delta"].to_numpy(float),
        "tau": maidads["tau"].to_numpy(float),
        "omega": float(maidads["omega"].iloc[0]),
        "kappa": float(maidads["kappa"].iloc[0]),
    }


def nutrition_per_kg() -> pd.DataFrame:
    nutrition = pd.read_csv(DATA_OUT / "nutrition_processed.csv").copy()
    for col in ["protein", "fat", "carb"]:
        nutrition[f"{col}_g_per_kg_as_purchased"] = nutrition[col] * 10 * nutrition["edible_share"] / 100

    grain_weights = pd.read_csv(DATA_OUT / "grain_weights_processed.csv")
    grain = grain_weights.merge(
        nutrition[
            [
                "code",
                "protein_g_per_kg_as_purchased",
                "fat_g_per_kg_as_purchased",
                "carb_g_per_kg_as_purchased",
            ]
        ],
        on="code",
        how="left",
    )
    grain_row = {
        "item": "grain",
        "group": "grain",
        "item_label_cn": ITEM_LABEL_CN["grain"],
        "kcal_per_kg": float((grain["kcal_weight"] * grain["kcal_per_kg_as_purchased"]).sum()),
        "protein_g_per_kg": float((grain["kcal_weight"] * grain["protein_g_per_kg_as_purchased"]).sum()),
        "fat_g_per_kg": float((grain["kcal_weight"] * grain["fat_g_per_kg_as_purchased"]).sum()),
        "carb_g_per_kg": float((grain["kcal_weight"] * grain["carb_g_per_kg_as_purchased"]).sum()),
    }

    oil_codes = ["SOYO", "RAPO", "GRDO"]
    oil = nutrition[nutrition["code"].isin(oil_codes)]
    oil_row = {
        "item": "oil",
        "group": "oil",
        "item_label_cn": ITEM_LABEL_CN["oil"],
        "kcal_per_kg": float(oil["kcal_per_kg_as_purchased"].mean()),
        "protein_g_per_kg": float(oil["protein_g_per_kg_as_purchased"].mean()),
        "fat_g_per_kg": float(oil["fat_g_per_kg_as_purchased"].mean()),
        "carb_g_per_kg": float(oil["carb_g_per_kg_as_purchased"].mean()),
    }

    rows = [grain_row, oil_row]
    for item, spec in pipe.FOOD_ITEMS.items():
        if item in {"grain", "oil"}:
            continue
        row = nutrition[nutrition["code"].eq(spec["code"])].iloc[0]
        group = next(g for g, items in pipe.GROUPS.items() if item in items)
        rows.append(
            {
                "item": item,
                "group": group,
                "item_label_cn": ITEM_LABEL_CN[item],
                "kcal_per_kg": float(row["kcal_per_kg_as_purchased"]),
                "protein_g_per_kg": float(row["protein_g_per_kg_as_purchased"]),
                "fat_g_per_kg": float(row["fat_g_per_kg_as_purchased"]),
                "carb_g_per_kg": float(row["carb_g_per_kg_as_purchased"]),
            }
        )
    return pd.DataFrame(rows)


def national_item_kcal_shares(item_nutrition: pd.DataFrame) -> pd.DataFrame:
    raw = pd.read_stata(ROOT / "ProvinceData" / "workdata" / "data.dta")
    panel = pd.read_csv(DATA_OUT / "maidads6_panel.csv")
    base = raw[raw["year"].eq(2023)][["province", "provincechn"] + [spec["q"] for spec in pipe.FOOD_ITEMS.values()]].copy()
    base = base.merge(panel[panel["year"].eq(2023)][["province", "population_10k"]], on="province", how="left")

    rows = []
    for _, nrow in item_nutrition.iterrows():
        item = nrow["item"]
        if item in {"grain", "oil"}:
            q_col = pipe.FOOD_ITEMS[item]["q"]
        else:
            q_col = pipe.FOOD_ITEMS[item]["q"]
        kg_total = (pd.to_numeric(base[q_col], errors="coerce") * base["population_10k"] * 10000).sum()
        kcal_total = kg_total * float(nrow["kcal_per_kg"])
        rows.append(
            {
                "item": item,
                "group": nrow["group"],
                "item_label_cn": nrow["item_label_cn"],
                "kg_total_2023": kg_total,
                "kcal_total_2023": kcal_total,
            }
        )
    out = pd.DataFrame(rows)
    group_total = out.groupby("group", as_index=False)["kcal_total_2023"].sum().rename(
        columns={"kcal_total_2023": "group_kcal_total_2023"}
    )
    out = out.merge(group_total, on="group", how="left")
    out["group_kcal_share_2023"] = out["kcal_total_2023"] / out["group_kcal_total_2023"]
    return out[["item", "group", "item_label_cn", "group_kcal_share_2023"]]


def build_income_bridge(panel: pd.DataFrame) -> dict[str, float]:
    raw = pd.read_stata(ROOT / "ProvinceData" / "workdata" / "data.dta")
    bridge = raw[["province", "year", "pgdp"]].merge(
        panel[["province", "year", "m", "population_10k", "total_price_index_2023"]],
        on=["province", "year"],
        how="inner",
    )
    bridge["pgdp_real_2023"] = bridge["pgdp"] / (bridge["total_price_index_2023"] / 100)
    intercept, slope = weighted_loglog_slope(bridge)
    base = bridge[bridge["year"].eq(2023)]
    return {
        "intercept": intercept,
        "slope": slope,
        "base_pgdp": float(np.average(base["pgdp_real_2023"], weights=base["population_10k"])),
        "base_m": float(np.average(base["m"], weights=base["population_10k"])),
        "pgdp_p05": weighted_quantile(
            bridge["pgdp_real_2023"].to_numpy(float),
            bridge["population_10k"].to_numpy(float),
            0.05,
        ),
        "pgdp_p95": weighted_quantile(
            bridge["pgdp_real_2023"].to_numpy(float),
            bridge["population_10k"].to_numpy(float),
            0.95,
        ),
        "m_min": float(bridge["m"].min()),
        "m_max": float(bridge["m"].max()),
    }


def predict_scenarios(panel: pd.DataFrame, bridge: dict[str, float]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    group_names = list(pipe.GROUPS.keys())
    params = load_params(group_names)
    base = panel[panel["year"].eq(2023)]
    p_fixed = np.array(
        [np.average(base[f"p_{g}_model"], weights=base["population_10k"]) for g in group_names],
        dtype=float,
    )
    multipliers = np.array([0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0])
    pgdp = bridge["base_pgdp"] * multipliers
    m = bridge["base_m"] * (pgdp / bridge["base_pgdp"]) ** bridge["slope"]
    arr = pipe.ModelArrays(
        obs_ids=np.array([f"gdp_{x:g}x" for x in multipliers]),
        provinces=np.zeros(len(multipliers), dtype=int),
        years=np.zeros(len(multipliers), dtype=int),
        group_names=group_names,
        x=np.zeros((len(multipliers), len(group_names))),
        p=np.tile(p_fixed, (len(multipliers), 1)),
        m=m,
    )
    xhat, u = pipe.predict_x(params, arr)
    if xhat is None:
        raise RuntimeError("MAIDADS prediction failed for GDP scenarios.")
    scenario = pd.DataFrame(
        {
            "scenario": [f"{x:g}x_2023_pgdp" for x in multipliers],
            "pgdp_multiplier_vs_2023": multipliers,
            "pgdp_real_2023_yuan_per_person": pgdp,
            "pgdp_index_2023_100": multipliers * 100,
            "model_m_real_2023_yuan_per_person": m,
            "m_support_flag": [
                pipe.support_flag(float(v), bridge["m_min"], bridge["m_max"])
                for v in m
            ],
            "u": u,
        }
    )

    group_rows = []
    for r, scen in scenario.iterrows():
        for j, group in enumerate(group_names):
            if group == "nonfood":
                continue
            group_rows.append(
                {
                    **scen.to_dict(),
                    "group": group,
                    "group_label_cn": GROUP_LABEL_CN[group],
                    "xhat_2000kcal_units_per_day": xhat[r, j],
                    "kcal_per_cap_day": xhat[r, j] * 2000,
                }
            )
    group_demand = pd.DataFrame(group_rows)
    return scenario, group_demand, pd.DataFrame({"group": group_names, "p_fixed_2023": p_fixed})


def add_kg_and_nutrients(group_demand: pd.DataFrame, item_nutrition: pd.DataFrame, shares: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    item_map = shares.merge(item_nutrition, on=["item", "group", "item_label_cn"], how="left")
    item_rows = []
    for _, grow in group_demand.iterrows():
        tmp = item_map[item_map["group"].eq(grow["group"])]
        for _, item in tmp.iterrows():
            item_kcal_day = float(grow["kcal_per_cap_day"]) * float(item["group_kcal_share_2023"])
            kg_per_cap_day = item_kcal_day / float(item["kcal_per_kg"])
            item_rows.append(
                {
                    "scenario": grow["scenario"],
                    "pgdp_multiplier_vs_2023": grow["pgdp_multiplier_vs_2023"],
                    "pgdp_real_2023_yuan_per_person": grow["pgdp_real_2023_yuan_per_person"],
                    "group": grow["group"],
                    "group_label_cn": grow["group_label_cn"],
                    "item": item["item"],
                    "item_label_cn": item["item_label_cn"],
                    "item_kcal_share_within_group_2023": item["group_kcal_share_2023"],
                    "kcal_per_cap_day": item_kcal_day,
                    "kg_per_cap_year": kg_per_cap_day * 365,
                    "protein_g_per_cap_day": kg_per_cap_day * float(item["protein_g_per_kg"]),
                    "fat_g_per_cap_day": kg_per_cap_day * float(item["fat_g_per_kg"]),
                    "carb_g_per_cap_day": kg_per_cap_day * float(item["carb_g_per_kg"]),
                }
            )
    item_demand = pd.DataFrame(item_rows)
    group_extra = item_demand.groupby(["scenario", "group"], as_index=False).agg(
        kg_per_cap_year=("kg_per_cap_year", "sum"),
        protein_g_per_cap_day=("protein_g_per_cap_day", "sum"),
        fat_g_per_cap_day=("fat_g_per_cap_day", "sum"),
        carb_g_per_cap_day=("carb_g_per_cap_day", "sum"),
    )
    group_demand = group_demand.merge(group_extra, on=["scenario", "group"], how="left")
    total_rows = []
    scenario_cols = [
        "scenario",
        "pgdp_multiplier_vs_2023",
        "pgdp_real_2023_yuan_per_person",
        "pgdp_index_2023_100",
        "model_m_real_2023_yuan_per_person",
        "m_support_flag",
        "u",
    ]
    for scenario, tmp in group_demand.groupby("scenario", sort=False):
        base = tmp.iloc[0][scenario_cols].to_dict()
        total_rows.append(
            {
                **base,
                "group": "all_food",
                "group_label_cn": GROUP_LABEL_CN["all_food"],
                "xhat_2000kcal_units_per_day": tmp["xhat_2000kcal_units_per_day"].sum(),
                "kcal_per_cap_day": tmp["kcal_per_cap_day"].sum(),
                "kg_per_cap_year": tmp["kg_per_cap_year"].sum(),
                "protein_g_per_cap_day": tmp["protein_g_per_cap_day"].sum(),
                "fat_g_per_cap_day": tmp["fat_g_per_cap_day"].sum(),
                "carb_g_per_cap_day": tmp["carb_g_per_cap_day"].sum(),
            }
        )
    group_demand = pd.concat([group_demand, pd.DataFrame(total_rows)], ignore_index=True)
    group_order = ["grain", "oil", "vegfruit", "pork", "meatother", "dairyegg", "all_food"]
    group_demand["group_order"] = group_demand["group"].map({g: i for i, g in enumerate(group_order)})
    group_demand = group_demand.sort_values(["pgdp_multiplier_vs_2023", "group_order"]).drop(columns="group_order")

    nutrition = item_demand.groupby(
        ["scenario", "pgdp_multiplier_vs_2023", "pgdp_real_2023_yuan_per_person"],
        as_index=False,
        sort=False,
    ).agg(
        energy_kcal_per_cap_day=("kcal_per_cap_day", "sum"),
        carbohydrate_g_per_cap_day=("carb_g_per_cap_day", "sum"),
        fat_g_per_cap_day=("fat_g_per_cap_day", "sum"),
        protein_g_per_cap_day=("protein_g_per_cap_day", "sum"),
        food_kg_per_cap_year=("kg_per_cap_year", "sum"),
    )
    nutrition["carb_energy_share_pct"] = nutrition["carbohydrate_g_per_cap_day"] * 4 / nutrition["energy_kcal_per_cap_day"] * 100
    nutrition["fat_energy_share_pct"] = nutrition["fat_g_per_cap_day"] * 9 / nutrition["energy_kcal_per_cap_day"] * 100
    nutrition["protein_energy_share_pct"] = nutrition["protein_g_per_cap_day"] * 4 / nutrition["energy_kcal_per_cap_day"] * 100
    nutrition = nutrition.sort_values("pgdp_multiplier_vs_2023")
    return group_demand, item_demand, nutrition


def build_markdown(
    bridge: dict[str, float],
    scenario: pd.DataFrame,
    group_demand: pd.DataFrame,
    item_demand: pd.DataFrame,
    nutrition: pd.DataFrame,
) -> str:
    demand_pivot = group_demand.pivot_table(
        index=["pgdp_multiplier_vs_2023", "pgdp_real_2023_yuan_per_person"],
        columns="group_label_cn",
        values="kg_per_cap_year",
    ).reset_index()
    kcal_pivot = group_demand.pivot_table(
        index=["pgdp_multiplier_vs_2023", "pgdp_real_2023_yuan_per_person"],
        columns="group_label_cn",
        values="kcal_per_cap_day",
    ).reset_index()
    display_cols = [
        "pgdp_multiplier_vs_2023",
        "pgdp_real_2023_yuan_per_person",
        "主粮",
        "食用油",
        "蔬菜水果",
        "肉类水产",
        "奶类蛋类",
        "覆盖食品合计",
    ]
    demand_pivot = demand_pivot[[c for c in display_cols if c in demand_pivot.columns]]
    kcal_pivot = kcal_pivot[[c for c in display_cols if c in kcal_pivot.columns]]
    display_rename = {
        "pgdp_multiplier_vs_2023": "人均GDP倍数(2023=1)",
        "pgdp_real_2023_yuan_per_person": "人均GDP(2023价, 元/人)",
    }
    demand_pivot = demand_pivot.rename(columns=display_rename)
    kcal_pivot = kcal_pivot.rename(columns=display_rename)
    nutrition_view = nutrition[
        [
            "pgdp_multiplier_vs_2023",
            "pgdp_real_2023_yuan_per_person",
            "energy_kcal_per_cap_day",
            "carbohydrate_g_per_cap_day",
            "fat_g_per_cap_day",
            "protein_g_per_cap_day",
            "carb_energy_share_pct",
            "fat_energy_share_pct",
            "protein_energy_share_pct",
        ]
    ].copy()
    nutrition_view = nutrition_view.rename(
        columns={
            "pgdp_multiplier_vs_2023": "人均GDP倍数(2023=1)",
            "pgdp_real_2023_yuan_per_person": "人均GDP(2023价, 元/人)",
            "energy_kcal_per_cap_day": "膳食能量(kcal/人/日)",
            "carbohydrate_g_per_cap_day": "碳水化合物(g/人/日)",
            "fat_g_per_cap_day": "脂肪(g/人/日)",
            "protein_g_per_cap_day": "蛋白质(g/人/日)",
            "carb_energy_share_pct": "碳水供能比(%)",
            "fat_energy_share_pct": "脂肪供能比(%)",
            "protein_energy_share_pct": "蛋白质供能比(%)",
        }
    )
    scenario_view = scenario[
        [
            "pgdp_multiplier_vs_2023",
            "pgdp_real_2023_yuan_per_person",
            "model_m_real_2023_yuan_per_person",
            "m_support_flag",
        ]
    ].rename(
        columns={
            "pgdp_multiplier_vs_2023": "人均GDP倍数(2023=1)",
            "pgdp_real_2023_yuan_per_person": "人均GDP(2023价, 元/人)",
            "model_m_real_2023_yuan_per_person": "映射到模型支出m(2023价, 元/人)",
            "m_support_flag": "模型收入支持区间",
        }
    )
    base = group_demand[group_demand["pgdp_multiplier_vs_2023"].eq(1.0)]
    high = group_demand[group_demand["pgdp_multiplier_vs_2023"].eq(2.0)]
    change = base[["group", "group_label_cn", "kg_per_cap_year", "kcal_per_cap_day"]].merge(
        high[["group", "kg_per_cap_year", "kcal_per_cap_day"]],
        on="group",
        suffixes=("_2023_pgdp", "_2x_pgdp"),
    )
    change["kg_change_pct"] = (change["kg_per_cap_year_2x_pgdp"] / change["kg_per_cap_year_2023_pgdp"] - 1) * 100
    change["kcal_change_pct"] = (change["kcal_per_cap_day_2x_pgdp"] / change["kcal_per_cap_day_2023_pgdp"] - 1) * 100
    change = change[
        [
            "group_label_cn",
            "kg_per_cap_year_2023_pgdp",
            "kg_per_cap_year_2x_pgdp",
            "kg_change_pct",
            "kcal_per_cap_day_2023_pgdp",
            "kcal_per_cap_day_2x_pgdp",
            "kcal_change_pct",
        ]
    ].rename(
        columns={
            "group_label_cn": "食物类别",
            "kg_per_cap_year_2023_pgdp": "2023 GDP水平 kg/人/年",
            "kg_per_cap_year_2x_pgdp": "2倍GDP水平 kg/人/年",
            "kg_change_pct": "kg变化(%)",
            "kcal_per_cap_day_2023_pgdp": "2023 GDP水平 kcal/人/日",
            "kcal_per_cap_day_2x_pgdp": "2倍GDP水平 kcal/人/日",
            "kcal_change_pct": "kcal变化(%)",
        }
    )

    item_sample = item_demand[item_demand["pgdp_multiplier_vs_2023"].isin([1.0, 2.0])].copy()
    group_order = {g: i for i, g in enumerate(["主粮", "食用油", "蔬菜水果", "肉类水产", "奶类蛋类"])}
    item_sample["group_order"] = item_sample["group_label_cn"].map(group_order)
    item_sample = item_sample[
        [
            "pgdp_multiplier_vs_2023",
            "group_label_cn",
            "item_label_cn",
            "kg_per_cap_year",
            "kcal_per_cap_day",
            "group_order",
        ]
    ].sort_values(["pgdp_multiplier_vs_2023", "group_order", "item_label_cn"]).drop(columns="group_order")
    item_sample = item_sample.rename(
        columns={
            "pgdp_multiplier_vs_2023": "人均GDP倍数(2023=1)",
            "group_label_cn": "食物大类",
            "item_label_cn": "细项",
            "kg_per_cap_year": "kg/人/年",
            "kcal_per_cap_day": "kcal/人/日",
        }
    )

    notes = [
        "# 人均 GDP 增长下的食物需求与营养摄入情景结果",
        "",
        "## 口径说明",
        "",
        "- 本结果使用主模型 `MAIDADS_sat` 参数，价格固定为 2023 年省级人口加权均值，只看人均 GDP/收入增长带来的需求变化。",
        "- `pgdp_real_2023` 为原始人均 GDP 用省级总 CPI 折为 2023 年价格后的值。",
        f"- 模型本身以人均总支出 `m` 驱动；这里用 2015-2023 年省级面板估计人口加权关系：`ln(m) = {bridge['intercept']:.4f} + {bridge['slope']:.4f} ln(pgdp_real_2023)`，并以 2023 年全国人口加权均值为锚点。",
        f"- 2023 年锚点：人均 GDP={bridge['base_pgdp']:.0f} 元/人，人均模型支出 m={bridge['base_m']:.0f} 元/人。样本 5%-95% 的 `pgdp_real_2023` 区间约为 {bridge['pgdp_p05']:.0f}-{bridge['pgdp_p95']:.0f} 元/人。",
        "- 食物大类的模型数量 `x` 是每日每人 2000 kcal 单位；`kg/人/年` 和营养素按 2023 年全国组内细项 kcal 份额、营养成分表及可食部换算得到。",
        "- 因此本表是条件情景模拟，不是包含人口、价格、城镇化、年龄结构变化的完整预测。",
        "",
        "### GDP 情景与模型支出桥接",
        "",
        md_table(scenario_view, 2),
        "",
        "## 结果一：人均 GDP 增长下，各类食物人均需求量变化",
        "",
        "### 各类食物 kg/人/年",
        "",
        md_table(demand_pivot, 2),
        "",
        "### 各类食物 kcal/人/日",
        "",
        md_table(kcal_pivot, 2),
        "",
        "### 从 2023 年人均 GDP 到 2 倍人均 GDP 的变化",
        "",
        md_table(change, 2),
        "",
        "### 细项 kg/人/年示例：2023 年人均 GDP 与 2 倍人均 GDP",
        "",
        md_table(item_sample, 2),
        "",
        "## 结果二：人均 GDP 增长下，膳食能量和三大营养素摄入变化",
        "",
        md_table(nutrition_view, 2),
        "",
        "## 结果解读",
        "",
        "- 主粮和食用油随人均 GDP 上升而下降，体现出高收入阶段的饱和与替代。",
        "- 肉类水产、奶类蛋类和蔬菜水果随人均 GDP 上升而增加，其中动物性食品增幅更明显。",
        "- 覆盖食品总能量变化相对温和，但营养结构明显变化：碳水化合物下降，脂肪和蛋白质上升。",
        "- 超出样本收入支持区间的高 GDP 倍数应作为外推情景阅读；正式论文中应结合完整收入、价格和人口路径再报告预测结论。",
        "",
        "## 配套 CSV",
        "",
        "- `GDP_food_demand_by_group.csv`：按 GDP 情景和五大食物组的 kg、kcal、三大营养素。",
        "- `GDP_food_demand_by_item.csv`：按 GDP 情景和细项食品的 kg、kcal、三大营养素。",
        "- `GDP_nutrition_intake.csv`：按 GDP 情景汇总的能量、碳水、脂肪、蛋白质摄入量。",
        "- `GDP_scenario_bridge.csv`：人均 GDP 到模型支出 `m` 的情景桥接表。",
    ]
    return "\n".join(notes)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = pd.read_csv(DATA_OUT / "maidads6_panel.csv")
    bridge = build_income_bridge(panel)
    item_nutrition = nutrition_per_kg()
    shares = national_item_kcal_shares(item_nutrition)
    scenario, group_demand, fixed_prices = predict_scenarios(panel, bridge)
    group_demand, item_demand, nutrition = add_kg_and_nutrients(group_demand, item_nutrition, shares)

    scenario.to_csv(OUT_DIR / "GDP_scenario_bridge.csv", index=False)
    group_demand.to_csv(OUT_DIR / "GDP_food_demand_by_group.csv", index=False)
    item_demand.to_csv(OUT_DIR / "GDP_food_demand_by_item.csv", index=False)
    nutrition.to_csv(OUT_DIR / "GDP_nutrition_intake.csv", index=False)
    item_nutrition.to_csv(OUT_DIR / "nutrition_per_kg_used.csv", index=False)
    shares.to_csv(OUT_DIR / "item_kcal_shares_2023.csv", index=False)
    fixed_prices.to_csv(OUT_DIR / "fixed_prices_2023_used.csv", index=False)

    md = build_markdown(bridge, scenario, group_demand, item_demand, nutrition)
    out = OUT_DIR / "人均GDP增长_食物需求与营养摄入变化.md"
    out.write_text(md, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
