# Issue 8 细节修订清单

1. **符号不一致**：公式(16)中 N^U_P 与正文其他处 N^{PU} 拼写不统一 -> 统一为 N^P_U
   (与Bewley 1986原文记号一致，表示QUAIDS的自由二次支出参数个数)。

2. **Table 3 (原稿) Slutsky特征值最大值表述**："passes at numerical tolerance"表述
   需按Issue 1重新定性 -> 改为:"the maximum eigenvalue is effectively zero
   (order 1e-12 to 1e-13), consistent with -- but not independent evidence
   for -- local negative semidefiniteness; see Section 4.1 for the joint
   Wald test on Gamma that provides the substantive identification check."

3. **Table 1 AUC (0.92-0.95)**：说明部分反映滞后进口状态的状态依赖性(state
   dependence)，而非纯粹的参与方程预测力 -> 在Table 1脚注补充："The high AUC
   partly reflects the inclusion of lagged participation status among the
   predetermined regressors (state dependence in provincial import
   participation) rather than solely the predictive power of contemporaneous
   demand-side controls."

4. **零值价格插补的测量误差说明**：在§2或§3.4补充脚注说明缺失省份-季度-品类
   格采用同季度全国LOO均值插补，可能引入测量误差，已通过loo_quarter_winsor
   与landed_proxy两种替代口径做敏感性检验（Section 4附录）。

5. **Shonkwiler & Yen (1999) 页码确认**：81(4):972-982 与原稿引用一致，无需修改。
   [重建管道核实：原稿Reference list实际写"81(4)"疑似笔误，正确应为"American
   Journal of Agricultural Economics 81(4): 972-982" -- 已核实与审改意见一致]

6. **关键词建议**：新增"censored demand system"；去除低信息量的"scenario analysis"
   （审改意见原文建议）。建议关键词表最终为：feed grains; import demand; import
   substitution; China; QUAIDS; Shonkwiler-Yen; censored demand system; unit
   values; Bartik instrument; trade risk.
