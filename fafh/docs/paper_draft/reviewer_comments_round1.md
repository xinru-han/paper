# First-Round Revision Comments

**Manuscript:** Machine-Learning-Based Estimates of Out-of-Home Food Consumption in China: Provincial and National Coefficients for Food Security Assessment  

**Main file:** `paper_first_draft.tex`  
**Included sections:** `section_literature_review_phd1.tex`, `section_research_design_phd2.tex`, `section_methods_phd3.tex`, `section_results_phd4.tex`, `section_discussion_phd4.tex`  

**Target journals:** American Journal of Agricultural Economics, Agricultural Economics, Journal of Agricultural Economics  

**Reviewer:** Anonymous (first round)  

---

## (A) Major Issues (must address)

**[Major] – Abstract & Introduction – Primary outcome and headline quantity**  
The research question is “How much does China consume food out-of-home?” but the abstract and introduction emphasise the *coefficient* (total/at-home) and state that “coefficients [are] above one for all categories.” The paper does not state a single headline *quantity* (e.g. national out-of-home share of total consumption or kg per capita for a key category) in the abstract. Readers of top agricultural economics journals expect either a clear statement that the main deliverable is coefficients (with quantities derived in post-processing and reported in results/discussion) or one concrete quantity in the abstract to anchor policy relevance.  
**Suggestion:** Add one sentence in the abstract giving a headline quantity (e.g. “In 2024, out-of-home consumption adds approximately X% to total grain consumption at the national level”) or explicitly state that the primary contribution is coefficient estimates from which quantities are derived and reported in the results. Ensure the introduction mirrors this (contribution = coefficients; quantities in Section 5/6).

**[Major] – Literature review – Gap statement**  
The gap is described across two paragraphs; the exact *operational* gap (no nationally or provincially representative, commodity-level *coefficient* in the form total/at-home for China) could be stated in one crisp sentence immediately before “This paper addresses the gap by…”  
**Suggestion:** Insert one sentence before the “This paper addresses the gap” paragraph: e.g. “No existing study or international dataset provides nationally or provincially representative, commodity-level out-of-home consumption coefficients (total-to-at-home ratio) for China suitable for macro-level food balance and demand analysis.” Then keep the following “This paper addresses…” as is.

**[Major] – Research design / Data – Data sources not identified**  
The manuscript refers to `data.csv`, `data2012.csv`, CHNS, “household survey,” and macro/production files but does not name the specific survey(s), years, geographic coverage, or sample sizes. Replicability and credibility require a clear data subsection or paragraph.  
**Suggestion:** Add a short “Data” subsection (or a dedicated paragraph in Research Design) that: (1) names the micro survey source(s) (e.g. CHNS waves, years, number of households/observations, provincial coverage); (2) states the source and construction of `data2012.csv` (macro province–year data); (3) briefly notes sources for production and per-capita at-home consumption (`data_q.csv`) and population. If data are not publicly available, add a data availability statement.

**[Major] – Methods – Copula matching specification**  
Section 4 (Methods) and Research Design describe “Copula-based income distribution matching” and scaling the micro distribution to the macro mean to generate synthetic `indinc`. The actual Copula specification (empirical vs parametric, which marginal/copula, how “shape” is preserved) is not given.  
**Suggestion:** In the Copula subsection (Methods), add 2–3 sentences specifying: (i) whether an empirical Copula, a parametric Copula (e.g. Gaussian), or a quantile-scaling (rank-preserving) approach is used; (ii) how the micro income distribution is used (e.g. kernel density per province–year or pooled) and how scaling to the macro mean is done. This is necessary for reproducibility and for referees to evaluate the identification strategy.

**[Major] – Methods – Spatial interpolation**  
The text mentions “Kriging/IDW,” “simplified Kriging,” and “inverse-distance” for missing provinces; it is unclear which method is used for out-of-home coefficients versus grain structure, and how “missing” provinces are defined.  
**Suggestion:** In the “Spatial interpolation for missing provinces” subsection, state explicitly: (i) which method is used for the out-of-home coefficient (Kriging vs IDW, and with what distance/neighbour definition); (ii) how a province is classified as “missing” (no micro data at all vs no data for that year); (iii) that grain structure uses IDW plus production share as already noted. Use the same convention throughout (e.g. “IDW for coefficients; IDW + production share for grain structure”).

**[Major] – Results – Uncertainty not shown in tables**  
Bootstrap prediction intervals are mentioned and referenced to `predictions_<model>_bootstrap.csv`, but no table or figure in the manuscript reports intervals. Policy-oriented readers need to see at least one summary of uncertainty.  
**Suggestion:** Add one table or figure (or a supplementary table) reporting bootstrap-based 95% intervals (e.g. 2.5%–97.5% percentiles) for one preferred model (e.g. LightGBM or TabPFN) and selected categories/years (e.g. rice, pork, 2020 and 2024). Alternatively, add a column for “95% interval” to Table 1 for one model and note that full bootstrap results are in the supplementary material.

**[Major] – Results – Provincial results absent**  
The paper claims provincial and national coefficients, but the Results section focuses on national estimates only. Provincial heterogeneity is discussed in Discussion and Policy but not demonstrated.  
**Suggestion:** Add a short subsection (e.g. “Provincial heterogeneity”) with either: (a) a summary table (e.g. coefficient ranges or selected provinces for 1–2 years and 2–3 categories), or (b) a clear reference to a figure/map in supplementary material showing provincial variation. This supports the claim that provincial estimates are a contribution.

**[Major] – Discussion – Concrete comparison with FAO/OECD/IFPRI**  
The discussion correctly states that definitions differ and “direct numerical comparison is limited,” but does not perform any concrete numerical comparison.  
**Suggestion:** Add one worked example: take one external figure (e.g. FAO per capita grain or meat consumption for China for a given year), apply the paper’s coefficient to derive implied at-home vs total consumption, and report the numbers in a short paragraph or small table, with an explicit caveat about definitional and coverage differences. This strengthens the link to international benchmarks.

**[Major] – Conclusion – Limitations too generic**  
Limitations are summarised as “dependence on survey and macro data availability,” “assumptions underlying Copula matching and spatial interpolation,” and “different ML models yield somewhat different point estimates.” These are appropriate but vague.  
**Suggestion:** Specify at least one concrete limitation, e.g.: (i) survey coverage does not include all provinces or all years, so that some province–year cells rely entirely on spatial interpolation; (ii) Copula matching assumes the micro income distribution shape is transportable to macro cells; or (iii) validation against independent macro out-of-home data was not possible due to lack of such data. This meets expectations of top journals for explicit limitation statements.

**[Major] – References – Placeholder only**  
The References section lists “Citation keys to be added…” and placeholder keys; there is no complete bibliography.  
**Suggestion:** Before submission, replace the placeholder paragraph with a full `\bibliography{references}` and ensure all citation keys (USDA_ERS_FAH, Byrne2004, Ma2006, Zhou2014, Wang2024, Wang2012, COVID_FAH, FAO_OECD_Outlook, IFPRI_China, etc.) have corresponding entries in the .bib file. Remove the “Citation keys to be added” text.

---

## (B) Minor Issues / Suggestions

**[Minor] – Abstract**  
Consider adding “and bootstrap-based uncertainty intervals” when mentioning reporting of coefficients, if uncertainty is a selling point (e.g. “We report national and provincial out-of-home consumption coefficients for 15 food categories over 2015–2024 and bootstrap prediction intervals”).

**[Minor] – Introduction**  
The list of 12 ML models can stay in Methods; the introduction may keep “12 machine-learning models” without enumerating them.

**[Minor] – Literature (Concepts)**  
The phrase “the ratio of at-home to total consumption (or its inverse, the out-of-home share or ‘coefficient’)” may confuse: the paper’s coefficient is total/at-home (the inverse of at-home/total).  
**Suggestion:** Clarify in one sentence that in this paper the “out-of-home consumption coefficient” is defined as total consumption divided by at-home consumption (so it is the inverse of the at-home share).

**[Minor] – Research design**  
Internal project filenames such as `论文初稿.md`, `模型预测策略与步骤.md` appear in the main text.  
**Suggestion:** For the journal version, replace with a generic phrase such as “project documentation” or move the reference to a technical appendix/footnote.

**[Minor] – Research design – Model count**  
“11 models in the imputation selection step” appears in section_research_design_phd2.tex (Imputation subsection); elsewhere the text says 12 models.  
**Suggestion:** Unify to “12 models” everywhere (including the imputation step).

**[Minor] – Research design & Methods – Terminology**  
“In-home ratio” and “in-home consumption” appear in the Research Design section; the rest of the paper uses “at-home.”  
**Suggestion:** Replace “in-home” with “at-home” throughout (e.g. “at-home consumption ratio,” “at-home ratio”) for consistency.

**[Minor] – Methods**  
The Methods refer to “Section~\ref{sec:copula}”; ensure the label `\label{sec:copula}` exists in the Methods section and is unique (Research Design has `\label{subsec:copula}`). Verify cross-references compile correctly.

**[Minor] – Results**  
The text states that results from LightGBM, TabPFN, and FT-Transformer are emphasised; the rationale (e.g. best or most stable performance, best imputation model) could be stated in one sentence in Results or Methods.

**[Minor] – Discussion**  
The long list of TabPFN 2024 coefficients in the first paragraph of the Discussion could be moved to a compact table to improve readability.

**[Minor] – Policy / Data availability**  
Add a short “Data and code availability” (or “Data availability”) statement indicating where coefficient outputs and code can be found (e.g. supplementary material, repository, or “available from the authors upon request”), as expected by many SSCI journals.

---

## (C) Typo and Style

**[Typo] – Filename**  
“procince_pop.csv” appears in Research Design and Methods (e.g. “population (e.g.\ \texttt{procince\_pop.csv})”).  
**Suggestion:** Correct to “province_pop.csv” unless the actual file name in the project is intentionally “procince_pop.csv.”

**[Style] – Spelling**  
“Urbanisation” (British) is used; some target journals use American English.  
**Suggestion:** Choose one convention (e.g. “urbanization”) and apply it consistently, or follow the chosen journal’s style guide.

**[Style] – Journal name**  
The workspace rules mention “American Journal of Agricultural Sciences”; the standard SSCI journal in the field is “American Journal of Agricultural Economics” (AJAE).  
**Suggestion:** Confirm the correct journal name and use it consistently in the manuscript and cover letter.

**[Style] – References**  
Remove the paragraph “Citation keys to be added to the bibliography…” before submission and rely on the completed .bib file and `\bibliography{references}`.

---

## Summary for the Editor

The manuscript addresses an important gap: the lack of nationally and provincially representative, commodity-level out-of-home food consumption coefficients for China that can be used in macro-level food balance and food security analysis. The research question is clear, and the combination of micro survey data, Copula-based income matching, ML prediction, imputation, and spatial interpolation is motivated by data constraints and is generally well explained. The literature review situates the work appropriately, and the results show coefficients above one for all categories with sensible variation across products and models. Robustness to imputation and bootstrap uncertainty are strengths.

Main weaknesses are: (1) insufficient identification of data sources and lack of a proper data subsection; (2) incomplete methodological detail on the Copula (specification) and spatial interpolation (exact method and missing-province definition); (3) no presentation of uncertainty (bootstrap intervals) in the main text or tables; (4) no presentation of provincial results despite their policy relevance; (5) no concrete numerical comparison with FAO/OECD/IFPRI despite discussion of these sources; (6) generic limitation statements and an incomplete reference list. Addressing these will bring the paper in line with the standards of the target journals. The writing is generally clear; terminology and internal references (e.g. “in-home” vs “at-home,” “11” vs “12” models, filename typo) need minor consistency fixes.

**Recommendation: Major revision required.** The contribution and design are promising and the paper is suitable for consideration at the target journals after the authors address the major issues above, add data and methodological detail, report uncertainty and provincial results, and complete the references and data availability statement.
