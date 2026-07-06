"""用《汇编》实测面板重建 6 区参数：大豆成本 + 玉米机会收益（联动核心）。

输入 data/cost_benefit_panel.csv（extract_cost_panel.py 产出, 2006-2024）
输出:
  data/regions.csv          — 更新: 大豆成本列改为实测, 新增玉米联动列
  data/corn_soy_dynamics.yaml — 价格/收益随机过程参数（历史面板估计）

经济口径（同一块地上大豆 vs 玉米, 土地成本对消）:
  作物剩余 surplus = 产值 − 生产成本(物质服务+人工)          [元/亩, 不含补贴]
  农户选择差 ΔV = (soy_surplus + sub_soy) − (corn_surplus + sub_corn)
  社会边际成本 MC_soy = (soy_prod_cost + corn_surplus) / yield  [元/吨]
    —— 种豆的资源成本 + 放弃玉米的机会成本

实证校验（黑龙江 2024）: soy_surplus−corn_surplus = −182 元/亩,
  生产者补贴差 366−118 = +248 元/亩 → 边际近似无差异, 与观测面积份额一致。
"""
import os

import numpy as np
import pandas as pd
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'data')

# 区域 -> (省, 大豆播种面积权重 万亩, NBS 2023)
# 黑龙江约7400万亩按北部高寒/中南各半拆分（第三/四/五积温带 vs 一/二积温带）
REGION_PROV = {
    'R1': [('黑龙江', 3700)],
    'R2': [('黑龙江', 3700), ('吉林', 550)],
    'R3': [('内蒙古', 1877)],
    'R4': [('河北', 190), ('山东', 440), ('河南', 620), ('安徽', 940), ('江苏', 320)],
    'R5': [('四川', 570), ('湖北', 340)],          # 西南带状复合(云贵渝无大豆分省表,四川湖北代理)
    'R6': [('山西', 230), ('辽宁', 160), ('陕西', 190)],
}
REGION_NAME = {
    'R1': '黑龙江北部高寒', 'R2': '黑龙江中南部及吉林', 'R3': '内蒙古东部',
    'R4': '黄淮海(豫皖鲁冀苏)', 'R5': '西南带状复合(川渝云贵)', 'R6': '其他产区',
}
# 生产者补贴 元/亩（2024 政策现状, 省级政策文件口径）:
#   东北+内蒙古: 大豆生产者补贴 ~366(黑), 玉米 ~118(黑); 黄淮海/西南无生产者补贴,
#   仅部分轮作/带状复合补贴(~150 大豆倾斜)。R4-R6 取 (150, 0)。
SUB_BASE = {
    'R1': (366.0, 118.0), 'R2': (366.0, 118.0), 'R3': (420.0, 35.0),
    'R4': (150.0, 0.0), 'R5': (150.0, 0.0), 'R6': (150.0, 0.0),
}
# 结构参数保留列（无实测口径, struct）
STRUCT_KEEP = ['quality_theta', 'proc_radius_km', 'service_level']


def _avg(panel, provs_w, crop, years, col):
    """省级面积加权均值（缺省份回退到已有省, 全缺回退全国平均）。"""
    sub = panel[(panel.crop == crop) & panel.data_year.isin(years)]
    vals, ws = [], []
    for p, w in provs_w:
        v = sub[sub.province == p][col].dropna()
        if len(v):
            vals.append(v.mean()); ws.append(w)
    if not vals:
        v = sub[sub.province == '全国平均'][col].dropna()
        return float(v.mean()) if len(v) else np.nan
    return float(np.average(vals, weights=ws))


def build(years=(2022, 2023, 2024)):
    panel = pd.read_csv(os.path.join(DATA, 'cost_benefit_panel.csv'))
    panel['surplus'] = panel['revenue'] - panel['prod_cost']
    old = pd.read_csv(os.path.join(DATA, 'regions.csv'))

    rows = []
    for rid, provs in REGION_PROV.items():
        g = lambda crop, col: _avg(panel, provs, crop, years, col)
        soy_yield = g('大豆', 'yield_kg_mu')
        soy_prod = g('大豆', 'prod_cost')
        soy_land = g('大豆', 'land_cost')
        corn_surplus = g('玉米', 'surplus')
        corn_yield = g('玉米', 'yield_kg_mu')
        corn_prod = g('玉米', 'prod_cost')
        o = old[old.region_id == rid].iloc[0]
        sub_soy, sub_corn = SUB_BASE[rid]
        rows.append(dict(
            region_id=rid, name=REGION_NAME[rid],
            area_share=o.area_share, area_wan_mu=o.area_wan_mu,
            yield_kg_mu=round(soy_yield, 1),
            # 供给成本口径: 机会成本 = 玉米剩余(放弃), 直接成本 = 大豆生产成本
            land_opp_cost_cny_mu=round(corn_surplus, 1),
            other_cost_cny_mu=round(soy_prod, 1),
            soy_land_cost_cny_mu=round(soy_land, 1),
            corn_yield_kg_mu=round(corn_yield, 1),
            corn_prod_cost_cny_mu=round(corn_prod, 1),
            corn_surplus_cny_mu=round(corn_surplus, 1),
            sub_soy_cny_mu=sub_soy, sub_corn_cny_mu=sub_corn,
            quality_theta=o.quality_theta, proc_radius_km=o.proc_radius_km,
            service_level=o.service_level,
            calib_flag='anchor_costdata|struct_quality'))
    regions = pd.DataFrame(rows)
    regions.to_csv(os.path.join(DATA, 'regions.csv'), index=False)

    # ---- 价格/收益随机过程（主产省面板 2006-2024）----
    def ar1_log(series):
        s = np.log(series.dropna().to_numpy())
        x, y = s[:-1], s[1:]
        rho = float(np.corrcoef(x, y)[0, 1])
        b = float(np.polyfit(x, y, 1)[0])
        resid = y - np.polyfit(x, y, 1)[1] - b * x
        return dict(rho=round(b, 3), sigma=round(float(resid.std()), 4),
                    mean_log=round(float(s.mean()), 4))

    hl = panel[panel.province == '黑龙江'].pivot_table(
        index='data_year', columns='crop',
        values=['price_yuan_50kg', 'surplus'])
    p_soy = hl[('price_yuan_50kg', '大豆')] * 20     # 元/吨
    p_corn = hl[('price_yuan_50kg', '玉米')] * 20
    dyn = dict(
        source='黑龙江面板 2006-2024（《汇编》各年鉴）',
        p_soy_ar1=ar1_log(p_soy),
        p_corn_ar1=ar1_log(p_corn),
        price_corr_yoy=round(float(
            np.corrcoef(np.diff(np.log(p_soy.dropna())),
                        np.diff(np.log(p_corn.dropna())))[0, 1]), 3),
        surplus_gap_mean=round(float(
            (hl[('surplus', '大豆')] - hl[('surplus', '玉米')]).mean()), 1),
        surplus_gap_2024=round(float(
            (hl[('surplus', '大豆')] - hl[('surplus', '玉米')]).iloc[-1]), 1),
        p_corn_2024=round(float(p_corn.iloc[-1]), 0),
        p_soy_2024=round(float(p_soy.iloc[-1]), 0),
    )
    with open(os.path.join(DATA, 'corn_soy_dynamics.yaml'), 'w') as f:
        yaml.safe_dump(dyn, f, allow_unicode=True, sort_keys=False)
    return regions, dyn


if __name__ == '__main__':
    regions, dyn = build()
    print(regions.to_string(index=False))
    print()
    print(yaml.safe_dump(dyn, allow_unicode=True, sort_keys=False))
