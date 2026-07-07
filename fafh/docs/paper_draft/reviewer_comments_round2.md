# Second-Round Revision Comments

**Manuscript:** Machine-Learning-Based Estimates of Out-of-Home Food Consumption in China: Provincial and National Coefficients for Food Security Assessment  

**Main file:** `paper_first_revision.tex`  
**Included sections:** `section_literature_review_phd1.tex`, `section_research_design_phd2.tex`, `section_methods_phd3.tex`, `section_results_phd4.tex`, `section_discussion_phd4.tex`  

**Target journal:** American Journal of Agricultural Economics  

**Reviewer:** Anonymous (second round)  

---

## (A) Major Issues (must address)

**[Major] – Data subsection – Survey and sources still unnamed**  
The Data subsection refers to “household food consumption survey,” “data availability statement,” and file names (\texttt{data.csv}, \texttt{data2012.csv}) but does not name the micro survey (e.g., CHNS or other), waves/years, approximate sample size, or provincial coverage in the main text. Replicability and credibility require at least one sentence in the Data subsection that identifies the micro survey by name and states coverage (e.g., “The micro data come from [Survey name], waves [years], with approximately [N] households and coverage of [X] provinces.”).  
**Suggestion:** Add one to two sentences in the Data subsection (Section~\ref{subsec:data}) naming the survey and giving waves, approximate N, and provincial coverage; keep the data availability statement for full details and access.

**[Major] – Results – Bootstrap intervals not in main text**  
Bootstrap prediction intervals are described and referenced to supplementary material or authors, but no interval is reported in the main manuscript. Policy-oriented readers need to see at least one concrete interval in the results.  
**Suggestion:** Add one sentence or one small table in the Uncertainty Quantification subsection reporting bootstrap-based 95\% intervals for one preferred model (e.g., LightGBM or TabPFN) and 2–3 categories/years (e.g., rice and pork, 2020 and 2024), with a note that full intervals are in the supplementary material.

**[Major] – Introduction vs Methods – Spatial interpolation wording**  
The Introduction states “spatial interpolation (Kriging/IDW)”; the Methods section states that out-of-home coefficients use IDW (inverse-distance weighting) and grain structure uses IDW plus production share. The mixed “Kriging/IDW” in the Introduction may suggest both are used for the same object.  
**Suggestion:** In the Introduction (and abstract if applicable), replace “Kriging/IDW” with “spatial interpolation (IDW, with production shares for grain structure)” or equivalent so the wording matches the Methods section.

**[Major] – Results – Provincial table codes unexplained**  
Table 2 (Provincial heterogeneity) uses numeric province codes (11, 21, 13) without mapping to province names. Readers outside the project cannot interpret which regions these represent.  
**Suggestion:** Add one sentence or a footnote that maps codes to province names (e.g., 11 = Beijing, 21 = Liaoning, 13 = Hebei), or add a “Province name” column to the table for the selected provinces.

---

## (B) Minor Issues / Suggestions

**[Minor] – Abstract**  
The phrase “bootstrap-based prediction intervals where available” is slightly vague. Consider specifying “and bootstrap-based 95\% prediction intervals (reported in the results and supplementary material)” so readers know where to find them.

**[Minor] – Results – Rationale for preferred models**  
The text explains that LightGBM, TabPFN, and FT-Transformer are emphasized; one tighter sentence could state explicitly that these are chosen for best stability and prediction performance (e.g., “We emphasize LightGBM, TabPFN, and FT-Transformer for their combination of prediction accuracy and stability across categories.”).

**[Minor] – Discussion – FAO worked example**  
The numerical illustration uses “suppose FAO or similar sources report total per capita cereal… as approximately 150 kg/year.” Citing the actual FAO figure and year (e.g., “FAO reports approximately 150 kg per capita for [year]”) where possible would strengthen the link to international benchmarks; if the 150 kg is purely illustrative, add “(illustrative)” next to the figure.

**[Minor] – Policy – Data and code availability**  
The Data and code availability paragraph is clear. If the journal requires a dedicated “Data availability” or “Conflict of interest” subsection, consider moving this paragraph into a short subsection to satisfy checklist requirements.

---

## (C) Typo and Style

**[Typo] – Filename**  
The filename \texttt{procince\_pop.csv} appears in the Data subsection and Methods (and possibly elsewhere). If the actual file name in the project is \texttt{province\_pop.csv}, correct it throughout; if \texttt{procince\_pop.csv} is intentional (e.g., legacy naming in code), add a short footnote: “Filename as in the project codebase.”

**[Style] – “vs” in body text**  
In the Results section, “1.139 (main) vs 1.221 (robust)” and similar use “vs” without a period. For consistency with the rest of the manuscript, use “vs.” (e.g., “1.139 (main) vs. 1.221 (robust)”).

**[Style] – References**  
Ensure the \texttt{references.bib} file contains full entries for all citation keys used in the manuscript (e.g., USDA\_ERS\_FAH, Byrne2004, Ma2006, Zhou2014, Wang2024, Wang2012, COVID\_FAH, FAO\_OECD\_Outlook, IFPRI\_China) and that no placeholder text remains in the compiled references list.

---

## Summary for the Editor

The first revision and language polish have improved clarity and consistency. The research question, design, methods (including Copula and spatial interpolation), and limitations are now clearly stated; provincial results and a concrete FAO-style numerical illustration are present; and the conclusion specifies limitations in concrete terms.

Remaining issues are: (1) the micro survey and data sources are still not named in the Data subsection, which is important for replicability; (2) bootstrap uncertainty is still not illustrated in the main text with at least one interval or small table; (3) the Introduction’s “Kriging/IDW” wording should be aligned with Methods (IDW for coefficients; IDW + production share for grain structure); and (4) provincial table codes need a brief mapping to province names. Addressing these four points and the minor/typo items above will bring the manuscript to a standard suitable for acceptance at the American Journal of Agricultural Economics.

**Recommendation: Minor revision.** The paper is close to acceptance; the requested changes are focused and should be straightforward to implement.
