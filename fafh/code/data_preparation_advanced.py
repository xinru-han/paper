#!/usr/bin/env python3
"""
高级数据准备模块
包含Copula收入分布匹配、Kriging空间插值等改进方法
"""

import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import StandardScaler, LabelEncoder
from scipy.spatial.distance import cdist
from scipy.stats import gaussian_kde
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

# 统一随机种子
SEED = 42
np.random.seed(SEED)

# 省份坐标
PROVINCE_COORDS = {
    11: (39.9, 116.4), 12: (39.1, 117.2), 13: (38.0, 114.5), 14: (37.8, 112.5), 
    15: (40.8, 111.7), 21: (41.8, 123.4), 22: (43.9, 125.3), 23: (45.7, 126.6), 
    31: (31.2, 121.5), 32: (32.0, 118.8), 33: (30.3, 120.2), 34: (31.8, 117.3), 
    35: (26.1, 119.3), 36: (28.7, 115.9), 37: (36.7, 117.0), 41: (34.8, 113.7), 
    42: (30.6, 114.3), 43: (28.2, 113.0), 44: (23.1, 113.3), 45: (22.8, 108.3), 
    46: (20.0, 110.3), 50: (29.6, 106.5), 51: (30.7, 104.1), 52: (26.6, 106.6), 
    53: (25.0, 102.7), 54: (29.6, 91.1),  61: (34.3, 108.9), 62: (36.1, 103.8), 
    63: (36.6, 101.8), 64: (38.5, 106.3), 65: (43.8, 87.6)
}

BASE_DIR = os.getcwd()
DATA_PATH = os.path.join(BASE_DIR, "data", "data.csv")
MACRO_PRED_PATH = os.path.join(BASE_DIR, "data", "data2012.csv")
PRODUCTION_PATH_1 = os.path.join(BASE_DIR, "data", "data_production1.csv")
PRODUCTION_PATH_2 = os.path.join(BASE_DIR, "data", "data_production2.csv")
PRODUCTION_PATH_3 = os.path.join(BASE_DIR, "data", "data_production3.csv")
MIN_PREDICT_YEAR = 2015  # 从该年起预测

PRODUCTION_VARS = [
    'qliangshi', 'qdaogu', 'qxiaomai', 'qyumi', 'qdoulei', 'qshulei', 'qyouliao', 
    'qshuiguo', 'qroulei', 'qzhurou', 'qniurou', 'qyangrou', 'qnailei', 'qqindan', 'qshuichan'
]

def calc_outdoor_coef(home_share):
    """户内消费系数（户内/户内外，0-1）转为户外消费系数（户内外/户内）。"""
    return 1.0 / np.maximum(np.asarray(home_share, dtype=np.float64), 1e-6)

def prepare_synthetic_columns(df_micro):
    """准备合成列：粮食、谷物、肉类"""
    if 'total_大米' in df_micro.columns and 'total_小麦' in df_micro.columns:
        df_micro['total_粮食'] = df_micro['total_大米'].fillna(0) + df_micro['total_小麦'].fillna(0)
        if 'total_杂粮' in df_micro.columns:
            df_micro['total_粮食'] += df_micro['total_杂粮'].fillna(0)
    
    if 'total_大米' in df_micro.columns and 'total_小麦' in df_micro.columns:
        df_micro['total_谷物'] = df_micro['total_大米'].fillna(0) + df_micro['total_小麦'].fillna(0)
    
    if 'total_猪肉' in df_micro.columns:
        df_micro['total_肉类'] = df_micro['total_猪肉'].fillna(0)
        for col in ['total_牛肉', 'total_羊肉', 'total_禽肉']:
            if col in df_micro.columns:
                df_micro['total_肉类'] += df_micro[col].fillna(0)
    # 牛羊肉合并：用于预测户外消费系数（牛肉+羊肉为一品种）
    if 'total_牛肉' in df_micro.columns and 'total_羊肉' in df_micro.columns:
        df_micro['total_牛羊肉'] = df_micro['total_牛肉'].fillna(0) + df_micro['total_羊肉'].fillna(0)
        if 'home_牛肉' in df_micro.columns and 'home_羊肉' in df_micro.columns:
            df_micro['home_牛羊肉'] = df_micro['home_牛肉'].fillna(0) + df_micro['home_羊肉'].fillna(0)
            mask = df_micro['total_牛羊肉'] > 1e-6
            df_micro.loc[mask, 'ratio_牛羊肉'] = (df_micro.loc[mask, 'home_牛羊肉'] / df_micro.loc[mask, 'total_牛羊肉']).clip(0, 1)
    
    # 创建ratio列（从子类别计算）
    # ratio_粮食：从 ratio_大米、ratio_小麦、ratio_杂粮 加权平均
    if 'total_粮食' in df_micro.columns:
        ratio_col = 'ratio_粮食'
        if ratio_col not in df_micro.columns or df_micro[ratio_col].isna().all():
            total_大米 = df_micro['total_大米'].fillna(0)
            total_小麦 = df_micro['total_小麦'].fillna(0)
            total_杂粮 = df_micro['total_杂粮'].fillna(0) if 'total_杂粮' in df_micro.columns else 0
            total_sum = total_大米 + total_小麦 + total_杂粮
            
            # 计算加权平均ratio
            ratio_粮食 = np.nan
            if 'ratio_大米' in df_micro.columns and 'ratio_小麦' in df_micro.columns:
                mask = total_sum > 0
                ratio_大米_vals = df_micro.loc[mask, 'ratio_大米'].fillna(0)
                ratio_小麦_vals = df_micro.loc[mask, 'ratio_小麦'].fillna(0)
                ratio_杂粮_vals = df_micro.loc[mask, 'ratio_杂粮'].fillna(0) if 'ratio_杂粮' in df_micro.columns else 0
                
                df_micro.loc[mask, ratio_col] = (
                    ratio_大米_vals * total_大米[mask] +
                    ratio_小麦_vals * total_小麦[mask] +
                    ratio_杂粮_vals * total_杂粮[mask]
                ) / total_sum[mask]
    
    # ratio_谷物：从 ratio_大米、ratio_小麦 加权平均
    if 'total_谷物' in df_micro.columns:
        ratio_col = 'ratio_谷物'
        if ratio_col not in df_micro.columns or df_micro[ratio_col].isna().all():
            total_大米 = df_micro['total_大米'].fillna(0)
            total_小麦 = df_micro['total_小麦'].fillna(0)
            total_sum = total_大米 + total_小麦
            
            # 计算加权平均ratio
            if 'ratio_大米' in df_micro.columns and 'ratio_小麦' in df_micro.columns:
                mask = total_sum > 0
                ratio_大米_vals = df_micro.loc[mask, 'ratio_大米'].fillna(0)
                ratio_小麦_vals = df_micro.loc[mask, 'ratio_小麦'].fillna(0)
                
                df_micro.loc[mask, ratio_col] = (
                    ratio_大米_vals * total_大米[mask] +
                    ratio_小麦_vals * total_小麦[mask]
                ) / total_sum[mask]
    
    # ratio_肉类：从子类别加权平均
    if 'total_肉类' in df_micro.columns:
        ratio_col = 'ratio_肉类'
        if ratio_col not in df_micro.columns or df_micro[ratio_col].isna().all():
            meat_cols = ['total_猪肉', 'total_牛肉', 'total_羊肉', 'total_禽肉']
            ratio_cols = ['ratio_猪肉', 'ratio_牛肉', 'ratio_羊肉', 'ratio_禽肉']
            
            total_sum = sum(df_micro[col].fillna(0) for col in meat_cols if col in df_micro.columns)
            
            if all(col in df_micro.columns for col in ratio_cols):
                mask = total_sum > 0
                weighted_sum = sum(
                    df_micro.loc[mask, ratio_col].fillna(0) * df_micro.loc[mask, meat_col].fillna(0)
                    for meat_col, ratio_col in zip(meat_cols, ratio_cols)
                    if meat_col in df_micro.columns and ratio_col in df_micro.columns
                )
                df_micro.loc[mask, ratio_col] = weighted_sum / total_sum[mask]
    
    return df_micro

def match_income_copula(df_micro, df_macro):
    """
    使用Copula方法匹配收入分布
    参考：Elbers et al. (2003)
    """
    print("  使用Copula方法进行收入分布匹配...")
    
    matched_incomes = []
    income_k_map = {}
    
    for (province, year), macro_group in df_macro.groupby(['T1', 'wave']):
        macro_income_mean = macro_group['income'].iloc[0]
        
        # 获取该省份-年份的微观收入数据
        micro_group = df_micro[(df_micro['T1'] == province) & (df_micro['wave'] == year)]
        
        if len(micro_group) == 0:
            # 如果没有微观数据，使用全局分布
            micro_group = df_micro
        
        micro_income = micro_group['indinc'].values
        micro_income = micro_income[micro_income > 0]  # 移除零值
        
        if len(micro_income) < 10:
            # 数据不足，使用简单比例
            scale_factor = macro_income_mean / (micro_group['indinc'].mean() + 1e-6)
            income_k_map[(province, year)] = scale_factor
            matched_incomes.extend([macro_income_mean] * len(macro_group))
            continue
        
        # 估计微观收入的核密度
        try:
            kde = gaussian_kde(micro_income)
        except:
            # 如果KDE失败，使用简单比例
            scale_factor = macro_income_mean / micro_income.mean()
            income_k_map[(province, year)] = scale_factor
            matched_incomes.extend([macro_income_mean] * len(macro_group))
            continue
        
        # 计算缩放因子，使均值匹配宏观均值
        scale_factor = macro_income_mean / micro_income.mean()
        income_k_map[(province, year)] = scale_factor
        
        # 方法：保持分布形状，缩放均值
        # 为宏观数据中的每个观测生成匹配的收入值
        n_samples = len(macro_group)
        if n_samples == 1:
            matched_incomes.append(macro_income_mean)
        else:
            # 使用分位数方法：从微观分布的分位数中采样
            quantiles = np.linspace(0.1, 0.9, n_samples)
            micro_quantiles = np.quantile(micro_income, quantiles)
            scaled_quantiles = micro_quantiles * scale_factor
            matched_incomes.extend(scaled_quantiles.tolist())
    
    df_macro = df_macro.copy()
    df_macro['indinc'] = matched_incomes[:len(df_macro)]
    
    return df_macro, income_k_map

def variogram(h, values, coords):
    """
    计算变异函数（Variogram）
    """
    n = len(coords)
    pairs = []
    
    for i in range(n):
        for j in range(i+1, n):
            dist = np.sqrt(np.sum((coords[i] - coords[j])**2))
            if dist <= h:
                pairs.append((dist, (values[i] - values[j])**2))
    
    if len(pairs) == 0:
        return 0.0
    
    distances, squared_diffs = zip(*pairs)
    return np.mean(squared_diffs)

def kriging_interpolation(known_provinces, known_values, unknown_province, coords_dict):
    """
    使用Kriging进行空间插值
    简化版本：使用指数变异函数
    """
    if unknown_province not in coords_dict:
        return np.nan
    
    unknown_coord = np.array(coords_dict[unknown_province])
    known_coords = np.array([coords_dict[p] for p in known_provinces])
    known_values = np.array(known_values)
    
    # 计算距离矩阵
    distances = cdist([unknown_coord], known_coords)[0]
    
    # 简化Kriging：使用指数变异函数
    # gamma(h) = C0 + C1 * (1 - exp(-h/a))
    # 这里简化为：权重与距离的倒数相关
    epsilon = 1e-6
    weights = 1.0 / (distances + epsilon)
    weights = weights / weights.sum()
    
    # 预测值
    prediction = np.dot(weights, known_values)
    
    # Kriging方差（简化）
    kriging_variance = np.dot(weights, distances) * np.var(known_values)
    
    return prediction, kriging_variance

def apply_grain_structure_interpolation(res_df, known_provinces, value_col, output_col, 
                                        X_pred_feats, grain_type='paddy'):
    """
    粮食结构预测的空间插值（与户外消费系数同样思路：空间插值 + 各省产量占比）
    
    参数:
    - grain_type: 'paddy' (稻谷), 'wheat' (小麦), 'beans' (豆类), 'other' (杂粮)
    - X_pred_feats: 含产量列 qliangshi, qdaogu, qxiaomai, qdoulei（杂粮占比 = (qliangshi-qdaogu-qxiaomai-qdoulei)/qliangshi）
    
    微观数据不存在的省份：用 IDW 空间插值 + 该省该品种产量占粮食产量比重融合得到占比；
    若没有已知省份可插值，则直接用该省产量占比。
    """
    res_df = res_df.copy()
    # 统一省份为 int，避免 str/int 导致 known_provinces 与 res_df 无法匹配、插值不写入
    res_df['Province'] = res_df['Province'].astype(int)
    res_df['Year'] = res_df['Year'].astype(int)
    known_provinces = set(int(p) for p in known_provinces)
    
    res_df[output_col] = res_df[value_col].astype(np.float64)
    all_provinces = list(res_df['Province'].unique())
    missing_provinces = [p for p in all_provinces if p not in known_provinces]
    
    if not missing_provinces:
        return res_df
    
    # 计算产量占比（从 X_pred_feats 获取）；键统一为 (int, int) 便于查找
    production_ratios = {}
    for _, row in X_pred_feats.iterrows():
        province = int(row['T1'])
        year = int(row['wave'])
        qliangshi = float(row.get('qliangshi', 0) or 0)
        qdaogu = float(row.get('qdaogu', 0) or 0)
        qxiaomai = float(row.get('qxiaomai', 0) or 0)
        qdoulei = float(row.get('qdoulei', 0) or 0)
        total_val = max(qliangshi, 1e-6)
        if grain_type == 'paddy':
            ratio = qdaogu / total_val
        elif grain_type == 'wheat':
            ratio = qxiaomai / total_val
        elif grain_type == 'beans':
            ratio = qdoulei / total_val
        elif grain_type == 'other':
            other_val = max(0, qliangshi - qdaogu - qxiaomai - qdoulei)
            ratio = other_val / total_val
        else:
            ratio = 0.0
        production_ratios[(province, year)] = np.clip(ratio, 0.0, 1.0)
    
    source_provinces = [p for p in known_provinces if p in all_provinces]
    
    if source_provinces:
        # 空间插值（IDW）+ 产量占比融合
        source_coords = np.array([PROVINCE_COORDS.get(p, (0, 0)) for p in source_provinces])
        target_coords = np.array([PROVINCE_COORDS.get(p, (0, 0)) for p in missing_provinces])
        dists = cdist(target_coords, source_coords, metric='euclidean')
        spatial_weights = 1.0 / (np.maximum(dists, 1e-5) ** 2)
        spatial_weights /= spatial_weights.sum(axis=1, keepdims=True)
    else:
        spatial_weights = None
    
    for year in res_df['Year'].unique():
        year = int(year)
        year_mask = res_df['Year'] == year
        if source_provinces and spatial_weights is not None:
            source_values = []
            for p in source_provinces:
                val = res_df.loc[year_mask & (res_df['Province'] == p), value_col].values
                source_values.append(val[0] if len(val) > 0 else np.nan)
            source_values = np.array(source_values, dtype=np.float64)
            if np.isnan(source_values).any():
                source_values[np.isnan(source_values)] = np.nanmean(source_values)
            spatial_interp_vals = np.dot(spatial_weights, source_values)
        else:
            spatial_interp_vals = None
        
        for i, p_missing in enumerate(missing_provinces):
            idx = res_df.index[year_mask & (res_df['Province'] == p_missing)]
            if len(idx) == 0:
                continue
            prod_ratio = production_ratios.get((p_missing, year), 0.0)
            if source_provinces and spatial_interp_vals is not None:
                alpha = 1.0 / (1.0 + np.exp(10 * (prod_ratio - 0.05)))
                if prod_ratio < 0.001:
                    alpha = 1.0
                elif prod_ratio > 0.3:
                    alpha = 0.2
                interp_val = spatial_interp_vals[i] if i < len(spatial_interp_vals) else np.nan
                if np.isfinite(interp_val):
                    final_value = alpha * interp_val + (1 - alpha) * prod_ratio
                else:
                    # 空间插值为 NaN 时（如已知省该年无数值），用产量占比或均匀 0.25
                    final_value = prod_ratio if np.isfinite(prod_ratio) and prod_ratio > 0 else 0.25
            else:
                final_value = prod_ratio if np.isfinite(prod_ratio) and prod_ratio > 0 else 0.25
            final_value = np.clip(float(final_value), 0.0, 1.0)
            res_df.loc[idx, output_col] = final_value
            if 'Interpolation_Flag' not in res_df.columns:
                res_df['Interpolation_Flag'] = None
            res_df.loc[idx, 'Interpolation_Flag'] = 'Weighted_Spatial_ProdRatio' if source_provinces else 'ProductionRatio_Only'
    
    return res_df

def apply_kriging_interpolation(res_df, known_provinces, value_col, output_col):
    """
    应用Kriging插值到未知省份（按年插值，每年独立计算使需插值省份每年数值不同）
    """
    res_df = res_df.copy()
    res_df[output_col] = res_df[value_col].copy()
    
    all_provinces = res_df['Province'].unique()
    missing_provinces = [p for p in all_provinces if p not in known_provinces]
    if not missing_provinces:
        return res_df
    source_provinces = [p for p in known_provinces if p in all_provinces]
    res_df[output_col] = res_df[output_col].astype(np.float64)
    for year in res_df['Year'].unique():
        year_mask = res_df['Year'] == year
        source_values = []
        for p in source_provinces:
            val = res_df.loc[year_mask & (res_df['Province'] == p), value_col].values
            source_values.append(val[0] if len(val) > 0 else np.nan)
        source_values = np.array(source_values, dtype=np.float64)
        if np.isnan(source_values).any():
            source_values[np.isnan(source_values)] = np.nanmean(source_values)
        for province in missing_provinces:
            if province not in PROVINCE_COORDS:
                continue
            pred, _ = kriging_interpolation(source_provinces, source_values.tolist(), province, PROVINCE_COORDS)
            if not np.isnan(pred):
                idx = res_df.index[year_mask & (res_df['Province'] == province)]
                if len(idx) > 0:
                    res_df.loc[idx, output_col] = float(pred)
    return res_df


def apply_spatial_interpolation(df_pred, known_provinces, target_col, output_col):
    """空间插值（IDW，按年插值），供其他模型使用。"""
    df_pred = df_pred.copy()
    df_pred[output_col] = df_pred[target_col]
    df_pred[output_col] = df_pred[output_col].astype(np.float64)
    all_provinces = df_pred['Province'].unique()
    missing_provinces = [p for p in all_provinces if p not in known_provinces]
    if not missing_provinces:
        return df_pred
    source_provinces = [p for p in known_provinces if p in all_provinces]
    source_coords = np.array([PROVINCE_COORDS.get(p, (0, 0)) for p in source_provinces])
    target_coords = np.array([PROVINCE_COORDS.get(p, (0, 0)) for p in missing_provinces])
    dists = cdist(target_coords, source_coords, metric='euclidean')
    weights = 1.0 / (np.maximum(dists, 1e-5) ** 2)
    weights /= weights.sum(axis=1, keepdims=True)
    for year in df_pred['Year'].unique():
        year_mask = df_pred['Year'] == year
        source_values = []
        for p in source_provinces:
            val = df_pred.loc[year_mask & (df_pred['Province'] == p), target_col].values
            source_values.append(val[0] if len(val) > 0 else np.nan)
        source_values = np.array(source_values, dtype=np.float64)
        if np.isnan(source_values).any():
            source_values[np.isnan(source_values)] = np.nanmean(source_values)
        interp_vals = np.dot(weights, source_values)
        for i, p_missing in enumerate(missing_provinces):
            idx = df_pred.index[year_mask & (df_pred['Province'] == p_missing)]
            if len(idx) > 0:
                df_pred.loc[idx, output_col] = float(interp_vals[i])
                if 'Interpolation_Flag' not in df_pred.columns:
                    df_pred['Interpolation_Flag'] = None
                df_pred.loc[idx, 'Interpolation_Flag'] = 'Spatial_IDW'
    return df_pred


def load_production_and_merge(df_macro: pd.DataFrame) -> pd.DataFrame:
    """从 data_production1/2/3.csv 按 wave、T1 合并农产品产量到宏观表。"""
    out = df_macro.copy()
    # 统一列名：生产表为 t1，宏观表为 T1
    for path, cols in [
        (PRODUCTION_PATH_1, ['qliangshi', 'qdaogu', 'qxiaomai', 'qyumi', 'qdoulei', 'qshulei', 'qyouliao', 'qshuiguo']),
        (PRODUCTION_PATH_2, ['qroulei', 'qzhurou', 'qniurou', 'qyangrou', 'qnailei', 'qqindan']),
        (PRODUCTION_PATH_3, ['qshuichan']),
    ]:
        if not os.path.isfile(path):
            continue
        df_p = pd.read_csv(path)
        if 't1' in df_p.columns and 'T1' not in df_p.columns:
            df_p = df_p.rename(columns={'t1': 'T1'})
        use = ['wave', 'T1'] + [c for c in cols if c in df_p.columns]
        df_p = df_p[use].groupby(['wave', 'T1'], as_index=False).median()
        out = out.drop(columns=[c for c in use if c in out.columns and c not in ('wave', 'T1')], errors='ignore')
        out = pd.merge(out, df_p, on=['wave', 'T1'], how='left')
    for var in PRODUCTION_VARS:
        if var not in out.columns:
            out[var] = 0
        else:
            out[var] = pd.to_numeric(out[var], errors='coerce')
            out[var] = out[var].fillna(out[var].mean()).fillna(0)
    return out


def load_and_prepare_data_advanced(use_copula=True, imputed_ratios_path=None):
    """
    加载并准备数据（高级版本）
    农产品产量从 data_production1/2/3.csv 按 wave、T1 匹配；预测仅从 MIN_PREDICT_YEAR 年起。
    imputed_ratios_path: 预计算补缺失结果 CSV（含 ratio_filled_大米 等列），若存在则合并到 df_micro。
    """
    print("加载数据...")
    df_micro = pd.read_csv(DATA_PATH)
    df_macro_raw = pd.read_csv(MACRO_PRED_PATH)
    df_macro_pred = df_macro_raw.groupby(['wave', 'T1'], as_index=False).median()
    df_macro_pred = load_production_and_merge(df_macro_pred)
    df_macro_pred = df_macro_pred[df_macro_pred['wave'] >= MIN_PREDICT_YEAR].copy()
    
    # 准备合成列
    df_micro = prepare_synthetic_columns(df_micro)
    
    # 收入分布匹配
    if use_copula:
        df_macro_pred, income_k_map = match_income_copula(df_micro, df_macro_pred)
    else:
        # 回退到省份-年份匹配
        income_k_map = df_micro.groupby(['T1', 'wave']).apply(
            lambda x: x['indinc'].mean() / (x['income'].mean() + 1e-6)
        ).to_dict()
        
        def get_income_k(row):
            key = (row['T1'], row['wave'])
            return income_k_map.get(key, 1.0)
        
        df_macro_pred['indinc'] = df_macro_pred.apply(
            lambda row: row['income'] * get_income_k(row), axis=1
        )
    
    # 特征列
    micro_features = ['indinc'] 
    macro_features = ['income', 'urbanrate', 'oldrate', 'engel', 'foodpindex', 'zyywsr', 'cyyye', 'cyyysr'] + PRODUCTION_VARS
    feature_cols = micro_features + macro_features + ['T1', 'wave']
    
    # 计算预测用的特征
    income_k_map_count = df_micro.groupby('T1')['indinc'].count().to_dict()
    known_provinces = list(income_k_map_count.keys())
    
    X_pred = df_macro_pred.copy()
    X_pred_feats = X_pred[feature_cols]
    
    # 品类映射：预测户外消费系数。含食用油、糖；牛肉与羊肉分开预测。
    category_map = {
        'q_daogu': 'total_大米',
        'q_xiaomai': 'total_小麦',
        'q_doulei': 'total_豆类',
        'q_zaliang': 'total_杂粮',
        'q_shucai': 'total_蔬菜',
        'q_zhurou': 'total_猪肉',
        'q_niurou': 'total_牛肉',
        'q_yangrou': 'total_羊肉',
        'q_qinlei': 'total_禽肉',
        'q_shuichanpin': 'total_水产品',
        'q_danlei': 'total_蛋类',
        'q_nailei': 'total_奶类',
        'q_guaguo': 'total_水果',
        'q_youliao': 'total_食用油',
        'q_tang': 'total_糖',
    }
    
    # 若提供预计算补缺失结果，合并到 df_micro（主流程共用同一补缺失样本）
    if imputed_ratios_path and os.path.isfile(imputed_ratios_path):
        try:
            loaded = pd.read_csv(imputed_ratios_path, index_col=0)
            ratio_cols = [c for c in loaded.columns if c.startswith("ratio_filled_")]
            for col in ratio_cols:
                df_micro[col] = loaded[col].reindex(df_micro.index).values
        except Exception:
            pass
    
    return df_micro, X_pred_feats, feature_cols, category_map, known_provinces


def evaluate_imputation_cv(df_micro, feature_cols, total_col, home_col, train_regressor_func, n_splits=5):
    """
    在观测到的 (total, home) 上做交叉验证：用 train 训练 home/total 模型，在 val 上预测 ratio，与真实 ratio 比较。
    返回 dict: MAE, RMSE, R2（R2 可能为负）。
    """
    from sklearn.model_selection import KFold
    df_full = df_micro.dropna(subset=feature_cols).copy()
    if total_col not in df_full.columns or home_col not in df_full.columns:
        return None
    mask_obs = df_full[total_col].notna() & df_full[home_col].notna() & (df_full[total_col] > 1e-6)
    df_obs = df_full[mask_obs]
    if len(df_obs) < 30:
        return None
    X_all, scaler, label_enc = prepare_features_combined(df_obs[feature_cols], feature_cols)
    y_ratio = (df_obs[home_col] / df_obs[total_col]).clip(0, 1).values
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=SEED)
    mae_list, rmse_list, r2_list = [], [], []
    for train_idx, val_idx in kf.split(X_all):
        X_train, X_val = X_all[train_idx], X_all[val_idx]
        y_train_ratio = y_ratio[train_idx]
        y_val_ratio = y_ratio[val_idx]
        home_train = df_obs[home_col].iloc[train_idx].astype(float).values
        total_train = df_obs[total_col].iloc[train_idx].astype(float).values
        model_home = train_regressor_func(X_train, home_train)
        model_total = train_regressor_func(X_train, total_train)
        home_pred = model_home.predict(X_val)
        total_pred = np.maximum(model_total.predict(X_val), 1e-6)
        ratio_pred = np.clip(home_pred / total_pred, 0.0, 1.0)
        err = ratio_pred - y_val_ratio
        mae_list.append(np.abs(err).mean())
        rmse_list.append(np.sqrt((err ** 2).mean()))
        ss_res = (err ** 2).sum()
        ss_tot = ((y_val_ratio - y_val_ratio.mean()) ** 2).sum()
        r2_list.append(1.0 - ss_res / (ss_tot + 1e-12))
    return {"MAE": np.mean(mae_list), "RMSE": np.mean(rmse_list), "R2": np.mean(r2_list)}


def impute_home_total_and_ratio(df_micro, feature_cols, total_col, home_col, train_regressor_func):
    """
    用 data 中能用的特征先预测缺失的户内消费量、户内外消费量，再得到户内消费系数（=户内/户内外）。
    与系数预测使用相同的预测方法（由 train_regressor_func 指定，如 LightGBM）。
    返回：带 ratio_filled 列的 DataFrame（全样本中：有观测用观测 ratio，缺失用 imputed home/total 算出的 ratio）。
    """
    df_full = df_micro.dropna(subset=feature_cols).copy()
    if len(df_full) < 10:
        return None
    if total_col not in df_full.columns or home_col not in df_full.columns:
        return None
    mask_obs = df_full[total_col].notna() & df_full[home_col].notna() & (df_full[total_col] > 1e-6)
    ratio_filled = np.full(len(df_full), np.nan, dtype=np.float64)
    ratio_filled[mask_obs] = (df_full.loc[mask_obs, home_col] / df_full.loc[mask_obs, total_col]).clip(0, 1).values
    need_impute = ~mask_obs
    if need_impute.sum() == 0:
        df_full["ratio_filled"] = ratio_filled
        return df_full
    df_obs = df_full[mask_obs]
    if len(df_obs) < 10:
        df_full["ratio_filled"] = ratio_filled
        return df_full
    X_obs, scaler, label_enc = prepare_features_combined(df_obs[feature_cols], feature_cols)
    model_home = train_regressor_func(X_obs, df_obs[home_col].astype(float).values)
    model_total = train_regressor_func(X_obs, df_obs[total_col].astype(float).values)
    X_full, _, _ = prepare_features_combined(df_full[feature_cols], feature_cols, scaler, label_enc)
    home_pred = model_home.predict(X_full)
    total_pred = np.maximum(model_total.predict(X_full), 1e-6)
    ratio_imputed = np.clip(home_pred / total_pred, 0.0, 1.0)
    ratio_filled[need_impute] = ratio_imputed[need_impute]
    df_full["ratio_filled"] = ratio_filled
    return df_full


def prepare_features_for_model(X_df, feature_cols, scaler=None, label_enc=None):
    """
    准备特征数据，返回数值特征和分类特征
    """
    cats = X_df['T1'].values
    nums = X_df.drop(columns=['T1', 'wave']).values
    
    nums = np.nan_to_num(nums, nan=0.0)
    
    if scaler is None:
        scaler = StandardScaler()
        X_num_scaled = scaler.fit_transform(nums)
    else:
        X_num_scaled = scaler.transform(nums)
    
    X_num_scaled = np.nan_to_num(X_num_scaled, nan=0.0)
    
    if label_enc is None:
        label_enc = LabelEncoder()
        X_cat_enc = label_enc.fit_transform(cats)
    else:
        known = set(label_enc.classes_)
        cats_safe = [c if c in known else label_enc.classes_[0] for c in cats]
        X_cat_enc = label_enc.transform(cats_safe)
    
    return X_num_scaled, X_cat_enc, scaler, label_enc

def prepare_features_combined(X_df, feature_cols, scaler=None, label_enc=None):
    """
    准备特征数据，返回合并后的特征
    """
    X_num, X_cat, scaler, label_enc = prepare_features_for_model(X_df, feature_cols, scaler, label_enc)
    X_combined = np.hstack([X_num, X_cat.reshape(-1, 1)])
    return X_combined, scaler, label_enc
