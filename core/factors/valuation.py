import os
print("🔥 valuation 文件路径:", os.path.abspath(__file__))
print("🔥 valuation 新版本已加载")

import pandas as pd
import numpy as np


def _safe_inverse(series: pd.Series) -> pd.Series:
    out = 1.0 / series
    return out.replace([np.inf, -np.inf], np.nan)


def _zscore(series: pd.Series) -> pd.Series:
    mean = series.mean()
    std = series.std()
    if std == 0 or np.isnan(std):
        return pd.Series(0, index=series.index)
    return (series - mean) / std


def compute_valuation_factors(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    # =========================
    # ⚠️ 关键修复：适配你的字段
    # =========================
    # 你没有 psTTM / pcfNcfTTM
    # 👉 用 pbMRQ + peTTM 构建估值

    df['FACTOR_EP'] = _safe_inverse(df['peTTM'])   # 盈利收益率
    df['FACTOR_BP'] = _safe_inverse(df['pbMRQ'])   # 账面收益率

    # =========================
    # 横截面标准化
    # =========================
    df['EP_Z'] = df.groupby('date')['FACTOR_EP'].transform(_zscore)
    df['BP_Z'] = df.groupby('date')['FACTOR_BP'].transform(_zscore)

    # =========================
    # 合成因子（核心）
    # =========================
    df['FACTOR_VALUE_COMPOSITE'] = (
        df[['EP_Z', 'BP_Z']].mean(axis=1)
    )

    # =========================
    # 最终标准化
    # =========================
    df['FACTOR_VALUE_Z'] = (
        df.groupby('date')['FACTOR_VALUE_COMPOSITE']
        .transform(_zscore)
    )

    factor_cols = [
        'FACTOR_EP',
        'FACTOR_BP',
        'FACTOR_VALUE_COMPOSITE',
        'FACTOR_VALUE_Z'
    ]

    df[factor_cols] = df[factor_cols].replace([np.inf, -np.inf], np.nan)
    df[factor_cols] = df.groupby('code')[factor_cols].ffill()

    return df[factor_cols]