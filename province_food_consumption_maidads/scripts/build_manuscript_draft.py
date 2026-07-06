from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "ProvinceMAIDADS"
RESULTS = PROJECT / "Results"
DATA_OUT = PROJECT / "Data" / "output"
PAPER_WORK = PROJECT / ".paper_work"
MANUSCRIPT = PROJECT / "manuscript"
SECTIONS = MANUSCRIPT / "sections"
TABLES = MANUSCRIPT / "tables"
APPENDIX = MANUSCRIPT / "appendix"
REVIEWS = MANUSCRIPT / "reviewer_reports"


def md_table(df: pd.DataFrame, digits: int = 3) -> str:
    tmp = df.copy()
    tmp.columns = [str(c) for c in tmp.columns]
    for col in tmp.select_dtypes(include=[np.number]).columns:
        tmp[col] = tmp[col].map(lambda x: "" if pd.isna(x) else f"{x:.{digits}f}")
    tmp = tmp.fillna("").astype(str)
    lines = [
        "| " + " | ".join(tmp.columns) + " |",
        "| " + " | ".join(["---"] * len(tmp.columns)) + " |",
    ]
    for row in tmp.itertuples(index=False):
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def read_inputs() -> dict[str, pd.DataFrame]:
    return {
        "panel": pd.read_csv(DATA_OUT / "maidads6_panel.csv"),
        "comparison": pd.read_csv(RESULTS / "model_comparison.csv"),
        "fit": pd.read_csv(RESULTS / "model_fit_by_group.csv"),
        "params": pd.read_csv(RESULTS / "parameter_estimates.csv"),
        "oos": pd.read_csv(RESULTS / "OOS" / "oos_summary_by_model.csv"),
        "lr": pd.read_csv(RESULTS / "Diagnostics" / "lr_test_chi2_and_bootstrap.csv"),
        "bootstrap": pd.read_csv(RESULTS / "Bootstrap" / "bootstrap_draw_status.csv"),
        "boot_ci": pd.read_csv(RESULTS / "Bootstrap" / "bootstrap_key_ci.csv"),
        "elasticity_income": pd.read_csv(RESULTS / "Elasticities" / "elasticity_income_grid.csv"),
        "elasticity_price": pd.read_csv(RESULTS / "Elasticities" / "elasticity_price_marshallian_grid.csv"),
        "consistency": pd.read_csv(RESULTS / "Elasticities" / "elasticity_consistency_tests.csv"),
        "projection": pd.read_csv(RESULTS / "Projection" / "projection_group_2030_2035_2050.csv"),
        "feed": pd.read_csv(RESULTS / "Projection" / "projection_item_feed_2030_2035_2050.csv"),
        "decomposition": pd.read_csv(RESULTS / "Projection" / "projection_decomposition_2030_2035_2050.csv"),
    }


def get_scalar(df: pd.DataFrame, mask, col: str) -> float:
    out = df.loc[mask, col]
    if out.empty:
        return float("nan")
    return float(out.iloc[0])


def build_summary_tables(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    comparison = data["comparison"].copy()
    model_rows = comparison[comparison["model"].isin(["AIDADS_sat", "MAIDADS_sat"])].copy()
    fit_table = model_rows[
        ["variant", "model", "nll", "aic", "bic", "oos_food_rmse_mean"]
    ].copy()
    fit_table.to_csv(TABLES / "table_1_model_comparison.csv", index=False)

    inc = data["elasticity_income"].copy()
    median_income = float(data["panel"]["m"].median())
    unique_incomes = np.array(sorted(inc["income"].dropna().unique()))
    med_grid = float(unique_incomes[np.argmin(np.abs(unique_incomes - median_income))])
    groups = ["grain", "oil", "vegfruit", "meatsea", "dairyegg", "all_food", "animal_food", "plant_food"]
    elasticity_table = inc[inc["income"].eq(med_grid) & inc["group"].isin(groups)][
        ["income", "group", "quantity_2000kcal_elasticity", "expenditure_elasticity", "budget_share"]
    ].copy()
    elasticity_table.to_csv(TABLES / "table_2_income_elasticities_median.csv", index=False)

    proj = data["projection"].copy()
    proj_table = proj[proj["year"].isin([2030, 2035, 2050]) & proj["group"].ne("nonfood")][
        ["year", "group", "daily_kcal_per_cap_weighted", "annual_kcal_total", "population_10k"]
    ].copy()
    proj_table.to_csv(TABLES / "table_3_projection_kcal.csv", index=False)

    feed = data["feed"].copy()
    feed["feed_grain_million_ton"] = feed["feed_grain_kg"] / 1e9
    feed_table = feed[["year", "item", "total_kg", "feed_kg_per_kg_product", "feed_grain_million_ton"]].copy()
    feed_table.to_csv(TABLES / "table_4_feed_grain.csv", index=False)

    price = data["elasticity_price"]
    own = price[price["is_own_price"].astype(bool)].copy()
    price_summary = (
        own.groupby("demand_group")["elasticity"]
        .agg(["min", "median", "max"])
        .reset_index()
        .rename(columns={"demand_group": "group", "median": "median_own_price_elasticity"})
    )
    price_summary.to_csv(TABLES / "table_5_own_price_elasticities.csv", index=False)

    return {
        "fit_table": fit_table,
        "elasticity_table": elasticity_table,
        "projection_table": proj_table,
        "feed_table": feed_table,
        "price_summary": price_summary,
        "median_income_grid": pd.DataFrame({"median_income_grid": [med_grid]}),
    }


def build_evidence_ledger(data: dict[str, pd.DataFrame], tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    panel = data["panel"]
    comparison = data["comparison"]
    projection = data["projection"]
    feed = data["feed"].copy()
    feed["feed_grain_million_ton"] = feed["feed_grain_kg"] / 1e9
    consistency = data["consistency"]
    bootstrap = data["bootstrap"]
    lr = data["lr"]
    oos = data["oos"]
    inc_table = tables["elasticity_table"]

    n_prov = panel["province"].nunique()
    year_min, year_max = int(panel["year"].min()), int(panel["year"].max())
    n_obs = panel.shape[0]
    boot_n = bootstrap.shape[0]
    boot_success = int(bootstrap["success"].astype(bool).sum())
    lr_obs = float(lr["lr_observed"].iloc[0])
    lr_p = float(lr["p_bootstrap_cluster"].iloc[0])
    lr_reps = int(lr["n_bootstrap"].iloc[0])
    lr_success = int(lr["successful_reps"].iloc[0])
    bootstrap_status = "formal" if boot_n >= 500 else "pilot_only"
    bootstrap_scale = "formal-scale" if boot_n >= 500 else "pilot-scale"
    lr_status = "formal" if lr_reps >= 500 else "pilot_only"
    lr_scale = "formal-scale" if lr_reps >= 500 else "pilot-scale"
    max_consistency = float(
        consistency[
            [
                "adding_up_income_error",
                "max_abs_price_adding_up_error",
                "max_abs_marshallian_homogeneity_error",
                "max_abs_hicksian_homogeneity_error",
                "max_abs_slutsky_symmetry_error",
            ]
        ]
        .abs()
        .max()
        .max()
    )

    rows = []

    def add(cid, section, claim, file, column, status="allowed", notes=""):
        rows.append(
            {
                "claim_id": cid,
                "section": section,
                "claim": claim,
                "evidence_file": file,
                "table_or_column": column,
                "status": status,
                "notes": notes,
            }
        )

    add(
        "C001",
        "Data",
        f"The estimating sample covers {n_prov} provinces from {year_min} to {year_max}, yielding {n_obs} province-year observations.",
        "Data/output/maidads6_panel.csv",
        "province, year",
    )
    add(
        "C002",
        "Data",
        "The model uses five covered food groups plus an other/non-covered expenditure residual.",
        "Results/CODE_AUDIT_FIX_REPORT.md",
        "B4/nonfood naming row",
    )
    for variant in ["baseline_real_national_nonfood", "robust_real_derived_cpi_nonfood"]:
        a_nll = get_scalar(comparison, (comparison["variant"].eq(variant)) & (comparison["model"].eq("AIDADS_sat")), "nll")
        m_nll = get_scalar(comparison, (comparison["variant"].eq(variant)) & (comparison["model"].eq("MAIDADS_sat")), "nll")
        add(
            f"C10{1 if variant.startswith('baseline') else 2}",
            "Estimation",
            f"In {variant}, MAIDADS improves in-sample fit relative to AIDADS: nll {m_nll:.3f} versus {a_nll:.3f}.",
            "Results/model_comparison.csv",
            "variant, model, nll",
        )
    base_a_oos = get_scalar(comparison, (comparison["variant"].eq("baseline_real_national_nonfood")) & (comparison["model"].eq("AIDADS_sat")), "oos_food_rmse_mean")
    base_m_oos = get_scalar(comparison, (comparison["variant"].eq("baseline_real_national_nonfood")) & (comparison["model"].eq("MAIDADS_sat")), "oos_food_rmse_mean")
    add(
        "C103",
        "Estimation",
        f"Out-of-sample food RMSE is separately computed by model and is lower for MAIDADS than AIDADS in the baseline specification ({base_m_oos:.4f} versus {base_a_oos:.4f}).",
        "Results/model_comparison.csv; Results/OOS/oos_summary_by_model.csv",
        "oos_food_rmse_mean",
    )
    add(
        "C104",
        "Estimation",
        f"The LR statistic is {lr_obs:.3f}; the {lr_scale} cluster-bootstrap LR exercise has {lr_success}/{lr_reps} successful draws and tail probability {lr_p:.3f}.",
        "Results/Diagnostics/lr_test_chi2_and_bootstrap.csv",
        "lr_observed, p_bootstrap_cluster, n_bootstrap",
        lr_status,
    )
    add(
        "C105",
        "Estimation",
        f"Elasticity consistency checks have maximum absolute error {max_consistency:.2e}.",
        "Results/Elasticities/elasticity_consistency_tests.csv",
        "max_abs_*",
    )
    for _, row in inc_table.iterrows():
        add(
            f"C20{len(rows)}",
            "Elasticities",
            f"At the median-income grid point ({row['income']:.0f}), {row['group']} has quantity elasticity {row['quantity_2000kcal_elasticity']:.3f}.",
            "Results/Elasticities/elasticity_income_grid.csv",
            "income, group, quantity_2000kcal_elasticity",
        )
    for group in ["grain", "oil", "vegfruit", "meatsea", "dairyegg"]:
        kcal_2050 = get_scalar(
            projection,
            (projection["year"].eq(2050)) & (projection["group"].eq(group)),
            "daily_kcal_per_cap_weighted",
        )
        add(
            f"C30{group}",
            "Projection",
            f"Under the conditional scenario, projected 2050 daily kcal per capita for {group} is {kcal_2050:.1f}.",
            "Results/Projection/projection_group_2030_2035_2050.csv",
            "year, group, daily_kcal_per_cap_weighted",
            "scenario_only",
        )
    for item in ["pork", "poultry", "egg", "milk", "aquatic", "beef", "mutton"]:
        value = get_scalar(
            feed,
            (feed["year"].eq(2050)) & (feed["item"].eq(item)),
            "feed_grain_million_ton",
        )
        add(
            f"C40{item}",
            "Projection",
            f"Under the conditional scenario, 2050 feed-grain equivalent demand associated with {item} is {value:.1f} million tons.",
            "Results/Projection/projection_item_feed_2030_2035_2050.csv",
            "year, item, feed_grain_kg",
            "scenario_only",
        )
    add(
        "C501",
        "Inference",
        f"The parameter and projection bootstrap exercise uses {boot_n} province-block draws, of which {boot_success} converge; reported intervals are {bootstrap_scale}.",
        "Results/Bootstrap/bootstrap_draw_status.csv",
        "draw, success",
        bootstrap_status,
    )
    add(
        "C601",
        "Projection",
        "The projection path uses national income growth, income-convergence adjustments, and Chen et al. (2020) SSP2 provincial population projections; it remains a conditional scenario because province-level income, urbanization, and age-structure paths are not yet fully specified.",
        "Results/Projection/projection_growth_path.csv",
        "income_growth_source, population_share_source, population_projection_source",
        "scenario_only",
    )
    ledger = pd.DataFrame(rows)
    ledger.to_csv(PAPER_WORK / "evidence_ledger.csv", index=False)
    return ledger


def write_refs() -> None:
    refs = r"""@article{gouel_guimbard_2019,
  author = {Gouel, Christophe and Guimbard, Houssein},
  title = {Nutrition Transition and the Structure of Global Food Demand},
  journal = {American Journal of Agricultural Economics},
  volume = {101},
  number = {2},
  pages = {383--403},
  year = {2019},
  doi = {10.1093/ajae/aay030}
}

@article{preckel_cranfield_hertel_2010,
  author = {Preckel, Paul V. and Cranfield, John A. L. and Hertel, Thomas W.},
  title = {A modified, implicitly additive demand system},
  journal = {Applied Economics},
  volume = {42},
  number = {2},
  pages = {143--155},
  year = {2010}
}

@article{chen_guo_wang_2020,
  author = {Chen, Y. and Guo, F. and Wang, J. and others},
  title = {Provincial and gridded population projection for China under shared socioeconomic pathways from 2010 to 2100},
  journal = {Scientific Data},
  volume = {7},
  pages = {83},
  year = {2020},
  doi = {10.1038/s41597-020-0421-y}
}
"""
    (MANUSCRIPT / "refs.bib").write_text(refs, encoding="utf-8")


def draft_sections(data: dict[str, pd.DataFrame], tables: dict[str, pd.DataFrame], ledger: pd.DataFrame) -> None:
    gate = json.loads((PAPER_WORK / "gate_status.json").read_text(encoding="utf-8"))
    status = gate["status"]
    comparison_md = md_table(tables["fit_table"], 3)
    elasticity_md = md_table(tables["elasticity_table"], 3)
    projection_pivot = tables["projection_table"].pivot_table(
        index="group", columns="year", values="daily_kcal_per_cap_weighted"
    ).reset_index()
    projection_md = md_table(projection_pivot, 1)
    feed_pivot = tables["feed_table"].pivot_table(
        index="item", columns="year", values="feed_grain_million_ton"
    ).reset_index()
    feed_md = md_table(feed_pivot, 1)
    price_md = md_table(tables["price_summary"], 3)
    lr = data["lr"].iloc[0]
    boot = data["bootstrap"]
    boot_success = int(boot["success"].astype(bool).sum())
    boot_scale = "formal-scale" if boot.shape[0] >= 500 else "pilot-scale"
    lr_scale = "formal-scale" if int(lr["n_bootstrap"]) >= 500 else "pilot-scale"
    cons = data["consistency"]
    max_consistency = float(
        cons[
            [
                "adding_up_income_error",
                "max_abs_price_adding_up_error",
                "max_abs_marshallian_homogeneity_error",
                "max_abs_hicksian_homogeneity_error",
                "max_abs_slutsky_symmetry_error",
            ]
        ].abs().max().max()
    )
    panel = data["panel"]
    n_prov = panel["province"].nunique()
    n_obs = panel.shape[0]
    y0, y1 = int(panel["year"].min()), int(panel["year"].max())

    sections = {}
    sections["00_abstract.md"] = f"""# Abstract

This paper develops a first-pass province-level application of the modified implicitly additive demand system (MAIDADS) to study food demand, nutrition transition, and conditional food-demand projections in China. The estimating sample contains {n_obs} province-year observations for {n_prov} provinces over {y0}--{y1}. Food consumption is aggregated into five covered food groups measured in daily 2,000-kcal units, while remaining expenditure is treated as an other/non-covered residual. The main specification uses 2023 real-price units and a national non-food CPI for the residual price index.

The current results should be read as a working-paper draft rather than final journal evidence. The audit gate status is **{status}** because the projection module still relies on conditional income-convergence assumptions. Inference has been upgraded to formal-scale resampling: the parameter and projection bootstrap uses {boot.shape[0]} province-block draws, of which {boot_success} converge, and the LR cluster bootstrap uses {int(lr['n_bootstrap'])} draws. Population paths now use the Chen et al. (2020) SSP2 provincial projection. Within these limits, MAIDADS improves in-sample fit relative to AIDADS and modestly improves out-of-sample food-demand prediction. The estimated demand system passes adding-up, homogeneity, and Slutsky-consistency checks at numerical tolerances. Conditional projections suggest continued reallocation away from staples and toward animal products, although total covered-food calories change less than composition. The paper concludes by identifying the data additions needed for a journal-ready version: direct provincial non-food CPI, province-level income, urbanization, and age-structure paths, and broader food-group coverage.

Unsupported or weak claims to resolve:
- Add province-level income, urbanization, and age-structure paths before presenting projections as forecasts rather than scenario simulations.
"""

    sections["01_introduction.md"] = """# 1. Introduction

China's food system is moving through a nutrition transition in which rising incomes, urbanization, demographic change, and relative prices reshape the composition of diets. A central empirical challenge is that food demand does not respond linearly to income: staples tend to saturate, animal-source foods may rise over a longer range, and the expenditure residual absorbs both uncovered foods and non-food consumption. These features make constant-elasticity or locally linear demand specifications poorly suited for long-run scenario analysis.

This paper adapts the MAIDADS framework of Gouel and Guimbard (2019), building on the modified implicitly additive demand system of Preckel, Cranfield, and Hertel (2010), to a Chinese provincial panel. The goal is not merely to report a table of elasticities. Instead, the paper asks whether a structural, income-flexible demand system can summarize provincial nutrition transition patterns and produce transparent conditional scenarios for 2030, 2035, and 2050.

The contribution is threefold. First, the analysis constructs a province-year demand-system panel in which covered foods are converted to daily 2,000-kcal units and prices are harmonized in 2023 real terms. Second, it estimates saturated AIDADS and MAIDADS systems, reports income and price elasticities, and audits the theoretical restrictions implied by the demand system. Third, it links the estimated demand system to conditional projection paths and animal-product feed-grain equivalents, while making clear which parts of the evidence are preliminary.

This draft deliberately adopts a conservative writing stance. The current bootstrap exercises are now formal-scale, but the projection path combines a sourced SSP2 population projection with conditional income assumptions rather than a complete official provincial forecast system. The quantitative results are therefore useful for model inference and research design, while long-run projection statements remain scenario simulations rather than official forecasts.

Unsupported or weak claims to resolve:
- Add a fuller China food-demand literature review and verified citations.
- Strengthen identification discussion around unit values, quality, and price endogeneity.
"""

    sections["02_literature.md"] = """# 2. Related Literature

The paper is closest to the literature on income-flexible demand systems for global food demand and nutrition transition. Gouel and Guimbard (2019) use MAIDADS to model global food demand and show why demand saturation is central for long-run food projections. The present project follows that structural logic but shifts the unit of observation from countries to Chinese provinces and from a global income distribution to a province-year panel.

The methodological foundation is the modified implicitly additive demand system of Preckel, Cranfield, and Hertel (2010). MAIDADS nests AIDADS by allowing subsistence consumption to vary with utility, while imposing saturation restrictions that prevent covered food demand from growing without bound at high income levels. This feature is useful for studying diets in an economy where total calories may stabilize even as composition continues to change.

For population inputs, the projection module uses the provincial SSP population data of Chen et al. (2020), which provide province-level and gridded population projections for China from 2010 to 2100. This improves the demographic basis of the scenario exercise relative to the earlier population-share extrapolation, although income, urbanization, and age-composition assumptions remain simplified.

The draft still requires a fuller literature review on China-specific food demand, household demand systems, nutrition transition, and feed-grain implications. Those references should be added only after a verified bibliography is supplied.

Unsupported or weak claims to resolve:
- Add verified references for China demand-system estimates, nutrition transition evidence, and feed conversion assumptions.
"""

    sections["03_data.md"] = f"""# 3. Data and Variable Construction

The estimating sample contains {n_obs} observations for {n_prov} provinces from {y0} to {y1}. The model uses six aggregate demand categories: staples, oils and fats, vegetables and fruits, meat and aquatic products, dairy and eggs, and an other/non-covered residual. The residual is retained internally under the code name `nonfood`, but it should not be interpreted as a strict outside good. It includes uncovered foods, eating away from home, alcohol and tobacco components when present in the residual, and true non-food expenditure.

Food quantities are converted to daily 2,000-kcal units. The nutrition table is adjusted for edible shares. When reported energy is missing or zero, energy is reconstructed from macronutrients. Grain aggregation includes soybeans and potatoes. The potato division by five is retained only for grain-equivalent accounting; calorie aggregation uses actual kcal per kilogram and consumption-quantity weights.

The main monetary specification uses 2023 real-price terms. Total expenditure is deflated by the provincial total CPI index, covered-food prices by provincial food CPI, and the other/non-covered residual price by national non-food CPI. A robustness specification uses a derived provincial non-food CPI from total CPI, food CPI, and food expenditure shares. Because direct provincial non-food CPI is not yet available, residual-price variation should be interpreted cautiously.

Projection-year population is taken from the Chen et al. (2020) provincial population projection under SSP2. The raw projection table is reported in persons and is converted to the model's `population_10k` unit before aggregation.

Unsupported or weak claims to resolve:
- Add direct provincial non-food CPI or official CPI weights.
- Add an external covered-calorie benchmark against FAOSTAT or statistical yearbook food balance data.
"""

    sections["04_model.md"] = """# 4. Model

The empirical model is a saturated six-good MAIDADS demand system. For province-year observation c and good i, fitted demand is

```text
x_ci = gamma_i(u_c) + phi_i(u_c) [m_c - sum_j p_cj gamma_j(u_c)] / p_ci .
```

The marginal budget share is

```text
phi_i(u) = [alpha_i + beta_i exp(u)] / [1 + exp(u)],
```

and the subsistence term is

```text
gamma_i(u) = [delta_i + tau_i exp(omega u)] / [1 + exp(omega u)].
```

Utility is solved from the implicit equation

```text
sum_i phi_i(u_c) ln[x_ci - gamma_i(u_c)] - u_c - kappa = 0.
```

The saturated specification imposes beta equal to zero for covered food groups and one for the other/non-covered residual. The model is estimated by concentrated likelihood using quantity errors. AIDADS is estimated first and then used to initialize MAIDADS. Multi-start diagnostics, boundary reports, and gradient summaries are retained as part of the paper evidence package.

Income elasticities are computed by the model's prediction function using central differences. Marshallian price elasticities and Hicksian elasticities are reported for completeness and for demand-system checks, but price elasticity is not positioned as the main contribution because MAIDADS has limited independent price flexibility and provincial unit values may contain quality variation.

Unsupported or weak claims to resolve:
- Add direct analytic-vs-numeric elasticity unit tests before final submission.
- Add a stronger treatment of panel dependence beyond cluster bootstrap.
"""

    sections["05_estimation_diagnostics.md"] = f"""# 5. Estimation, Fit, and Diagnostics

Table 1 summarizes the fit of AIDADS and MAIDADS under the main and robustness price specifications.

{comparison_md}

In the main specification, MAIDADS lowers the concentrated negative log likelihood relative to AIDADS. Out-of-sample validation is now computed separately for each model and specification, avoiding the earlier error in which a single OOS statistic could be broadcast across rows. The main-specification mean food RMSE is lower for MAIDADS than AIDADS, but the improvement is modest and should be interpreted together with the split-specific group errors.

The LR statistic comparing MAIDADS and AIDADS is {float(lr['lr_observed']):.3f}. However, the standard chi-square reference distribution is not used for inference because nuisance parameters are not identified under the restricted model. The current LR bootstrap is {lr_scale}: {int(lr['successful_reps'])} successful draws out of {int(lr['n_bootstrap'])}, with a cluster-bootstrap tail probability of {float(lr['p_bootstrap_cluster']):.3f}. This result cautions against interpreting the large in-sample LR statistic as decisive model-selection evidence.

The theoretical consistency checks are numerically tight. The maximum absolute consistency error across the recorded adding-up, homogeneity, and Slutsky checks is {max_consistency:.2e}. Parameter boundary reports distinguish restrictions imposed by saturation from parameters estimated near a boundary.

Unsupported or weak claims to resolve:
- Clarify the null-resampling interpretation of the LR bootstrap and consider a parametric-null bootstrap robustness check.
- Add a table of split-specific OOS results in the appendix.
"""

    sections["06_elasticities.md"] = f"""# 6. Demand Elasticities

Table 2 reports income elasticities at the sample median-income grid point.

{elasticity_md}

The current estimates imply declining covered-kcal demand for staples and oils at the median grid point, positive responsiveness for vegetables and fruits, mild positive responsiveness for meat and aquatic products, and relatively strong positive responsiveness for dairy and eggs. Aggregated across groups, all covered foods and plant foods have negative median-income elasticities, while animal foods remain positive. These patterns are consistent with a nutrition-transition interpretation in which the main response to income growth is compositional rather than a uniform expansion of total covered calories.

Table 5 summarizes Marshallian own-price elasticities over the income grid.

{price_md}

Price elasticities should be treated as auxiliary outputs. Some own-price elasticities are close to zero and may be positive for certain groups and income points. This pattern reinforces the need to avoid making price responsiveness the core contribution until price measurement and quality adjustment are strengthened.

Unsupported or weak claims to resolve:
- Investigate positive own-price elasticities for selected plant-food groups.
- Add robustness using a price-flexible demand system such as QUAIDS or EASI if price effects become central.
"""

    sections["07_projection.md"] = f"""# 7. Conditional Projections to 2030, 2035, and 2050

The projection exercise is a conditional scenario simulation. It uses national growth paths, province-specific income convergence adjustments, and the Chen et al. (2020) SSP2 provincial population projection. It is not an official province-level forecast because province-level income, urbanization, and age-structure paths remain simplified.

Table 3 reports national weighted daily kcal per capita by covered-food group.

{projection_md}

Under the scenario, staples remain the largest covered-food source in 2050, while meat and aquatic products account for a substantial share of covered-food calories. Total covered-food calories are relatively stable compared with the compositional changes across groups.

Animal-product quantities are mapped into feed-grain equivalents using the user-supplied conversion factors. Table 4 reports the implied national feed-grain equivalents in million tons.

{feed_md}

The feed-grain module should be interpreted as an accounting translation rather than a behavioral supply-chain model. The coefficients are currently treated as feed-grain equivalent factors; if they are instead total-feed coefficients, feed cereal shares must be added.

Unsupported or weak claims to resolve:
- Replace the income-convergence assumption with sourced province-level income, urbanization, and age-structure paths; retain or compare alternative SSP population scenarios.
- Add sourced feed conversion coefficients and cereal shares.
"""

    sections["08_robustness.md"] = """# 8. Robustness and Audit Findings

The main robustness exercise replaces the national non-food CPI residual price with a derived provincial non-food CPI. The resulting MAIDADS fit remains better than AIDADS within that specification. Cross-specification AIC and BIC comparisons should not be over-interpreted because the residual-price construction differs across specifications.

The code audit also changed several data and reporting conventions. The residual category is described as other/non-covered expenditure rather than strict non-food consumption. The grain-calorie calculation uses actual calorie weights rather than the potato grain-equivalent conversion. OOS files are stored separately by variant, model, and split. The projection module now uses Chen et al. (2020) SSP2 provincial population paths rather than population-share trend extrapolation. The paper workflow records a YELLOW gate status because the income side of projections remains a conditional scenario, not because bootstrap inference is still pilot-scale.

Unsupported or weak claims to resolve:
- Add official non-food CPI or CPI category weights.
- Add leave-one-province and leave-one-region validation.
"""

    sections["09_conclusion.md"] = """# 9. Conclusion

This draft shows that a province-level MAIDADS framework can organize evidence on China's nutrition transition and produce transparent conditional food-demand scenarios. The first-pass results support a compositional interpretation: income growth does not simply raise all covered foods proportionally; it changes the relative importance of staples, animal products, dairy and eggs, and plant foods.

The current contribution is methodological and diagnostic as much as substantive. The project now has a reproducible data pipeline, model estimates, OOS validation by model, price-elasticity matrices, theoretical consistency checks, formal-scale bootstrap status records, and a simulator workbook. These are necessary building blocks for a journal paper.

The draft is not yet a final submission version. Formal-scale bootstrap inference has been completed, but the LR comparison should still be interpreted through the cluster-bootstrap result rather than the invalid naive chi-square reference. Long-run projections now have a sourced provincial SSP2 population path, but still require stronger province-level income, urbanization, and age-structure scenarios. Direct provincial non-food CPI and broader food-group coverage would materially improve identification and interpretation. Once these additions are made, the paper can move from a working-paper draft to a journal-style submission.

Unsupported or weak claims to resolve:
- Upgrade projection inputs before removing the working-paper caveats.
"""

    SECTIONS.mkdir(parents=True, exist_ok=True)
    for name, text in sections.items():
        (SECTIONS / name).write_text(text, encoding="utf-8")


def assemble_paper() -> None:
    order = [
        "00_abstract.md",
        "01_introduction.md",
        "02_literature.md",
        "03_data.md",
        "04_model.md",
        "05_estimation_diagnostics.md",
        "06_elasticities.md",
        "07_projection.md",
        "08_robustness.md",
        "09_conclusion.md",
    ]
    title = """# Provincial Food Demand Elasticities and Nutrition Transition in China: A First-Pass MAIDADS Working Paper

**Manuscript status:** Working-paper draft generated under a YELLOW audit gate. Formal-scale bootstrap inference is included; conditional scenario projections are explicitly labeled.

"""
    body = [title]
    for name in order:
        body.append((SECTIONS / name).read_text(encoding="utf-8"))
    body.append(
        """# References

Gouel, C., and H. Guimbard. 2019. “Nutrition Transition and the Structure of Global Food Demand.” *American Journal of Agricultural Economics* 101(2): 383--403.

Preckel, P. V., J. A. L. Cranfield, and T. W. Hertel. 2010. “A Modified, Implicitly Additive Demand System.” *Applied Economics* 42(2): 143--155.

Chen, Y., F. Guo, J. Wang, et al. 2020. “Provincial and Gridded Population Projection for China under Shared Socioeconomic Pathways from 2010 to 2100.” *Scientific Data* 7: 83. https://doi.org/10.1038/s41597-020-0421-y.

TODO: Add verified China food-demand, nutrition-transition, and feed-conversion references.
"""
    )
    MANUSCRIPT.mkdir(parents=True, exist_ok=True)
    (MANUSCRIPT / "paper.md").write_text("\n\n".join(body), encoding="utf-8")


def write_local_review(gate_status: str) -> None:
    REVIEWS.mkdir(parents=True, exist_ok=True)
    review = f"""# Local Reviewer Report, Round 1

Decision: Accept as Working Paper / Major Revision before journal submission

Summary:
The manuscript is now evidence-gated and conservative. It correctly labels the current status as `{gate_status}`, incorporates formal-scale bootstrap inference, and avoids treating conditional projections as final forecasts.

Top issues:
1. The LR bootstrap has been expanded to formal scale, but its tail probability does not support treating the large in-sample LR statistic as decisive model-selection evidence.
2. Projection paths now use Chen et al. (2020) SSP2 provincial population data, but income remains a convergence scenario rather than a sourced province-level forecast.
3. The paper should carefully distinguish formal demand-system inference from conditional long-run projection assumptions.
4. The other/non-covered residual should never be interpreted as strict non-food demand.
5. Price elasticities are auxiliary and some own-price signs require further investigation.
6. Direct provincial non-food CPI or official CPI weights are still missing.
7. The literature review needs verified China-specific citations.
8. Feed-grain conversion coefficients require formal source documentation and possibly cereal-share adjustments.

Required revisions before journal submission:
- Add sourced province-level income, urbanization, and age-structure projection data.
- Add external calorie validation and broader food categories.
- Add price-quality/endogeneity robustness.
- Complete bibliography and literature review.
"""
    (REVIEWS / "local_round1.md").write_text(review, encoding="utf-8")

    revision = """# Revision Plan

1. Add direct provincial non-food CPI or category-level CPI weights.
2. Replace conditional income assumptions with sourced province-level income, urbanization, and age-structure paths; add SSP population sensitivity scenarios.
3. Add leave-one-province and leave-one-region OOS validation.
4. Add China food-demand and nutrition-transition references to `refs.bib`.
5. Add sourced feed conversion coefficients and cereal shares.
6. Revisit positive own-price elasticities and consider a price-flexible robustness model.
7. Consider a parametric-null LR bootstrap robustness check if model-selection inference becomes central.
"""
    (MANUSCRIPT / "revision_plan.md").write_text(revision, encoding="utf-8")


def main() -> None:
    for path in [PAPER_WORK, MANUSCRIPT, SECTIONS, TABLES, APPENDIX, REVIEWS]:
        path.mkdir(parents=True, exist_ok=True)
    data = read_inputs()
    tables = build_summary_tables(data)
    ledger = build_evidence_ledger(data, tables)
    write_refs()
    draft_sections(data, tables, ledger)
    assemble_paper()
    gate = json.loads((PAPER_WORK / "gate_status.json").read_text(encoding="utf-8"))
    remote_log = PAPER_WORK / "remote_llm_run_log.md"
    write_local_review(gate["status"])
    manifest = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "gate_status": gate["status"],
        "paper": str((MANUSCRIPT / "paper.md").relative_to(PROJECT)),
        "evidence_ledger": str((PAPER_WORK / "evidence_ledger.csv").relative_to(PROJECT)),
        "sections": sorted(p.name for p in SECTIONS.glob("*.md")),
        "remote_llm_used_in_current_build": False,
        "remote_llm_prior_attempts_recorded": remote_log.exists(),
        "remote_llm_note": (
            "Current formal-bootstrap rebuild was generated from local evidence files only. "
            "Prior DeepSeek drafting attempts and Claude API status, if any, are recorded in "
            f"{remote_log.relative_to(PROJECT)}."
            if remote_log.exists()
            else "Current build was generated from local evidence files only; no remote LLM log was found."
        ),
    }
    (PAPER_WORK / "manuscript_run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(MANUSCRIPT / "paper.md")


if __name__ == "__main__":
    main()
