import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 设置中文显示（Windows 常见字体）
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# --- 路径配置 ---
RAW_DIR = Path(r"D:\量化平台\QuantFlow_Lab\data\raw")
DATA_FILE = RAW_DIR / "full_feature_data.parquet"
IND_FILE = RAW_DIR / "industry_map.parquet"

def run_backtest():
    print("🔄 正在加载百万级数据并计算回测...")
    df = pd.read_parquet(DATA_FILE)
    df_ind = pd.read_parquet(IND_FILE)
    
    # 1. 数据对齐与预处理
    df['date'] = pd.to_datetime(df['date'])
    df = pd.merge(df, df_ind[['code', 'industry']], on='code', how='left')
    df['peTTM'] = pd.to_numeric(df['peTTM'], errors='coerce')
    df['pctChg'] = pd.to_numeric(df['pctChg'], errors='coerce') / 100 # 转为小数
    
    # 2. 定义调仓日（每个月的最后一个交易日）
    trade_dates = df['date'].unique()
    trade_dates = np.sort(trade_dates)
    # 简单模拟：每月选一次
    monthly_dates = df.groupby(df['date'].dt.to_period('M'))['date'].max().tolist()
    
    strategy_returns = []
    market_returns = []
    
    # 3. 模拟轮动过程
    print("⏳ 开始模拟历史调仓...")
    for i in range(len(monthly_dates) - 1):
        current_date = monthly_dates[i]
        next_month_end = monthly_dates[i+1]
        
        # A. 选股：当前日期行业内 PE 最低的前 2 名
        today_data = df[df['date'] == current_date].copy()
        # 过滤亏损股
        today_data = today_data[today_data['peTTM'] > 0]
        
        # 分行业选股
        selected = today_data.groupby('industry').apply(
            lambda x: x.nsmallest(2, 'peTTM'), include_groups=False
        ).reset_index()
        
        # B. 计算选出的组合在“下个月”的平均收益
        # 寻找这些股票在下个月每一天的收益
        selected_codes = selected['code'].tolist()
        next_month_data = df[(df['date'] > current_date) & (df['date'] <= next_month_end)]
        
        # 组合收益率（简单平均）
        portfolio_ret = next_month_data[next_month_data['code'].isin(selected_codes)].groupby('date')['pctChg'].mean()
        # 全市场收益率（基准）
        market_ret = next_month_data.groupby('date')['pctChg'].mean()
        
        strategy_returns.append(portfolio_ret)
        market_returns.append(market_ret)

    # 4. 计算累计收益率
    strat_df = pd.concat(strategy_returns)
    mkt_df = pd.concat(market_returns)
    
    cum_strat = (1 + strat_df).cumprod()
    cum_mkt = (1 + mkt_df).cumprod()
    
    # 5. 可视化
    plt.figure(figsize=(12, 6))
    cum_strat.plot(label='行业低PE组合 (策略)', color='red', linewidth=2)
    cum_mkt.plot(label='800只股票平均 (基准)', color='gray', linestyle='--')
    plt.title('分行业低估值轮动策略：历史累计收益 (2020-2026)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    output_path = RAW_DIR / "backtest_result.png"
    plt.savefig(output_path)
    print(f"\n📈 回测完成！收益曲线图已保存至: {output_path}")
    print(f"💰 策略最终累计收益: {cum_strat.iloc[-1]:.2%}")
    print(f"📊 基准最终累计收益: {cum_mkt.iloc[-1]:.2%}")

if __name__ == "__main__":
    run_backtest()