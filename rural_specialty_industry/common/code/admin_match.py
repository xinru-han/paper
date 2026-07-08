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
        self.pcCoreC2code, ccore_cnt = {}, {}   # (省,县核心)->码
        self.pref2counties = {}    # (province_std, 城市std)->set(区县代码)  地市展开
        _CSUF = re.compile(r"(县|市|区|旗|自治县|自治旗|林区|特区)$")
        for _, r in self.county.iterrows():
            self.pc2code.setdefault((r["province_std"], r["county_std"]), r["区县代码"])
            core = _CSUF.sub("", r["county_std"])
            if core:
                ccore_cnt[(r["province_std"], core)] = ccore_cnt.get((r["province_std"], core), 0) + 1
                self.pcCoreC2code[(r["province_std"], core)] = r["区县代码"]
            self.pref2counties.setdefault(
                (r["province_std"], norm(r["城市"])), set()).add(r["区县代码"])
        self.ccore_unique = {k for k, v in ccore_cnt.items() if v == 1}
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

    def county_codes_flex(self, province, name):
        """返回 set：县级->单县；地市/州级->该市全部县；含撤县设区核心名回退。"""
        p = strip_prov(province)
        nm = norm(name)
        if (p, nm) in self.pc2code:
            return {self.pc2code[(p, nm)]}
        # 地市/州级授予 -> 展开
        pref = re.sub(r"(市|州|地区|自治州|盟)$", "", nm)
        for suf in ("市", "州", "地区", "自治州", "盟"):
            if (p, nm) in self.pref2counties:
                return set(self.pref2counties[(p, nm)])
        if (p, nm + "市") in self.pref2counties:
            return set(self.pref2counties[(p, nm + "市")])
        # 县核心名回退（撤县设区/市）
        core = re.sub(r"(县|市|区|旗|自治县|自治旗|林区|特区)$", "", nm)
        if core and (p, core) in self.ccore_unique:
            return {self.pcCoreC2code[(p, core)]}
        code = self.county_code(province, name)
        return {code} if code else set()

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
