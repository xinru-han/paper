"""M7: 全参数敏感性（Sobol on M1 Y*）与政策排序稳健性（LHS on ABM P1 vs P2）。"""
import numpy as np
import pandas as pd

from src import model_core as mc
from src import m1_planner as m1

ROOT = mc.ROOT

PROBLEM = {
    "num_vars": 8,
    "names": ["crisis_prob_pi", "crisis_import_loss_kappa", "mobilization_chi",
              "reserve_X", "ell0_scale", "vy_quality", "omega_scale", "phi_rigidity"],
    "bounds": [[0.01, 0.10], [0.10, 0.50], [0.05, 0.30], [500, 2000],
               [0.5, 2.0], [300, 1200], [0.85, 1.15], [1.0, 4.0]],
}


def _solve_ystar(cfg, sc, beta, base_x, row):
    sp = dict(cfg["structural_params"])
    P = m1.build_problem(cfg, sc,
                         omega_scale=float(row[6]),
                         vy_override=float(row[5]),
                         ell_override=cfg["derived"]["ell_qty"] * float(row[4])
                         * float(row[7]) / sp["phi_rigidity"],
                         X_override=float(row[3]))
    P["pi"] = float(row[0]); P["kappa"] = float(row[1]); P["chi"] = float(row[2])
    P = m1.calibrate_chain(cfg, P)
    P["beta_sec"] = beta
    return m1.solve(P, x0=base_x)["Y"]


def sobol_ystar(cfg, fast=True):
    from SALib.sample import saltelli
    from SALib.analyze import sobol
    N = 16 if fast else 256
    X = saltelli.sample(PROBLEM, N, calc_second_order=False)
    sc, _, _ = m1.calibrate_supply(cfg)
    beta, P0, base = m1.calibrate_beta(cfg, sc)
    Y = np.array([_solve_ystar(cfg, sc, beta, base["x"], r) for r in X])
    Si = sobol.analyze(PROBLEM, Y, calc_second_order=False)
    df = pd.DataFrame({"param": PROBLEM["names"], "S1": Si["S1"], "ST": Si["ST"]})
    return df.sort_values("ST", ascending=False), Y


def ranking_stability(cfg, fast=True):
    """LHS 抽样下 P2≻P1（福利）的稳健率。"""
    from src import m5_policy as m5
    rng = np.random.default_rng(3)
    n = 8 if fast else 200
    wins = 0; rows = []
    for i in range(n):
        cfg_i = mc.load_cfg()
        sp = cfg_i["structural_params"]
        sp["logit_tau"] = float(rng.uniform(20, 200))
        sp["theta_transmission"] = float(rng.uniform(0.1, 0.9))
        sp["risk_aversion_gamma"] = float(rng.uniform(0.5e-4, 5e-4))
        a1, _ = m5.eval_policy(cfg_i, "P1", n_seeds=3, n_agents=800)
        a2, _ = m5.eval_policy(cfg_i, "P2", n_seeds=3, n_agents=800)
        win = a2["welfare"] >= a1["welfare"]
        wins += win
        rows.append(dict(draw=i, tau=sp["logit_tau"], theta=sp["theta_transmission"],
                         gamma=sp["risk_aversion_gamma"], P2_wins=bool(win)))
    return wins / n, pd.DataFrame(rows)


def run(cfg=None, save=True, fast=True):
    cfg = cfg or mc.load_cfg()
    sob, Y = sobol_ystar(cfg, fast)
    stab, stab_df = ranking_stability(cfg, fast)
    print(f"[M7] Y* 范围 [{Y.min():.0f}, {Y.max():.0f}], P2≻P1 稳健率 = {stab:.0%}")
    if save:
        sob.round(4).to_csv(ROOT / "results/tables/T5_sensitivity.csv", index=False)
        stab_df.to_csv(ROOT / "results/tables/T_M7_ranking_stability.csv", index=False)
        plt = mc.setup_cjk()
        fig, ax = plt.subplots(figsize=(7, 4.5))
        s = sob.sort_values("ST")
        ax.barh(s.param, s.ST, color="#8c1f28", alpha=0.8, label="总效应 ST")
        ax.barh(s.param, s.S1, color="#2b6a99", alpha=0.8, label="一阶 S1")
        ax.set_title("Y* 的 Sobol 敏感性 (M7)"); ax.legend()
        fig.tight_layout()
        fig.savefig(ROOT / "results/figures/F9_sobol_tornado.png", dpi=300)
        plt.close(fig)
    return dict(sobol=sob, stability=float(stab), Y_range=[float(Y.min()), float(Y.max())])


if __name__ == "__main__":
    r = run(fast=True)
    print(r["sobol"].to_string(index=False))
