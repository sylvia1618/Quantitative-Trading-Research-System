import pandas as pd
from pathlib import Path

# 1. 定位行情表 (只改这个文件)
PRICE_PATH = Path(r"D:\量化平台\QuantFlow_Lab\data\derived\clean_factor_data.parquet")

print("正在读取行情数据...")
df = pd.read_parquet(PRICE_PATH)

# 2. 确保排序 (计算 shift 的前提)
df = df.sort_values(['code', 'date'])

print("正在追加多周期收益率标签...")
# 计算未来 N 日收益率
# 公式: (T+N日收盘价 / T日收盘价) - 1
df['ret_1d']  = df.groupby('code')['close'].shift(-1) / df.close - 1
df['ret_5d']  = df.groupby('code')['close'].shift(-5) / df.close - 1
df['ret_10d'] = df.groupby('code')['close'].shift(-10) / df.close - 1
df['ret_20d'] = df.groupby('code')['close'].shift(-20) / df.close - 1

# 3. 原位保存覆盖
df.to_parquet(PRICE_PATH, compression='snappy', index=False)
print("✅ 收益率标签追加完成！因子表无需重算。")