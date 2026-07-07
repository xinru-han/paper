## Round-1 referee report (anonymous)

### Recommendation

**Major revision required.** The paper addresses an important measurement gap (commodity-level out-of-home food consumption coefficients for China) and leverages a creative micro–macro bridging strategy. However, the current draft falls short of top-field standards in (i) data transparency and replicability, (ii) internal consistency of the methodological description, and (iii) disciplined external comparison and uncertainty reporting. These can be fixed **without re-running models** by tightening definitions, aligning statements with the implemented pipeline, and revising interpretation.

### Major comments

1. **Data description is not publication-grade (must be made precise).** The draft does not clearly state the micro survey name (or anonymity rationale), years, sample size, key representativeness limitations, unit definitions (edible weight vs raw), and provincial coverage; nor does it provide enough detail on the macro covariates’ sources and construction. Even if raw data cannot be shared, the paper must report **(a)** what each dataset is, **(b)** coverage, **(c)** key variable definitions, **(d)** how missingness is handled, and **(e)** what is reproducible from the shared code/CSV outputs.

2. **“Copula” wording appears inconsistent with the actual procedure described.** The Methods section describes a **rank-preserving quantile scaling** approach rather than a parametric Copula model; the Research Design section also labels it “Copula-based matching.” The paper must either (i) justify the label and precisely state the Copula structure used, or (ii) relabel as *distribution (quantile) matching* and reserve “Copula” only if a Copula is actually estimated. This matters for credibility.

3. **Spatial interpolation description is inconsistent (Kriging vs IDW).** Literature/Design mentions Kriging, while Methods describes IDW in `apply_kriging_interpolation`. This should be corrected and described consistently, including the distance metric, whether interpolation is done within-year, and which provinces are “missing” vs “sparse.”

4. **Results interpretation relies on claims that are not currently justified by evidence in-text.**
   - The statement “some models exhibit unstable or extreme point estimates” should be backed by a compact diagnostic table/appendix reference (even if you cannot re-run, you can reference existing CSVs).
   - The claim “TabPFN attains the best prediction MAE …” must be clearly tied to an evaluation design (train/test split? CV? across categories?), and it should be explicit that these metrics are **internal predictive accuracy**, not causal identification.

5. **Uncertainty quantification is currently too hand-wavy.** The “representative intervals” in the Results are labeled “approximate.” Either report intervals **directly from the saved bootstrap CSVs** (with a clear citation to file+columns) or remove the illustrative bracketed intervals and state where the full interval tables live (appendix/supplement). Top journals will not accept “approximate” intervals.

6. **External comparison (FAO/OECD/IFPRI) needs citations and careful boundary alignment.** The Discussion includes an illustrative FAO number without citation and mixes “cereal” with “rice.” This should be rewritten as a conceptual comparison only, unless you provide a clearly cited, definition-aligned numeric comparison. Otherwise it risks being misleading.

7. **Definition discipline: coefficient vs share.** The coefficient is defined as total/at-home, but the draft sometimes discusses “out-of-home share.” When translating coefficient to share, the paper should use \(1 - 1/\text{coef}\) and label it as implied share. Keep terminology consistent.

8. **Reproducibility and file naming.** There are file name typos (e.g., `procince_pop.csv`) and several places where the draft cites internal code filenames as if they were external supplementary material. A clean “Replication package” paragraph is needed that states exactly what is provided (CSV outputs + scripts) and what is not (raw survey microdata), and how the reader can reproduce tables from the outputs.

### Minor comments

- Tighten the abstract: reduce implementation details (model list) and add 1–2 concrete quantitative takeaways (e.g., coefficient ranges for key categories) while avoiding overclaiming.
- Standardize terminology: “out-of-home,” “food away from home (FAH),” “away-from-home.” Pick one primary term and define synonyms once.
- Avoid mixing Chinese column names in the main narrative. If CSV columns are Chinese, mention this once and map them to English symbols.
- Add a brief limitations paragraph that separates (i) extrapolation to missing provinces, (ii) distribution transportability, and (iii) lack of external validation.

