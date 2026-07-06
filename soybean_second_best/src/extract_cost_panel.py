"""从《全国农产品成本收益资料汇编》提取大豆-玉米分省成本收益面板。

数据源 /root/data/数据/成本收益数据/：
  - 年鉴文件夹 2007-2016, 2019, 2025（数据年 = 年鉴年-1）：各地区大豆/玉米成本收益 xls
    2017-2019 年鉴 xls 为 Excel 默认加密（VelvetSweatshop），用 msoffcrypto 解密
  - mineru OCR 数据库 provincial_cost_benefit_long.csv：补 2019-2023 数据年

输出 data/cost_benefit_panel.csv：province × data_year × crop 长表
列：yield_kg_mu, price_yuan_50kg, revenue, main_revenue, total_cost, prod_cost,
    material_cost, labor_cost, land_cost, net_profit, cash_income
单位：元/亩（产量 kg/亩，价格 元/50kg）
"""
import glob
import io
import os
import re

import pandas as pd

ROOT = '/root/data/数据/成本收益数据'
OUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'cost_benefit_panel.csv')

VAR_MAP = {
    '主产品产量': 'yield_kg_mu',
    '平均出售价格': 'price_yuan_50kg',
    '产值合计': 'revenue',
    '主产品产值': 'main_revenue',
    '总成本': 'total_cost',
    '生产成本': 'prod_cost',
    '物质与服务费用': 'material_cost',
    '人工成本': 'labor_cost',
    '土地成本': 'land_cost',
    '净利润': 'net_profit',
    '现金收益': 'cash_income',
}


def _norm(s):
    """去掉全角/半角空格。"""
    if not isinstance(s, str):
        return s
    return re.sub(r'[\s　]+', '', s)


def _norm_prov(s):
    """省名归一化：去行政后缀。"""
    return re.sub(r'(省|市|壮族自治区|回族自治区|维吾尔自治区|自治区)$', '', _norm(s))


def _read_any(path):
    """读 xls/xlsx，加密的用 Excel 默认密码解密。"""
    try:
        return pd.read_excel(path, header=None)
    except Exception:
        import msoffcrypto
        with open(path, 'rb') as f:
            of = msoffcrypto.OfficeFile(f)
            of.load_key(password='VelvetSweatshop')
            buf = io.BytesIO()
            of.decrypt(buf)
        return pd.read_excel(buf, header=None)


def parse_sheet(df, crop, data_year):
    """解析一张分省成本收益表（可能有多个并排块），返回长表记录。"""
    recs = []
    hdr_rows = [i for i in range(len(df))
                if any(_norm(v) == '项目' for v in df.iloc[i] if isinstance(v, str))]
    for hr in hdr_rows:
        header = df.iloc[hr]
        item_cols = [j for j, v in enumerate(header) if isinstance(v, str) and _norm(v) == '项目']
        for bi, ic in enumerate(item_cols):
            end = item_cols[bi + 1] if bi + 1 < len(item_cols) else len(header)
            prov_cols = {}
            for j in range(ic + 1, end):
                v = header.iloc[j]
                if isinstance(v, str) and _norm(v) not in ('单位', ''):
                    prov_cols[j] = _norm(v).replace('平均', '全国平均') if _norm(v) == '平均' else _norm(v)
            r = hr + 1
            while r < len(df):
                name = df.iloc[r, ic]
                if isinstance(name, str) and any(_norm(v) == '项目' for v in df.iloc[r] if isinstance(v, str)):
                    break  # 下一个表头
                key = VAR_MAP.get(_norm(name)) if isinstance(name, str) else None
                if key:
                    for j, prov in prov_cols.items():
                        val = pd.to_numeric(df.iloc[r, j], errors='coerce')
                        if pd.notna(val):
                            recs.append(dict(province=prov, data_year=data_year,
                                             crop=crop, variable=key, value=float(val)))
                r += 1
    return recs


def extract_yearbooks():
    """扫描各年鉴文件夹，解析大豆/玉米分省表（含续表/分块文件）。"""
    recs = []
    for ydir in sorted(os.listdir(ROOT)):
        p = os.path.join(ROOT, ydir)
        if not os.path.isdir(p) or not re.match(r'20\d\d$', ydir):
            continue
        mains = {}  # prefix -> (crop, data_year)
        files = sorted(glob.glob(p + '/**/*.xls*', recursive=True))
        for f in files:
            try:
                head = _read_any(f)
            except Exception:
                continue
            title = _norm(str(head.iloc[0, 0])) if len(head) else ''
            m = re.search(r'(20\d\d)年各地区(玉米|大豆)成本收益', title)
            if m:
                data_year, crop = int(m.group(1)), m.group(2)
                base = os.path.basename(f)
                prefix = re.match(r'([\d\-]+)', base).group(1).rstrip('-')
                mains[(os.path.dirname(f), prefix)] = (crop, data_year)
                recs += parse_sheet(head, crop, data_year)
        # 续表 / 分块（a/b/c 或 "续表"）：同目录同前缀但标题不含完整信息
        for (d, prefix), (crop, data_year) in mains.items():
            for f in sorted(glob.glob(os.path.join(d, prefix + '*'))):
                try:
                    head = _read_any(f)
                except Exception:
                    continue
                title = _norm(str(head.iloc[0, 0])) if len(head) else ''
                if re.search(r'(20\d\d)年各地区(玉米|大豆)成本收益', title):
                    continue  # 主表已处理
                if '续' in title or re.search(prefix.replace('-', r'\-') + r'[b-f]', os.path.basename(f)):
                    recs += parse_sheet(head, crop, data_year)
    return recs


def extract_ocr_db():
    """OCR 数据库补 2019-2023 数据年（2024年鉴之前的近年）。"""
    db = os.path.join(ROOT, 'mineru_ocr_output', 'database', 'provincial_cost_benefit_long.csv')
    df = pd.read_csv(db, low_memory=False)
    inv = {k: v for k, v in VAR_MAP.items()}
    sub = df[df['product'].isin(['大豆', '玉米'])
             & df['data_year'].between(2019, 2023)
             & df['variable_key'].isin(inv)].copy()
    sub['variable'] = sub['variable_key'].map(inv)
    sub['province'] = sub['province_name'].map(_norm_prov)
    sub = sub.dropna(subset=['province'])
    return [dict(province=r.province, data_year=int(r.data_year), crop=r.product,
                 variable=r.variable, value=float(r.value))
            for r in sub.itertuples() if pd.notna(r.value)]


def main():
    recs = extract_yearbooks() + extract_ocr_db()
    long = pd.DataFrame(recs)
    long['province'] = long['province'].map(_norm_prov)
    long = long.drop_duplicates(
        subset=['province', 'data_year', 'crop', 'variable'], keep='first')
    wide = long.pivot_table(index=['province', 'data_year', 'crop'],
                            columns='variable', values='value').reset_index()
    wide = wide.sort_values(['crop', 'province', 'data_year'])
    wide.to_csv(OUT, index=False)
    print(f'saved {OUT}: {len(wide)} rows, years {wide.data_year.min()}-{wide.data_year.max()}, '
          f'{wide.province.nunique()} provinces')
    return wide


if __name__ == '__main__':
    main()
