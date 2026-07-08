#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""admin_match.py — 地名→行政代码匹配工具（被三篇 import）"""
import re
import pandas as pd

COMMON_OUT = "/root/paper/rural_specialty_industry/common/output"
_TOWN_SUFFIX = re.compile(r"(街道办事处|街道|镇|乡|苏木|民族乡)$")


def norm(s):
    return "" if pd.isna(s) else re.sub(r"\s+", "", str(s))


def strip_prov(s):
    s = norm(s)
    return re.sub(r"(省|市|自治区|特别行政区)$", "", s)


class AdminMatcher:
    def __init__(self):
        self.town = pd.read_csv(f"{COMMON_OUT}/name2code_town.csv", dtype=str)
        self.county = pd.read_csv(f"{COMMON_OUT}/name2code_county.csv", dtype=str)
        # 县：province+城市+区县名称 全串键 & province+区县 键
        self.county["cc_concat"] = (self.county["province_std"]
                                    + self.county["城市"].map(norm)
                                    + self.county["区县名称"].map(norm))
        self.cc2code = dict(zip(self.county["cc_concat"], self.county["区县代码"]))
        self.pc2code = {}          # (province_std, county_std)->code(唯一时)
        for _, r in self.county.iterrows():
            self.pc2code.setdefault((r["province_std"], r["county_std"]), r["区县代码"])
        # 镇：(province_std, county_std, town_std)->镇代码；(province_std, town_std)->唯一
        self.pct2code = {}
        self.pt2code, pt_cnt = {}, {}
        self.pcCore2code, core_cnt = {}, {}   # (省,县,核心名)->码；去乡镇后缀
        self.county_names = {}     # province_std -> set(county_std) 供地址扫描
        for _, r in self.town.iterrows():
            p, c, t = r["province_std"], r["county_std"], r["town_std"]
            self.pct2code.setdefault((p, c, t), r["镇代码"])
            pt_cnt[(p, t)] = pt_cnt.get((p, t), 0) + 1
            self.pt2code[(p, t)] = r["镇代码"]
            core = _TOWN_SUFFIX.sub("", t)
            if core:
                core_cnt[(p, c, core)] = core_cnt.get((p, c, core), 0) + 1
                self.pcCore2code[(p, c, core)] = r["镇代码"]
            self.county_names.setdefault(p, set()).add(c)
        self.pt_unique = {k for k, v in pt_cnt.items() if v == 1}
        self.core_unique = {k for k, v in core_cnt.items() if v == 1}

    # --- 县级匹配：province + city_county 拼接串 ---
    def county_code(self, province, city_county):
        p = strip_prov(province)
        key = p + norm(city_county)
        if key in self.cc2code:
            return self.cc2code[key]
        # 退化：city_county 尾部当作县名
        cc = norm(city_county)
        for cn in sorted(self.county_names.get(p, ()), key=len, reverse=True):
            if cc.endswith(cn):
                return self.pc2code.get((p, cn))
        return None

    # --- 镇级匹配：province + county(可空) + town ---
    def town_code(self, province, county, town):
        p = strip_prov(province)
        c, t = norm(county), norm(town)
        if (p, c, t) in self.pct2code:
            return self.pct2code[(p, c, t)]
        # 去后缀核心名回退（撤镇设街道/乡改镇等）
        core = _TOWN_SUFFIX.sub("", t)
        if core and (p, c, core) in self.core_unique:
            return self.pcCore2code[(p, c, core)]
        if (p, t) in self.pt_unique:
            return self.pt2code[(p, t)]
        return None

    # --- 从完整地址串（如"河北省石家庄市藁城区南营镇"）解析并匹配镇 ---
    def town_code_from_addr(self, province, addr):
        p = strip_prov(province)
        a = norm(addr)
        m = _TOWN_SUFFIX.search(a)
        # 取末端乡镇 token：从右向左截到县名之后
        # 先找该省中出现在地址里的最长县名
        cty = None
        for cn in sorted(self.county_names.get(p, ()), key=len, reverse=True):
            if cn and cn in a:
                cty = cn
                break
        town_tok = None
        if cty:
            tail = a.split(cty, 1)[1]
            if _TOWN_SUFFIX.search(tail):
                town_tok = tail
        if town_tok is None and m:
            # 退化：取末尾以乡镇后缀结尾的短串（最后2-6字）
            town_tok = a[max(0, m.end() - 6):m.end()]
        return self.town_code(province, cty or "", town_tok or "")
