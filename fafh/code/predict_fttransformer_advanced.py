#!/usr/bin/env python3
"""
使用 FT-Transformer 预测户外消费系数。
包含：1.Copula 2.Kriging空间插值 3.Bootstrap(见run_bootstrap.py) 4.早停 5.超参优化(50 trials) 6.统一种子(42) 7.补全CV。
补缺失与系数预测均使用 FT-Transformer。
"""

import pandas as pd
import numpy as np
import os
import torch
import torch.nn as nn
import torch.optim as optim
import optuna
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import TimeSeriesSplit, KFold
import random

SEED = int(os.environ.get("PREDICT_SEED", 42))
torch.manual_seed(SEED)
np.random.seed(SEED)
random.seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

if 'LD_LIBRARY_PATH' in os.environ:
    ld_paths = os.environ['LD_LIBRARY_PATH'].split(':')
    filtered_paths = [p for p in ld_paths if not any(x in p.lower() for x in ['cuda', 'cudnn'])]
    if filtered_paths != ld_paths:
        os.environ['LD_LIBRARY_PATH'] = ':'.join(filtered_paths) if filtered_paths else ''

from data_preparation_advanced import (
    load_and_prepare_data_advanced, calc_outdoor_coef,
    apply_kriging_interpolation, apply_grain_structure_interpolation, prepare_features_combined,
)
from postprocess_predictions import run as run_postprocess

BASE_DIR = os.getcwd()
OUTPUT_FILE = os.path.join(BASE_DIR, "predictions_fttransformer_advanced.csv")
OUTPUT_FILE_ROBUST = os.path.join(BASE_DIR, "predictions_fttransformer_advanced_robust.csv")
OUTPUT_FILE_BOOTSTRAP = os.path.join(BASE_DIR, "predictions_fttransformer_advanced_bootstrap.csv")
IMPUTED_RATIOS_FILE = os.path.join(BASE_DIR, "data", "imputed_ratios_best.csv")
MODEL_NAME = "fttransformer_advanced"

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
optuna.logging.set_verbosity(optuna.logging.WARNING)


# --- FT-Transformer 模型定义 ---
class FeatureTokenizer(nn.Module):
    def __init__(self, num_num_features, num_cat_features, num_cats, d_token):
        super().__init__()
        self.num_weight = nn.Parameter(torch.randn(num_num_features, d_token))
        self.num_bias = nn.Parameter(torch.randn(num_num_features, d_token))
        self.cat_emb = nn.Embedding(num_cats, d_token)
        self.cat_bias = nn.Parameter(torch.randn(num_cat_features, d_token))

    def forward(self, x_num, x_cat):
        x_num_emb = x_num.unsqueeze(-1) * self.num_weight.unsqueeze(0) + self.num_bias.unsqueeze(0)
        x_cat_emb = self.cat_emb(x_cat) + self.cat_bias.unsqueeze(0)
        return torch.cat([x_num_emb, x_cat_emb], dim=1)


class FT_Transformer(nn.Module):
    def __init__(self, num_num, num_cats, d_token=64, n_layers=3, n_heads=4, d_ffn=128, dropout=0.1, output_sigmoid=False):
        super().__init__()
        self.tokenizer = FeatureTokenizer(num_num, 1, num_cats, d_token)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_token, nhead=n_heads, dim_feedforward=d_ffn,
            dropout=dropout, batch_first=True, norm_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.output_norm = nn.LayerNorm(d_token)
        self.output_layer = nn.Linear(d_token, 1)
        self.output_sigmoid = output_sigmoid

    def forward(self, x_num, x_cat):
        x = self.tokenizer(x_num, x_cat)
        x = self.transformer(x)
        x = x.mean(dim=1)
        x = self.output_norm(x)
        out = self.output_layer(x)
        if self.output_sigmoid:
            out = torch.sigmoid(out)
        return out


class DirectRatioOptimizer:
    """FT-Transformer 回归：预测户内消费系数（0-1），带早停与 Optuna 50 trials。"""
    def __init__(self, name):
        self.name = name
        self.scaler = StandardScaler()
        self.label_enc = LabelEncoder()
        self.best_model = None
        self.best_params = {}

    def _prepare_data(self, X_df):
        cats = X_df['T1'].values
        nums = X_df.drop(columns=['T1']).values
        nums = np.nan_to_num(nums, nan=0.0)
        if not hasattr(self.scaler, 'n_features_in_'):
            X_num_scaled = self.scaler.fit_transform(nums)
            X_cat_enc = self.label_enc.fit_transform(cats)
            self.num_cats = len(self.label_enc.classes_)
            self.num_num = nums.shape[1]
        else:
            X_num_scaled = self.scaler.transform(nums)
            known = set(self.label_enc.classes_)
            cats_safe = [c if c in known else self.label_enc.classes_[0] for c in cats]
            X_cat_enc = self.label_enc.transform(cats_safe)
        X_num_scaled = np.nan_to_num(X_num_scaled, nan=0.0)
        return torch.FloatTensor(X_num_scaled).to(device), torch.LongTensor(X_cat_enc).unsqueeze(1).to(device)

    def _train_step(self, model, loader, optimizer, criterion):
        model.train()
        total_loss, n_batches = 0.0, 0
        for bn, bc, by in loader:
            optimizer.zero_grad()
            pred = model(bn, bc).reshape(-1)
            loss = criterion(pred, by)
            if torch.isnan(loss):
                continue
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            total_loss += loss.item()
            n_batches += 1
        return total_loss / max(n_batches, 1)

    def _evaluate_step(self, model, X_num, X_cat, y, criterion):
        model.eval()
        with torch.no_grad():
            pred = model(X_num, X_cat).reshape(-1)
            return criterion(pred, y).item()

    def train_with_early_stopping(self, model, train_loader, val_loader, criterion, optimizer, patience=5, max_epochs=50):
        best_val_loss = float('inf')
        patience_counter = 0
        best_model_state = None
        for epoch in range(max_epochs):
            train_loss = self._train_step(model, train_loader, optimizer, criterion)
            val_loss = self._evaluate_step(
                model, val_loader.dataset.tensors[0], val_loader.dataset.tensors[1], val_loader.dataset.tensors[2], criterion
            )
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                best_model_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            else:
                patience_counter += 1
                if patience_counter >= patience and best_model_state is not None:
                    model.load_state_dict(best_model_state)
                    break
        return model, best_val_loss

    def objective(self, trial, X_num, X_cat, y):
        d_token = trial.suggest_categorical('d_token', [64, 128])
        n_layers = trial.suggest_int('n_layers', 1, 3)
        n_heads = trial.suggest_categorical('n_heads', [2, 4, 8])
        lr = trial.suggest_float('lr', 1e-4, 1e-3, log=True)
        dropout = trial.suggest_float('dropout', 0.1, 0.4)
        batch_size = trial.suggest_categorical('batch_size', [32, 64, 128])
        epochs = 20
        tscv = TimeSeriesSplit(n_splits=3)
        scores = []
        criterion = nn.MSELoss()
        for train_idx, val_idx in tscv.split(X_num):
            model = FT_Transformer(
                self.num_num, self.num_cats, d_token=d_token, n_layers=n_layers, n_heads=n_heads,
                dropout=dropout, output_sigmoid=True
            ).to(device)
            optimizer = optim.AdamW(model.parameters(), lr=lr)
            Xt_num, Xv_num = X_num[train_idx], X_num[val_idx]
            Xt_cat, Xv_cat = X_cat[train_idx], X_cat[val_idx]
            yt, yv = y[train_idx], y[val_idx]
            train_ds = torch.utils.data.TensorDataset(Xt_num, Xt_cat, yt)
            train_loader = torch.utils.data.DataLoader(train_ds, batch_size=batch_size, shuffle=True)
            val_ds = torch.utils.data.TensorDataset(Xv_num, Xv_cat, yv)
            val_loader = torch.utils.data.DataLoader(val_ds, batch_size=batch_size, shuffle=False)
            try:
                model, val_loss = self.train_with_early_stopping(
                    model, train_loader, val_loader, criterion, optimizer, patience=5, max_epochs=epochs
                )
                if np.isnan(val_loss) or np.isinf(val_loss):
                    return float('inf')
                scores.append(val_loss)
            except Exception:
                return float('inf')
        return np.mean(scores) if scores else float('inf')

    def fit_and_optimize(self, df_train, feature_cols, target_total, target_ratio, n_trials=50):
        df_train = df_train.sort_values('wave').reset_index(drop=True)
        X_num_full, X_cat_full = self._prepare_data(df_train[feature_cols])
        mask = (df_train[target_total] > 0).values
        if mask.sum() < 10:
            self.best_model = FT_Transformer(self.num_num, self.num_cats, output_sigmoid=True).to(device)
            return
        X_num = X_num_full[mask]
        X_cat = X_cat_full[mask]
        ratio_vals = df_train.loc[mask, target_ratio].values
        y = torch.FloatTensor(ratio_vals).to(device)
        study = optuna.create_study(direction='minimize', sampler=optuna.samplers.TPESampler(seed=SEED))
        study.optimize(lambda t: self.objective(t, X_num, X_cat, y), n_trials=n_trials)
        self.best_params = study.best_params
        self.best_model = FT_Transformer(
            self.num_num, self.num_cats,
            **{k: v for k, v in self.best_params.items() if k not in ['lr', 'batch_size']},
            output_sigmoid=True
        ).to(device)
        optimizer = optim.AdamW(self.best_model.parameters(), lr=self.best_params['lr'])
        loader = torch.utils.data.DataLoader(
            torch.utils.data.TensorDataset(X_num, X_cat, y),
            batch_size=self.best_params.get('batch_size', 64), shuffle=True
        )
        val_loader = torch.utils.data.DataLoader(
            torch.utils.data.TensorDataset(X_num, X_cat, y),
            batch_size=self.best_params.get('batch_size', 64), shuffle=False
        )
        criterion = nn.MSELoss()
        self.best_model, _ = self.train_with_early_stopping(
            self.best_model, loader, val_loader, criterion, optimizer, patience=5, max_epochs=50
        )

    def predict(self, X_df):
        X_num, X_cat = self._prepare_data(X_df)
        self.best_model.eval()
        with torch.no_grad():
            out = self.best_model(X_num, X_cat).reshape(-1).cpu().numpy()
        return np.clip(out, 1e-6, 1.0)


class FTRegressionModel:
    """FT-Transformer 回归（用于补缺失 home/total）。"""
    def __init__(self, name="ft_reg"):
        self.name = name
        self.scaler = StandardScaler()
        self.label_enc = LabelEncoder()
        self.model = None
        self.num_num = self.num_cats = None

    def _prepare_data(self, X_df):
        cats = X_df['T1'].values
        nums = X_df.drop(columns=['T1']).values
        nums = np.nan_to_num(nums, nan=0.0)
        if not hasattr(self.scaler, 'n_features_in_'):
            X_num_scaled = self.scaler.fit_transform(nums)
            X_cat_enc = self.label_enc.fit_transform(cats)
            self.num_cats = len(self.label_enc.classes_)
            self.num_num = nums.shape[1]
        else:
            X_num_scaled = self.scaler.transform(nums)
            known = set(self.label_enc.classes_)
            cats_safe = [c if c in known else self.label_enc.classes_[0] for c in cats]
            X_cat_enc = self.label_enc.transform(cats_safe)
        X_num_scaled = np.nan_to_num(X_num_scaled, nan=0.0)
        return torch.FloatTensor(X_num_scaled).to(device), torch.LongTensor(X_cat_enc).unsqueeze(1).to(device)

    def fit(self, df_train, feature_cols, target_col, max_epochs=30, patience=5):
        X_num, X_cat = self._prepare_data(df_train[feature_cols])
        y = torch.FloatTensor(df_train[target_col].astype(float).values).to(device)
        self.model = FT_Transformer(
            self.num_num, self.num_cats, d_token=64, n_layers=2, n_heads=4,
            d_ffn=128, dropout=0.2, output_sigmoid=False
        ).to(device)
        opt = optim.AdamW(self.model.parameters(), lr=1e-3)
        criterion = nn.MSELoss()
        ds = torch.utils.data.TensorDataset(X_num, X_cat, y)
        loader = torch.utils.data.DataLoader(ds, batch_size=64, shuffle=True)
        best_loss, best_state, cnt = float('inf'), None, 0
        for _ in range(max_epochs):
            self.model.train()
            for bn, bc, by in loader:
                opt.zero_grad()
                loss = criterion(self.model(bn, bc).reshape(-1), by)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                opt.step()
            self.model.eval()
            with torch.no_grad():
                vl = criterion(self.model(X_num, X_cat).reshape(-1), y).item()
            if vl < best_loss:
                best_loss, best_state, cnt = vl, {k: v.cpu().clone() for k, v in self.model.state_dict().items()}, 0
            else:
                cnt += 1
                if cnt >= patience:
                    break
        if best_state is not None:
            self.model.load_state_dict(best_state)
        return self

    def predict(self, X_df):
        X_num, X_cat = self._prepare_data(X_df)
        self.model.eval()
        with torch.no_grad():
            out = self.model(X_num, X_cat).reshape(-1).cpu().numpy()
        return out


def evaluate_imputation_cv_fttransformer(df_micro, feature_cols, total_col, home_col, n_splits=5):
    """补全阶段交叉验证，与 evaluate_imputation_cv 返回格式一致。"""
    df_full = df_micro.dropna(subset=feature_cols).copy()
    if total_col not in df_full.columns or home_col not in df_full.columns:
        return None
    mask_obs = df_full[total_col].notna() & df_full[home_col].notna() & (df_full[total_col] > 1e-6)
    df_obs = df_full[mask_obs]
    if len(df_obs) < 30:
        return None
    y_ratio = (df_obs[home_col] / df_obs[total_col]).clip(0, 1).values
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=SEED)
    mae_list, rmse_list, r2_list = [], [], []
    for train_idx, val_idx in kf.split(df_obs):
        df_train = df_obs.iloc[train_idx]
        df_val = df_obs.iloc[val_idx]
        y_val_ratio = y_ratio[val_idx]
        try:
            reg_home = FTRegressionModel("home").fit(df_train, feature_cols, home_col)
            reg_total = FTRegressionModel("total").fit(df_train, feature_cols, total_col)
            home_pred = reg_home.predict(df_val[feature_cols])
            total_pred = np.maximum(reg_total.predict(df_val[feature_cols]), 1e-6)
            ratio_pred = np.clip(home_pred / total_pred, 0.0, 1.0)
        except Exception:
            ratio_pred = np.full(len(val_idx), 0.5)
        err = ratio_pred - y_val_ratio
        mae_list.append(np.abs(err).mean())
        rmse_list.append(np.sqrt((err ** 2).mean()))
        ss_res = (err ** 2).sum()
        ss_tot = ((y_val_ratio - y_val_ratio.mean()) ** 2).sum()
        r2_list.append(1.0 - ss_res / (ss_tot + 1e-12))
    return {"MAE": np.mean(mae_list), "RMSE": np.mean(rmse_list), "R2": np.mean(r2_list)}


def impute_home_total_and_ratio_fttransformer(df_micro, feature_cols, total_col, home_col):
    """用 FT-Transformer 补缺失 ratio_filled。"""
    df_full = df_micro.dropna(subset=feature_cols).copy()
    if len(df_full) < 10 or total_col not in df_full.columns or home_col not in df_full.columns:
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
    try:
        reg_home = FTRegressionModel("home").fit(df_obs, feature_cols, home_col)
        reg_total = FTRegressionModel("total").fit(df_obs, feature_cols, total_col)
        home_pred = reg_home.predict(df_full[feature_cols])
        total_pred = np.maximum(reg_total.predict(df_full[feature_cols]), 1e-6)
        ratio_imputed = np.clip(home_pred / total_pred, 0.0, 1.0)
        ratio_filled[need_impute] = ratio_imputed[need_impute]
    except Exception:
        pass
    df_full["ratio_filled"] = ratio_filled
    return df_full


def train_fttransformer_model(X_train, y_train, X_val=None, y_val=None, df_train=None, feature_cols=None):
    """与其余模型一致的入口：grain 时传入 df_train+feature_cols，内部用 DirectRatioOptimizer。"""
    if df_train is None or feature_cols is None:
        return None
    df_train = df_train.copy()
    df_train["dummy_total"] = 1.0
    opt = DirectRatioOptimizer("grain")
    opt.fit_and_optimize(df_train, feature_cols, "dummy_total", "target_y", n_trials=50)
    return opt


def predict_grain_structure(df_micro, X_pred_feats, feature_cols, known_provinces, X_pred, train_model_func):
    if 'total_大米' not in df_micro.columns:
        return None
    df_micro = df_micro.copy()
    df_micro['calc_稻谷'] = df_micro['total_大米'] / 0.7
    total_za = df_micro.get('total_杂粮', pd.Series(0.0, index=df_micro.index)).fillna(0)
    df_micro['Total_Grain_Mass'] = (df_micro['calc_稻谷'].fillna(0) + df_micro['total_小麦'].fillna(0) + df_micro['total_豆类'].fillna(0) + total_za)
    df_grain = df_micro[df_micro['Total_Grain_Mass'] > 0.1].copy()
    if len(df_grain) < 10:
        return None
    targets = {'Share_Paddy': ('calc_稻谷', 'paddy'), 'Share_Wheat': ('total_小麦', 'wheat'), 'Share_Beans': ('total_豆类', 'beans'), 'Share_Other': ('total_杂粮', 'other')}
    all_results = []
    for name, (total_col_name, grain_type) in targets.items():
        if total_col_name not in df_grain.columns:
            continue
        df_train = df_grain[feature_cols].copy()
        df_train['target_y'] = (df_grain[total_col_name] / df_grain['Total_Grain_Mass']).clip(0, 1)
        df_train = df_train.dropna(subset=feature_cols + ['target_y'])
        if len(df_train) < 10:
            continue
        X_train, scaler, label_enc = prepare_features_combined(df_train[feature_cols], feature_cols)
        y_target = df_train['target_y'].values
        model = train_model_func(X_train, y_target, df_train=df_train, feature_cols=feature_cols)
        if model is None:
            continue
        s_pred = model.predict(X_pred_feats)
        share = np.clip(s_pred, 0.0, 1.0)
        res_df = pd.DataFrame({'Province': X_pred['T1'], 'Year': X_pred['wave'], f'{name}_Direct': share.astype(np.float64)})
        res_df = apply_grain_structure_interpolation(res_df, known_provinces, f'{name}_Direct', f'{name}_Final', X_pred_feats, grain_type=grain_type)
        all_results.append(res_df[['Province', 'Year', f'{name}_Final']].copy())
    if all_results:
        df_final = all_results[0]
        for df in all_results[1:]:
            df_final = pd.merge(df_final, df, on=['Province', 'Year'], how='outer')
        share_cols = [c for c in df_final.columns if c.endswith('_Final') and 'Share_' in c]
        if share_cols:
            s = df_final[share_cols].fillna(0).clip(0, 1)
            tot = s.sum(axis=1).replace(0, np.nan)
            df_final[share_cols] = s.div(tot, axis=0).fillna(1.0 / len(share_cols))
        df_final.to_csv(os.path.join(BASE_DIR, "grain_structure_predictions_fttransformer_advanced.csv"), index=False)
        return df_final
    return None


def predict_category(q_col, total_col, ratio_col, df_micro, X_pred_feats, feature_cols, known_provinces, X_pred, use_imputation=False):
    short = total_col.replace("total_", "")
    precomputed_col = f"ratio_filled_{short}"
    df_clean = None
    if use_imputation and precomputed_col in df_micro.columns and df_micro[precomputed_col].notna().sum() >= 10:
        df_clean = df_micro.dropna(subset=[precomputed_col] + feature_cols).copy()
        if len(df_clean) >= 10:
            df_clean = df_clean.rename(columns={precomputed_col: ratio_col})
            df_clean[total_col] = 1.0
        else:
            df_clean = None
    if df_clean is None and use_imputation:
        home_col = "home_" + short
        if total_col in df_micro.columns and home_col in df_micro.columns:
            df_filled = impute_home_total_and_ratio_fttransformer(df_micro, feature_cols, total_col, home_col)
            if df_filled is not None and df_filled["ratio_filled"].notna().sum() >= 10:
                df_clean = df_filled.dropna(subset=["ratio_filled"]).copy()
                df_clean = df_clean.rename(columns={"ratio_filled": ratio_col})
                df_clean[total_col] = 1.0
    if df_clean is None:
        df_clean = df_micro.dropna(subset=feature_cols + [total_col, ratio_col]).copy()
        if len(df_clean) < 10:
            return None
        df_clean = df_clean[df_clean[total_col] > 0]
        if len(df_clean) < 10:
            return None
        y_ratio = df_clean[ratio_col].values
    if len(df_clean) < 10:
        return None
    opt = DirectRatioOptimizer(q_col)
    opt.fit_and_optimize(df_clean, feature_cols, total_col, ratio_col, n_trials=50)
    s_pred = np.clip(opt.predict(X_pred_feats), 1e-6, 1.0)
    coef_direct = calc_outdoor_coef(s_pred)
    res_df = pd.DataFrame({'Province': X_pred['T1'], 'Year': X_pred['wave'], 'Coef_Direct': coef_direct.astype(np.float64)})
    return apply_kriging_interpolation(res_df, known_provinces, 'Coef_Direct', 'Coef_Final')


if __name__ == "__main__":
    print("当前使用: FT-Transformer 预测户外消费系数")
    df_micro, X_pred_feats, feature_cols, category_map, known_provinces = load_and_prepare_data_advanced(use_copula=True)
    X_pred = X_pred_feats.copy()
    predict_grain_structure(df_micro, X_pred_feats, feature_cols, known_provinces, X_pred, train_fttransformer_model)

    seed_env = os.environ.get("PREDICT_SEED", "42")
    for use_impute, out_path, label in [(True, OUTPUT_FILE, "主流程（补缺失）"), (False, OUTPUT_FILE_ROBUST, "稳健性（不补缺失）")]:
        if seed_env != "42" and not use_impute:
            continue
        if seed_env != "42" and use_impute:
            out_path = os.path.join(BASE_DIR, f"predictions_{MODEL_NAME}_seed{seed_env}.csv")
        if use_impute and os.path.isfile(IMPUTED_RATIOS_FILE):
            df_micro_use, _, _, _, _ = load_and_prepare_data_advanced(use_copula=True, imputed_ratios_path=IMPUTED_RATIOS_FILE)
        else:
            df_micro_use = df_micro
        all_results = []
        for q_col, total_col in category_map.items():
            ratio_col = f"ratio_{total_col.replace('total_', '')}"
            if total_col not in df_micro_use.columns or ratio_col not in df_micro_use.columns:
                continue
            res_df = predict_category(q_col, total_col, ratio_col, df_micro_use, X_pred_feats, feature_cols, known_provinces, X_pred, use_imputation=use_impute)
            if res_df is not None:
                res_df["Category"] = q_col
                all_results.append(res_df)
        if all_results:
            df_pivot = pd.concat(all_results, ignore_index=True).pivot_table(index=["Province", "Year"], columns="Category", values="Coef_Final", aggfunc="first").reset_index()
            df_pivot.columns.name = None
            df_pivot.to_csv(out_path, index=False)
            if seed_env == "42":
                print(f"✅ {label} 已保存: {out_path}")
                if out_path == OUTPUT_FILE_ROBUST:
                    import shutil
                    g = os.path.join(BASE_DIR, "grain_structure_predictions_fttransformer_advanced.csv")
                    if os.path.isfile(g):
                        shutil.copy(g, os.path.join(BASE_DIR, "grain_structure_predictions_fttransformer_advanced_robust.csv"))
                run_postprocess(predictions_path=out_path)
