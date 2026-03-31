import pandas as pd
import numpy as np
from pathlib import Path

class FactorAuditor:
    def __init__(self, df: pd.DataFrame, factor_col: str, ret_col: str = 'ret_5d', 
                 start_date=None, end_date=None):
        """
        因子审计核心引擎 (增强版：支持时间切片)
        """
        # 1. 确保日期格式正确
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        # 2. 时间区间过滤
        mask = pd.Series(True, index=df.index)
        if start_date:
            mask &= (df['date'] >= pd.to_datetime(start_date))
        if end_date:
            mask &= (df['date'] <= pd.to_datetime(end_date))
        
        filtered_df = df[mask].copy()
        
        # 3. 列选择与清洗
        cols = ['date', 'code', 'industry', factor_col, ret_col]
        # 动态寻找所有 ret_Xd 列
        ret_cols = [c for c in df.columns if c.startswith('ret_') and c.endswith('d')]
        all_cols = list(set(cols + ret_cols))
        
        # 排除不存在的列
        all_cols = [c for c in all_cols if c in filtered_df.columns]
        
        self.df = filtered_df[all_cols].dropna(subset=[factor_col, ret_col]).copy()
        self.factor = factor_col
        self.ret = ret_col
        self._ic_series = None
        
        # 保存区间信息
        self.audit_range = {
            "start": filtered_df['date'].min() if not filtered_df.empty else None,
            "end": filtered_df['date'].max() if not filtered_df.empty else None,
            "count": len(filtered_df['date'].unique())
        }

    def _safe_spearman(self, group):
        f_val = group[self.factor]
        r_val = group[self.ret]
        if f_val.nunique() <= 1 or r_val.nunique() <= 1:
            return np.nan
        return f_val.corr(r_val, method='spearman')

    def calc_ic(self):
        if self._ic_series is None:
            if self.df.empty:
                return pd.Series(dtype=float)
            # include_groups=False 适配 Pandas 2.2+
            ic = self.df.groupby('date').apply(self._safe_spearman, include_groups=False)
            self._ic_series = ic.dropna()
        return self._ic_series

    def calc_ic_stats(self):
        ic = self.calc_ic()
        if ic.empty:
            return ic, {k: 0.0 for k in ["IC Mean", "IC Std", "ICIR", "IC > 0", "t-stat"]}
        
        mean = ic.mean()
        std = ic.std()
        n = len(ic)
        
        return ic, {
            "IC Mean": float(mean),
            "IC Std": float(std),
            "ICIR": float(mean / std) if std > 1e-10 else 0.0,
            "IC > 0": float((ic > 0).mean()),
            "t-stat": float(mean / (std / np.sqrt(n))) if std > 1e-10 else 0.0,
        }

    def calc_quantile_analysis(self, q=5):
        if self.df.empty:
            return pd.DataFrame(), pd.Series(dtype=float)
            
        df = self.df[['date', self.factor, self.ret]].copy()
        ic_mean = self.calc_ic().mean() if not self.calc_ic().empty else 0
        
        # 扰动处理防止 qcut 报错
        df[self.factor] += np.random.normal(0, 1e-12, len(df))
        
        df['group'] = df.groupby('date')[self.factor].transform(
            lambda x: pd.qcut(x, q, labels=False, duplicates='drop')
        )
        
        # 自动对齐：确保 Group 0 是最优组
        if ic_mean < 0:
            df['group'] = (q - 1) - df['group']
            
        group_ret = df.groupby(['date', 'group'])[self.ret].mean().unstack()
        
        if 0 in group_ret.columns and (q-1) in group_ret.columns:
            ls_ret = group_ret[0] - group_ret[q-1]
        else:
            ls_ret = pd.Series(0, index=group_ret.index)
            
        return group_ret, ls_ret

    def calc_decay(self, horizons=(1, 5, 10, 20)):
        res = {}
        for h in horizons:
            col = f'ret_{h}d'
            if col in self.df.columns:
                def _temp_corr(group):
                    if group[self.factor].nunique() <= 1 or group[col].nunique() <= 1:
                        return np.nan
                    return group[self.factor].corr(group[col], method='spearman')
                
                ic_val = self.df.groupby('date').apply(_temp_corr, include_groups=False).mean()
                res[f'{h}D'] = ic_val if pd.notna(ic_val) else 0.0
        return pd.Series(res)

    def full_report(self):
        """生成全维度审计报告"""
        if self.df.empty:
            raise ValueError("当前筛选条件下没有足够的有效数据")
            
        ic, ic_stats = self.calc_ic_stats()
        group_ret, ls_ret = self.calc_quantile_analysis()
        
        # 行业 IC 归因 (新增：方便在 UI 的 Tab 3 显示)
        industry_ic = self.df.groupby('industry').apply(
            lambda x: x[self.factor].corr(x[self.ret], method='spearman'),
            include_groups=False
        ).dropna()

        dist_stats = self.df.groupby('date')[self.factor].agg(['mean', 'std', 'skew'])
        
        return {
            "ic_series": ic,
            "ic_stats": ic_stats,
            "group_ret": group_ret,
            "long_short": ls_ret,
            "decay": self.calc_decay(),
            "rolling_ic": ic.rolling(60, min_periods=20).mean(),
            "industry_ic": industry_ic,
            "coverage": float(self.df[self.factor].notna().mean()),
            "distribution": {
                "Skewness": float(dist_stats['skew'].mean()),
                "Avg Std": float(dist_stats['std'].mean()),
                "Avg Mean": float(dist_stats['mean'].mean())
            }
        }

    # --- 注意：compare_periods 是静态方法，必须与 __init__ 同级 ---
    @staticmethod
    def compare_periods(df, factor_col, split_date, ret_col='ret_5d'):
        """🚀 实验区与禁区一键对比静态方法"""
        split_dt = pd.to_datetime(split_date)
        
        # 实验区审计
        in_sample = FactorAuditor(df, factor_col, ret_col, 
                                  end_date=split_dt - pd.Timedelta(days=1))
        # 禁区审计
        out_of_sample = FactorAuditor(df, factor_col, ret_col, 
                                      start_date=split_dt)
        
        _, stats_in = in_sample.calc_ic_stats()
        _, stats_out = out_of_sample.calc_ic_stats()
        
        comparison = pd.DataFrame({
            "实验区 (In-Sample)": stats_in,
            "禁区 (Out-of-Sample)": stats_out
        })
        
        # 计算变化率并处理除零情况
        def calc_change(row):
            ins = row["实验区 (In-Sample)"]
            oos = row["禁区 (Out-of-Sample)"]
            if abs(ins) < 1e-10: return "N/A"
            return f"{(oos / ins - 1):.2%}"

        comparison['变化率'] = comparison.apply(calc_change, axis=1)
        return comparison