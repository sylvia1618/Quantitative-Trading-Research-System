import akshare as ak
import pandas as pd
import numpy as np
from pathlib import Path

DATA_PATH = Path("../data")
RAW_PATH = DATA_PATH / "raw"
DERIVED_PATH = DATA_PATH / "derived"

print("🚀 使用 AkShare 构建市值数据")

# 读取股票池
close = pd.read_parquet(RAW_PATH / "close.parquet")
symbols = close.columns.tolist()

print("股票数量:", len(symbols))

# 获取实时A股数据
spot = ak.stock_zh_a_spot_em()

print("AkShare字段:", spot.columns)

# 列名统一
spot = spot.rename(columns={
    "代码": "code",
    "总市值": "total_mv",
    "流通市值": "float_mv",
    "总市值(元)": "total_mv",
    "流通市值(元)": "float_mv"
})

# 转数值
spot["total_mv"] = pd.to_numeric(spot["total_mv"], errors="coerce")
spot["float_mv"] = pd.to_numeric(spot["float_mv"], errors="coerce")

# 代码格式转换
def convert_code(code):

    if code.startswith(("600","601","603","605","688")):
        return "sh." + code
    else:
        return "sz." + code

spot["code"] = spot["code"].astype(str).apply(convert_code)
spot = spot.set_index("code")

# 构建矩阵
dates = close.index

float_mv_matrix = pd.DataFrame(index=dates, columns=symbols)
total_mv_matrix = pd.DataFrame(index=dates, columns=symbols)

for s in symbols:

    if s in spot.index:

        float_mv_matrix[s] = spot.loc[s,"float_mv"]
        total_mv_matrix[s] = spot.loc[s,"total_mv"]

# 填充
float_mv_matrix = float_mv_matrix.ffill()
total_mv_matrix = total_mv_matrix.ffill()

# 保存
float_mv_matrix.to_parquet(RAW_PATH / "float_mv.parquet")
total_mv_matrix.to_parquet(RAW_PATH / "total_mv.parquet")

print("✅ float_mv.parquet 已生成")
print("✅ total_mv.parquet 已生成")

# log市值
log_mv = np.log(float_mv_matrix.replace(0,np.nan))

log_mv.to_parquet(DERIVED_PATH / "log_mv.parquet")

print("✅ log_mv.parquet 已生成")

print("🏁 完成")