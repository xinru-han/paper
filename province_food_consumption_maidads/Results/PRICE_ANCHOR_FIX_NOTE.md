# Node-table price-anchor correction (issue ①)

**Problem.** Table 3 (mean-GDP income elasticities), Table 4 (US$-node income
elasticities) and the milestone CSV were originally built with **full-sample
mean prices** (`arr.p.mean(axis=0)`), while the income-elasticity grid and
**Figure 3** use **2023 mean prices held fixed** (Methods ¶31). Same corrected
optimum, different price vector → the tables and figure disagreed on close
inspection (e.g. pork@US$15k table 0.112 vs figure 0.184).

**Fix.** `build_docx_node_tables.py` now anchors every node table at 2023 mean
prices (`panel[year==2023][p_*_model].mean()`), matching Methods ¶31 and
Figure 3. The script also now emits **Table 4** itself
(`table4_node_elasticity_ci_pval.csv` + `elasticity_usd_milestones_MAIN.csv`),
which previously had no in-package generator.

**Effect (2023-price anchor, authoritative):**
- T3 mean-GDP: Staples −0.405, Oils −0.222, Veg/fruit +0.390, **Pork +0.317**,
  Non-pork meat/aquatic +0.153, Dairy/eggs +0.568, Other +1.119.
- T4 pork path: US$15k +0.184 → 20k +0.111 → 25k +0.071 → 30k +0.047 (matches
  Figure 3). Grain −0.398 → −0.383.

**Figure 3 was already correct** (built from `elasticity_income_grid.csv`, 2023
prices) and needs no regeneration. Only the tables were re-anchored.
