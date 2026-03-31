import pandas as pd
import numpy as np
from pathlib import Path
import time
import sys

# 自动处理路径，确保能 import core.factors
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from core.factors.fundamental import compute_fundamental_factors
from core.factors.liquidity import compute_liquidity_factors
from core.factors.momentum import compute_momentum_factors
from core.factors.reversal import compute_reversal_factors
from core.factors.valuation import compute_valuation_factors
from core.factors.volatility import compute_volatility_factors

class QuantFlowFactory:
    def __init__(self, data_path: str, output_dir: str):
        self.data_path = Path(data_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 注册因子函数
        self.factor_funcs = {
            "fundamental": compute_fundamental_factors,
            "liquidity": compute_liquidity_factors,
            "momentum": compute_momentum_factors,
            "reversal": compute_reversal_factors,
            "valuation": compute_valuation_factors,
            "volatility": compute_volatility_factors,
        }

    def produce(self):
        print(f"🚀 开始生产原始因子池...")
        
        # 1. 加载原始行情
        df = pd.read_parquet(self.data_path)
        df = df.sort_values(['code', 'date'])

        # 💡 [关键新增] 计算未来收益率标签 (Target Label)
        # 这里的 ret_1d 代表“今天收盘后，到明天收盘”的收益率
        print("📈 正在生成未来收益率标签...")
        g = df.groupby('code')
        # 次日收益率 (Forward 1-day return)
        df['ret_1d'] = g['close'].shift(-1) / df['close'] - 1
        # 未来5日收益率
        df['ret_5d'] = g['close'].shift(-5) / df['close'] - 1
        # 未来10日收益率
        df['ret_10d'] = g['close'].shift(-10) / df['close'] - 1
        # 未来20日收益率
        df['ret_20d'] = g['close'].shift(-20) / df['close'] - 1

        # 2. 逐个模块计算并“挂载”
        all_factor_cols = []
        
        for name, func in self.factor_funcs.items():
            start_t = time.time()
            print(f"🧪 提取模块: {name} ...", end="")
            try:
                # 调用各个 .py 里的计算函数
                res = func(df)
                
                # 找出该模块新生成的 FACTOR_ 开头的列
                new_cols = [c for c in res.columns if c.startswith('FACTOR_')]
                
                # 💡 核心修复逻辑：挂载前先检查并删除已存在的同名因子列
                for col in new_cols:
                    if col in df.columns:
                        # 如果列已存在（比如在之前的模块算过），先删除旧的
                        df = df.drop(columns=[col])
                    
                    df[col] = res[col]
                    if col not in all_factor_cols:
                        all_factor_cols.append(col)
                
                print(f" 完成 ({len(new_cols)}个因子, 耗时{time.time()-start_t:.2f}s)")
            except Exception as e:
                print(f" ❌ 出错: {e}")

        # 3. 筛选最终大表字段
        info_cols = ['date', 'code', 'industry', 'open', 'high', 'low', 'close', 'volume', 'amount', 'turn']
        # 自动识别所有以 ret_ 开头的收益率列
        ret_cols = [c for c in df.columns if c.startswith('ret_')]
        
        # 组合所有列
        final_cols = info_cols + ret_cols + all_factor_cols
        
        # 💡 二次保障：确保 final_cols 列表本身没有重复项
        final_cols = list(dict.fromkeys(final_cols)) 
        
        # 确保列确实存在于 df 中
        final_cols = [c for c in final_cols if c in df.columns]
        
        raw_pool = df[final_cols].copy()

        # 4. 保存为原始因子大表
        output_path = self.output_dir / "raw_factors_pool.parquet"
        print(f"💾 正在保存原始大表 (已自动去重): {output_path}")
        
        # 强制检查：如果还有重复列名，手动清理
        raw_pool = raw_pool.loc[:, ~raw_pool.columns.duplicated()]
        
        raw_pool.to_parquet(
            output_path, 
            compression='zstd',
            index=False
        )
        print(f"🎉 原始因子合成完毕！总规模: {len(raw_pool):,} 行 x {len(raw_pool.columns)} 列")

if __name__ == "__main__":
    # 配置你的实际路径
    RAW_DATA = r"D:\量化平台\QuantFlow_Lab\data\derived\ready_to_factor_data.parquet"
    OUTPUT_DIR = r"D:\量化平台\QuantFlow_Lab\data\factors"

    factory = QuantFlowFactory(RAW_DATA, OUTPUT_DIR)
    factory.produce()