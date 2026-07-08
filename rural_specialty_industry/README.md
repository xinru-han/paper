# 乡村特色产业论文组合（rural_specialty_industry）

三篇论文的方案、代码与结果。数据底座：`/root/data/乡村特色产业数据/`（本地，不入库）。

## 目录

- `docs/` — 论文方案
  - `README.md` — 总览：数据家底、三篇定位、共同地基、外部数据需求
  - `paper1_产业强镇因果效应.md` — 英文旗舰：产业强镇"建设—认定"两阶段交错DID（AJAE/JDE/WD）
  - `paper2_认证叠加边际回报.md` — Certification stacking：县×产品逐层事件研究（Food Policy/AJAE）
  - `paper3_亿元村十亿元镇.md` — 超级明星：政策培育 vs 政策追认（中国农村经济/管理世界）
- `code/`
  - `01_build_policy_events.py` — 全部政策名单 → 统一事件长表 + 超级明星结果表 + 省年计数面板
- `output/`
  - `policy_events_long.csv` — 13,413条政策事件（policy×status×batch_year×省县镇×产品）
  - `superstar_outcomes.csv` — 亿元村693 + 十亿元镇466（含期次年份）
  - `province_year_counts.csv` — 省×年×政策计数面板
  - `summary_stats.md` — 核对汇总
  - `grain_county_800_2009.csv` / `grain_capacity_720_2024.csv` — 产粮大县名单（带标准化县代码，三篇共用异质性/政治经济学维度）

## 核对基准

产业强镇建设1,643（2018–2024七批）/ 认定770（2018–2021）+第二批合并认定257；产业园创建338/认定238；特优区307（4批）；集群220；GI 3,510（2008–2022）；名特优新5,605；品牌目录525（三期）。

## 下一步

1. 镇/县名→行政区划代码匹配（三篇共同地基）
2. GI县域字段提取（paper2）
3. 亿元村进入风险面板组装（paper3 先行成稿）
4. VIIRS灯光下载与乡镇聚合（paper1）
