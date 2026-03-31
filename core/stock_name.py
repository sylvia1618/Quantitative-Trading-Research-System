import akshare as ak
import pandas as pd
from pathlib import Path

def update_stock_info():
    # 抓取全A股实时行情数据（包含代码和名字）
    df_info = ak.stock_zh_a_spot_em()
    # 只保留代码和名称，代码需要处理成 6 位字符串
    df_info = df_info[['代码', '名称']]
    df_info.columns = ['code', 'name']
    
    # 保存到你的项目数据目录
    save_path = Path(r"D:\量化平台\QuantFlow_Lab\data\all_stock_names.parquet")
    df_info.to_parquet(save_path)
    print(f"✅ 股票名称库已更新，存至: {save_path}")

# 建议手动运行一次这个函数
# update_stock_info()