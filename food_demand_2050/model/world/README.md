# CASM-World：中国膳食转型情景的世界市场影响（2024–2050）

用 CASM-World 联合模型（中国 CASM 平衡表 + PEATSim 世界结构，13 区域 × 31 商品，
基期 2023，纯 numpy）评估中国膳食转型情景（BS/PTS/HDS/MTS）到 2050 年
对世界农业市场的影响。

## 代码组织

- 模型本体：`/root/data/CASM/casm_world/cw/`（**只读导入，未做任何修改**）。
- 本目录 `run_scenarios.py`：情景运行器，包含
  1. 期限延长（2036–2050），2. 中国偏好 shifter 注入，3. 长表输出。
- 结果：`/root/paper/food_demand_2050/results/world/`
  - `world_results_long.csv` — scenario, commodity, region, year, variable, value
    （变量 PRD/CON/FOO/FEE/CRU/EXP/IMP/AHV/PDOM/PCN/PRF，年份 2024/2030/2035/2040/2045/2050）
  - `world_impacts_summary.md` — 2050 年相对 BS 的关键世界影响

## 方法

### 1. 期限延长到 2050

`Data()` 构建后仅修改内存对象（不落盘）：

- `d.macro` 的 POP、RGDP 按各区域 **2030–2035 年均增速（CAGR）** 外推到 2050；
- RXCHRATE（实际汇率）与关税（TMBASE/TM2BASE）持 2035 年值不变；
- 递归动态照抄 `cw.simulate.run_baseline` 的循环，years=2024–2050。

### 2. 偏好 shifter 注入（afhgr0 同构机制）

CASM-World 的食物需求方程（`model.py`）：

```
FOO(i,r,t) = consfoo(i,r) · Π_j PCN(j,r)^fodela(i,j,r) · pcrgdp(r,t)^gdpela(i,r) · POP(r,t)
```

BS 基线中的中国食用需求增长已由收入路径（pcrgdp^gdpela）驱动。膳食情景在此之上
叠加**偏好 shifter**（与中国单国 CASM 的 afhgr0/AFH 机制同构）：每年求解前把
中国列的食物截距乘以

```
consfoo(i, CHN, t) = consfoo0(i, CHN) · (1 + g_i)^(t − 2024)
```

g_i 为情景年增长率（2024 年因子=1，即 shock 自 2025 年起生效）。原奶（MLK 非贸易，
经乳品加工出清）另按 MILK 增长率同步缩放中国原奶消费截距 consmlk（报告口径；
对世界市场的传导通过乳制品食用需求实现）。BS 情景所有 g=0，与基线**完全一致**。
截距每年从基期副本重建，情景间无状态泄漏；世界其他区域不加 shock。

### 3. 商品映射表（论文 afhgr0 → CASM-World）

| 论文商品 | 世界模型商品 | PTS | HDS | MTS |
|---|---|---:|---:|---:|
| RICE 稻米 | RIC | −0.25 | −1.50 | −0.875 |
| WHEA 小麦 | WHE | −0.20 | −1.50 | −0.85 |
| 植物油 SOYO/RAPO/GRDO | SBO / RBO / NBO | +0.20 | −2.25 | −1.025 |
| PIGM 猪肉 | PRK | +0.40 | −4.69 | −2.145 |
| CATM 牛肉 | BFV | +0.25 | −4.90 | −2.325 |
| CHKM 禽肉 | PLM | +0.30 | +1.30 | +0.80 |
| MILK 奶类 | BUT/CHE/NDM/FMK/WDM/ODA 食用需求 + 原奶 consmlk | +0.75 | +3.00 | +1.875 |

单位：%/年，2025–2050 恒定；MTS = (PTS+HDS)/2。

### 4. 覆盖范围与未覆盖商品

**未覆盖**（世界模型商品空间中不存在，其 shock 未注入，解读结果时须注明）：
- SHGM 羊肉、EGGS 蛋类、FISH 水产、VEGT 蔬菜、FRTO 水果；
- SUGR 糖：世界模型有 SUG，但论文情景未给糖的 afhgr0，未注入。

因此本评估捕捉的是**主粮、植物油、猪牛禽肉、奶类**渠道的世界传导；
HDS 下水产大增的世界影响（鱼粉—豆粕替代等）不在模型范围内。

## 运行

```bash
python3 run_scenarios.py    # 4 情景 × 27 年，约 4–5 分钟
```

依赖：numpy；模型数据从 `/root/data/CASM/`（SILK 宏观/弹性工作簿 + CASM 平衡表）
只读加载。收敛判据：各年世界出清残差 |excess| < 1e-8（实际 ~1e-13）。
