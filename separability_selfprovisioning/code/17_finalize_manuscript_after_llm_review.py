#!/usr/bin/env python3
"""Finalize full manuscript after DeepSeek rewrite and Claude review.

This script uses the complete Codex draft as the structural base because it
contains the full paper and tables, then integrates the main Claude reviewer
comments and the more conservative DeepSeek wording.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "manuscript"
BASE = OUT / "paper1_manuscript_draft_revised.md"
FINAL_MD = OUT / "paper1_manuscript_final_after_llm_review.md"
FINAL_DOCX = OUT / "paper1_manuscript_final_after_llm_review.docx"
LOG = ROOT / "outputs" / "logs" / "paper1_manuscript_final_after_llm_review_log.md"


def load_markdown_to_docx():
    script = ROOT / "code" / "16_llm_manuscript_revision.py"
    spec = importlib.util.spec_from_file_location("llm_manuscript_revision", script)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.markdown_to_docx


def replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        raise ValueError(f"Target text not found: {old[:120]}")
    return text.replace(old, new, 1)


def main() -> int:
    text = BASE.read_text(encoding="utf-8")

    old_abs = """Agricultural household models predict that, under complete markets and price-taking behavior, production decisions should be separable from household preferences and demographic composition. Most empirical tests of this prediction focus on labor demand or production input choices. This paper studies a different but substantively important margin: whether rural households enter self-provisioning for specific food categories. Using a pooled repeated cross-section of 3,565 rural Chinese households observed in 2023 or 2024, converted to 28,520 household-category observations across eight food categories, I test whether household size, child share, elderly share, and female share jointly predict category-specific self-provisioning. The preferred common-sample specification indicates that household composition predicts self-provisioning participation after controlling for household resources, local market access, agro-ecological suitability, purchase-side unit values, county text indicators, food-category fixed effects, province fixed effects, and survey-year fixed effects (Wald = 16.733, p = 0.002). The evidence is concentrated on the participation margin: full-sample transformed quantity outcomes are not significant in the preferred specification. However, the result is control-set sensitive. It is not significant in parsimonious specifications and does not survive a village fixed-effects participation-margin check, although log and IHS quantity margins become significant within villages. Category-level tests show strongest detectability for eggs, oils, vegetables, and fruits after false-discovery-rate adjustment, but these rankings should be interpreted as test-statistic detectability rather than economic magnitudes. The results provide cautious reduced-form evidence that household composition remains conditionally associated with rural food self-provisioning, while also underscoring the limits of cross-sectional separability tests without stronger panel or instrumental-variable identification."""
    new_abs = """Agricultural household models predict that, under complete markets and price-taking behavior, production decisions should be separable from household preferences and demographic composition. Most empirical tests of this prediction focus on labor demand or production input choices. This paper studies a different but substantively important margin: whether rural households enter self-provisioning for specific food categories. Using a pooled repeated cross-section of 3,565 rural Chinese households observed in 2023 or 2024, converted to 28,520 household-category observations across eight food categories, I test whether household size, child share, elderly share, and female share jointly predict category-specific self-provisioning. The preferred common-sample specification indicates a conditional association between household composition and self-provisioning participation after controlling for household resources, local market access, agro-ecological suitability, purchase-side unit values, county text indicators, food-category fixed effects, province fixed effects, and survey-year fixed effects (Wald = 16.733, p = 0.002). This association is control-set sensitive: it is not significant in parsimonious specifications and does not survive a village fixed-effects participation-margin check (p = 0.171), while log and IHS quantity margins become significant under village fixed effects. Thus neither participation nor quantity is robustly dominant across all specifications. Category-level tests show strongest Wald-statistic detectability for eggs, oils, vegetables, and fruits after false-discovery-rate adjustment, but these rankings are not economic effect sizes; oils also require item-code verification, and dairy is excluded because participation is nearly degenerate. Purchase-side unit values are imperfect price proxies, with roughly one-quarter hedonically imputed at moderate precision. The paper provides cautious reduced-form evidence that household composition remains conditionally associated with rural food self-provisioning under the maintained M3 controls, while underscoring the limits of cross-sectional separability tests without stronger panel or instrumental-variable identification."""
    text = replace_once(text, old_abs, new_abs)

    old_intro = """The central finding is deliberately stated cautiously. Household composition significantly predicts self-provisioning participation in the preferred M3 common-sample specification, but not in simpler M0 or M1 specifications. The participation result appears after adding market-access, agro-ecological, and province controls, and remains significant when estimated with logit and probit. Yet it does not survive a village fixed-effects participation check. This pattern suggests that the data support a conditional association between household composition and self-provisioning, especially on the extensive margin, but do not justify a strong causal or structural claim that household demographics independently determine self-provisioning."""
    new_intro = """The central finding is deliberately stated cautiously. Household composition significantly predicts self-provisioning participation in the preferred M3 common-sample specification, but not in simpler M0 or M1 specifications. The participation result appears after adding market-access, agro-ecological, and province controls, and remains significant when estimated with logit and probit. Yet it does not survive a village fixed-effects participation check: with village fixed effects, the participation-margin Wald test has p = 0.171, while log and IHS quantity margins become significant. This inversion suggests that the detectable association shifts with the level of geographic controls. The data therefore support a conditional association under the maintained M3 controls, not a robust within-village structural rejection of separability."""
    text = replace_once(text, old_intro, new_intro)

    old_contrib = """The paper makes three contributions. First, it extends separability testing from farm input demand to the food self-provisioning margin. Second, it shows that the association between household composition and self-provisioning is highly category-specific: eggs, oils, vegetables, and fruits remain significant after Benjamini-Hochberg false-discovery-rate correction, while dairy has too little variation to interpret substantively. Third, it provides a transparent account of weak evidence. Market-friction interactions do not provide strong mechanism evidence, candidate instrumental variables have weak first stages, purchase-side unit values are imperfect price proxies, and village fixed effects weaken the participation result."""
    new_contrib = """The paper makes three contributions. First, it extends separability testing from farm input demand to the food self-provisioning margin while being explicit that the exercise is reduced-form and cross-sectional. Second, it shows that the conditional association is category-specific: eggs, oils, vegetables, and fruits remain significant after Benjamini-Hochberg false-discovery-rate correction, although oils require item-code verification and dairy has too little variation to interpret substantively. Third, it provides a transparent account of weak evidence. Market-friction interactions do not provide strong mechanism evidence, candidate instrumental variables have weak first stages, purchase-side unit values are imperfect price proxies, and village fixed effects materially weaken the participation result."""
    text = replace_once(text, old_contrib, new_contrib)

    old_price_framework = """Let \(D_h\) be household composition and \(X_h\), \(M_v\), \(A_v\), and \(P_{hct}\) denote household resources, local market environment, agro-ecological conditions, and prices or price proxies. Under separability, conditional on the appropriate production-side controls, \(D_h\) should not predict \(y_{hct}\). The empirical test is whether the coefficients on household composition are jointly zero."""
    new_price_framework = """Let \(D_h\) be household composition and \(X_h\), \(M_v\), \(A_v\), and \(P_{hct}\) denote household resources, local market environment, agro-ecological conditions, and prices or price proxies. In the data, \(P_{hct}\) is proxied by purchase-side unit values rather than farm-gate prices; about 27 percent are hedonically imputed, with county-model \(R^2\) near 0.43 and log RMSE near 0.72. These variables help condition on food-cost differences but cannot fully satisfy the price-conditioning requirement of a structural separability test. Under separability, conditional on the appropriate production-side controls, \(D_h\) should not predict \(y_{hct}\). The empirical test is whether the coefficients on household composition are jointly zero."""
    text = replace_once(text, old_price_framework, new_price_framework)

    old_results = """Table 2 reports the M0-M3 sequence on the common M3 sample. The preferred M3 participation model rejects the joint exclusion of household composition (Wald = 16.733, p = 0.002). The same is not true in the parsimonious specifications: M0 has p = 0.178 and M1 has p = 0.106. The participation result becomes significant only after adding market, agro-ecological, and province controls."""
    new_results = """Table 2 reports the M0-M3 sequence on the common M3 sample. The preferred M3 participation model is inconsistent with the joint exclusion of household composition under the maintained M3 controls (Wald = 16.733, p = 0.002). The same is not true in the parsimonious specifications: M0 has p = 0.178 and M1 has p = 0.106. The participation result becomes significant only after adding market, agro-ecological, and province controls."""
    text = replace_once(text, old_results, new_results)

    old_quantity = """This contrast supports an extensive-margin interpretation in the preferred pooled specification, but it also reveals that the empirical pattern is sensitive to the control set."""
    new_quantity = """This contrast supports an extensive-margin interpretation in the preferred pooled specification, but village fixed effects reverse the detectable pattern. The empirical evidence therefore does not establish that either the participation or quantity margin is robustly dominant."""
    text = replace_once(text, old_quantity, new_quantity)

    old_reveal = """This pattern means the M3 result should not be presented as invariant across reasonable specifications. Rather, it is a conditional association that emerges after accounting for regional, market-access, and agro-ecological heterogeneity."""
    new_reveal = """This pattern means the M3 result should not be presented as invariant across reasonable specifications. Rather, it is a conditional association that appears after adding regional, market-access, and agro-ecological controls; those controls change the identifying variation rather than revealing a structural demographic effect."""
    text = replace_once(text, old_reveal, new_reveal)

    old_sec6 = """For this reason, the paper treats participation as the primary margin and conditional intensity as supplementary. The full-sample log and IHS models do not reject in M3, and transformed outcomes with many zeros are sensitive to scale and transformation choices."""
    new_sec6 = """For this reason, the two-part conditional-intensity result is descriptive rather than structural. The village fixed-effects quantity results should be treated with the same caution: they show that transformed quantities can become detectable within villages, but they do not solve selection into positive self-provisioning and remain sensitive to scale and transformation choices. The paper therefore treats the location of the detectable association as specification-dependent, rather than claiming that participation is uniformly the primary margin."""
    text = replace_once(text, old_sec6, new_sec6)

    old_nsi = """The Non-Separability Index (NSI) is defined as a category's household-composition Wald statistic divided by the mean Wald statistic across categories. This index is a relative detectability ranking, not an economic effect size."""
    new_nsi = """The Non-Separability Index (NSI), used here only as a Wald Detectability Ratio, is defined as a category's household-composition Wald statistic divided by the mean Wald statistic across categories. This index is a relative detectability ranking, not an economic effect size."""
    text = replace_once(text, old_nsi, new_nsi)

    old_cat = """After Benjamini-Hochberg FDR correction, eggs, oils, vegetables, and fruits remain significant at 5 percent. Beans is significant before correction but not after FDR correction. Oils require definition caution because the item-code audit is incomplete. Vegetables have the highest self-sufficiency rate but also high participation, so binary variation is compressed near the ceiling. Dairy is excluded from main category interpretation because almost no households self-provision dairy."""
    new_cat = """After Benjamini-Hochberg FDR correction, eggs, vegetables, and fruits remain significant at 5 percent, and oils also remains significant but is flagged before interpretation because the item-code audit is incomplete. Beans is significant before correction but not after FDR correction. Vegetables have the highest self-sufficiency rate but also high participation, so binary variation is compressed near the ceiling. Dairy is excluded from main category interpretation because almost no households self-provision dairy."""
    text = replace_once(text, old_cat, new_cat)

    insert_before_mech = """## 9. Mechanism Diagnostics"""
    price_para = """### 8.1 Price and Unit-Value Sensitivity\n\nThe price controls should be read as imperfect purchase-side unit-value controls rather than exogenous market prices. In the analysis-ready file, 73.1 percent of unit values are observed from household purchase data and 26.9 percent are hedonically imputed. The county hedonic model has \(R^2 \\approx 0.43\) and log RMSE \(\\approx 0.72\), implying substantial prediction noise. The observed-only price robustness check remains statistically similar for participation (p = 0.002), but it is estimated on a selected purchasing subsample. These facts limit how strongly price conditioning can be interpreted in a market-separability framework.\n\n"""
    text = text.replace(insert_before_mech, price_para + insert_before_mech, 1)

    old_mech = """The preferred interpretation is that household composition is conditionally associated with self-provisioning participation. A stronger mechanism claim would require evidence that this association is amplified where markets are less complete or more costly to access. The available market-friction interactions do not provide that evidence. Interaction Wald tests using survey market friction, POI market friction, and combined market-friction measures are statistically weak across participation and quantity outcomes."""
    new_mech = """The conditional association documented above is detectable under the preferred M3 controls but is sensitive to control-set choice and is not robust to village fixed effects on the participation margin. The following diagnostics therefore explore possible correlates of the pattern without claiming to identify a causal mechanism. A stronger market-incompleteness claim would require evidence that the association is amplified where markets are less complete or more costly to access. The available market-friction interactions do not provide that evidence. Interaction Wald tests using survey market friction, POI market friction, and combined market-friction measures are statistically weak across participation and quantity outcomes. The village fixed-effects result is also important for mechanism interpretation: once village-level market access, agro-ecological conditions, local production norms, province variation, and county text variation are absorbed, household composition no longer predicts participation."""
    text = replace_once(text, old_mech, new_mech)

    old_discussion = """The empirical evidence is best read as a disciplined but cautious separability test. The preferred pooled specification rejects the joint exclusion of household composition on the self-provisioning participation margin. The result is not driven by LPM functional form and remains when income and expenditure controls are removed. The category pattern also suggests that self-provisioning is not a uniform rural practice: it is more detectable for eggs, oils, vegetables, and fruits than for staples, meat/aquatic products, or dairy."""
    new_discussion = """The empirical evidence is best read as a disciplined but cautious reduced-form separability exercise. The preferred pooled specification is inconsistent with the joint exclusion of household composition on the self-provisioning participation margin, but that result is not present in parsimonious models and does not survive village fixed effects. The result is not driven by LPM functional form and remains when income and expenditure controls are removed. The category pattern also suggests that self-provisioning is not a uniform rural practice: the Wald test is more detectable for eggs, oils, vegetables, and fruits than for staples, meat/aquatic products, or dairy, although oils and dairy require the caveats discussed above."""
    text = replace_once(text, old_discussion, new_discussion)

    old_conclusion = """The main conclusion is therefore conservative: household composition conditionally predicts entry into self-provisioning, providing reduced-form evidence that the separable agricultural household benchmark is incomplete for this margin. The evidence does not establish a causal demographic effect or a clean market-friction mechanism. Future work should use panel data, validated item-level category definitions, better farm-gate and purchase price measures, and stronger instruments or natural experiments to distinguish market incompleteness from home-good quality preferences and unobserved household heterogeneity."""
    new_conclusion = """The main conclusion is therefore conservative: household composition conditionally predicts entry into self-provisioning under the maintained M3 controls, but this association is not robust to village fixed effects and should not be read as a causal demographic effect or a clean market-friction mechanism. The results are most useful as transparent reduced-form evidence that the separable agricultural household benchmark may be incomplete for food self-provisioning, while also showing where the current data are insufficient. Future work should use panel data, validated item-level category definitions, better farm-gate and purchase price measures, and stronger instruments or natural experiments to distinguish market incompleteness from home-good quality preferences and unobserved household heterogeneity."""
    text = replace_once(text, old_conclusion, new_conclusion)

    FINAL_MD.write_text(text, encoding="utf-8")
    markdown_to_docx = load_markdown_to_docx()
    markdown_to_docx(text, FINAL_DOCX)

    LOG.write_text(
        "# Manuscript Finalization After LLM Review\n\n"
        "- Base: `outputs/manuscript/paper1_manuscript_draft_revised.md`.\n"
        "- DeepSeek outputs used for conservative wording: `paper1_manuscript_deepseek_front.md`, `paper1_manuscript_deepseek_back.md`.\n"
        "- Claude reviewer comments used: `paper1_claude_reviewer_comments.md` and segment memos.\n"
        "- Final full manuscript: `outputs/manuscript/paper1_manuscript_final_after_llm_review.md`.\n"
        "- Final DOCX: `outputs/manuscript/paper1_manuscript_final_after_llm_review.docx`.\n",
        encoding="utf-8",
    )
    print(FINAL_MD)
    print(FINAL_DOCX)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())