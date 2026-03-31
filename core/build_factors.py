import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# --- 核心修复：自动定位项目根目录 ---
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.pipeline import AlphaPipeline
from core.factors.fundamental import FundamentalFactors

def build_all():
    processed_dir = project_root / "data" / "processed"
    raw_dir = project_root / "data" / "raw"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # 0. 提前加载价格数据作为基准（对齐索引使用）
    if not (raw_dir / "close.parquet").exists():
        print("❌ 错误：找不到 close.parquet，无法对齐数据。")
        return
    close = pd.read_parquet(raw_dir / "close.parquet")

    # 1. 定义因子计算任务
    tasks = {}

    # --- 因子 A: 20日动量 ---
    tasks['momentum_20'] = close.pct_change(20)

    # --- 因子 B: 换手率稳定性 ---
    if (raw_dir / "turnover.parquet").exists():
        turnover = pd.read_parquet(raw_dir / "turnover.parquet")
        tasks['to_stable'] = FundamentalFactors.calculate_turnover_volatility(turnover, period=5)

    # --- 因子 C: 估值因子 (EP) ---
    if (raw_dir / "pe_ttm.parquet").exists():
        pe = pd.read_parquet(raw_dir / "pe_ttm.parquet")
        # 逻辑：PE越大，因子值越大 (代表越贵)
        # 这里直接用 pe 确保数值越大代表越贵，或者用 - (1 / pe)
        tasks['ep'] = 1 / pe

    # 2. 执行手工批量加工 (跳过 Pipeline 黑箱)
    for name, df in tasks.items():
        print(f"⚙️ 正在手工加工: {name}...")
        try:
            # A. 对齐索引：确保因子矩阵和价格矩阵维度一致
            processed_df = df.reindex_like(close)
            
            # B. 截面标准化 (Z-Score)：在每一天(axis=1)内部做标准化
            # 这能保证因子在不同日期之间具有可比性，同时不丢失有效样本
            row_mean = processed_df.mean(axis=1)
            row_std = processed_df.std(axis=1)
            processed_df = processed_df.sub(row_mean, axis=0).div(row_std, axis=0)
            
            # C. 极值处理 (Winsorize)：将超出 3 倍标准差的异常值拉回
            processed_df = processed_df.clip(-3, 3)

            # D. 存储
            save_path = processed_dir / f"factor_{name}.parquet"
            processed_df.to_parquet(save_path)
            
            valid_count = processed_df.notna().sum().sum()
            print(f"✅ 成功! 已存至: {save_path.name} | 有效值: {valid_count}")
            
        except Exception as e:
            print(f"❌ {name} 加工失败: {e}")

if __name__ == "__main__":
    build_all()