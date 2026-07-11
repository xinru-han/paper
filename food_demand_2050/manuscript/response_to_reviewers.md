# Response to Reviewers

**Original manuscript:** *Alternative pathways for China's diet transition: Implications for food security, nutrition and greenhouse gas emissions to 2050*
**Revised manuscript:** *China's dietary transition to 2050 reshapes global agricultural markets and environmental footprints*

We are grateful to the reviewer for a careful and constructive report. The reviewer judged the question original and important but found the execution wanting in three respects: unclear methodology, inadequately documented data, and presentation that failed to communicate the findings. We took this assessment seriously and undertook a structural revision rather than a patch: the model has been re-implemented in open-source Python and validated cell-by-cell against the original; a multi-region world market model, a fully cited four-dimension footprint library, and a global net-effect accounting framework have been added; all data sources are now cited to the primary reference; and the results are presented through four main figures and four Extended Data figures instead of structurally identical tables. Below we respond point by point ("Comment → Response → Location of change").

---

## General comments

**G1. The methodology is not clearly explained; the market-equilibrium mechanism is never explained or cited.**
*Response:* The Methods now devote a full subsection to CASM's mechanism: recursive-dynamic mixed-complementarity equilibrium, acreage/yield supply equations, livestock feed-cost linkages, the seven demand components, four household groups with at-home/away-from-home split, and the price-transmission and trade-clearing mechanism through which scenario shocks propagate. The world model (CASM-World) is described analogously with its PEATSim-type lineage cited. The complete algebraic specification and source code are now open.
*Location:* Methods, "The China Agricultural Sector Model (CASM)" and "CASM-World and the transmission experiment"; Code availability.

**G2. CASM is not referenced, so readers cannot examine the specification independently.**
*Response:* We go beyond a citation: the full model—code, parameter files, base-year database and a validation report showing machine-precision agreement with the original implementation (median relative deviation ≤ 1.4 × 10⁻¹⁶ across all 19 scenarios)—is publicly released at github.com/xinru-han/paper (folder `food_demand_2050`). Every number in the paper can be reproduced cell-by-cell.
*Location:* Methods, "Validation and reproducibility"; Data and Code availability; Extended Data Fig. 4; Supplementary Note 1.

**G3. Data sources are not clearly identified (e.g. food composition attributed only to "national nutrition authorities").**
*Response:* All sources are now cited to the primary reference: China Food Composition Tables, 6th edn (Yang et al. 2018) for nutrients; FAOSTAT emission intensities (2023) for farm-gate carbon; Poore & Nemecek (2018) for life-cycle carbon and land; Mekonnen & Hoekstra (2011, 2012) for water; Ludemann et al. (2022), IPCC (2019), Leach et al. (2012) and Uwizeye et al. (2020) for nitrogen; CASS-IQTE and UN WPP 2024 for population. The coefficient library itself is published with a per-value citation and an explicit "no unsourced value" policy.
*Location:* Methods, "Nutrition accounting" and "Environmental footprint accounting"; Supplementary Table 12; repository `modules/coefficients/`.

**G4. The out-of-home consumption extension is undocumented.**
*Response:* Methods now explain that food demand is modelled for four household groups (urban/rural × at-home/away-from-home), and that the base-year database reconciles NBS household-survey quantities with supply-utilisation accounts, allocating the survey-unrecorded residual to away-from-home and processing uses. The reconciliation procedure and base-year balances are in the open repository, and the rationale (omitting eating-out biases dietary assessments) is cited to Sheng et al. (2021).
*Location:* Methods, "The China Agricultural Sector Model (CASM)".

**G5. Trade vs emissions inconsistency: the model trades internationally but emissions use only Chinese production coefficients; nowhere acknowledged.**
*Response:* This comment reshaped the paper. Rather than acknowledging the inconsistency as a limitation, we resolved it: the revised paper uses a sequentially linked world-market transmission experiment and computes the **global net effect** of each dietary scenario—China's domestic footprint change *plus* trade-induced production adjustments in all partner regions, evaluated under a single coefficient boundary. This is now a headline result: China's healthy-diet transition lowers *global* agricultural emissions by 495 Mt CO₂e (−9.3%), with 91% of the carbon saving (and 77–96% of water/nitrogen/land physical reductions) occurring outside China. A domestic-coefficient-only account would have missed nine-tenths of the effect. We additionally separate consumption- and production-boundary footprints for China and report both.
*Location:* Results, "Global transmission" and "The global net effect"; Methods, "The global net-effect (trade–emissions consistency) framework"; Figs 3–4; Supplementary Tables 7, 10.

**G6. No in-text references to the appendices.**
*Response:* The revised manuscript references every Supplementary Table and Extended Data figure explicitly at the point of use (e.g. Supplementary Tables 1–11, Extended Data Figs 1–4 are each called out in Results or Methods).
*Location:* Throughout Results and Methods.

**G7. Scenario codes A1–C6 are not defined in the main text.**
*Response:* Table 1 in the main text now defines all 19 codes compactly (pathway × population × urbanisation × ageing), and the first mention of each pathway gives its representative code (e.g. "PTS (scenario A1)"). The full matrix with numerical assumptions is Supplementary Table 1, released as a machine-readable file.
*Location:* Main text Table 1; Results §1; Supplementary Table 1.

**G8. The healthy-diet benchmark quantities are never tabulated, and base-year consumption is not shown.**
*Response:* Supplementary Table 2 now tabulates the benchmark in full: the five guideline systems' recommended intakes, the composite band and midpoint, edible-share conversions to purchase quantities, and the 2023 base-year CASM consumption for each food group. The construction rule (cross-system min/max of midpoints; Korean guideline excluded for lack of gram weights) is stated in Methods. Fig. 1 displays the benchmark band graphically against all pathways, and 2024 base values appear in Supplementary Tables 3–5.
*Location:* Methods, "The composite healthy-diet benchmark"; Supplementary Table 2; Fig. 1b.

**G9. Presentation: only structurally identical tables of absolute quantities; add percentage changes and figures.**
*Response:* The results are now communicated through four main figures (framework/pathways; China multi-dimensional outcomes; global transmission map and price panel; global net-effect bridge and MTS realisation curve) and four Extended Data figures. All quantity tables have moved to the Supplementary Information and every one carries percentage-change columns versus BS 2050.
*Location:* Figs 1–4; Extended Data Figs 1–4; Supplementary Tables 3–7.

**G10. The Results section is monotonous — long enumerations of numbers.**
*Response:* The Results have been rewritten from scratch around five arguments (three diets restructure demand and nutrition; composition effects on China's own footprint are modest; global transmission; global net effect; the economics of a moderate transition), each led by its finding rather than by scenario-by-scenario enumeration. Commodity-by-commodity listings have been replaced by figures and summary statistics, with full detail in the SI.
*Location:* Results, entire section.

**G11. Citations supporting one idea should appear in ascending year order.**
*Response:* Done throughout; the revised manuscript uses Nature-style numbered citations, and multi-reference groups are ordered by year (e.g. refs 1–3, 10–14).
*Location:* Throughout.

---

## Specific comments

**S1 (p4 r1). "This transition has improved food availability" does not follow logically.**
*Response:* The sentence has been removed. The introduction now describes the transition's consequences directly (diet-quality, disease-risk and environmental pressures) without the non-sequitur.
*Location:* Main, paragraph 1.

**S2 (p4 r12–14). Energy intake declined while the fat share rose — needs explanation.**
*Response:* Now explained explicitly: "Because fat carries more than twice the energy per gram of carbohydrate, this structural shift has raised the fat share of dietary energy even as total energy intake plateaued."
*Location:* Main, paragraph 1.

**S3 (p6 r7). Colon required after "follows".**
*Response:* The passage was rewritten; no such construction remains.
*Location:* n/a (restructured).

**S4 (p6 r13). Citation needed for CASM.**
*Response:* CASM v2.2.7 is now identified with its institutional home, full Methods description, and a public repository containing the complete specification, code and validation—stronger than a citation alone (see G1–G2).
*Location:* Methods; Code availability.

**S5 (p6 r29). Why exchange rates? Does the model capture imports (e.g. beef from AUS/NZ)? How much of each category is imported?**
*Response:* Methods now state the price-linkage mechanism (domestic and border prices connected through tariff-and-margin wedges and the exchange rate; net trade clears each market). Import dependence is now a result in its own right: Extended Data Fig. 3 and Supplementary Table 7 report self-sufficiency ratios and net imports by commodity and scenario (e.g. 2050 BS net imports of 9.0 Mt beef, 11.7 Mt pork, 115.8 Mt soybeans; dairy self-sufficiency falling to 0.37 under HDS), and the world model resolves which regions supply them (beef from Brazil/Argentina/Australia; dairy from NZ/EU/US).
*Location:* Methods, CASM subsection; Results §3; Extended Data Fig. 3; Supplementary Table 7.

**S6 (p7 r3–5). How were the out-of-home update, urban–rural differences and supply-use consistency implemented, with what data?**
*Response:* Documented in Methods (see G4): NBS household-survey quantities reconciled with supply-utilisation accounts; four household groups; residual allocation to away-from-home/processing. The base-year database is in the open repository.
*Location:* Methods, CASM subsection.

**S7 (p7 r26). "Food income elasticities", not "demand elasticities".**
*Response:* Corrected; the revised text uses "income elasticities of food demand" throughout.
*Location:* Methods, "Scenario design".

**S8 (p8 r12–14). Population figures need citation.**
*Response:* All demographic assumptions are now cited: medium projection from the Institute of Quantitative and Technical Economics, CASS; high/low from UN World Population Prospects 2024 (ref. 31); values updated to the current projection vintage (1.367 bn in 2035, 1.259 bn in 2050; high 1.420/1.389 bn; low 1.345/1.200 bn) and tabulated with urbanisation anchors in Table 1 and Supplementary Table 1.
*Location:* Methods, "Scenario design"; Table 1; Supplementary Table 1.

**S9 (p8 Table 1). A6/B6/C6 "ageing considered" undefined; appendix not referenced.**
*Response:* Table 1 now specifies the ageing adjustment (adult-equivalent consumers from age–sex energy requirements: 1.397 bn in 2035, 1.270 bn in 2050; plus an elasticity adjustment of −0.0314 per percentage point of old-age share), Methods explain the conversion, and ageing-scenario results—including the emissions the original could not report—appear in Supplementary Tables 5, 6 and 9.
*Location:* Table 1; Methods, "Scenario design"; Supplementary Tables 1, 9.

**S10 (p9 r18–23). Rationale for combining dietary recommendation systems; detail needed.**
*Response:* Methods now give the rationale (a single national guideline embeds one dietary culture; the composite band spans five internally consistent systems and reduces dependence on any single normative choice) and the exact construction rule; Supplementary Table 2 provides the complete numerical benchmark by system and food group, including the excluded Korean guideline and why.
*Location:* Methods, "The composite healthy-diet benchmark"; Supplementary Table 2.

**S11 (p10 r1). List the food groups under analysis.**
*Response:* The 14 projected commodities are listed in Fig. 1 and enumerated in Supplementary Tables 3–4 (rice, wheat, edible oils, fruits, vegetables, pork, beef, mutton, poultry, eggs, dairy, aquatic products, plus sugar and legumes within the benchmark's 11 food groups); the CASM commodity space (37) and world commodity space (31) are stated in Methods.
*Location:* Fig. 1; Methods; Supplementary Tables 2–4.

**S12 (p10 data sources). First paragraph incomplete; all sources need clear references for replicability.**
*Response:* The data-sources text has been rewritten with primary citations for every input (see G3), and replicability is guaranteed by the open release of every input file.
*Location:* Methods; Data availability; Supplementary Table 12.

**S13 (p11). Long enumerations of numbers difficult to follow; vary sentence styles.**
*Response:* The Results were rewritten argument-first with figures carrying the detail (see G10).
*Location:* Results, entire section.

**S14 (p11 r16/22). B1, C1 etc. never defined.**
*Response:* Defined at first use and in Table 1 (see G7).
*Location:* Table 1; Results §1.

**S15 (p11 r21). Which foods count as "micronutrient-rich"?**
*Response:* The vague phrase has been dropped. The revised text names foods explicitly (dairy, aquatic products, poultry, vegetables) and quantifies diet quality against guideline ranges in Supplementary Table 8.
*Location:* Results §1; Supplementary Table 8.

**S16 (p12 Table 2 notes). Notes must be standalone; spell out abbreviations in all tables.**
*Response:* Every table and figure legend now spells out all scenario abbreviations (BS/PTS/HDS/MTS and A/B/C codes) and units in its own note.
*Location:* Table 1; Supplementary Tables 1–12; figure legends.

**S17 (p12 Table 2). Processed foods, sweets, sugary drinks not included though they rise with income/urbanisation.**
*Response:* Now acknowledged and bounded: CASM covers primary and first-stage processed commodities; sugar and oils are inside the model (added-sugar intake is reported: 13 g per day, Supplementary Table 8), but highly processed foods and sugar-sweetened beverages are not separately represented, so the nutrition results likely understate the unhealthy tail of the preference-driven pathway. This is stated in the Discussion's limitations.
*Location:* Discussion, limitations paragraph; Supplementary Table 8.

**S18 (p12 r7). "Aggregate demand more sensitive to population than urbanisation" is a mathematical given — reframe.**
*Response:* Reframed. Population variants are described as pure rescaling (±7% "without changing composition"), and the analytical content now lies in the composition-versus-scale distinction and in the non-trivial ageing result (adult-equivalent demand 3–7% lower, ranking of pathways preserved).
*Location:* Results §1.

**S19 (p14 r6). "C6 remains below C1" uninterpretable without scenario definitions.**
*Response:* All such passages now name the scenario in words ("the ageing-adjusted moderate-transition case") with codes defined in Table 1.
*Location:* Results §1; Table 1.

**S20 (p20 limitations). Acknowledge (a) missing processed/sugary foods; (b) whether trade is in the model and how emissions vary with domestic vs imported coefficients.**
*Response:* (a) Acknowledged as in S17. (b) Superseded by construction: trade is explicit in both models, and the domestic-versus-imported coefficient question is now the paper's central methodological contribution—the global net-effect framework applies region-resolved farm-gate coefficients to all regions' trade-adjusted production, and the farm-gate versus life-cycle boundary sensitivity (Extended Data Fig. 2) bounds the coefficient question from both sides. The remaining limitations (fixed 2023 coefficients, M&H water vintage, world-model commodity coverage) are stated candidly.
*Location:* Discussion, limitations; Methods, "The global net-effect framework"; Extended Data Fig. 2.

---

## Note on corrected numbers

In re-implementing and validating the model we found that the original Table 4 mixed two coefficient vintages: BS/PTS nutrition values came from a legacy workbook computed with an outdated energy-coefficient table (e.g. BS 2050 energy 3,070.27 kcal), while HDS/MTS used the current table. The revised manuscript uses the single internally consistent set throughout (BS 2050 energy 3,035.84 kcal; 2024 base 2,957.57 kcal); the correction changes no qualitative finding. Similarly, the original implementation left emissions for the ageing scenarios (A6/B6/C6) uncomputed; the new footprint module covers all 19 scenarios (Supplementary Note 1).
