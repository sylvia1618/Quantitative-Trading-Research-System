import pandas as pd
import numpy as np
from pathlib import Path

class VectorizedBacktester:
    def __init__(self, df, path_300=None, path_905=None, path_1000=None, signal_col='FINAL_SCORE', buy_count=50):
        """
        ✨ 修正：增加了 path_1000 支持
        """
        self.df = df.copy()
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.signal_col = signal_col
        self.buy_count = buy_count
        self.path_300 = Path(path_300) if path_300 else None
        self.path_905 = Path(path_905) if path_905 else None
        self.path_1000 = Path(path_1000) if path_1000 else None

    def _load_bench_ret(self, path):
        if path is None or not path.exists():
            return None
        try:
            bench = pd.read_parquet(path)
            if 'date' in bench.columns:
                bench = bench.set_index('date')
            bench.index = pd.to_datetime(bench.index)
            
            # 优先取预处理好的 next_ret (T+1收益)
            if 'next_ret' in bench.columns:
                return bench[['next_ret']].rename(columns={'next_ret': 'ret'})
            elif 'ret' in bench.columns:
                return bench[['ret']]
            elif 'close' in bench.columns:
                # 兜底计算：如果是当日 close，通过 shift(-1) 转换为 T+1 收益
                return bench['close'].pct_change().shift(-1).fillna(0).to_frame(name='ret')
            return None
        except Exception as e:
            print(f"加载基准失败 {path}: {e}")
            return None

    def run_backtest(self):
        # 1. 基础数据清理
        self.df = self.df.dropna(subset=[self.signal_col, 'ret_1d'])
        
        # 2. 选股与计算策略每日收益率 (T+1)
        self.df['rank'] = self.df.groupby('date')[self.signal_col].rank(ascending=False, method='first')
        self.df['is_holding'] = (self.df['rank'] <= self.buy_count).astype(int)
        daily_ret = self.df[self.df['is_holding'] == 1].groupby('date')['ret_1d'].mean().fillna(0)
        
        # 3. 计算换手率
        hold_matrix = self.df.pivot(index='date', columns='code', values='is_holding').fillna(0)
        turnover = hold_matrix.diff().abs().sum(axis=1) / (self.buy_count * 2)
        
        # 4. 初始化结果表
        res = pd.DataFrame({
            'daily_return': daily_ret, 
            'turnover': turnover.fillna(0)
        })

        # 5. 合并基准收益率并计算累计净值与超额 (✨ 增加 1000 指数映射)
        bench_map = [
            (self.path_300, 'ret_300', 'cum_hs300', 'alpha_300_daily', 'cum_alpha_300'),
            (self.path_905, 'ret_905', 'cum_zz500', 'alpha_905_daily', 'cum_alpha_500'),
            (self.path_1000, 'ret_1000', 'cum_zz1000', 'alpha_1000_daily', 'cum_alpha_1000')
        ]
        
        for path, r_col, c_col, a_d_col, a_c_col in bench_map:
            b_data = self._load_bench_ret(path)
            if b_data is not None:
                res = res.join(b_data.rename(columns={'ret': r_col}), how='left').fillna(0)
                # 计算基准累计净值
                res[c_col] = (1 + res[r_col]).cumprod()
                # 计算每日超额收益率与累计超额净值
                res[a_d_col] = res['daily_return'] - res[r_col]
                res[a_c_col] = (1 + res[a_d_col]).cumprod()

        # 6. 【统一口径】策略累计净值
        # 插入 T-1 日初始行，确保曲线从 1.0 开始
        if not res.empty:
            first_date = res.index.min()
            initial_row = pd.DataFrame(0.0, index=[first_date - pd.Timedelta(days=1)], columns=res.columns)
            res = pd.concat([initial_row, res]).sort_index()
            res['cum_return'] = (1 + res['daily_return']).cumprod()
            
        return res

    def compute_metrics(self, results):
        """
        ✨ 修正：统一了超额收益指标的列名读取逻辑
        """
        if results.empty: return {}
        
        # 剔除初始 1.0 占位行，避免天数计算错误
        valid_res = results[results['daily_return'] != 0].copy()
        if valid_res.empty: valid_res = results
            
        d_rets = valid_res['daily_return']
        cum_rets = valid_res['cum_return']
        num_days = len(valid_res)
        
        # 基础指标计算
        total_ret = cum_rets.iloc[-1] - 1
        ann_ret = (cum_rets.iloc[-1] ** (242 / num_days)) - 1 if num_days > 0 else 0
        sharpe = (d_rets.mean() / d_rets.std()) * np.sqrt(242) if d_rets.std() != 0 else 0
        max_dd = (cum_rets / cum_rets.cummax() - 1).min()
        
        m = {
            "累计收益": f"{total_ret:.2%}",
            "年化收益": f"{ann_ret:.2%}",
            "夏普比率": f"{sharpe:.2f}",
            "最大回撤": f"{max_dd:.2%}",
            "平均换手": f"{valid_res['turnover'].mean():.2%}",
            "交易天数": int(num_days)
        }
        
        # ✨ 动态添加不同基准的超额指标
        bench_metrics = [
            ('alpha_300_daily', '超额年化(vs300)'),
            ('alpha_905_daily', '超额年化(vs500)'),
            ('alpha_1000_daily', '超额年化(vs1000)')
        ]
        
        for col, label in bench_metrics:
            if col in valid_res.columns:
                a_rets = valid_res[col]
                m[label] = f"{a_rets.mean() * 242:.2%}"
                # 如果是主要对比基准，计算信息比率 (IR)
                ir = (a_rets.mean() / a_rets.std()) * np.sqrt(242) if a_rets.std() != 0 else 0
                m[f"IR({label.split('vs')[-1][:-1]})"] = f"{ir:.2f}"
            
        return m