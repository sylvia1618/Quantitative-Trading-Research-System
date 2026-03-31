import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import os

# 导入你现有的逻辑
from core.data_engine import main as sync_raw_main
from core.factory import run_factory
from core.standardized_factors import aggregate_and_standardize

class QuantFlowPipeline:
    def __init__(self):
        self.raw_dir = Path(r"D:\量化平台\QuantFlow_Lab\data\raw")
        self.factor_dir = Path(r"D:\量化平台\QuantFlow_Lab\data\factors")
        self.final_pool = Path(r"D:\量化平台\QuantFlow_Lab\data\final_standardized_pool.parquet")

    def get_last_date(self, file_path):
        """获取本地文件的最新日期"""
        if not Path(file_path).exists():
            return "2020-01-01"
        df = pd.read_parquet(file_path)
        return str(df['date'].max())

    def run_smart_update(self, callback=None):
        # --- 步骤 1: 增量下载原始数据 ---
        last_raw_date = self.get_last_date(self.raw_dir / "close.parquet")
        today = datetime.now().strftime("%Y-%m-%d")
        
        if last_raw_date < today:
            if callback: callback(f"📡 发现数据落后，从 {last_raw_date} 开始增量同步...")
            # 注意：你需要稍微修改 data_engine.py 接受 start_date 参数
            # 此处演示调用原 main，建议在 data_engine 内部加入日期判断逻辑
            sync_raw_main() 
        else:
            if callback: callback("✨ 原始行情已是最新，跳过下载。")

        # --- 步骤 2: 生成因子 ---
        # 我们可以通过比较 raw 数据和因子数据的最后日期来决定是否重算
        # 因子计算建议取全量行情以保证滑动窗口（如MA20）的准确性
        if callback: callback("🧪 启动工厂流水线生产因子...")
        raw_full_path = self.raw_dir / "full_feature_data.parquet"
        run_factory(str(raw_full_path), str(self.factor_dir))

        # --- 步骤 3: 标准化与大表合并 ---
        if callback: callback("⚖️ 执行 MAD 标准化与宽表合并...")
        aggregate_and_standardize(str(self.factor_dir), str(self.final_pool))
        
        if callback: callback("✅ 系统同步完成！")