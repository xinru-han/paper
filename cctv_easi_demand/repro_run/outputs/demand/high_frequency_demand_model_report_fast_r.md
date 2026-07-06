# R 高频月度需求模型报告（快速正规方程版）

- 家庭-月观测：584,835
- 家庭数：27,653
- 月份：2020-01 至 2022-12

## 自价格弹性

          food_group10 own_price_elasticity is_negative
                <char>                <num>      <lgcl>
 1:           G01_主食           -0.3234687        TRUE
 2:         G02_食用油            0.4624007       FALSE
 3:           G03_蔬菜           -1.0389384        TRUE
 4:           G04_水果           -1.0641082        TRUE
 5:           G05_猪肉           -0.6953002        TRUE
 6: G06_禽类及其他肉类            0.7352150       FALSE
 7:         G07_牛羊肉           -1.2655230        TRUE
 8:           G08_海鲜           -0.3817193        TRUE
 9:         G09_乳制品            0.1826061       FALSE
10:           G10_坚果           -3.6646768        TRUE

## 约束

                      model                         restriction
                     <char>                              <char>
1: constrained_sy_easi_fast                           adding_up
2: constrained_sy_easi_fast         homogeneity_relative_prices
3: constrained_sy_easi_fast slutsky_symmetry_price_coefficients
                                       status max_abs_error
                                       <char>         <num>
1:       by_construction_predicted_10th_share  2.220446e-16
2:            by_construction_relative_prices  0.000000e+00
3: by_construction_symmetric_parameterization  0.000000e+00

说明：该 R 版使用外部锚定、fold-excluded 内部价格信号和受约束 SY-EASI；结果解释为 monthly food-expenditure elasticity 和 measured market-price variation 下的条件需求响应。
