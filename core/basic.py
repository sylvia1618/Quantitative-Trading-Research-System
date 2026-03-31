import pandas as pd
from pathlib import Path

def update_benchmark_with_next_day_ret(file_path):
    path = Path(file_path)
    if not path.exists():
        print(f"❌ 找不到文件: {path}")
        return

    # 1. 读取数据
    df = pd.read_parquet(path)
    print(f"--- 正在处理: {path.name} ---")
    
    # 2. 预处理：确保日期是索引且升序排列
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df = df.set_index('date')
    else:
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()

    # 3. 计算次日收益率 (next_ret)
    # 逻辑：将 T+1 日的收盘价涨幅 挪到 T 日那一行，消除回测时的“未来函数”直觉误区
    if 'close' in df.columns:
        # 先计算当日涨跌幅：(今日收盘 / 昨日收盘) - 1
        # 然后使用 shift(-1) 向上平移一行
        df['next_ret'] = df['close'].pct_change().shift(-1)
    else:
        print(f"⚠️ 文件 {path.name} 缺少 'close' 列，无法计算！")
        return

    # 4. 清洗：最后一行因为没有后一天的价格，会是 NaN，填充为 0
    df['next_ret'] = df['next_ret'].fillna(0)

    # 5. 打印校验
    print("📅 校验（最后3天数据）：")
    print(df[['close', 'next_ret']].tail(3))
    
    # 6. 保存回原文件 (原地覆盖)
    df.to_parquet(path)
    print(f"✅ 次日收益率 'next_ret' 已存入: {path}\n")

# --- 严格匹配你的实际路径 ---
BASE_DIR = Path(r"D:\量化平台\QuantFlow_Lab\data")

# 拼接子文件夹 (根据你的目录习惯，000852 通常放在 sz 文件夹)
path_300 = BASE_DIR / "sh" / "000300.parquet"
path_905 = BASE_DIR / "sz" / "000905.parquet"
path_852 = BASE_DIR / "sz" / "000852.parquet"  # 中证1000

# 执行处理
update_benchmark_with_next_day_ret(path_300)
update_benchmark_with_next_day_ret(path_905)
update_benchmark_with_next_day_ret(path_852)