#!/usr/bin/env python3
"""Build 71-item food quantity and price descriptives from survey microdata."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_SURVEY = Path("/root/data/数据/食物消费调查数据")


# module, item code, Chinese item name, analytic family, community categories
ITEMS = [
    ("主食部分.csv", "zhushi_1", "大米", "主食原粮/薯类", ["大米"]),
    ("主食部分.csv", "zhushi_2_1", "面粉", "主食原粮/薯类", ["面粉"]),
    ("主食部分.csv", "zhushi_3", "玉米面", "主食原粮/薯类", ["玉米面"]),
    ("主食部分.csv", "zhushi_3_1", "玉米棒", "主食原粮/薯类", ["玉米棒"]),
    ("主食部分.csv", "zhushi_5", "其他杂粮（小米/薏米/燕麦等）", "主食原粮/薯类", ["其他杂粮（小米/薏米/燕麦等）"]),
    ("主食部分.csv", "zhushi_6", "土豆", "主食原粮/薯类", ["土豆"]),
    ("主食部分.csv", "zhushi_7", "红薯", "主食原粮/薯类", ["红薯"]),
    ("主食加工品的获取与消费.csv", "zhushi_1_1", "米线/米粉", "主食加工品", ["米线/米粉"]),
    ("主食加工品的获取与消费.csv", "zhushi_2", "面食（馒头/面条/面包/饼/玉米饼）", "主食加工品", ["面食（馒头/面条/面包/饼/玉米饼）"]),
    ("主食加工品的获取与消费.csv", "zhushi_2_2", "带馅的面食（包子/饺子）", "主食加工品", ["带馅的面食（包子/饺子）"]),
    ("主食加工品的获取与消费.csv", "zhushi_8", "其他主食加工品（方便面等）", "主食加工品", ["其他主食加工品（方便面等）"]),
    ("豆类过去7天的消费.csv", "doulei_1", "黄豆", "豆类", ["黄豆"]),
    ("豆类过去7天的消费.csv", "doulei_4", "绿豆/红豆/黑豆等杂豆", "豆类", ["绿豆/红豆"]),
    ("豆制品的获取与消费.csv", "doulei_2", "豆浆", "豆制品", ["豆浆"]),
    ("豆制品的获取与消费.csv", "doulei_3", "豆腐/豆腐皮/豆干", "豆制品", ["豆腐/豆腐皮/豆干"]),
    ("豆制品的获取与消费.csv", "xiancai_4", "发酵豆制品（豆腐乳/豆酱/豆豉等）", "豆制品", ["发酵豆制品（豆腐乳/豆酱/豆豉等）"]),
    ("肉类.csv", "roulei_1", "猪肉（不含排骨、腊肉）", "畜禽肉", ["猪肉（不含排骨、腊肉）"]),
    ("肉类.csv", "roulei_2", "猪排骨", "畜禽肉", ["猪排骨"]),
    ("肉类.csv", "roulei_3", "牛肉", "畜禽肉", ["牛肉"]),
    ("肉类.csv", "roulei_4", "羊肉", "畜禽肉", ["羊肉"]),
    ("肉类.csv", "roulei_9", "下水内脏", "畜禽肉", ["下水内脏"]),
    ("肉类.csv", "roulei_5", "鸡肉", "畜禽肉", ["鸡肉"]),
    ("肉类.csv", "roulei_6", "其他禽肉（鸭肉/鹅肉/其他）", "畜禽肉", ["其他禽肉（鸭肉/鹅肉/其他）"]),
    ("肉类.csv", "roulei_7", "活禽（鸡）", "畜禽肉", ["活禽（鸡）"]),
    ("肉类.csv", "roulei_8", "活禽（鸭/鹅/其他）", "畜禽肉", ["活禽（鸭/鹅/其他）"]),
    ("肉类.csv", "shuichan_1", "水产品（淡水鱼/海水鱼/虾/蟹/贝壳类）", "水产品", ["水产品（淡水鱼/海水鱼/虾/蟹/贝壳类）"]),
    ("肉制品.csv", "xiancai_3", "腊肉/熏肉/精肉火腿/香肠（不含淀粉火腿肠）", "肉制品", ["腊肉/熏肉/精肉火腿/香肠（不包括含淀粉的火腿肠）"]),
    ("肉制品.csv", "roulei_11", "含淀粉的火腿肠", "肉制品", ["含淀粉的火腿肠"]),
    ("肉制品.csv", "roulei_12", "肉干/肉脯", "肉制品", ["肉干/肉脯"]),
    ("肉制品.csv", "roulei_13", "咸鱼虾酱等腌制水产品", "水产制品", ["咸鱼虾酱等腌制水产品"]),
    ("蛋类.csv", "danlei_1", "鸡蛋", "蛋类", ["鸡蛋"]),
    ("蛋类.csv", "danlei_2", "鸭蛋/鹅蛋", "蛋类", ["鸭蛋/鹅蛋"]),
    ("蛋制品.csv", "danlei_3", "咸蛋/松花蛋", "蛋制品", ["咸蛋/松花蛋"]),
    ("奶类.csv", "nailei_1", "液态牛奶/羊奶", "奶类", ["液态牛奶/羊奶"]),
    ("奶类.csv", "nailei_2", "酸奶", "奶类", ["酸奶"]),
    ("奶类.csv", "nailei_3", "奶粉", "奶类", ["奶粉"]),
    ("油脂类.csv", "youzhi_1", "大豆油", "油脂", ["大豆油"]),
    ("油脂类.csv", "youzhi_2", "菜籽油", "油脂", ["菜籽油"]),
    ("油脂类.csv", "youzhi_3", "花生油", "油脂", ["花生油"]),
    ("油脂类.csv", "youzhi_4", "色拉油/调和油", "油脂", ["色拉油/调和油"]),
    ("油脂类.csv", "youzhi_5", "其他植物油", "油脂", ["其他植物油"]),
    ("油脂类.csv", "youzhi_6", "动物油", "油脂", ["动物油"]),
    ("_蔬菜.csv", "shucai_1", "鲜豆类（豌豆/荷兰豆/扁豆/豇豆等）", "鲜菜", ["鲜豆类（豌豆/荷兰豆/扁豆/豇豆等）"]),
    ("_蔬菜.csv", "shucai_2", "茄果类（西红柿/茄子/青椒等）", "鲜菜", ["茄果类（西红柿/茄子/青椒等）"]),
    ("_蔬菜.csv", "shucai_3", "花菜类（西兰花/菜花/芥蓝等）", "鲜菜", ["花菜类（西兰花/菜花/芥蓝等）"]),
    ("_蔬菜.csv", "shucai_4", "根茎类（萝卜/胡萝卜/藕/莴笋/竹笋/洋葱等）", "鲜菜", ["根茎类（萝卜/胡萝卜/藕/莴笋/竹笋/洋葱等）"]),
    ("_蔬菜.csv", "shucai_5", "瓜类（黄瓜/南瓜/西葫芦/角瓜/冬瓜/苦瓜等）", "鲜菜", ["瓜类（黄瓜/南瓜/西葫芦/角瓜/冬瓜/苦瓜等）"]),
    ("_蔬菜.csv", "shucai_6", "叶菜类（菠菜/油菜/小白菜/芹菜/韭菜/蒜苗/白菜/生菜/卷心菜等）", "鲜菜", ["叶菜类（菠菜/油菜/小白菜/芹菜/韭菜/蒜苗/白菜/生菜/卷心菜等）"]),
    ("_蔬菜.csv", "shucai_7", "菌藻类（各类菌菇/海藻/海带等）", "鲜菜", ["菌藻类（各类菌菇/海藻/海带等）"]),
    ("_蔬菜.csv", "shucai_8", "辣椒和葱姜蒜类", "鲜菜", ["辣椒和葱姜蒜类（辣椒/大蒜/大葱/姜等）"]),
    ("_蔬菜.csv", "shucai_9", "其他新鲜或冷冻蔬菜", "鲜菜", ["其他新鲜或冷冻蔬菜（罐装菜/干菜/发酵菜/腌制菜除外）"]),
    ("蔬菜制品.csv", "xiancai_1", "咸菜（泡菜/榨菜/酸豆角等）", "蔬菜制品", ["咸菜（泡菜/榨菜/酸豆角等）"]),
    ("蔬菜制品.csv", "xiancai_2", "干菜（脱水蔬菜/金针菜/粉条/粉皮等）", "蔬菜制品", ["干菜（脱水蔬菜/金针菜/粉条/粉皮等）"]),
    ("水果干果.csv", "shuiguo_1", "瓜果类（西瓜/甜瓜/哈密瓜等）", "鲜果", ["瓜果类（西瓜/甜瓜/哈密瓜等）"]),
    ("水果干果.csv", "shuiguo_2", "柑橘类（橘/柑/橙/柚等）", "鲜果", ["柑橘类（橘/柑/橙/柚等）"]),
    ("水果干果.csv", "shuiguo_3", "浆果类（葡萄/草莓等）", "鲜果", ["浆果类（葡萄/草莓等）"]),
    ("水果干果.csv", "shuiguo_7", "核果类（苹果/梨/桃/鲜枣等）", "鲜果", ["核果类（苹果/梨/桃/鲜枣/杏/杨梅/石榴/樱桃/枇杷/李子等）"]),
    ("水果干果.csv", "shuiguo_6", "干果（花生/瓜子/核桃等）", "干果", ["干果（花生/瓜子/南瓜子/西瓜子/核桃/杏仁/开心果等）"]),
    ("水果制品.csv", "shuiguo_4", "罐头/果脯/糖渍水果", "水果制品", ["罐头/果脯/糖渍水果"]),
    ("水果制品.csv", "shuiguo_5", "其他水果干（不含果脯）", "水果制品", ["其他除果脯以外的水果干（苹果干/草莓干/香蕉干/干枣等）"]),
    ("调料.csv", "tiaoliao_1", "盐", "调料", ["盐"]),
    ("调料.csv", "tiaoliao_2", "味精/鸡精", "调料", ["味精/鸡精"]),
    ("调料.csv", "tiaoliao_3", "酱油类（生抽/老抽/味极鲜/蚝油等）", "调料", ["酱油类"]),
    ("调料.csv", "tiaoliao_4", "醋", "调料", ["醋"]),
    ("烟酒糖茶.csv", "yanjiu_1", "烟", "烟草", ["烟"]),
    ("烟酒糖茶.csv", "yanjiu_2", "白酒", "酒类", ["白酒"]),
    ("烟酒糖茶.csv", "yanjiu_3", "啤酒", "酒类", ["啤酒"]),
    ("烟酒糖茶.csv", "yanjiu_4", "葡萄酒/果酒/米酒/黄酒", "酒类", ["葡萄酒/果酒", "米酒/黄酒"]),
    ("烟酒糖茶.csv", "yanjiu_7", "白糖", "糖", ["白糖"]),
    ("烟酒糖茶.csv", "yanjiu_8", "红糖", "糖", ["红糖"]),
    ("烟酒糖茶.csv", "yanjiu_9", "茶", "茶", ["茶"]),
]


FAMILY_ORDER = {
    name: i
    for i, name in enumerate(
        [
            "主食原粮/薯类", "主食加工品", "豆类", "豆制品", "畜禽肉",
            "水产品", "肉制品", "水产制品", "蛋类", "蛋制品", "奶类",
            "油脂", "鲜菜", "蔬菜制品", "鲜果", "干果", "水果制品",
            "调料", "烟草", "酒类", "糖", "茶",
        ],
        1,
    )
}


def numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce").astype(float)
    text = series.astype("string").str.strip()
    text = text.str.replace("，", ".", regex=False).str.replace("。", ".", regex=False)
    direct = pd.to_numeric(text, errors="coerce")
    fraction = text.str.extract(r"^\s*(-?\d+(?:\.\d+)?)\s*/\s*(-?\d+(?:\.\d+)?)\s*$")
    numerator = pd.to_numeric(fraction[0], errors="coerce")
    denominator = pd.to_numeric(fraction[1], errors="coerce")
    frac_value = numerator / denominator.where(denominator.ne(0))
    first_number = pd.to_numeric(text.str.extract(r"(-?\d+(?:\.\d+)?)", expand=False), errors="coerce")
    return direct.fillna(frac_value).fillna(first_number).astype(float)


def catalogue() -> pd.DataFrame:
    rows = []
    six = {
        "主食原粮/薯类": "主食", "主食加工品": "主食", "豆类": "豆类及制品",
        "豆制品": "豆类及制品", "畜禽肉": "肉类及制品", "水产品": "肉类及制品",
        "肉制品": "肉类及制品", "水产制品": "肉类及制品", "油脂": "油脂",
        "鲜菜": "蔬菜", "蔬菜制品": "蔬菜", "鲜果": "水果", "干果": "水果",
        "水果制品": "水果",
    }
    for seq, (module, code, name, family, community) in enumerate(ITEMS, 1):
        rows.append(
            {
                "item_order": seq,
                "module": module.removesuffix(".csv"),
                "item_code": code,
                "item_name": name,
                "analytic_family": family,
                "family_order": FAMILY_ORDER[family],
                "previous_six_group": six.get(family, "未纳入原六类"),
                "community_categories": "; ".join(community),
                "community_mapping_count": len(community),
                "quantity_unit": "包/月" if code == "yanjiu_1" else "斤/月",
                "price_unit": "元/包" if code == "yanjiu_1" else "元/斤",
                "fixed_questionnaire_item": 1,
            }
        )
    result = pd.DataFrame(rows)
    if len(result) != 71 or result["item_code"].duplicated().any():
        raise RuntimeError("The fixed item catalogue must contain 71 unique codes")
    return result


def question_var(columns: set[str], prefix: str, question: str, code: str) -> str | None:
    candidates = [
        f"{prefix}_laiyuan-{question}-{code}",
        f"{prefix}_laiyuan_{question}_{code}",
    ]
    return next((name for name in candidates if name in columns), None)


def extract_item(frame: pd.DataFrame, prefix: str, code: str) -> tuple[pd.DataFrame, dict]:
    columns = set(frame.columns)
    variables = {q: question_var(columns, prefix, q, code) for q in ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "17", "21"]}
    required = ["00", "02", "03", "04", "05", "06", "09", "10", "11", "17"]
    missing = [q for q in required if variables[q] is None]
    if missing:
        raise RuntimeError(f"Missing question fields {missing} for {prefix}/{code}")

    values = {
        q: numeric(frame[var]) if var is not None else pd.Series(np.nan, index=frame.index, dtype=float)
        for q, var in variables.items()
    }
    days = numeric(frame["freq_period_days"])
    factor = np.where(
        values["00"].eq(2),
        30.0 / 7.0,
        np.where(values["00"].eq(1) & days.gt(0), 30.0 / days, np.nan),
    )
    factor_valid = np.isfinite(factor)
    q_acq, exp = values["02"], values["03"]
    q_direct = values["04"]
    direct_observed = q_direct.ge(0) & factor_valid
    residual = (
        q_acq
        - values["21"].fillna(0)
        - values["05"].fillna(0)
        - values["17"].fillna(0)
        - values["06"].fillna(0)
    ).clip(lower=0)
    residual_observed = (~direct_observed) & q_acq.gt(0) & factor_valid
    typical = values["10"] * values["11"]
    typical_observed = (
        (~direct_observed)
        & (~residual_observed)
        & values["10"].gt(0)
        & values["11"].gt(0)
    )
    purchased = (
        np.where(direct_observed, q_direct * factor, 0.0)
        + np.where(residual_observed, residual * factor, 0.0)
        + np.where(typical_observed, typical, 0.0)
    )
    own = np.where(values["07"].gt(0) & factor_valid, values["07"] * factor, 0.0)
    gift = np.where(values["09"].gt(0) & factor_valid, values["09"] * factor, 0.0)
    acquisition = np.where(q_acq.ge(0) & factor_valid, q_acq * factor, 0.0)
    expenditure = np.where(exp.ge(0) & factor_valid, exp * factor, 0.0)
    unit_value = np.where(q_acq.gt(0) & exp.gt(0), exp / q_acq, np.nan)
    own_price = np.where(values["07"].gt(0) & values["08"].gt(0), values["08"], np.nan)
    total = purchased + own + gift

    output = pd.DataFrame(
        {
            "household_id": frame["nhCode"].astype("string").str.strip(),
            "purchase_consumed_month": purchased,
            "own_consumed_month": own,
            "gift_consumed_month": gift,
            "total_consumed_month": total,
            "purchase_acquired_month": acquisition,
            "purchase_expenditure_month": expenditure,
            "purchase_unit_value": unit_value,
            "own_reported_price": own_price,
            "purchase_method": np.select(
                [direct_observed, residual_observed, typical_observed],
                ["q04_direct", "q02_residual", "q10xq11_typical"],
                default="none",
            ),
        }
    )
    nonnegative_fields = [values[q] for q in ["02", "03", "04", "05", "06", "07", "09", "10", "11", "17", "21"]]
    invalid_negative = int(pd.concat(nonnegative_fields, axis=1).lt(0).any(axis=1).sum())
    audit = {
        "item_code": code,
        "module_prefix": prefix,
        "rows": len(frame),
        "invalid_negative_rows": invalid_negative,
        "frequency_missing_with_positive_flow": int((~factor_valid & (q_acq.gt(0) | values["07"].gt(0) | values["09"].gt(0))).sum()),
        "purchase_direct_rows": int(direct_observed.sum()),
        "purchase_residual_rows": int(residual_observed.sum()),
        "purchase_typical_rows": int(typical_observed.sum()),
        "positive_total_rows": int((total > 0).sum()),
    }
    return output, audit


def household_core(path: Path) -> pd.DataFrame:
    roster = [f"family1_{i:02d}_HA1" for i in range(1, 9)]
    columns = ["nhCode", "data_year", "HA0", *roster]
    frame = pd.read_stata(path, columns=columns, convert_categoricals=False)
    frame["household_id"] = frame["nhCode"].astype("string").str.strip()
    reported = numeric(frame["HA0"])
    roster_size = frame[roster].notna().sum(axis=1).astype(float)
    frame["household_size"] = reported.where(reported.between(1, 20), roster_size.where(roster_size.gt(0)))
    if frame.duplicated(["household_id", "data_year"]).any():
        raise RuntimeError("Duplicate household-year IDs in household core")
    return frame[["household_id", "data_year", "household_size"]]


def build_household_long(food_root: Path, core_path: Path, catalog: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    core = household_core(core_path)
    outputs, audits, module_audits = [], [], []
    items_by_module = catalog.groupby("module", sort=False)
    for year in [2023, 2024]:
        year_core = core.loc[core["data_year"].eq(year)].copy()
        for module_name, entries in items_by_module:
            path = food_root / str(year) / f"{module_name}.csv"
            names = pd.read_csv(path, nrows=0, encoding="utf-8-sig").columns.tolist()
            prefix_fields = [c.split("_laiyuan-")[0] for c in names if "_laiyuan-02-" in c]
            if not prefix_fields:
                raise RuntimeError(f"Cannot identify module prefix in {path}")
            prefix = pd.Series(prefix_fields).mode().iloc[0]
            needed = ["nhCode", "freq_period_days"]
            for code in entries["item_code"]:
                needed.extend([c for c in names if re.search(rf"_laiyuan[-_]\d{{2}}[-_]{re.escape(code)}$", c)])
            needed = list(dict.fromkeys(needed))
            frame = pd.read_csv(path, usecols=needed, encoding="utf-8-sig", low_memory=False, dtype={"nhCode": "string"})
            duplicate_rows = int(frame["nhCode"].astype("string").str.strip().duplicated().sum())
            if duplicate_rows:
                raise RuntimeError(f"Duplicate household IDs in {path}: {duplicate_rows}")
            module_ids = set(frame["nhCode"].astype("string").str.strip())
            core_ids = set(year_core["household_id"])
            module_audits.append(
                {
                    "year": year,
                    "module": module_name,
                    "module_rows": len(frame),
                    "core_rows": len(year_core),
                    "module_not_core": len(module_ids - core_ids),
                    "core_not_module": len(core_ids - module_ids),
                }
            )
            for row in entries.itertuples(index=False):
                part, audit = extract_item(frame, prefix, row.item_code)
                part["data_year"] = year
                part["item_code"] = row.item_code
                part = year_core.merge(part, on=["household_id", "data_year"], how="left", validate="one_to_one", indicator=True)
                part["module_observed"] = part["_merge"].eq("both").astype(int)
                part = part.drop(columns="_merge")
                quantity_columns = [
                    "purchase_consumed_month", "own_consumed_month", "gift_consumed_month",
                    "total_consumed_month", "purchase_acquired_month", "purchase_expenditure_month",
                ]
                part[quantity_columns] = part[quantity_columns].fillna(0.0)
                part["total_consumed_pc_month"] = part["total_consumed_month"] / part["household_size"]
                outputs.append(part)
                audits.append({"year": year, "module": module_name, **audit})
    result = pd.concat(outputs, ignore_index=True)
    result = result.merge(
        catalog[["item_code", "item_order", "item_name", "analytic_family", "quantity_unit", "price_unit"]],
        on="item_code",
        how="left",
        validate="many_to_one",
    )
    result = result.sort_values(["data_year", "household_id", "item_order"]).reset_index(drop=True)
    return result, pd.DataFrame(audits), pd.DataFrame(module_audits)


def percentile(series: pd.Series, p: float) -> float:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    return float(clean.quantile(p)) if len(clean) else np.nan


def distribution_stats(series: pd.Series, prefix: str, positive_only: bool = False) -> dict:
    values = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if positive_only:
        values = values[values > 0]
    stats = {f"{prefix}_n": int(len(values))}
    if not len(values):
        for name in ["mean", "sd", "p01", "p10", "p25", "p50", "p75", "p90", "p95", "p99", "max"]:
            stats[f"{prefix}_{name}"] = np.nan
        return stats
    stats.update(
        {
            f"{prefix}_mean": float(values.mean()),
            f"{prefix}_sd": float(values.std(ddof=1)) if len(values) > 1 else np.nan,
            f"{prefix}_p01": percentile(values, 0.01),
            f"{prefix}_p10": percentile(values, 0.10),
            f"{prefix}_p25": percentile(values, 0.25),
            f"{prefix}_p50": percentile(values, 0.50),
            f"{prefix}_p75": percentile(values, 0.75),
            f"{prefix}_p90": percentile(values, 0.90),
            f"{prefix}_p95": percentile(values, 0.95),
            f"{prefix}_p99": percentile(values, 0.99),
            f"{prefix}_max": float(values.max()),
        }
    )
    return stats


def quantity_summary(group: pd.DataFrame, period: str) -> dict:
    total = group["total_consumed_month"]
    consumers = total[total > 0]
    pc_consumers = group.loc[total > 0, "total_consumed_pc_month"]
    aggregate = float(total.sum())
    sorted_total = consumers.sort_values(ascending=False)
    top_n = max(1, math.ceil(len(sorted_total) * 0.01)) if len(sorted_total) else 0
    p99 = percentile(consumers, 0.99)
    winsor_p99 = total.clip(upper=p99) if np.isfinite(p99) else total
    excluded_top1 = total.drop(index=sorted_total.iloc[:top_n].index) if top_n else total
    remaining_consumers = consumers.drop(index=sorted_total.iloc[:top_n].index) if top_n else consumers
    q25, q75 = percentile(consumers, 0.25), percentile(consumers, 0.75)
    outer_fence = q75 + 3 * (q75 - q25) if np.isfinite(q25) and np.isfinite(q75) else np.nan
    record = {
        "period": period,
        "item_code": group["item_code"].iloc[0],
        "households": int(len(group)),
        "module_observed_households": int(group["module_observed"].sum()),
        "consumer_households": int((total > 0).sum()),
        "participation_total": float((total > 0).mean()),
        "participation_purchase": float((group["purchase_consumed_month"] > 0).mean()),
        "participation_own": float((group["own_consumed_month"] > 0).mean()),
        "participation_gift": float((group["gift_consumed_month"] > 0).mean()),
        "quantity_total_sum": aggregate,
        "quantity_household_mean_all": float(total.mean()),
        "quantity_household_sd_all": float(total.std(ddof=1)),
        "quantity_household_mean_winsor_p99": float(winsor_p99.mean()),
        "quantity_household_mean_excl_top1pct_consumers": float(excluded_top1.mean()),
        "quantity_consumer_mean_excl_top1pct_consumers": float(remaining_consumers.mean()) if len(remaining_consumers) else np.nan,
        "quantity_percap_mean_all": float(group["total_consumed_pc_month"].mean()),
        "purchase_quantity_share": float(group["purchase_consumed_month"].sum() / aggregate) if aggregate > 0 else np.nan,
        "own_quantity_share": float(group["own_consumed_month"].sum() / aggregate) if aggregate > 0 else np.nan,
        "gift_quantity_share": float(group["gift_consumed_month"].sum() / aggregate) if aggregate > 0 else np.nan,
        "top1pct_quantity_share": float(sorted_total.iloc[:top_n].sum() / aggregate) if aggregate > 0 and top_n else np.nan,
        "outer_fence_3iqr": outer_fence,
        "share_consumers_above_outer_fence": float((consumers > outer_fence).mean()) if len(consumers) and np.isfinite(outer_fence) else np.nan,
    }
    record.update(distribution_stats(consumers, "quantity_consumer", positive_only=True))
    record.update(distribution_stats(pc_consumers, "quantity_pc_consumer", positive_only=True))
    return record


def summarize_quantities(long: pd.DataFrame, catalog: pd.DataFrame) -> pd.DataFrame:
    records = []
    for item, group in long.groupby("item_code", sort=False):
        records.append(quantity_summary(group, "pooled_2023_2024"))
        for year, annual in group.groupby("data_year"):
            records.append(quantity_summary(annual, str(int(year))))
    result = pd.DataFrame(records).merge(catalog, on="item_code", how="left", validate="many_to_one")
    return result.sort_values(["item_order", "period"]).reset_index(drop=True)


def price_summary(group: pd.DataFrame, period: str) -> dict:
    uv = group.loc[group["purchase_unit_value"].gt(0), "purchase_unit_value"]
    own = group.loc[group["own_reported_price"].gt(0), "own_reported_price"]
    record = {
        "period": period,
        "item_code": group["item_code"].iloc[0],
        "households": len(group),
        "purchase_uv_share_lt_0_1": float((uv < 0.1).mean()) if len(uv) else np.nan,
        "purchase_uv_share_lt_0_5": float((uv < 0.5).mean()) if len(uv) else np.nan,
        "purchase_uv_n_unique_3dp": int(uv.round(3).nunique()),
        "own_price_share_lt_0_1": float((own < 0.1).mean()) if len(own) else np.nan,
    }
    record.update(distribution_stats(uv, "purchase_uv", positive_only=True))
    record.update(distribution_stats(own, "own_price", positive_only=True))
    return record


def summarize_household_prices(long: pd.DataFrame, catalog: pd.DataFrame) -> pd.DataFrame:
    records = []
    for item, group in long.groupby("item_code", sort=False):
        records.append(price_summary(group, "pooled_2023_2024"))
        for year, annual in group.groupby("data_year"):
            records.append(price_summary(annual, str(int(year))))
    result = pd.DataFrame(records).merge(catalog, on="item_code", how="left", validate="many_to_one")
    return result.sort_values(["item_order", "period"]).reset_index(drop=True)


def community_price_long(village_path: Path, label_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    labels = pd.read_csv(label_path, encoding="utf-8-sig")
    parsed = []
    for row in labels.itertuples(index=False):
        parts = str(row.label).split("｜")
        if len(parts) == 3 and parts[2] in {"最高单价", "最低单价"}:
            parsed.append({"var": row.var, "market_module": parts[0], "community_category": parts[1], "endpoint": "high" if parts[2] == "最高单价" else "low"})
    dictionary = pd.DataFrame(parsed)
    dictionary = dictionary.loc[~dictionary["community_category"].isin(["08", "09", "10"])].copy()
    dictionary["outlet"] = dictionary["market_module"].str.extract(r"^(大超市|食品杂货店|自由市场/农贸市场|肉店/水产店)")
    if dictionary["outlet"].isna().any():
        raise RuntimeError("Unparsed community market outlet labels")
    village = pd.read_stata(
        village_path,
        columns=["xzcCode_clean", "data_year", *dictionary["var"].tolist()],
        convert_categoricals=False,
    )
    melted = village.melt(id_vars=["xzcCode_clean", "data_year"], value_vars=dictionary["var"], var_name="var", value_name="price")
    melted = melted.merge(dictionary, on="var", how="left", validate="many_to_one")
    melted["price"] = numeric(melted["price"])
    melted["valid_positive"] = melted["price"].gt(0)
    wide = (
        melted.pivot_table(
            index=["xzcCode_clean", "data_year", "outlet", "market_module", "community_category"],
            columns="endpoint",
            values="price",
            aggfunc="first",
        )
        .reset_index()
        .rename_axis(columns=None)
    )
    for endpoint in ["low", "high"]:
        if endpoint not in wide:
            wide[endpoint] = np.nan
        wide.loc[wide[endpoint].le(0), endpoint] = np.nan
    wide["midpoint"] = (wide["low"] + wide["high"]) / 2
    wide["reversed_endpoints"] = (wide["high"] < wide["low"]).fillna(False).astype(int)
    audit = pd.DataFrame(
        [
            {"check": "community_dictionary_price_variables", "value": len(dictionary)},
            {"check": "community_fixed_categories", "value": dictionary["community_category"].nunique()},
            {"check": "community_village_year_rows", "value": village[["xzcCode_clean", "data_year"]].drop_duplicates().shape[0]},
            {"check": "community_positive_low_quotes", "value": int(wide["low"].notna().sum())},
            {"check": "community_positive_high_quotes", "value": int(wide["high"].notna().sum())},
            {"check": "community_reversed_endpoint_pairs", "value": int(wide["reversed_endpoints"].sum())},
        ]
    )
    return wide, audit


def community_distribution(group: pd.DataFrame, period: str, key: str, value: str) -> dict:
    lows = group["low"].dropna()
    highs = group["high"].dropna()
    mids = group["midpoint"].dropna()
    record = {
        "period": period,
        key: value,
        "village_years": int(group[["xzcCode_clean", "data_year"]].drop_duplicates().shape[0]),
        "outlet_village_pairs": int(len(group)),
        "reversed_endpoint_pairs": int(group["reversed_endpoints"].sum()),
        "low_share_lt_0_1": float((lows < 0.1).mean()) if len(lows) else np.nan,
        "low_share_lt_0_5": float((lows < 0.5).mean()) if len(lows) else np.nan,
        "low_share_lt_1": float((lows < 1).mean()) if len(lows) else np.nan,
        "low_n_unique_3dp": int(lows.round(3).nunique()),
        "low_modal_value_share_3dp": float(lows.round(3).value_counts(normalize=True).iloc[0]) if len(lows) else np.nan,
    }
    record.update(distribution_stats(lows, "community_low", positive_only=True))
    record.update(distribution_stats(highs, "community_high", positive_only=True))
    record.update(distribution_stats(mids, "community_mid", positive_only=True))
    return record


def summarize_community_categories(long: pd.DataFrame) -> pd.DataFrame:
    records = []
    for category, group in long.groupby("community_category", sort=True):
        records.append(community_distribution(group, "pooled_2023_2024", "community_category", category))
        for year, annual in group.groupby("data_year"):
            records.append(community_distribution(annual, str(int(year)), "community_category", category))
    return pd.DataFrame(records).sort_values(["community_category", "period"]).reset_index(drop=True)


def summarize_community_items(long: pd.DataFrame, catalog: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    mapping = catalog[["item_code", "community_categories"]].copy()
    mapping["community_category"] = mapping["community_categories"].str.split("; ")
    mapping = mapping.explode("community_category")[["item_code", "community_category"]]
    mapped = mapping.merge(long, on="community_category", how="left", validate="many_to_many", indicator=True)
    missing = mapped.loc[mapped["_merge"].ne("both"), ["item_code", "community_category"]].drop_duplicates()
    if len(missing):
        raise RuntimeError(f"Community price mapping not found:\n{missing.to_string(index=False)}")
    mapped = mapped.drop(columns="_merge")
    records = []
    for item, group in mapped.groupby("item_code", sort=False):
        records.append(community_distribution(group, "pooled_2023_2024", "item_code", item))
        for year in [2023, 2024]:
            annual = group.loc[group["data_year"].eq(year)]
            records.append(community_distribution(annual, str(year), "item_code", item))
    result = pd.DataFrame(records).merge(catalog, on="item_code", how="left", validate="many_to_one")
    return result.sort_values(["item_order", "period"]).reset_index(drop=True), mapping


def family_outputs(
    long: pd.DataFrame,
    community_long_frame: pd.DataFrame,
    catalog: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Aggregate compatible questionnaire items into 22 transparent families."""
    family_catalog = (
        catalog.sort_values("item_order")
        .groupby("analytic_family", as_index=False, sort=False)
        .agg(
            item_order=("family_order", "first"),
            item_name=("item_name", lambda x: "；".join(x)),
            item_count=("item_code", "size"),
            module=("module", lambda x: "；".join(dict.fromkeys(x))),
            previous_six_group=("previous_six_group", lambda x: "；".join(dict.fromkeys(x))),
            community_categories=("community_categories", lambda x: "; ".join(x)),
            community_mapping_count=("community_mapping_count", "sum"),
            quantity_unit=("quantity_unit", "first"),
            price_unit=("price_unit", "first"),
        )
    )
    family_catalog["item_code"] = family_catalog["analytic_family"]
    family_catalog["fixed_questionnaire_item"] = 0
    family_catalog["family_order"] = family_catalog["item_order"]
    family_catalog = family_catalog[
        [
            "item_order", "module", "item_code", "item_name", "analytic_family",
            "family_order", "previous_six_group", "community_categories",
            "community_mapping_count", "quantity_unit", "price_unit",
            "fixed_questionnaire_item", "item_count",
        ]
    ]

    family_long = (
        long.groupby(
            ["household_id", "data_year", "household_size", "analytic_family"],
            as_index=False,
        )
        .agg(
            purchase_consumed_month=("purchase_consumed_month", "sum"),
            own_consumed_month=("own_consumed_month", "sum"),
            gift_consumed_month=("gift_consumed_month", "sum"),
            total_consumed_month=("total_consumed_month", "sum"),
            purchase_acquired_month=("purchase_acquired_month", "sum"),
            purchase_expenditure_month=("purchase_expenditure_month", "sum"),
            module_observed=("module_observed", "min"),
        )
    )
    family_long["item_code"] = family_long["analytic_family"]
    family_long["total_consumed_pc_month"] = family_long["total_consumed_month"] / family_long["household_size"]
    family_long["purchase_unit_value"] = family_long["purchase_expenditure_month"] / family_long["purchase_acquired_month"]
    family_long.loc[
        ~(
            family_long["purchase_expenditure_month"].gt(0)
            & family_long["purchase_acquired_month"].gt(0)
        ),
        "purchase_unit_value",
    ] = np.nan
    family_long["own_reported_price"] = np.nan

    quantity_records, price_records = [], []
    for family, group in family_long.groupby("item_code", sort=False):
        quantity_records.append(quantity_summary(group, "pooled_2023_2024"))
        price_records.append(price_summary(group, "pooled_2023_2024"))
        for year in [2023, 2024]:
            annual = group.loc[group["data_year"].eq(year)]
            quantity_records.append(quantity_summary(annual, str(year)))
            price_records.append(price_summary(annual, str(year)))
    family_quantities = pd.DataFrame(quantity_records).merge(family_catalog, on="item_code", validate="many_to_one")
    family_prices = pd.DataFrame(price_records).merge(family_catalog, on="item_code", validate="many_to_one")

    mapping = catalog[["analytic_family", "community_categories"]].copy()
    mapping["community_category"] = mapping["community_categories"].str.split("; ")
    mapping = mapping.explode("community_category")[["analytic_family", "community_category"]]
    family_community_long = mapping.merge(community_long_frame, on="community_category", how="left", validate="many_to_many")
    community_records = []
    for family, group in family_community_long.groupby("analytic_family", sort=False):
        community_records.append(community_distribution(group, "pooled_2023_2024", "item_code", family))
        for year in [2023, 2024]:
            annual = group.loc[group["data_year"].eq(year)]
            community_records.append(community_distribution(annual, str(year), "item_code", family))
    family_community = pd.DataFrame(community_records).merge(family_catalog, on="item_code", validate="many_to_one")
    family_selection = selection_table(family_catalog, family_quantities, family_prices, family_community)
    return family_selection, family_quantities, family_prices, family_community


def selection_table(catalog: pd.DataFrame, quantities: pd.DataFrame, household_prices: pd.DataFrame, community_prices: pd.DataFrame) -> pd.DataFrame:
    q = quantities.loc[quantities["period"].eq("pooled_2023_2024")].copy()
    h = household_prices.loc[household_prices["period"].eq("pooled_2023_2024")].copy()
    c = community_prices.loc[community_prices["period"].eq("pooled_2023_2024")].copy()
    qcols = [
        "item_code", "households", "consumer_households", "participation_total",
        "quantity_household_mean_all", "quantity_household_mean_winsor_p99",
        "quantity_household_mean_excl_top1pct_consumers", "quantity_consumer_mean",
        "quantity_consumer_mean_excl_top1pct_consumers", "quantity_consumer_p50", "quantity_consumer_p90",
        "quantity_consumer_p99", "quantity_consumer_max", "quantity_percap_mean_all",
        "purchase_quantity_share", "own_quantity_share", "gift_quantity_share",
        "top1pct_quantity_share", "share_consumers_above_outer_fence",
    ]
    hcols = [
        "item_code", "purchase_uv_n", "purchase_uv_p01", "purchase_uv_p10", "purchase_uv_p50",
        "purchase_uv_p90", "purchase_uv_p99", "purchase_uv_max", "purchase_uv_share_lt_0_1",
        "purchase_uv_share_lt_0_5", "own_price_n", "own_price_p50",
    ]
    ccols = [
        "item_code", "village_years", "outlet_village_pairs", "community_low_n",
        "community_low_p01", "community_low_p10", "community_low_p50", "community_low_p90",
        "community_high_p50", "community_mid_p50", "low_share_lt_0_1", "low_share_lt_0_5",
        "low_share_lt_1", "low_modal_value_share_3dp", "reversed_endpoint_pairs",
    ]
    result = catalog.merge(q[qcols], on="item_code", validate="one_to_one")
    result = result.merge(h[hcols], on="item_code", how="left", validate="one_to_one")
    result = result.merge(c[ccols], on="item_code", how="left", validate="one_to_one")
    result["low_participation_lt_5pct"] = result["participation_total"].lt(0.05).astype(int)
    result["quantity_top1_share_gt_25pct"] = result["top1pct_quantity_share"].gt(0.25).astype(int)
    result["household_uv_low_tail_flag"] = (result["purchase_uv_share_lt_0_5"].gt(0.05)).astype(int)
    result["community_low_tail_flag"] = (result["low_share_lt_0_5"].gt(0.05)).astype(int)
    result["community_price_is_range_not_same_quality"] = 1
    return result.sort_values("item_order").reset_index(drop=True)


def validation_table(catalog: pd.DataFrame, long: pd.DataFrame, quantities: pd.DataFrame, hp: pd.DataFrame, cp: pd.DataFrame, family_selection: pd.DataFrame, extraction_audit: pd.DataFrame, module_audit: pd.DataFrame, community_audit: pd.DataFrame) -> pd.DataFrame:
    rows = [
        ("fixed_item_count", len(catalog), 71),
        ("unique_item_code_count", catalog["item_code"].nunique(), 71),
        ("household_item_long_rows", len(long), long[["household_id", "data_year"]].drop_duplicates().shape[0] * 71),
        ("duplicate_household_year_item", int(long.duplicated(["household_id", "data_year", "item_code"]).sum()), 0),
        ("negative_rebuilt_total_quantities", int((long["total_consumed_month"] < 0).sum()), 0),
        ("nonpositive_household_sizes", int((long["household_size"] <= 0).sum()), 0),
        ("quantity_summary_rows", len(quantities), 71 * 3),
        ("household_price_summary_rows", len(hp), 71 * 3),
        ("community_item_summary_rows", len(cp), 71 * 3),
        ("analytic_family_count", len(family_selection), 22),
        ("module_to_core_unmatched_ids", int(module_audit["module_not_core"].sum()), 0),
        ("core_missing_module_rows_total", int(module_audit["core_not_module"].sum()), 0),
    ]
    result = pd.DataFrame(rows, columns=["check", "observed", "expected"])
    result["pass"] = np.where(result["observed"].eq(result["expected"]), 1, 0)
    diagnostics = pd.DataFrame(
        [
            {
                "check": "diagnostic_frequency_missing_with_positive_flow",
                "observed": int(extraction_audit["frequency_missing_with_positive_flow"].sum()),
                "expected": np.nan,
                "pass": np.nan,
            },
            {
                "check": "diagnostic_raw_negative_item_rows",
                "observed": int(extraction_audit["invalid_negative_rows"].sum()),
                "expected": np.nan,
                "pass": np.nan,
            },
        ]
    )
    community = community_audit.rename(columns={"value": "observed"}).copy()
    community["expected"] = np.nan
    community["pass"] = np.nan
    return pd.concat([result, diagnostics, community], ignore_index=True)


def markdown_summary(selection: pd.DataFrame, validation: pd.DataFrame) -> str:
    lines = [
        "# 71类食物细项统计描述",
        "",
        "本表按原始农户问卷固定细项重建，不沿用六类聚合。消费量为月度家庭总消费，等于购买后直接食用、自家生产后直接食用和受赠后直接食用之和；价格同时列出家庭购买单位价值与村表市场价格区间，两者不可混为同一价格。",
        "",
        "## 核心口径",
        "",
        "- 样本期：2023和2024年，合并统计另保留分年度统计。",
        "- 数量单位：除烟为包/月外，其余按问卷为斤/月；啤酒在农户问卷中折算为500ml。",
        "- 家庭单位价值：购买花费/购买获得量，只保留正分子、正分母，不做缩尾。",
        "- 社区价格：村表在大超市、杂货店、农贸市场及肉店/水产店记录的最低/最高单价；它们反映类别内质量区间，不是同质商品均价。",
        "- 7个`tiankong*`空白列因没有食品名称而排除，不能把不同家庭填写的未知食品合成一个细项。",
        "",
        "## 合并样本细项表",
        "",
        "|类别|细项|参与率|户均月消费（原值）|户均月消费（P99缩尾）|消费户中位数|人均月消费|购买占比|自产占比|家庭单位价值中位数|社区最低价中位数|社区区间中点中位数|",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    def fmt(value: float, pct: bool = False) -> str:
        if pd.isna(value):
            return "NA"
        return f"{value * 100:.1f}%" if pct else f"{value:.3f}"
    for row in selection.itertuples(index=False):
        lines.append(
            f"|{row.analytic_family}|{row.item_name}|{fmt(row.participation_total, True)}|"
            f"{fmt(row.quantity_household_mean_all)}|{fmt(row.quantity_household_mean_winsor_p99)}|"
            f"{fmt(row.quantity_consumer_p50)}|"
            f"{fmt(row.quantity_percap_mean_all)}|{fmt(row.purchase_quantity_share, True)}|"
            f"{fmt(row.own_quantity_share, True)}|{fmt(row.purchase_uv_p50)}|"
            f"{fmt(row.community_low_p50)}|{fmt(row.community_mid_p50)}|"
        )
    flagged = selection.loc[
        selection[["low_participation_lt_5pct", "quantity_top1_share_gt_25pct", "household_uv_low_tail_flag", "community_low_tail_flag"]].max(axis=1).eq(1)
    ]
    lines.extend(
        [
            "",
            "## 重新分类时需要优先复核",
            "",
            f"共有{len(flagged)}个细项至少触发一项诊断标志（低参与率、消费量过度集中、家庭单位价值低尾或社区最低价低尾）。标志用于定位原始记录，不代表自动删除。完整分位数、最大值、年度差异及标志见`FOOD_ITEM_DESCRIPTIVES.xlsx`和`item_selection_table.csv`。",
            "",
            "## 验证",
            "",
            "|检查|观察值|期望值|通过|",
            "|---|---:|---:|---:|",
        ]
    )
    for row in validation.to_dict(orient="records"):
        expected = "NA" if pd.isna(row["expected"]) else f"{row['expected']:g}"
        passed = "NA" if pd.isna(row["pass"]) else f"{int(row['pass'])}"
        lines.append(f"|{row['check']}|{row['observed']:g}|{expected}|{passed}|")
    return "\n".join(lines) + "\n"


def write_excel(path: Path, catalog: pd.DataFrame, selection: pd.DataFrame, family_selection: pd.DataFrame, quantities: pd.DataFrame, family_quantities: pd.DataFrame, hp: pd.DataFrame, cp: pd.DataFrame, categories: pd.DataFrame, extraction: pd.DataFrame, module: pd.DataFrame, validation: pd.DataFrame) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        catalog.to_excel(writer, sheet_name="Item_Catalog", index=False)
        selection.to_excel(writer, sheet_name="Selection_Table", index=False)
        family_selection.to_excel(writer, sheet_name="22_Family_Selection", index=False)
        quantities.loc[quantities["period"].eq("pooled_2023_2024")].to_excel(writer, sheet_name="Quantity_Pooled", index=False)
        quantities.loc[~quantities["period"].eq("pooled_2023_2024")].to_excel(writer, sheet_name="Quantity_ByYear", index=False)
        family_quantities.to_excel(writer, sheet_name="22_Family_Quantity", index=False)
        hp.loc[hp["period"].eq("pooled_2023_2024")].to_excel(writer, sheet_name="HH_Prices_Pooled", index=False)
        hp.loc[~hp["period"].eq("pooled_2023_2024")].to_excel(writer, sheet_name="HH_Prices_ByYear", index=False)
        cp.loc[cp["period"].eq("pooled_2023_2024")].to_excel(writer, sheet_name="Community_Pooled", index=False)
        cp.loc[~cp["period"].eq("pooled_2023_2024")].to_excel(writer, sheet_name="Community_ByYear", index=False)
        categories.to_excel(writer, sheet_name="Community_Categories", index=False)
        extraction.to_excel(writer, sheet_name="Extraction_Audit", index=False)
        module.to_excel(writer, sheet_name="Module_Merge_Audit", index=False)
        validation.to_excel(writer, sheet_name="Validation", index=False)
        for sheet in writer.book.worksheets:
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            sheet.sheet_view.showGridLines = False
            for column_cells in sheet.columns:
                width = min(45, max(10, max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells) + 2))
                sheet.column_dimensions[column_cells[0].column_letter].width = width


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--survey-root", type=Path, default=DEFAULT_SURVEY)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "outputs")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    catalog = catalogue()
    food_root = args.survey_root / "导出的数据/家庭食物获取消费/cleaned"
    core_path = args.survey_root / "处理后的data/户表数据_已清洗.dta"
    village_path = args.survey_root / "处理后的data/村表数据_已清洗.dta"
    village_labels = args.survey_root / "处理后的data/村表数据_已清洗_变量标签.csv"

    household_long, extraction_audit, module_audit = build_household_long(food_root, core_path, catalog)
    quantities = summarize_quantities(household_long, catalog)
    household_prices = summarize_household_prices(household_long, catalog)
    community_long, community_audit = community_price_long(village_path, village_labels)
    community_categories = summarize_community_categories(community_long)
    community_items, mapping = summarize_community_items(community_long, catalog)
    selection = selection_table(catalog, quantities, household_prices, community_items)
    family_selection, family_quantities, family_prices, family_community = family_outputs(household_long, community_long, catalog)
    validation = validation_table(catalog, household_long, quantities, household_prices, community_items, family_selection, extraction_audit, module_audit, community_audit)

    catalog.to_csv(args.output / "item_catalog.csv", index=False, encoding="utf-8-sig")
    quantities.to_csv(args.output / "item_consumption_descriptives.csv", index=False, encoding="utf-8-sig")
    household_prices.to_csv(args.output / "item_household_price_descriptives.csv", index=False, encoding="utf-8-sig")
    community_items.to_csv(args.output / "item_community_price_descriptives.csv", index=False, encoding="utf-8-sig")
    community_categories.to_csv(args.output / "community_category_price_descriptives.csv", index=False, encoding="utf-8-sig")
    community_long.to_csv(args.output / "community_price_endpoint_long.csv", index=False, encoding="utf-8-sig")
    mapping.to_csv(args.output / "household_community_price_mapping.csv", index=False, encoding="utf-8-sig")
    extraction_audit.to_csv(args.output / "item_extraction_audit.csv", index=False, encoding="utf-8-sig")
    module_audit.to_csv(args.output / "module_merge_audit.csv", index=False, encoding="utf-8-sig")
    validation.to_csv(args.output / "validation_checks.csv", index=False, encoding="utf-8-sig")
    selection.to_csv(args.output / "item_selection_table.csv", index=False, encoding="utf-8-sig")
    family_selection.to_csv(args.output / "analytic_family_selection_table.csv", index=False, encoding="utf-8-sig")
    family_quantities.to_csv(args.output / "analytic_family_consumption_descriptives.csv", index=False, encoding="utf-8-sig")
    family_prices.to_csv(args.output / "analytic_family_household_price_descriptives.csv", index=False, encoding="utf-8-sig")
    family_community.to_csv(args.output / "analytic_family_community_price_descriptives.csv", index=False, encoding="utf-8-sig")
    household_long.to_stata(args.output / "household_item_long.dta", write_index=False, version=118)
    (args.output / "ITEM_LEVEL_SUMMARY.md").write_text(markdown_summary(selection, validation), encoding="utf-8")
    text_columns = [
        "item_order", "analytic_family", "item_name", "quantity_unit", "price_unit",
        "participation_total", "quantity_household_mean_all", "quantity_consumer_p50",
        "quantity_household_mean_winsor_p99", "quantity_household_mean_excl_top1pct_consumers",
        "quantity_consumer_mean", "quantity_consumer_mean_excl_top1pct_consumers",
        "quantity_consumer_p90", "quantity_consumer_p99", "quantity_consumer_max",
        "quantity_percap_mean_all", "purchase_quantity_share", "own_quantity_share",
        "gift_quantity_share", "purchase_uv_n", "purchase_uv_p10", "purchase_uv_p50",
        "purchase_uv_p90", "purchase_uv_p99", "community_low_n", "community_low_p10",
        "community_low_p50", "community_low_p90", "community_high_p50",
        "community_mid_p50", "top1pct_quantity_share", "low_share_lt_0_5",
    ]
    selection[text_columns].to_csv(args.output / "完整细项统计表.txt", sep="\t", index=False, encoding="utf-8-sig")
    write_excel(
        args.output / "FOOD_ITEM_DESCRIPTIVES.xlsx", catalog, selection, family_selection,
        quantities, family_quantities, household_prices, community_items,
        community_categories, extraction_audit, module_audit, validation,
    )
    print(f"Built {len(catalog)} items, {len(household_long):,} household-item rows")
    print(f"Outputs: {args.output}")


if __name__ == "__main__":
    main()
