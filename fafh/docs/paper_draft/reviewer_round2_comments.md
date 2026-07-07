## Round-2 referee report (anonymous)

### Recommendation

**Major revision to minor revision (borderline).** The authors have substantially improved internal consistency (income matching terminology; IDW interpolation; bootstrap reporting). Remaining issues are mostly about tightening claims and improving transparency in a way that does not require re-estimation.

### Major comments

1. **Data transparency is still too vague for a top journal.** The paper now states that microdata are access-restricted, but it still lacks the minimum descriptive statistics needed for readers to interpret representativeness: years covered in the micro sample, number of households/observations, and provincial coverage. If the authors cannot disclose the survey name, they should at least report these coverage statistics and provide a clear rationale for anonymity.

2. **Clarify the estimand and interpretation.** The coefficient is total/at-home. The paper should explicitly state that it is a *scaling factor* that transforms at-home consumption to total consumption under aligned definitions, and that it is not a behavioral parameter. Relatedly, the Discussion should avoid language that could be read causally (“drivers”) unless supported.

3. **Model evaluation and model choice need a more disciplined presentation.** The Results section ranks models by MAE/RMSE, but the paper should clarify:
   - what the evaluation target is (ratio vs coefficient),
   - what the validation design is (CV on micro; not an out-of-sample macro validation),
   - why focusing on LightGBM/TabPFN/FT-Transformer is appropriate (e.g., stability + accuracy), and
   - whether “unstable/extreme” models are excluded from any summary tables (and if so, document the rule).

4. **External comparison section should be tightened further.** After revisions, it is mostly conceptual; good. Still, please remove any remaining suggestion that the coefficients can be directly reconciled with FAO/OECD/IFPRI totals without boundary alignment, and add a short paragraph that lists the key boundary mismatches (supply-use vs edible consumption; feed/processing; institutional catering).

### Minor comments

- Standardize hyphenation: use “out-of-home” consistently.
- Make the “replication package” paragraph more concrete: list the exact output files needed to reproduce each table in the paper.
- Consider adding one short “reader’s guide” sentence in Methods that maps: ratio \(\rightarrow\) coefficient \(\rightarrow\) implied out-of-home share \(1 - 1/\text{coef}\).

