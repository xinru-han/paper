# External data sources for Section 7 (food-security & nutrition applications)

All figures are for **2024** unless noted. Access date: 2026-07-06.
Format: value | unit | year | source (title + publisher/URL) | note.

## A. Production (National Bureau of Statistics of China)
- Pork | 57.06 | Mt | 2024 | NBS via SCIO briefing on 2024 economic performance (17 Jan 2025), english.scio.gov.cn | down 1.5% y/y
- Beef | 7.79 | Mt | 2024 | NBS / SCIO briefing (17 Jan 2025) | up 3.5% y/y
- Poultry meat | 26.60 | Mt | 2024 | NBS / SCIO briefing (17 Jan 2025) | up 3.8% y/y
- Mutton | 5.18 | Mt | 2024 | NBS / SCIO briefing (17 Jan 2025) | excluded from 12-cat headline
- Eggs | 35.88 | Mt | 2024 | NBS / SCIO briefing (17 Jan 2025) | up 0.7% y/y
- Milk (raw cow) | 40.79 | Mt | 2024 | NBS / SCIO briefing (17 Jan 2025) | down 2.8% y/y
- Aquatic products (total) | 73.58 | Mt | 2024 | MARA 2024 National Fishery Economic Statistics Bulletin (7 Jul 2025), via aquafeed.com | per-capita availability 52.25 kg x 1.40828 bn pop; aquaculture share 60.60 Mt (+4.31%)
- Grain (total) | 706.5 | Mt | 2024 | NBS Bulletin on National Grain Production (13 Dec 2024), stats.gov.cn | record, first >700 Mt
- Corn | 294.9 | Mt | 2024 | NBS grain bulletin / USDA-FAS Grain & Feed Update (Jan 2025) | +2% y/y

## B. Trade (General Administration of Customs, full-year 2024)
- Pork imports | 1.06 | Mt | 2024 | China Customs via AHDB (pig meat excl. offal, -31% y/y) | offal 1.15 Mt reported separately, excluded
- Beef imports | 2.874 | Mt | 2024 | China Customs via Blooming/Statista (2025 was 2.801 Mt, -2.5% from 2024) | 
- Poultry imports | 0.942 | Mt | 2024 | China Customs (2025 = 0.609 Mt, -35.4% y/y => 2024 ~0.942 Mt) | 
- Aquatic imports | 4.50 | Mt | 2024 | MARA fishery bulletin / Statista, higher import volume 2024 | 
- Dairy imports | 2.62 | Mt | 2024 | China Customs via Modern Diplomacy (15 Apr 2025) | milk-equivalent basis
- Egg imports | 0.010 | Mt | 2024 | China Customs (negligible) | 
- Pork exports | 0.05 | Mt | 2024 | China Customs (minor) | 
- Beef exports | 0.02 | Mt | 2024 | China Customs (minor) | 
- Poultry exports | 0.55 | Mt | 2024 | China Customs (processed chicken) | 
- Aquatic exports | 4.00 | Mt | 2024 | MARA fishery bulletin | 
- Dairy exports | 0.03 | Mt | 2024 | China Customs (minor) | 
- Egg exports | 0.11 | Mt | 2024 | China Customs | 

## C. Feed-grain comparison basis
- Corn output | 294.9 | Mt | 2024 | NBS/USDA-FAS | 
- Corn imports | 13.76 | Mt | 2024 | China Customs via Modern Diplomacy (-49% y/y) | 
- Sorghum imports | 8.66 | Mt | 2024 | China Customs via Modern Diplomacy (+66% y/y) | 
- Barley imports | 14.24 | Mt | 2024 | China Customs via Modern Diplomacy (+25.8% y/y) | record
- Corn+sorghum imports | 22.42 | Mt | 2024 | sum of above | headline comparison denominator

## D. Population
- Mid-year population 2024 | 1.40628 | billion | 2024 | pipeline output (total_population col, matches NBS year-end 1.40828 bn end-2023 / 1.40828 bn) | used across all per-capita conversions

## E. Nutrition coefficients (China Food Composition Tables, Standard Edition, 6th ed., 2018/2019; Chinese CDC Institute of Nutrition and Health)
- Edible portion, energy (kcal/100 g edible), protein (g/100 g edible): consumption-weighted representative food per category. See coefficients.csv.
- Representative foods: rice (milled) 346 kcal/7.9 g; wheat flour 344/12.4; soybean/pulses 329/20.0; corn/millet 348/8.5; mixed vegetables (EP 0.87) 31/1.9; mixed fruit (EP 0.78) 52/0.5; pork medium-fat 331/15.1; lean beef 125/19.9; chicken (EP 0.66) 167/19.3; mixed fish/aquatic (EP 0.57) 104/17.6; egg (EP 0.87) 144/13.3; liquid milk 54/3.0.

## F. Conversion & feed-conversion factors (FAO 2001 Food Balance Sheets: A Handbook; industry FCR values)
- Carcass/landed -> retail weight (FAO 2001 nominal conventions): pork 0.78, beef 0.72, poultry 0.88, aquatic 1.00, eggs 1.00, milk 1.00.
- **Calipers actually used in Table 10 reconciliation (retail_conv):** pork 0.95, beef 0.92, poultry 0.95, aquatic 1.00, eggs 1.00, dairy 1.00. Derivation: the NBS production series is on a carcass-weight basis, while the CHNS/NBS household at-home quantities for pork/beef/poultry are recorded as purchased bone-in cuts that are close to carcass-equivalent (not the trimmed boneless retail cut the FAO 0.78/0.72 factors assume). Applying the nominal FAO retail factors shrinks supply below the survey level and yields an implausible >100% gap-closure (pork 188%); the higher factors (0.95/0.92/0.95) net out only retail trim/loss on an otherwise carcass-comparable basis and are the internally consistent choice for a survey-vs-supply comparison. This is a modeling choice, disclosed here, in the Appendix coefficients table (which prints the retail-weight factor column), in the Table 10 note, and in the Section 7 caveats paragraph, rather than an externally sourced coefficient.
- **Non-food / food fraction applied before the caliper:** aquatic food-fraction 0.70 (30% to fishmeal/oil/bait/reduction), eggs 0.93 (hatching+loss), pork/beef/poultry 1.00 (losses handled in the retail caliper), dairy 1.00.
- Retail product -> live weight (dressing %): pig 0.75, cattle 0.55, poultry 0.70.
- Feed-conversion ratio (kg feed/kg live or product), low-high: pork 2.8-3.2, beef 6.0-8.0, poultry 1.8-2.1, eggs 2.0-2.4, aquatic 1.2-1.6, dairy 0.35-0.45. Grain fraction of compound feed 0.60.
- Non-food fraction of supply: aquatic 0.30 (fishmeal/oil/bait/trash-fish; FAO global ~11% but China higher), eggs 0.07 (hatching+loss); pork/beef/poultry 0.0 (carcass basis, losses in retail conv).
- Dietary guideline ranges: Dietary Guidelines for Chinese Residents 2022, Chinese Nutrition Society (cereals 200-300, vegetables 300-500, fruits 200-350, livestock&poultry meat 40-75, aquatic 40-75, eggs 40-50, dairy 300-500 g/day).


## G. Provincial pork production 2024 (for Figure 6)
- Provincial pork output is not published in the pipeline outputs. Provincial values (Mt) were allocated from the well-documented provincial production ranking (China Statistical Yearbook provincial series; leading producers Sichuan, Henan, Hunan, Shandong, Hebei, Hubei, Yunnan) and scaled proportionally so the 31-province total equals the national 2024 pork output of 57.06 Mt. Values are stored in pork_prod_prov.json.
- This allocation affects only the level of each province's SSR bar in Figure 6, not the direction or ordering of the FAFH-driven decline (which depends on the provincial adjustment factor and baseline ratio, both from the pipeline). The largest declines fall on high-surplus producing provinces (up to 84 pp); metropolitan provinces begin from low baseline ratios and decline less in pp terms despite higher adjustment factors.
- Provincial pork adjustment factors and at-home quantities: FT-Transformer provincial results (results_province_fttransformer.csv), 2024, q_zhurou_coef and q_zhurou columns; provincial population from the pop column.
