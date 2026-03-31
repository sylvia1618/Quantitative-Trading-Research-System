import pandas as pd
import numpy as np
import statsmodels.api as sm
from pathlib import Path
import time

class FactorProcessor:
    def __init__(self, input_path: str):
        self.input_path = Path(input_path)
        self.df = None
        self.factor_cols = []

    def load_data(self):
        print(f"📖 正在加载原始大表: {self.input_path}")
        self.df = pd.read_parquet(self.input_path)
        self.df = self.df.sort_values(['code', 'date'])
        self.factor_cols = [c for c in self.df.columns if c.startswith('FACTOR_')]
        
        # 💡 核心步骤：先生成代理市值 (基于成交额)
        print("📈 正在计算代理市值 (mcap_proxy)...")
        self.df['mcap_proxy'] = self.df.groupby('code')['amount'].transform(
            lambda x: x.rolling(20, min_periods=1).mean()
        )
        self.df['log_mcap'] = np.log1p(self.df['mcap_proxy']).fillna(0)
        return self

    def _mad_clip(self, s, n=3):
        """MAD 去极值逻辑"""
        median = s.median()
        mad = (s - median).abs().median()
        limit = n * 1.4826 * mad
        return s.clip(median - limit, median + limit)

    def _neutralize(self, group_df, y_name, use_ind=True, use_mcap=True):
        """截面中性化回归逻辑"""
        x_cols = []
        if use_mcap: x_cols.append('log_mcap')
        
        # 提取必要列
        needed = [y_name] + x_cols + (['industry'] if use_ind else [])
        data = group_df[needed].dropna()
        
        if len(data) < 30: return group_df[y_name]
        
        y = data[y_name]
        X = data[x_cols].copy() if x_cols else pd.DataFrame(index=data.index)
        
        if use_ind:
            # 行业 One-hot 编码
            ind_dummies = pd.get_dummies(data['industry'], drop_first=True)
            X = pd.concat([X, ind_dummies], axis=1)
            
        X = sm.add_constant(X.astype(float))
        model = sm.OLS(y, X).fit()
        
        res = pd.Series(np.nan, index=group_df.index)
        res.loc[data.index] = model.resid
        return res

    def run_pipeline(self, output_name: str, neutralized: bool = False):
        """执行清洗流水线"""
        start_t = time.time()
        print(f"\n🚀 开始生成: {output_name} (中性化={neutralized})")
        
        # 复制一份数据进行加工，不影响原始 df
        working_df = self.df.copy()
        
        for col in self.factor_cols:
            print(f"   ∟ 正在加工: {col}")
            
            # 1. 截面去极值 (MAD)
            working_df[col] = working_df.groupby('date')[col].transform(self._mad_clip)
            
            # 2. 中性化 (如果开启)
            if neutralized:
                working_df[col] = working_df.groupby('date').apply(
                    lambda x: self._neutralize(x, col)
                ).reset_index(level=0, drop=True)
                
            # 3. 截面标准化 (Z-Score)
            working_df[col] = working_df.groupby('date')[col].transform(
                lambda x: (x - x.mean()) / (x.std() + 1e-8)
            )

        # 保存结果
        out_path = self.input_path.parent / f"{output_name}.parquet"
        working_df.to_parquet(out_path, compression='zstd', index=False)
        print(f"✅ 已保存至: {out_path} (耗时: {time.time()-start_t:.2f}s)")

if __name__ == "__main__":
    RAW_POOL = r"D:\量化平台\QuantFlow_Lab\data\factors\raw_factors_pool.parquet"
    
    # 初始化处理器
    proc = FactorProcessor(RAW_POOL).load_data()
    
    # 1. 生成仅去极值+标准化的版本 (Raw)
    proc.run_pipeline("refined_raw", neutralized=False)
    
    # 2. 生成中性化版本 (Neutralized)
    proc.run_pipeline("refined_neutralized", neutralized=True)
    
    print("\n🎉 所有精炼工作已完成！你可以开始在 Streamlit 中对比分析了。")