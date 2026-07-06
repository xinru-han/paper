"""M3: 生产网络放大与短缺损失曲率 ℓ 的测算（命题 7.3）。

使用真实《2023年全国投入产出表》(211部门) 聚合的 9 部门表（src/io_aggregate.py 生成，
竞争型口径：流量含进口——对大豆供给冲击分析恰当，因为进口中断正是冲击本身）。

  Λ = L b（Domar 权重, L=(I−A)⁻¹, b=居民消费权重）
  冲击实验: 压榨部门原料成本冲击 d ln z = −20% → d ln p = (I−A')⁻¹ · (−a_soy,crush·dlnz)
  ℓ = φ·E / Q_s² · Λ_s²  （E=食品支出亿元, Q_s=大豆部门营业额亿元 → ℓ 单位 亿元/万吨² 需换算）

换算: 理论中 ℓ 定义在数量空间(万吨)。营业额口径 Q_s(亿元) = D(万吨)×p(元/吨)×1e-4。
  短缺 s 万吨 → 营业额缺口 s×p×1e-4 亿元 → 损失 0.5·ℓ_value·(s·p·1e-4)²,
  故 ℓ_qty = ℓ_value·(p·1e-4)², ℓ_value = φ·E·Λ_s²/Q_s²。
运行后把 derived 段写回 config/calibration.yaml。
"""
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

from src import model_core as mc

ROOT = mc.ROOT


def run(cfg=None, save=True):
    cfg = cfg or mc.load_cfg()
    A = pd.read_csv(ROOT / "data/io_table_9sector.csv", index_col=0)
    meta = pd.read_csv(ROOT / "data/io_meta_9sector.csv")
    sectors = list(A.index)
    labels = dict(zip(meta.sector, meta.label))
    Am = A.to_numpy()
    n = len(sectors)
    L = np.linalg.inv(np.eye(n) - Am)
    sr = float(np.max(np.abs(np.linalg.eigvals(Am))))
    assert sr < 1, f"谱半径 {sr:.3f} ≥ 1"

    b = meta.b_weight.to_numpy()
    Lambda = L @ b                                     # Domar 权重
    dom = {s: float(Lambda[i]) for i, s in enumerate(sectors)}

    # 传导路径分解: Λ_s1 = Σ_j L[0,j]·b_j
    path = pd.DataFrame({"sector": sectors, "label": [labels[s] for s in sectors],
                         "L_soy_to_j": L[0, :], "b_j": b,
                         "contrib": L[0, :] * b})
    path["contrib_share"] = path.contrib / path.contrib.sum()

    # 冲击实验: 压榨部门(索引1)大豆原料 -20% 供给冲击 → 成本推动价格传导
    # d ln p = (I − A')⁻¹ · v, v_crush = a_{soy,crush} · (−d ln z_soy), 大豆自身价格冲击对应份额1
    dlnz = -0.20
    v = np.zeros(n)
    v[0] = -dlnz                       # 大豆自身价格上涨 20%（供给减少的价格对偶）
    v[1] = 0.0                         # 压榨部门通过 A 内生传导
    dlnp = np.linalg.solve(np.eye(n) - Am.T, v)
    dlnPC = float(b @ dlnp)            # 食品/消费价格指数变化

    # ℓ 测算（命题 7.3 的量纲一致化实现）
    # E 是"食品支出"（90000亿），故 Domar 权重也用食品最终消费口径:
    #   b_food = 食品相关部门(s1..s8)居民消费权重(归一化), Λ_f = (L·b_food)_s1
    #   —— 校核: 9部门表 s1..s8 居民消费合计 ≈ 9.4 万亿, 与 E=9 万亿吻合。
    # 短缺损失 L(x)=0.5·φ·E·Λ_f·x², x=比例短缺 s/Q_wt（Hulten一阶 dlnP_C=Λ_f·φ·x
    #   的消费者损失取二阶近似），故 ℓ_qty = ell0_scale·φ·E·Λ_f / Q_wt²（亿元/万吨²）。
    # 与理论文档 ℓ=ℓ0·Λ² 的关系: ℓ0=φE/Q², Λ² 中一个 Λ 由价格传导吸收进 φ 的
    #   有效值（φ_eff=φΛ/直接份额），此处直接采用食品口径 Λ_f 一次方以保持单位一致。
    phi = cfg["structural_params"]["phi_rigidity"]
    scale = cfg["structural_params"].get("ell0_scale", 1.0)
    E = cfg["structural_params"]["food_expenditure_E"]
    D = cfg["demand"]["D_total"]                       # 万吨
    p_bar = cfg["prices"]["p_import_landed_2024"]      # 元/吨
    Q_s = D * p_bar * mc.WT_CNY_TO_YI                  # 亿元营业额（报告用）
    b_food = np.where(np.arange(n) < 8, meta.HH_cons_yi_yuan.to_numpy(), 0.0)
    b_food = b_food / b_food.sum()
    Lam_f = float((L @ b_food)[0])                     # 食品口径 Domar
    Lam_s = Lambda[0]                                  # 全经济口径（报告用）
    ell_qty = scale * phi * E * Lam_f / D ** 2         # 亿元/万吨²
    ell_value = ell_qty / (p_bar * mc.WT_CNY_TO_YI) ** 2   # 1/亿元（营业额口径）

    # 2×2 区间: φ∈[1,4] × Λ_f ±30%（部门拆分不确定性）
    grid = {}
    for pl, ph in [("low_phi", 1.0), ("high_phi", 4.0)]:
        for ll, lk in [("low_Lam", 0.7), ("high_Lam", 1.3)]:
            grid[f"{pl}_{ll}"] = float(round(scale * ph * E * Lam_f * lk / D ** 2, 8))

    res = dict(spectral_radius=sr, Domar=dom, dlnp=dict(zip(sectors, dlnp)),
               dln_food_price_index=dlnPC, ell_value=ell_value, ell_qty=ell_qty,
               ell_grid=grid, Lambda_soy=float(Lam_s), Lambda_food=Lam_f, Q_s_yi=Q_s)

    if save:
        (ROOT / "results/tables").mkdir(parents=True, exist_ok=True)
        path.round(6).to_csv(ROOT / "results/tables/T_M3_domar_paths.csv", index=False)
        pd.DataFrame({"sector": sectors, "label": [labels[s] for s in sectors],
                      "Domar": Lambda, "dlnp_shock": dlnp}).round(6).to_csv(
            ROOT / "results/tables/T_M3_network.csv", index=False)
        # 写回 yaml derived 段
        cfg_path = ROOT / "config/calibration.yaml"
        with open(cfg_path, encoding="utf-8") as f:
            full = yaml.safe_load(f)
        full["derived"] = {
            "ell_qty": float(round(ell_qty, 8)), "ell_value": float(ell_value),
            "ell_grid": grid, "Lambda_soy": float(round(Lam_s, 6)),
            "Lambda_food": float(round(Lam_f, 6)),
            "dln_food_price_20pct_shock": float(round(dlnPC, 6)),
            "note": "由 m3_network.py 自动写入; ell_qty 单位 亿元/万吨^2"}
        # 先序列化成功再落盘（原子替换），避免写坏配置
        text = yaml.safe_dump(full, allow_unicode=True, sort_keys=False)
        tmp = cfg_path.with_suffix(".yaml.tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(cfg_path)
        # 图: 部门价格响应
        plt = mc.setup_cjk()
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.bar([labels[s] for s in sectors], dlnp * 100, color="#8c1f28")
        ax.set_ylabel("价格响应 %"); ax.set_title("大豆供给冲击20%的网络价格传导 (2023年投入产出表)")
        ax.tick_params(axis="x", rotation=30)
        fig.tight_layout()
        (ROOT / "results/figures").mkdir(parents=True, exist_ok=True)
        fig.savefig(ROOT / "results/figures/F5_network_passthrough.png", dpi=300)
        plt.close(fig)
    return res


if __name__ == "__main__":
    r = run()
    print(f"Λ_soy={r['Lambda_soy']:.4f}  dlnP_C={r['dln_food_price_index']*100:.3f}%  "
          f"ell_qty={r['ell_qty']:.5f} 亿元/万吨²")
    print("ell_grid:", r["ell_grid"])
