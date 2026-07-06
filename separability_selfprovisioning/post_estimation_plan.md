# Post-Estimation Plan — Paper 1 (Separability on the Food Self-Provisioning Margin)

This file specifies every analysis referenced by the double-bracketed placeholders `[[...]]` in
**Section 5.6** of `paper1_manuscript_v3.docx`. Run the blocks below on the **common M3 estimation
sample** (27,568 household–category observations, 350 village clusters), fill the placeholders, and
send the numbers back for integration. Each analysis states its **prediction in advance** — the
manuscript is written so that results confirm or overturn stated predictions rather than being
selected ex post.

---

## 0. Setup and configuration (edit variable names once, here)

```r
# install.packages(c("fixest","dplyr","dineq","purrr"))
library(fixest); library(dplyr); library(dineq); library(purrr)

df <- readRDS("m3_sample.rds")   # the M3 common estimation sample, one row = household×category

## ---- EDIT THESE NAMES TO MATCH YOUR DATA ----
comp     <- c("hhsize","child_share","elderly_share","female_share")   # composition vector D_h
controls <- c("income","expenditure","ag_days","offfarm_days","sown_area",
              "asset_index","head_age","head_edu","head_male",
              "friction_survey","poi_access_lag","gaez_overall","gaez_staple","gaez_constraint",
              "unit_value","text_policy1","text_policy2")              # your M3 control set
idvars   <- c(village="village_id", category="food_cat", year="wave",
              province="prov_id", hh="hh_id")
## outcomes
# participation : 1{self-produced quantity > 0}
# ihs_qty       : asinh(self-produced quantity, kg/month)
# self_suff     : bounded self-sufficiency rate, see below
## ---------------------------------------------

# Self-sufficiency rate (scale-free intensive-margin outcome; bounded [0,1]):
#   self_suff = min(1, self_qty / cons_qty)  where cons_qty > 0
#   cells with cons_qty == 0 -> NA (report how many are dropped)
df <- df %>% mutate(self_suff = ifelse(cons_qty > 0, pmin(1, self_qty/cons_qty), NA_real_))

FE  <- "category + year + province"        # pooled FE block (M3)
FEv <- "category + year + village"         # within-village FE block
CL  <- ~village
rhs <- function(v) paste(v, collapse = " + ")
```

Conventions: village-clustered SEs everywhere; report **Wald, df, p** for every joint test;
keep 4 significant digits; dairy excluded from category-level analyses (A4).

---

## A0. Omnibus two-margin separability test  →  `[[POST-A0]]`

**Purpose.** One number answering the *overall* question: is composition jointly excluded from
**both** margins simultaneously? (Manuscript 5.6, first block.)

**Design.** Stack the data twice — once with `y = participation` (margin `ext`), once with
`y = ihs_qty` (margin `int`). Give **every** regressor and every fixed effect a margin-specific
coefficient (fully interacted system = seemingly-unrelated stacking). Test the 8 composition
coefficients (4 per margin) jointly, clustering by village (clusters nest households across the
two stacks, so the cross-margin dependence is absorbed).

```r
stack <- bind_rows(df %>% mutate(y = participation, margin = "ext"),
                   df %>% mutate(y = ihs_qty,       margin = "int"))
vars <- c(comp, controls)
for (v in vars) {
  stack[[paste0(v,"_ext")]] <- stack[[v]] * (stack$margin=="ext")
  stack[[paste0(v,"_int")]] <- stack[[v]] * (stack$margin=="int")
}
rhsA0 <- rhs(c(paste0(vars,"_ext"), paste0(vars,"_int")))
mA0 <- feols(as.formula(paste0("y ~ ", rhsA0,
        " | margin^category + margin^year + margin^province")),
        data = stack, cluster = CL)
wald(mA0, keep = paste0("^(", paste(comp, collapse="|"), ")_(ext|int)$"))   # df = 8
```

**Prediction.** Strong rejection (both margins contribute). **Fill:** stacked Wald, df = 8, p.

---

## A1. Mundlak between–within decomposition  →  Table 7 cells `[[A1-a]] … [[A1-l]]`

**Purpose.** The formal test of the *geography of the margin*: cross-village composition variation
should load on participation; within-village variation should load on intensity. This is the single
most important post-estimation result.

**Design.** Augment the pooled M3 specification with **village means** of the composition vector.
With levels + village means included, the coefficient on the household-level term equals the
**within-village** effect, and the joint test on the village-mean block is the Mundlak test of
between ≠ within (numerically equivalent to the explicit demeaned parametrization).

```r
df <- df %>% group_by(village_id) %>%
  mutate(across(all_of(comp), ~mean(.x, na.rm=TRUE), .names = "{.col}_vm")) %>% ungroup()
compvm <- paste0(comp, "_vm")

mund <- function(yvar) feols(as.formula(paste0(
          yvar, " ~ ", rhs(c(comp, compvm, controls)), " | ", FE)),
          data = df, cluster = CL)

m_part <- mund("participation"); m_ss <- mund("self_suff"); m_ihs <- mund("ihs_qty")

W <- function(m, block) wald(m, keep = paste0("^(", paste(block, collapse="|"), ")$"))
W(m_part, compvm)  # between  -> A1-a (Wald), A1-b (p)
W(m_part, comp)    # within   -> A1-c, A1-d
W(m_ss,   compvm)  #          -> A1-e, A1-f
W(m_ss,   comp)    #          -> A1-g, A1-h
W(m_ihs,  compvm)  #          -> A1-i, A1-j
W(m_ihs,  comp)    #          -> A1-k, A1-l
```

**Predictions.** Participation: between significant, within not (mirrors 16.73 vs 6.41).
Self-sufficiency and IHS: within significant, between weak (mirrors the village-FE results and
frees the intensive margin from the scale-dependence caveat). Note the `self_suff` sample is
slightly smaller (cons_qty > 0 cells); report its N.

---

## A1b. Component-wise decomposition  →  `[[POST-A1b]]`

**Purpose.** Convert Table 4's coefficient pattern into formal statements: which single restriction
does the data reject, and does the joint rejection depend on any one component?

```r
m3 <- feols(as.formula(paste0("participation ~ ", rhs(c(comp, controls)), " | ", FE)),
            data = df, cluster = CL)
# (i) single-restriction tests
for (v in comp) print(wald(m3, keep = paste0("^", v, "$")))
# (ii) leave-one-out joint tests (drop one component from the tested block)
for (v in comp) print(wald(m3, keep = paste0("^(", paste(setdiff(comp, v), collapse="|"), ")$")))
```

Run the same loop on the **within-village IHS** model. **Prediction.** The joint rejection survives
dropping any single component *except* the elderly share (leave-out-elderly should weaken markedly).

---

## A2. RIF quantile profile of the intensive margin  →  `[[POST-A2]]`

**Purpose.** Band logic: composition should matter more for households *deeper inside* the band.
Trace the elderly-share coefficient across the self-sufficiency distribution.

**Design.** Unconditional (RIF) quantile regressions at τ ∈ {0.5, 0.6, 0.7, 0.8, 0.9}, with village
fixed effects and village-clustered inference; then a formal trend test by stacking the RIF outcomes.

```r
taus <- c(.5,.6,.7,.8,.9)
d2 <- df %>% filter(!is.na(self_suff))
fits <- map(taus, function(tt){
  d2$rif_y <- rif(d2$self_suff, method = "quantile", quantile = tt)
  feols(as.formula(paste0("rif_y ~ ", rhs(c(comp, controls)), " | ", FEv)),
        data = d2, cluster = CL)
})
cbind(tau = taus, elderly = map_dbl(fits, ~coef(.x)["elderly_share"]),
      se = map_dbl(fits, ~se(.x)["elderly_share"]))

# Trend test: stack the five RIF datasets, interact composition with centered tau
stk <- map_dfr(taus, function(tt){
  d2$rif_y <- rif(d2$self_suff, method="quantile", quantile=tt); d2$tau <- tt; d2 })
stk$tau_c <- stk$tau - mean(taus)
mtr <- feols(as.formula(paste0("rif_y ~ ", rhs(comp), " + ",
        paste0(comp, ":tau_c", collapse=" + "), " + ", rhs(controls), " | ", FEv)),
        data = stk, cluster = CL)
wald(mtr, keep = "elderly_share:tau_c")
```

**Prediction.** β_elderly(τ) rises with τ; trend coefficient positive and significant.
(Village clustering nests the repeated observations across τ; if you prefer, add a
village-level bootstrap of the trend coefficient, 999 reps, as a check.)

---

## A3. Composition × market-access on the within-village intensive margin  →  `[[POST-A3]]`

**Purpose.** Mechanism probe: if the channel is the transaction-cost band, the within-village
intensity association should **narrow** where access is better (band thinner). Corroborative only —
the proxies are village/county-level while the theoretical wedge is household–category-specific.

```r
Mv <- c("poi_access_lag","friction_survey")   # ← your exact market-access variable names
ints <- as.vector(outer(comp, Mv, paste, sep = ":"))
mA3 <- feols(as.formula(paste0("ihs_qty ~ ", rhs(comp), " + ", paste(ints, collapse=" + "),
        " + ", rhs(controls), " | ", FEv)),   # Mv main effects absorbed by village FE
        data = df, cluster = CL)
wald(mA3, keep = ":")                          # joint test of all interactions
wald(mA3, keep = "elderly_share:")             # elderly-specific block
```

**Prediction.** Negative elderly × access interactions; joint p informative even if modest.
Repeat with `self_suff` as outcome.

---

## A4. Category-attribute meta-regression (H3 gradient)  →  `[[POST-A4]]`

**Purpose.** Ask whether the category ranking is monotone in proxied band width. Seven usable
categories — descriptive by construction; report Spearman ρ (+ p) and a one-line WLS.

**Step 1 — code the attributes (1 = low, 2 = medium, 3 = high).** Draft below; adjust and freeze
*before* looking at the correlation:

| Category | Perishability | Courtyard producibility | Market thinness |
|---|---|---|---|
| Eggs | 3 | 3 | 2 |
| Edible oils | 1 | 2 | 2 |
| Vegetables | 3 | 3 | 1 |
| Fruits | 3 | 2 | 2 |
| Beans | 1 | 2 | 2 |
| Meat & aquatic | 3 | 1 | 1 |
| Staple grains | 1 | 2 | 1 |

**Step 2 — correlate with the category Wald statistics** (from Table 5; dairy excluded):

```r
meta <- tibble(cat = c("eggs","oils","veg","fruit","beans","meat","staple"),
               waldc = c(<W_eggs>, <W_oils>, <W_veg>, <W_fruit>, <W_beans>, <W_meat>, <W_staple>),
               perish = c(3,1,3,3,1,3,1), courty = c(3,2,3,2,2,1,2), thin = c(2,2,1,2,2,1,1))
meta$bandwidth <- rowMeans(meta[,c("perish","courty","thin")])
cor.test(meta$waldc, meta$bandwidth, method = "spearman")
lm(waldc ~ bandwidth, data = meta)   # descriptive WLS/OLS, n = 7
```

**Prediction.** ρ > 0. **Fill:** Spearman ρ and p.

---

## A5. External validity (robustness appendix; no manuscript placeholder)

```r
# (i) wave split: estimate M3 on 2023, validate on 2024 (and reverse)
for (w in unique(df$wave)) print(wald(
  feols(as.formula(paste0("participation ~ ", rhs(c(comp,controls)), " | category + province")),
        data = filter(df, wave==w), cluster = CL),
  keep = paste0("^(", paste(comp, collapse="|"), ")$")))
# (ii) leave-one-province joint Walds (pooled participation + within-village IHS)
for (p in unique(df$prov_id)) { d <- filter(df, prov_id != p); ... }
```

**Prediction.** Rejection stable across waves; no single province drives the margin flip.

---

## Placeholder map (what to send back)

| Token in manuscript | Location | Value(s) needed |
|---|---|---|
| `[[POST-A0]]` | §5.6, omnibus paragraph | stacked Wald, df=8, p |
| `[[A1-a]]…[[A1-l]]` | §5.6, Table 7 | 6 Wald + 6 p (3 outcomes × between/within) |
| `[[POST-A1b]]` | §5.6, component paragraph | single-restriction p's; leave-one-out joint Walds |
| `[[POST-A2]]` | §5.6, distribution paragraph | elderly β(τ) at 5 quantiles; trend coef + p |
| `[[POST-A3]]` | §5.6, mechanism paragraph | joint interaction p (IHS and self_suff) |
| `[[POST-A4]]` | §5.6, mechanism paragraph | Spearman ρ, p (+ final attribute codes) |

Send back the filled numbers (a screenshot of the R output per block is enough) plus the N used in
each self_suff model, and I will integrate them, rewrite the surrounding sentences to match what the
data actually say (including any overturned prediction — that must be reported, not smoothed over),
and refresh Figure/Table cross-references.
