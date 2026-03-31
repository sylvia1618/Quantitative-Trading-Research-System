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

def compute_reversal_factors(df: pd.DataFrame) -> pd.DataFrame:
    """
    反转因子计算

    输入字段要求：
    - date
    - code
    - close
    - pctChg

    输出：
    - FACTOR_SHORT_REVERSAL
    - FACTOR_INTRADAY_REVERSAL
    - FACTOR_OVERREACTION
    - FACTOR_REVERSAL_Z
    """

    df = df.copy()

    # =========================
    # 1️⃣ 基础清洗
    # =========================
    cols = ['close', 'pctChg']
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.replace([np.inf, -np.inf], np.nan)

    g = df.groupby('code')

    # =========================
    # 2️⃣ 短期反转（核心）
    # =========================
    # 昨天涨 → 今天做空（反转）
    df['FACTOR_SHORT_REVERSAL'] = -g['pctChg'].shift(1)

    # =========================
    # 3️⃣ 日内反转（价格偏离）
    # =========================
    # close 相对短期均值的偏离（类似乖离率）
    rolling_mean_5 = (
        g['close']
        .transform(lambda x: x.rolling(5, min_periods=3).mean())
    )

    df['FACTOR_INTRADAY_REVERSAL'] = (
        df['close'] / rolling_mean_5 - 1
    )

    # =========================
    # 4️⃣ 过度反应（标准化冲击）
    # =========================
    rolling_mean_5_ret = (
        g['pctChg']
        .transform(lambda x: x.rolling(5, min_periods=3).mean())
    )

    rolling_std_5_ret = (
        g['pctChg']
        .transform(lambda x: x.rolling(5, min_periods=3).std())
    )

    df['FACTOR_OVERREACTION'] = rolling_mean_5_ret / rolling_std_5_ret

    # =========================
    # 5️⃣ 横截面标准化（主反转因子）
    # =========================
    df['FACTOR_REVERSAL_Z'] = (
        df.groupby('date')['FACTOR_SHORT_REVERSAL']
        .transform(_zscore)
    )

    # =========================
    # 6️⃣ 清洗
    # =========================
    factor_cols = [
        'FACTOR_SHORT_REVERSAL',
        'FACTOR_INTRADAY_REVERSAL',
        'FACTOR_OVERREACTION',
        'FACTOR_REVERSAL_Z'
    ]

    df[factor_cols] = df[factor_cols].replace([np.inf, -np.inf], np.nan)

    # 时间维度连续性
    df[factor_cols] = df.groupby('code')[factor_cols].ffill()

    # =========================
    # 7️⃣ 输出
    # =========================
    return df[factor_cols]