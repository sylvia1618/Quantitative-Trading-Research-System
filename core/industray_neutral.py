import pandas as pd
import numpy as np
from pathlib import Path

# --- 配置路径 ---
RAW_DIR = Path(r"D:\量化平台\QuantFlow_Lab\data\raw")
DATA_FILE = RAW_DIR / "full_feature_data.parquet"
IND_FILE = RAW_DIR / "industry_map.parquet"

def sector_analysis_v2():
    # 1. 加载数据
    df = pd.read_parquet(DATA_FILE)
    df_ind = pd.read_parquet(IND_FILE)
    
    # 2. 提取最新数据并合并
    latest_date = df['date'].max()
    print(f"📅 正在分析日期: {latest_date}")
    
    today_df = df[df['date'] == latest_date].copy()
    today_df = pd.merge(today_df, df_ind[['code', 'industry']], on='code', how='left')
    
    # 3. 核心清洗：强制转换并剔除无效项
    today_df['peTTM'] = pd.to_numeric(today_df['peTTM'], errors='coerce')
    # 过滤掉 PE <= 0 (亏损) 和 没有行业信息的股票
    valid_df = today_df[(today_df['peTTM'] > 0) & (today_df['industry'].notna())].copy()
    
    print(f"📊 有效样本数: {len(valid_df)} (剔除了亏损股和无行业标签股)")
    
    if valid_df.empty:
        print("❌ 错误：有效样本为 0。请检查 peTTM 字段是否有数据。")
        print("PE 数据预览：", today_df['peTTM'].head())
        return

    # 4. 分行业找“最便宜”的前 3 名 (消除警告的新写法)
    # 使用 group_keys=False 配合 nsmallest
    top_value_in_sector = valid_df.groupby('industry', group_keys=False).apply(
        lambda x: x.nsmallest(3, 'peTTM'), include_groups=True
    ).reset_index(drop=True)
    
    # 5. 展示所有行业的统计 (不设白名单)
    print("\n💡 全行业低估值名单预览 (Top 3 per sector):")
    # 按照 PE 从低到高排，看看谁才是全市场的价值洼地
    result = top_value_in_sector.sort_values('peTTM')
    
    print(result[['industry', 'code', 'peTTM', 'close', 'pctChg']].head(20))

if __name__ == "__main__":
    sector_analysis_v2()