import pandas as pd
from pathlib import Path

# --- 路径配置 ---
INPUT_FILE = Path(r"D:\量化平台\QuantFlow_Lab\data\derived\clean_factor_data_with_ind.parquet")
OUTPUT_FILE = Path(r"D:\量化平台\QuantFlow_Lab\data\derived\ready_to_factor_data.parquet")

def start_cleaning():
    print(f"📖 正在加载数据: {INPUT_FILE.name}...")
    df = pd.read_parquet(INPUT_FILE)
    orig_count = len(df)

    # 1. 🛑 剔除停牌 (成交量为0的行)
    # 量化回测中，停牌股无法买入也无法卖出，必须剔除
    df = df[df['volume'] > 0].copy()
    
    # 2. 🛡️ 剔除 ST (风险股)
    # 处理逻辑：明确为 1 的删掉，NaN 或 0 的保留（防止误删）
    if 'isST' in df.columns:
        df = df[df['isST'] != 1]
    
    # 3. 🐣 剔除上市不满 180 天的次新股
    # 逻辑：按代码分组，取每个代码序号 >= 180 的行
    print("⏳ 正在计算上市天数并剔除次新股...")
    df = df.sort_values(['code', 'date'])
    df['count'] = df.groupby('code').cumcount()
    df = df[df['count'] >= 180].drop(columns=['count'])

    # 4. 📉 剔除价格过低的股票 (低于 2.0 元)
    # 低价股往往伴随面值退市风险，不具备统计规律
    df = df[df['close'] > 2.0]

    final_count = len(df)
    removed = orig_count - final_count
    
    print("-" * 30)
    print(f"✅ 清洗完毕！")
    print(f"📉 原始记录: {orig_count}")
    print(f"✨ 剩余记录: {final_count}")
    print(f"🗑️ 剔除比例: {removed / orig_count:.2%}")
    
    # 存盘
    print(f"💾 正在保存至: {OUTPUT_FILE}")
    df.to_parquet(OUTPUT_FILE, compression='zstd', index=False)

if __name__ == "__main__":
    start_cleaning()