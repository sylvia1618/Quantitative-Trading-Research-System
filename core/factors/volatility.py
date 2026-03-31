import pandas as pd
import numpy as np


def _zscore(series: pd.Series) -> pd.Series:
    mean = series.mean()
    std = series.std()
    if std == 0 or np.isnan(std):
        return pd.Series(0, index=series.index)
    return (series - mean) / std


def compute_volatility_factors(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    # =========================
    # 基础清洗
    # =========================
    cols = ['high', 'low', 'pctChg']
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.replace([np.inf, -np.inf], np.nan)

    # 排序（必须）
    df = df.sort_values(['code', 'date'])

    # =========================
    # 1️⃣ 标准波动率（无lambda）
    # =========================
    df['FACTOR_VOL_20'] = (
        df.groupby('code')['pctChg']
        .rolling(20, min_periods=5)
        .std()
        .reset_index(level=0, drop=True)
    )

    # =========================
    # 2️⃣ Parkinson（完全向量化）
    # =========================
    hl = np.log(df['high'] / df['low']) ** 2

    df['FACTOR_PARKINSON_VOL'] = (
        hl.groupby(df['code'])
        .rolling(20, min_periods=5)
        .mean()
        .reset_index(level=0, drop=True)
    )

    # =========================
    # 3️⃣ 上行波动率（优化）
    # =========================
    pos = df['pctChg'].clip(lower=0)

    df['FACTOR_UPSIDE_VOL'] = (
        pos.groupby(df['code'])
        .rolling(20, min_periods=5)
        .std()
        .reset_index(level=0, drop=True)
    )

    # =========================
    # 4️⃣ 下行波动率
    # =========================
    neg = df['pctChg'].clip(upper=0)

    df['FACTOR_DOWNSIDE_VOL'] = (
        neg.groupby(df['code'])
        .rolling(20, min_periods=5)
        .std()
        .reset_index(level=0, drop=True)
    )

    # =========================
    # 5️⃣ 横截面标准化
    # =========================
    df['FACTOR_VOL_Z'] = (
        df.groupby('date')['FACTOR_VOL_20']
        .transform(_zscore)
    )

    # =========================
    # 清洗
    # =========================
    factor_cols = [
        'FACTOR_VOL_20',
        'FACTOR_PARKINSON_VOL',
        'FACTOR_UPSIDE_VOL',
        'FACTOR_DOWNSIDE_VOL',
        'FACTOR_VOL_Z'
    ]

    df[factor_cols] = df[factor_cols].replace([np.inf, -np.inf], np.nan)
    df[factor_cols] = df.groupby('code')[factor_cols].ffill()

    return df[factor_cols]