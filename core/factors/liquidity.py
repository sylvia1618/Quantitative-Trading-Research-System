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

def compute_liquidity_factors(df: pd.DataFrame) -> pd.DataFrame:
    """
    流动性因子计算

    输入字段要求：
    - date
    - code
    - close
    - pctChg
    - amount
    - volume

    输出：
    - FACTOR_AMIHUD_ILLIQ
    - FACTOR_AMT_TURNOVER_PROXY
    - FACTOR_PV_CORR
    - FACTOR_AMIHUD_ILLIQ_Z
    """

    df = df.copy()

    # =========================
    # 1️⃣ 基础清洗
    # =========================
    cols = ['pctChg', 'amount', 'volume', 'close']
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.replace([np.inf, -np.inf], np.nan)

    # =========================
    # 2️⃣ Amihud 非流动性
    # =========================
    # |ret| / amount
    df['ILLIQ_RAW'] = (df['pctChg'].abs() / df['amount'])

    g = df.groupby('code')

    df['FACTOR_AMIHUD_ILLIQ'] = (
        g['ILLIQ_RAW']
        .transform(lambda x: x.rolling(20, min_periods=5).mean())
    )

    # =========================
    # 3️⃣ 成交额强度（相对过去20日）
    # =========================
    amt = g['amount']

    rolling_mean_amt = amt.transform(lambda x: x.rolling(20, min_periods=5).mean())

    df['FACTOR_AMT_TURNOVER_PROXY'] = df['amount'] / rolling_mean_amt

    # =========================
    # 4️⃣ 量价相关性（rolling corr）
    # =========================
    # ⚠️ 这里用 transform + rolling corr（避免 apply）

    def rolling_corr(x):
        return x['close'].rolling(20, min_periods=5).corr(x['volume'])

    df['FACTOR_PV_CORR'] = (
        df.groupby('code')[['close', 'volume']]
        .apply(rolling_corr)
        .reset_index(level=0, drop=True)
    )

    # =========================
    # 5️⃣ 横截面标准化（可选但建议）
    # =========================
    df['FACTOR_AMIHUD_ILLIQ_Z'] = (
        df.groupby('date')['FACTOR_AMIHUD_ILLIQ']
        .transform(_zscore)
    )

    # =========================
    # 6️⃣ 统一清洗
    # =========================
    factor_cols = [
        'FACTOR_AMIHUD_ILLIQ',
        'FACTOR_AMT_TURNOVER_PROXY',
        'FACTOR_PV_CORR',
        'FACTOR_AMIHUD_ILLIQ_Z'
    ]

    df[factor_cols] = df[factor_cols].replace([np.inf, -np.inf], np.nan)

    # 前向填充（保证时间连续）
    df[factor_cols] = df.groupby('code')[factor_cols].ffill()

    # =========================
    # 7️⃣ 输出
    # =========================
    return df[factor_cols]