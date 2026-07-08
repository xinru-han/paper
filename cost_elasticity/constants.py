"""constants.py — 外部常数登记（REV-1 执行铁律：外部常数附来源）

稿件中出现的一切非 out/ 溯源的外部常数集中于此，每项标注来源、口径与用途。
R 侧脚本以硬编码复刻本表的值（R 无法 import py），改动此表须同步 grep R/。
"""

# ── 样本与规格 ────────────────────────────────────────────────────────────
YEARS = (2004, 2024)                 # 面板年份范围
T_CENTER = 2014                      # t = year - T_CENTER（translog 时间中心化）
REGIME_BREAK_YEAR = 2014             # M6 Γ 断点：D2 = 1{year >= 2014}
#   依据：刘易斯转折的经验拐点文献普遍定位 2010–2014；本文取样本中点 2014
#   兼顾"前后段样本量均衡"（2004–13 vs 2014–24）。断点年归属后段。

KAPPA_BASELINE = 1e6                 # cc 曲率惩罚（Terrell 1996 逐观测）
KAPPA_GRID = (1e4, 1e5, 1e6, 1e7)    # M3b κ 敏感性网格
BOOT_SEED = 20260703                 # 所有 bootstrap 的 RNG 种子
BOOT_B_MAIN = 500                    # M1 主 bootstrap draws
BOOT_B_HW_MINOR = 250               # M12a hw 次要品种下限
BOOT_B_REGIONAL = 200                # M8 区域系统 bootstrap
BOOT_B_LR = 200                      # M9 bootstrap 化 LR

# ── 要素与分组 ────────────────────────────────────────────────────────────
FACTORS = ("labor", "mach", "fert", "seed", "other")   # other = numeraire
DRY_CROPS = ("corn", "wheat", "soybean", "peanut", "rapeseed")   # 旱作组
RICE_CROPS = ("rice_early_indica", "rice_mid_indica",
              "rice_late_indica", "rice_japonica")               # 稻作组

# NBS 四大区域划分（M8 区域×品种第一阶段；<4 省或 obs<60 并入邻区，见日志）
REGION = {
    "河北": "huabei", "山西": "huabei", "山东": "huabei", "河南": "huabei",
    "北京": "huabei", "天津": "huabei",
    "内蒙古": "dongbei", "辽宁": "dongbei", "吉林": "dongbei", "黑龙江": "dongbei",
    "江苏": "changjiang", "浙江": "changjiang", "安徽": "changjiang",
    "江西": "changjiang", "湖北": "changjiang", "湖南": "changjiang", "上海": "changjiang",
    "福建": "huanan", "广东": "huanan", "广西": "huanan", "海南": "huanan",
    "重庆": "xinan", "四川": "xinan", "贵州": "xinan", "云南": "xinan", "西藏": "xinan",
    "陕西": "xibei", "甘肃": "xibei", "青海": "xibei", "宁夏": "xibei", "新疆": "xibei",
}

# ── 价格构造年份口径（M10 w_mach 构造年份敏感性剔除集）─────────────────────
WMACH_EXTRAP_YEARS = (2004, 2005)    # 发改委机耕费外推（2006–2010 对数趋势回推）
WMACH_INTERP_YEARS = (2011, 2013)    # 机耕费省内对数插值年
WMACH_PARTIAL_2024 = 2024            # 2024 发改委机耕费仅 1–3 月（错过机收旺季）
WMACH_DROP_SET = (2004, 2005, 2011, 2013, 2024)   # M10 剔除集

# M11 仅原生 xls 年份（不依赖 OCR 修正/补录的风险定界子样本）
XLSONLY_YEARS = tuple(list(range(2006, 2019)) + [2024])

# M13c 疫情剔除年
COVID_YEARS = (2020, 2021, 2022)

# ── OCR 修正/补录规模（M15 数据附录披露）──────────────────────────────────
OCR_BASE_CONFLICTS = 1573            # out/base_conflicts.csv：PDF 直读覆盖底库污染值数
OCR_PATCH_ROWS = 4823                # 续表缺页补录行数（两轮合计）

# ── INPUT（外部数据，待用户提供；到位前 M5 用降级方案）────────────────────
# INPUT-1 分省分品种播种面积（万亩，2004–2024，NBS/统计年鉴）→ M5 聚合权重
#   降级：2004 与 2024 两端可得年份面积份额均值作固定权重
# INPUT-2 分省农村居民消费价格指数（2004–2024）→ M5 实际平减
#   降级：全国农村 CPI 统一平减，披露"省际差异未平减"
INPUT1_SOWN_AREA = None              # 到位后填路径
INPUT2_RURAL_CPI = None
