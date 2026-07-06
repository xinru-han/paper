### Table R-Wage. Wage-income mechanism: full sample vs. 2013-2020 same-questionnaire-definition subsample

| Variable | Full sample (2013-2022) | 2013-2020 subsample (pre-break) |
|---|---|---|
| Log(Covid) | -0.2646*** | -1.6259* |
|  | (0.0977) | (0.8040) |
| N | 11,258 | 9,593 |
| Within R2 | 0.042 | 0.043 |

Note: SE clustered by township. Outcome = asinh(real wage income), self-built from itemized survey questions (hg02_1..hg11_1, 2013-2020) or aggregated new items (2021-2022) -- see revision/scripts/08_income_build.py, winsorized at 1%/99% before the asinh transform (identical construction to revision/07_mechanisms.R; the Full-sample column exactly reproduces the original M2 wage coefficient, -0.2646***, N=11,258). The questionnaire item set changes exactly at 2021, coinciding with the treatment period; the 2013-2020 subsample avoids this break entirely at the cost of dropping 2021-2022 variation, which also means 2020 is the ONLY post-treatment year identifying the coefficient in that column -- the much larger point estimate (-1.63 vs. -0.26) and wider SE should be read as reflecting this thinner identification (fewer post-treatment year x county cells), not necessarily a larger true effect. The two columns AGREE in sign and both remain significant at conventional levels, which is the robustness claim being tested here; the magnitude is not comparable across columns.

