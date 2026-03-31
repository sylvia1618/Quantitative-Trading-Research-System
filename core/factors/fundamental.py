import pandas as pd
import numpy as np


# =========================
# 工具函数
# =========================

def _safe_inverse(series: pd.Series) -> pd.Series:
    """
    安全倒数：避免除0 / inf
    """
    out = 1.0 / series
    return out.replace([np.inf, -np.inf], np.nan)


def _zscore(series: pd.Series) -> pd.Series:
    """
    横截面标准化
    """
    mean = series.mean()
    std = series.std()
    if std == 0 or np.isnan(std):
        return pd.Series(0, index=series.index)
    return (series - mean) / std


# =========================
# 主函数
# =========================

def compute_fundamental_factors(df: pd.DataFrame) -> pd.DataFrame:
    """
    基本面因子计算

    输入要求字段：
    - date
    - code
    - close
    - peTTM
    - pbMRQ
    - amount

    输出：
    - FACTOR_EP
    - FACTOR_BP
    - FACTOR_AMOUNT_STABILITY
    - FACTOR_EP_Z
    - FACTOR_BP_Z
    """

    df = df.copy()

    # =========================
    # 1️⃣ 基础清洗
    # =========================
    for col in ['peTTM', 'pbMRQ', 'amount']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.replace([np.inf, -np.inf], np.nan)

    # =========================
    # 2️⃣ 核心因子
    # =========================

    # --- 盈利收益率（EP）
    df['FACTOR_EP'] = _safe_inverse(df['peTTM'])

    # --- 账面市值比（BP）
    df['FACTOR_BP'] = _safe_inverse(df['pbMRQ'])

    # =========================
    # 3️⃣ 成交额稳定性（Rolling CV）
    # =========================
    g = df.groupby('code')['amount']

    rolling_mean = g.transform(lambda x: x.rolling(20, min_periods=5).mean())
    rolling_std = g.transform(lambda x: x.rolling(20, min_periods=5).std())

    df['FACTOR_AMOUNT_STABILITY'] = rolling_std / rolling_mean

    # =========================
    # 4️⃣ 横截面标准化（Z-score）
    # =========================
    df['FACTOR_EP_Z'] = df.groupby('date')['FACTOR_EP'].transform(_zscore)
    df['FACTOR_BP_Z'] = df.groupby('date')['FACTOR_BP'].transform(_zscore)

    # =========================
    # 5️⃣ 统一清洗
    # =========================
    factor_cols = [
        'FACTOR_EP',
        'FACTOR_BP',
        'FACTOR_AMOUNT_STABILITY',
        'FACTOR_EP_Z',
        'FACTOR_BP_Z'
    ]

    df[factor_cols] = (
        df[factor_cols]
        .replace([np.inf, -np.inf], np.nan)
    )

    # 可选：前向填充（更稳）
    df[factor_cols] = df.groupby('code')[factor_cols].ffill()

    # =========================
    # 6️⃣ 输出
    # =========================
    return df[factor_cols]