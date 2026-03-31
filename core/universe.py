import pandas as pd
import numpy as np
from pathlib import Path

def build_first_universe(panel_path, save_path):
    print(f"🚀 正在加载全市场宽表 (来源: {panel_path})...")
    df = pd.read_parquet(panel_path)
    
    # 强制所有列名小写
    df.columns = [c.lower() for c in df.columns]
    
    # 确保日期格式为 datetime
    df['date'] = pd.to_datetime(df['date'])
    initial_count = len(df)

    print("⏳ 开始执行私募级四步过滤法...")

    # --- 1. 剔除 ST ---
    st_col = 'isst' if 'isst' in df.columns else 'is_st'
    df = df[df[st_col] == 0].copy()

    # --- 2. 剔除停牌 ---
    df = df[df['volume'] > 0].copy()

    # --- 3. 流动性过滤 (过去20日平均成交额 Top 80%) ---
    df = df.sort_values(['code', 'date'])
    df['amt_ma20'] = df.groupby('code')['amount'].transform(lambda x: x.rolling(20).mean())
    df = df.dropna(subset=['amt_ma20'])
    df['amt_rank'] = df.groupby('date')['amt_ma20'].rank(pct=True)
    df = df[df['amt_rank'] >= 0.2].copy()

    # ========================================================
    # 4. 【新增：日期截断逻辑】 仅保留到 2024-03-17 (含) 之前的数据
    # ========================================================
    target_date = pd.to_datetime('2024-03-17') # 如果你的数据是2024年
    df = df[df['date'] <= target_date].copy()
    print(f"   [Step 5] 日期截断完成：仅保留至 {target_date.date()} 之前的数据")

    # --- 5. 整理并保存 ---
    drop_cols = ['amt_ma20', 'amt_rank']
    universe_v1 = df.drop(columns=drop_cols, errors='ignore').sort_values(['date', 'code'])
    
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    universe_v1.to_parquet(save_path, index=False)
    
    print(f"\n✅ 股票池底座构建成功！最终行数: {len(universe_v1)}")
    return universe_v1

if __name__ == "__main__":
    PANEL_FILE = r"D:\量化平台\QuantFlow_Lab\data\derived\all_stocks_panel.parquet"
    SAVE_FILE = r"D:\量化平台\QuantFlow_Lab\data\derived\universe_v1.parquet"
    
    pool = build_first_universe(PANEL_FILE, SAVE_FILE)
    
    # 最终验证最高日期
    print(f"📅 数据集中最大日期为: {pool['date'].max().date()}")