# -*- coding: utf-8 -*-
"""Build the final analysis dataset (56 effect sizes, one-per-study).

The dataset preserves the manuscript's dual-track standardisation and path
classification (Section 3). It merges:
  raw/meta_effect_sizes.csv   Track-1 PCC/SE, Track-2 elasticity, Target and
                              path classification (MCI/AMS/AML) as reported in
                              the manuscript;
  raw/study_descriptors.csv   study-level descriptors (dependent variable,
                              mechanisation variable, journal tier, region,
                              data years, model) for transparency;
  raw/sample_sizes_verified.csv  author-verified sample sizes (a data-quality
                              correction over the original extraction; only the
                              sample-size column is updated).

Path classification (manuscript Section 3.1):
  MCI  agricultural machinery capital input  (Indicator_Type = Capital)
  AMS  agricultural machinery socialised services (Indicator_Type = AMS)
  AML  comprehensive mechanisation level      (Indicator_Type = Rate)

Output: meta_dataset.csv
"""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")

core = pd.read_csv(os.path.join(RAW, "meta_effect_sizes.csv"))
desc = pd.read_csv(os.path.join(RAW, "study_descriptors.csv"))
desc.columns = [c.strip() for c in desc.columns]

PATH = {"Capital": "MCI", "AMS": "AMS", "Rate": "AML"}
core["Path"] = core["Indicator_Type"].map(PATH)

dep = [c for c in desc.columns if "因变量" in c][0]
mech = [c for c in desc.columns if "自变量" in c][0]
d = desc.set_index("编号")

# verified sample sizes (data-quality correction; other fields unchanged)
vs = pd.read_csv(os.path.join(RAW, "sample_sizes_verified.csv"))
vs = vs.set_index("study_id")["N_verified"]

out = core.copy()
out["dependent_var"] = out["编号"].map(d[dep])
out["mechanization_var"] = out["编号"].map(d[mech])
out["N_verified"] = out["编号"].map(vs).fillna(out["样本量"])
out["LogN"] = np.log(out["N_verified"])

out = out[["编号", "作者_年份", "dependent_var", "mechanization_var",
           "样本量", "N_verified", "PCC", "SE_PCC", "弹性", "Target", "Path",
           "LogN"]]
out.columns = ["study_id", "author_year", "dependent_var", "mechanization_var",
               "N_original", "N", "PCC", "SE_PCC", "elasticity", "Target",
               "Path", "LogN"]
out = out.dropna(subset=["PCC", "SE_PCC"]).reset_index(drop=True)
out.to_csv(os.path.join(HERE, "meta_dataset.csv"), index=False,
           encoding="utf-8-sig")
print(f"{len(out)} effect sizes ->", os.path.join(HERE, "meta_dataset.csv"))
print(pd.crosstab(out["Target"], out["Path"], margins=True))
print("N updated (verified vs original):",
      int((out["N"] != out["N_original"]).sum()), "studies")
