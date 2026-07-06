"""从《2023年全国投入产出表》(211产品部门, b01.xls) 聚合大豆产业链 9 部门表。

数据源: /root/data/数据/2023投入产出表/b01.xls（竞争型表，流量含进口，单位万元）。
211 部门表中大豆并入 "01002 其他农产品"，需拆分。拆分方法（混合锚定法）：

行拆分（大豆产品去向）—— 用物理量×价格锚定，非锚定余量归"非豆其他农产品"：
  - 大豆国内产值 V_dom = 2023年产量 2084.7 万吨 × 农户出售综合价 ≈4660 元/吨 ≈ 971 亿元
    （4660 元/吨 = 汇编黑龙江单位全成本口径的产值参照；与汇编亩产值 761.86 元/亩 ÷
     0.1327 吨/亩 = 5742 元/吨之间取压榨/食用加权 ≈ 4660–5000，取中值段下沿保守值）
  - 进口大豆 V_imp = 9941 万吨 × 3900 元/吨(2023到岸) ≈ 3877 亿元
  - 流向压榨(植物油加工): 2023 压榨量 ≈9280 万吨 × 3900 ≈ 3619 亿元
    （校验: 不得超过表内 01002→13019 流量 3825 亿元的 95%）
  - 直接饲用: ≈300 万吨 × 4200 ≈ 126 亿元
  - 食品加工(其他农副+其他食品, 豆制品): ≈450 亿元, 按两部门原流量比例分摊
  - 居民直接消费: ≈300 亿元；种用自用: ≈60 亿元；余量→存货/出口(最终使用)
列拆分（大豆生产的投入结构）：按 01002 列系数等比例缩放（大豆种植投入结构近似其他经济作物）。

部门映射（与执行方案 §2.5 的差异：211 部门表畜牧不分猪/禽/反刍 →
  s4=牲畜(猪牛羊等), s5=家禽, s6=屠宰肉类加工+乳制品；口径已在 README 注明）：
  s1 大豆 | s2 植物油加工(压榨) | s3 饲料加工 | s4 牲畜养殖 | s5 家禽养殖
  s6 屠宰肉类+乳制品 | s7 其他食品制造(粮油糖水产蔬果酒饮茶等) | s8 其他农林牧渔 | s9 其余经济

输出:
  data/io_table_9sector.csv   A 矩阵 (a_ij = z_ij / X_j, 竞争型直接消耗系数)
  data/io_meta_9sector.csv    各部门总产出 GO、进口 IM、居民消费、最终需求权重 b
"""
from pathlib import Path
import numpy as np
import pandas as pd

XLS = "/root/data/数据/2023投入产出表/b01.xls"
ROOT = Path(__file__).resolve().parents[1]

# ---- 大豆拆分锚 (亿元, 2023) ----
V_SOY_DOM = 2084.7 * 4660 / 1e4      # 国产大豆产值 ≈ 971 亿元
V_SOY_IMP = 9941.0 * 3900 / 1e4      # 进口大豆到岸值 ≈ 3877 亿元
SOY_TO_CRUSH = 9280.0 * 3900 / 1e4   # 压榨用豆 ≈ 3619 亿元
SOY_TO_FEED = 300.0 * 4200 / 1e4     # 直接饲用 ≈ 126 亿元
SOY_TO_FOODMFG = 450.0               # 豆制品等食品加工用
SOY_TO_HH = 300.0                    # 居民直接消费
SOY_SEED_SELF = 60.0                 # 种用自用

SEC_NAMES = ["s1_soybean", "s2_crush", "s3_feed", "s4_livestock", "s5_poultry",
             "s6_meat_dairy", "s7_foodmfg", "s8_agri_other", "s9_rest"]
SEC_LABELS = ["大豆", "植物油压榨", "饲料加工", "牲畜养殖", "家禽养殖",
              "肉乳加工", "其他食品制造", "其他农林牧渔", "其余经济"]


def load_raw():
    df = pd.ExcelFile(XLS).parse("Sheet1", header=None)
    n = 211
    Z = df.iloc[7:7 + n, 3:3 + n].to_numpy(float)          # 中间流量 (万元)
    GO = df.iloc[7:7 + n, 226].to_numpy(float)             # 总产出
    IM = df.iloc[7:7 + n, 225].to_numpy(float)             # 进口
    HH = (df.iloc[7:7 + n, 215].to_numpy(float)
          + df.iloc[7:7 + n, 216].to_numpy(float))         # 居民消费(农村+城镇)
    FIN = df.iloc[7:7 + n, 224].to_numpy(float)            # 最终使用合计
    codes = [str(c) for c in df.iloc[7:7 + n, 2]]
    return Z, GO, IM, HH, FIN, codes


def aggregate():
    Z, GO, IM, HH, FIN, codes = load_raw()
    idx = {c: i for i, c in enumerate(codes)}
    yi = 1e4  # 万元 -> 亿元
    Z, GO, IM, HH, FIN = Z / yi, GO / yi, IM / yi, HH / yi, FIN / yi

    i_oc = idx["01002"]  # 其他农产品
    mapping = {
        "s2_crush": ["13019"], "s3_feed": ["13018"], "s4_livestock": ["03005"],
        "s5_poultry": ["03004"], "s6_meat_dairy": ["13021", "14026"],
        "s7_foodmfg": ["13017", "13020", "13022", "13023", "13024",
                        "14025", "14027", "14028", "15029", "15030", "15031"],
        "s8_agri_other": ["01001", "02003", "04006", "04007", "05008"],  # + 非豆01002
    }
    assigned = {i_oc} | {idx[c] for v in mapping.values() for c in v}
    rest = [i for i in range(211) if i not in assigned]

    # --- 拆出大豆行 (对 211 列) ---
    soy_row = np.zeros(211)
    j_crush, j_feed = idx["13019"], idx["13018"]
    soy_row[j_crush] = min(SOY_TO_CRUSH, 0.95 * Z[i_oc, j_crush])
    soy_row[j_feed] = min(SOY_TO_FEED, 0.95 * Z[i_oc, j_feed])
    j_f1, j_f2 = idx["13024"], idx["14028"]
    w = np.array([Z[i_oc, j_f1], Z[i_oc, j_f2]])
    alloc = min(SOY_TO_FOODMFG, 0.5 * w.sum()) * w / w.sum()
    soy_row[j_f1], soy_row[j_f2] = alloc
    soy_row[i_oc] = SOY_SEED_SELF  # 种用自用，落在非豆列上后并入 s8/s1 按列拆分处理
    soy_hh = SOY_TO_HH
    soy_supply = V_SOY_DOM + V_SOY_IMP
    soy_fin_other = max(soy_supply - soy_row.sum() - soy_hh, 0.0)  # 存货/出口等

    oc_row = Z[i_oc, :] - soy_row          # 非豆其他农产品行
    oc_hh = HH[i_oc] - soy_hh
    # --- 拆列: 按比例 sigma = 国产大豆产值 / 01002 总产出 ---
    sigma = V_SOY_DOM / GO[i_oc]
    soy_col = Z[:, i_oc] * sigma
    oc_col = Z[:, i_oc] * (1 - sigma)
    soy_row_selfuse = soy_row[i_oc]  # 种用: 大豆->(大豆+非豆)列, 按 sigma 分
    go_soy, go_oc = V_SOY_DOM, GO[i_oc] - V_SOY_DOM
    im_soy, im_oc = V_SOY_IMP, IM[i_oc] - V_SOY_IMP

    # --- 构造 212 维扩展体系: 索引 211 = 大豆, i_oc = 非豆其他农产品 ---
    Zx = np.zeros((212, 212)); Zx[:211, :211] = Z
    Zx[211, :211] = soy_row; Zx[i_oc, :211] = oc_row
    Zx[:211, 211] = soy_col; Zx[:211, i_oc] = oc_col
    # 行内对 (大豆,非豆) 两列的交叉项按 sigma 分
    for r in (211, i_oc):
        tot = Zx[r, i_oc]
        Zx[r, 211], Zx[r, i_oc] = tot * sigma, tot * (1 - sigma)
    GOx = np.append(GO, go_soy); GOx[i_oc] = go_oc
    IMx = np.append(IM, im_soy); IMx[i_oc] = im_oc
    HHx = np.append(HH, soy_hh); HHx[i_oc] = oc_hh
    FINx = np.append(FIN, soy_hh + soy_fin_other); FINx[i_oc] = FIN[i_oc] - FINx[211]

    # --- 聚合到 9 部门 ---
    groups = [[211]] + [[idx[c] for c in mapping[s]] for s in
              ["s2_crush", "s3_feed", "s4_livestock", "s5_poultry",
               "s6_meat_dairy", "s7_foodmfg"]]
    groups.append([idx[c] for c in mapping["s8_agri_other"]] + [i_oc])
    groups.append(rest)
    K = len(groups)
    Zg = np.zeros((K, K)); GOg = np.zeros(K); IMg = np.zeros(K); HHg = np.zeros(K)
    for a, ga in enumerate(groups):
        GOg[a] = GOx[ga].sum(); IMg[a] = IMx[ga].sum(); HHg[a] = HHx[ga].sum()
        for b, gb in enumerate(groups):
            Zg[a, b] = Zx[np.ix_(ga, gb)].sum()
    A = Zg / GOg[None, :]
    b_w = HHg / HHg.sum()

    L = np.linalg.inv(np.eye(K) - A)
    lam = float(np.max(np.abs(np.linalg.eigvals(A))))
    assert lam < 1, f"谱半径 {lam:.3f} >= 1"

    adf = pd.DataFrame(A, index=SEC_NAMES, columns=SEC_NAMES).round(6)
    adf.index.name = "sector"
    adf.to_csv(ROOT / "data/io_table_9sector.csv")
    meta = pd.DataFrame({"sector": SEC_NAMES, "label": SEC_LABELS,
                         "GO_yi_yuan": GOg.round(1), "IM_yi_yuan": IMg.round(1),
                         "HH_cons_yi_yuan": HHg.round(1), "b_weight": b_w.round(6)})
    meta.to_csv(ROOT / "data/io_meta_9sector.csv", index=False)
    print(f"谱半径={lam:.4f}  大豆总供给={soy_supply:.0f}亿(国产{V_SOY_DOM:.0f}+进口{V_SOY_IMP:.0f})")
    print(f"大豆Domar权重(Lb)_s1={(L @ b_w)[0]:.4f}")
    print(meta.to_string(index=False))
    return A, b_w, GOg, meta


if __name__ == "__main__":
    aggregate()
