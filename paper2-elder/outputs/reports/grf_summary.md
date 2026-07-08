# Honest-forest heterogeneity of the adjusted association (appendix)
- grf::causal_forest is used as an ML heterogeneity diagnostic only; living arrangement is self-selected, so outputs are conditional CONTRASTS of an adjusted association, not CATEs/treatment effects.
- Adjusted average contrast, treated (forest; NOT a causal ATT): 0.536 (se 0.135)
- Calibration: mean prediction t=3.93, differential t=-1.46.
- **Heterogeneity NOT detected**: the differential-forest-prediction calibration coefficient is below 2, so the forest does **not** give statistical evidence of heterogeneity in the adjusted association. Subgroup conditional-contrast differences (and the leakage-by-subgroup contrasts they motivate) are therefore **suggestive only**, not established effect modification.
- Framing: conditional-association heterogeneity; treatment non-random.
