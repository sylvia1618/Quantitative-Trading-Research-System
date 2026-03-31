import pandas as pd
import numpy as np


# =========================
# 工具函数
# =========================

def _zscore(series: pd.Series) -> pd.Series:
    mean = series.mean()
    std = series.std()
    if std == 0 or np.isnan(std):
        return pd.Series(0, index=series.index)
    return (series - mean) / std


# =========================
# 主函数
# =========================

def compute_momentum_factors(df: pd.DataFrame) -> pd.DataFrame:
    """
    动量因子计算

    输入字段要求：
    - date
    - code
    - close
    - pctChg
    - volume

    输出：
    - FACTOR_MOM_3/5/20/60/120
    - FACTOR_VW_MOM
    - FACTOR_RISK_ADJ_MOM
    - FACTOR_MOM_20_Z
    """

    df = df.copy()

    # =========================
    # 1️⃣ 基础清洗
    # =========================
    cols = ['close', 'pctChg', 'volume']
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.replace([np.inf, -np.inf], np.nan)

    g = df.groupby('code')

    # =========================
    # 2️⃣ 多周期动量（价格动量）
    # =========================
    windows = [3, 5, 20, 60, 120]

    for n in windows:
        df[f'FACTOR_MOM_{n}'] = (
            g['close']
            .transform(lambda x: x / x.shift(n) - 1)
        )

    # =========================
    # 3️⃣ 成交量加权动量（VW Momentum）
    # =========================
    # 核心思想：
    # ∑(ret * volume) / ∑volume

    ret = df['pctChg']
    vol = df['volume']

    vw_ret = ret * vol

    df['VW_RET'] = vw_ret

    rolling_vw_ret = (
        g['VW_RET']
        .transform(lambda x: x.rolling(20, min_periods=5).sum())
    )

    rolling_vol = (
        g['volume']
        .transform(lambda x: x.rolling(20, min_periods=5).sum())
    )

    df['FACTOR_VW_MOM'] = rolling_vw_ret / rolling_vol

    # =========================
    # 4️⃣ 风险调整动量（Sharpe-like）
    # =========================
    rolling_mean = (
        g['pctChg']
        .transform(lambda x: x.rolling(20, min_periods=5).mean())
    )

    rolling_std = (
        g['pctChg']
        .transform(lambda x: x.rolling(20, min_periods=5).std())
    )

    df['FACTOR_RISK_ADJ_MOM'] = rolling_mean / rolling_std

    # =========================
    # 5️⃣ 横截面标准化（选一个核心做）
    # =========================
    df['FACTOR_MOM_20_Z'] = (
        df.groupby('date')['FACTOR_MOM_20']
        .transform(_zscore)
    )

    # =========================
    # 6️⃣ 清洗
    # =========================
    factor_cols = [
        'FACTOR_MOM_3',
        'FACTOR_MOM_5',
        'FACTOR_MOM_20',
        'FACTOR_MOM_60',
        'FACTOR_MOM_120',
        'FACTOR_VW_MOM',
        'FACTOR_RISK_ADJ_MOM',
        'FACTOR_MOM_20_Z'
    ]

    df[factor_cols] = df[factor_cols].replace([np.inf, -np.inf], np.nan)

    # 前向填充（时间连续性）
    df[factor_cols] = df.groupby('code')[factor_cols].ffill()

    # =========================
    # 7️⃣ 输出
    # =========================
    return df[factor_cols]