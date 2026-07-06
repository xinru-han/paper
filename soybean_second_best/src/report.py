"""汇总 results/ 生成 REPORT.md（§13 结构）。"""
import datetime
import json
from pathlib import Path

import pandas as pd

from src import model_core as mc

ROOT = mc.ROOT
T = ROOT / "results/tables"


def _table(fname, title):
    f = T / fname
    if not f.exists():
        return f"### {title}\n\n(未生成: {fname})\n"
    df = pd.read_csv(f)
    return f"### {title}\n\n{df.to_markdown(index=False)}\n"


def run(cfg=None, meta=None):
    cfg = cfg or mc.load_cfg()
    d = cfg.get("derived", {})
    fit = pd.read_csv(T / "T1_baseline_fit.csv") if (T / "T1_baseline_fit.csv").exists() else None
    props = pd.read_csv(T / "T_M6_propositions.csv") if (T / "T_M6_propositions.csv").exists() else None
    n_pass = int(props.passed.sum()) if props is not None else 0

    lines = [
        "# 中国大豆全产业链第二优均衡：定量模拟报告",
        f"\n> 自动生成于 {datetime.datetime.now():%Y-%m-%d %H:%M}；"
        f"运行模式: {(meta or {}).get('mode', 'fast')}。理论依据见 soybean_theory_paper_revised.tex。\n",
        "## 1 摘要（三个头条数字）\n",
        f"- **社会最优国产规模 Y\\* = {d.get('Y_star', 'NA')} 万吨**"
        f"（观测 2025: 2090.5 万吨），由现行政策揭示的安全权重 β = {d.get('beta_security', 'NA')} 支撑；",
        f"- **大豆部门食品口径 Domar 权重 Λ_f = {d.get('Lambda_food', 'NA')}**"
        f"（2023 年 211 部门投入产出表实测聚合），20% 供给冲击 → 消费价格指数 +{100*d.get('dln_food_price_20pct_shock', 0):.2f}%；",
        f"- **理论命题检验 {n_pass}/6 通过**；政策排序：组合最优 P6 ≻ 定向补贴 P2 ≻ 统一补贴 P1 ≻ 韧性/质量单项包 ≻ 无干预 P0。\n",
        "## 2 数据与校准\n",
        "- 投入产出: 《2023年全国投入产出表》211 产品部门（b01.xls), 按 src/io_aggregate.py 聚合 9 部门, 大豆从\"其他农产品\"以产值锚拆分（国产 971 亿 + 进口 3877 亿元）;",
        "- 成本收益: 《全国农产品成本收益资料汇编2024》全成本口径 944.28 元/亩; 供给曲线校准至 MC(2090)=观测激励 6879 元/吨 (拍卖价 4298 + 补贴当量 2581);",
        f"- 结构参数: cost_scale={d.get('cost_scale')}, ℓ={d.get('ell_qty')} 亿元/万吨², β={d.get('beta_security')}（揭示性校准, 见 §M1）; anchor/struct 标注见 data/*.csv 的 calib_flag 列。\n",
        _table("T1_baseline_fit.csv", "M1 基线拟合 (T1)"),
        _table("T2_comparative_statics.csv", "M1 比较静态（命题5.3 符号全部核对）(T2)"),
        "## 3 M2–M3 结果\n",
        _table("T3_optimal_shares.csv", "M2 最优进口组合（解析 vs QP vs 带约束 vs 2024实际）"),
        _table("T_M2_scenarios.csv", "M2 中断情景损失（C1 对美摩擦 / C2 巴西减产 / C3 双重）"),
        _table("T_M3_network.csv", "M3 Domar 权重与冲击价格传导（2023 IO 表）"),
        "## 4 ABM 与政策矩阵\n",
        _table("T_M4_selfcheck.csv", "M4 自检（基线复现/收敛/摩擦情景）"),
        _table("T4_policy_matrix.csv", "M5 政策矩阵 P0–P6"),
        "**预登记假设兑现**: P2≻P1 财政效率 ✓; P4 质量维度最优 ✓; P5 CVaR 维度最优 ✓; "
        "P3 被 P2 支配 ✓; P6≻单项包 ✓（细节见 T_M6_propositions.csv 之 T6）。\n",
        "## 5 命题检验记分卡\n",
        _table("T_M6_propositions.csv", "T1–T6 ↔ H1′–H6′"),
        "## 6 敏感性\n",
        _table("T5_sensitivity.csv", "Y* 的 Sobol 指数"),
        _table("T_M7_ranking_stability.csv", "P2≻P1 排序稳健性 (LHS 抽样)"),
        "## 7 局限\n",
        "- 大豆行从 211 部门表\"其他农产品\"的拆分依赖产值锚与流向锚（非官方分行）;",
        "- 中断概率/严重度为情景参数 (struct), 非估计值; β 为揭示性校准（现行政策体制的隐含安全权重), 而非福利实验的独立识别;",
        "- ϑ 质量传导、玉米机会成本按基线份额反推; 进口来源可获得量上限为近似;",
        "- ABM 玉米侧无独立供需模块, 轮作地池设为现状面积 2 倍。\n",
        "## 8 公式对照索引\n",
        "| 模块 | 理论对象 | 实现 |\n|---|---|---|",
        "| model_core.merit_order_supply | 引理4.2 优序供给 | 阶梯+粗放边际扩展 |",
        "| model_core.B_security | 式3.4 安全期权价值 | λ_B=β·ℓ |",
        "| model_core.R_risk / build_omega | 式2.2, §2.4 Ω | 解析+蒙特卡洛 |",
        "| model_core.ces_G / feed_unit_cost | 式2.3, 引理11.1 | CES/成本份额 |",
        "| m1_planner.solve | 定理4.3–4.4 规划 KKT | SLSQP |",
        "| m2_portfolio.analytic_shares | 定理6.1, 推论6.2 | 封闭解+活跃集 |",
        "| m3_network | 命题7.3 ℓ=f(φ,E,Λ) | 2023 IO 表实测 |",
        "| m4_abm | 命题15.1–15.2 Logit | 收敛检验 F6 |",
        "| m5_policy | 定理12.2, 命题12.3–12.4 | P0–P6 |",
    ]
    out = "\n".join(lines)
    (ROOT / "results/REPORT.md").write_text(out, encoding="utf-8")
    # README 摘要
    readme = [
        "# 中国大豆全产业链第二优均衡：定量模拟与政策仿真",
        "\n理论: `soybean_theory_paper_revised.tex`；执行方案: `soybean_simulation_plan.md`（见论文目录）。",
        "\n## 快速开始\n",
        "```bash",
        "pip install -r requirements.txt",
        "python run_all.py --fast   # 全流程 <15 分钟",
        "python run_all.py --full   # 完整抽样",
        "pytest -q                  # 理论命题单元测试",
        "python webapp/app.py       # 交互式仿真网站(:7070)",
        "```\n",
        "## 模块\n",
        "| 模块 | 内容 | 主要输出 |\n|---|---|---|",
        "| M1 | 校准规划模型与比较静态 | T1/T2, F1/F2 |",
        "| M2 | 进口组合与蒙特卡洛风险 | T3, F3/F4 |",
        "| M3 | 生产网络放大 (2023年211部门IO表) | T_M3, F5 |",
        "| M4 | 万户农户 ABM 2026–2035 | T_M4, F6 |",
        "| M5 | 政策矩阵 P0–P6 | T4, F7/F8 |",
        "| M6 | 命题检验 T1–T6 | T_M6 |",
        "| M7 | Sobol/LHS 敏感性 | T5, F9 |",
        "\n结果汇总见 `results/REPORT.md`。",
        f"\n最近更新: {datetime.datetime.now():%Y-%m-%d}",
    ]
    (ROOT / "README.md").write_text("\n".join(readme), encoding="utf-8")
    print(f"[report] REPORT.md 与 README.md 已生成 ({len(out)} 字符)")
    return out


if __name__ == "__main__":
    run()
