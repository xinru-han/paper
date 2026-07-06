# 3. Data and Variable Construction

The estimating sample contains 279 observations for 31 provinces from 2015 to 2023. The model uses six aggregate demand categories: staples, oils and fats, vegetables and fruits, meat and aquatic products, dairy and eggs, and an other/non-covered residual. The residual is retained internally under the code name `nonfood`, but it should not be interpreted as a strict outside good. It includes uncovered foods, eating away from home, alcohol and tobacco components when present in the residual, and true non-food expenditure.

Food quantities are converted to daily 2,000-kcal units. The nutrition table is adjusted for edible shares. When reported energy is missing or zero, energy is reconstructed from macronutrients. Grain aggregation includes soybeans and potatoes. The potato division by five is retained only for grain-equivalent accounting; calorie aggregation uses actual kcal per kilogram and consumption-quantity weights.

The main monetary specification uses 2023 real-price terms. Total expenditure is deflated by the provincial total CPI index, covered-food prices by provincial food CPI, and the other/non-covered residual price by national non-food CPI. A robustness specification uses a derived provincial non-food CPI from total CPI, food CPI, and food expenditure shares. Because direct provincial non-food CPI is not yet available, residual-price variation should be interpreted cautiously.

Projection-year population is taken from the Chen et al. (2020) provincial population projection under SSP2. The raw projection table is reported in persons and is converted to the model's `population_10k` unit before aggregation.

Unsupported or weak claims to resolve:
- Add direct provincial non-food CPI or official CPI weights.
- Add an external covered-calorie benchmark against FAOSTAT or statistical yearbook food balance data.
