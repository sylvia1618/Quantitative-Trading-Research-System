import baostock as bs  
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
import os

# 配置常量保持不变
START_DATE = "2020-01-01"
END_DATE   = "2026-03-17"
DATA_DIR   = Path("data")

# ==============================
# 1. 将所有逻辑封装进函数，不要让它们“裸奔”
# ==============================

def get_all_stocks():
    """获取股票列表逻辑"""
    for i in range(3):
        rs = bs.query_all_stock(day="2024-12-31")
        data = []
        while rs.next():
            data.append(rs.get_row_data())
        
        if len(data) > 0:
            df = pd.DataFrame(data, columns=rs.fields)
            df = df[df['code'].str.startswith(('sh.', 'sz.'))]
            df = df[~df['code'].str.contains('bj')]
            return df
        
        print(f"⚠️ 获取股票列表失败，第{i+1}次重试")
        bs.logout()
        time.sleep(1)
        bs.login()
    raise Exception("❌ 获取股票列表失败")

def download_and_save(code):
    """单股票下载逻辑"""
    try:
        rs = bs.query_history_k_data_plus(
            code,
            "date,open,high,low,close,volume,amount",
            start_date=START_DATE,
            end_date=END_DATE,
            frequency="d",
            adjustflag="2"
        )
        data = []
        while rs.next():
            data.append(rs.get_row_data())
        if len(data) == 0: return
        
        df = pd.DataFrame(data, columns=rs.fields)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        market, symbol = code.split('.')
        path = DATA_DIR / market / f"{symbol}.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Windows下rename前先删除旧文件，防止 WinError 183
        tmp_path = str(path) + ".tmp"
        df.to_parquet(tmp_path, compression='snappy', index=False)
        if path.exists():
            os.remove(path)
        os.rename(tmp_path, path)
        
    except Exception as e:
        print(f"❌ {code} 失败:", e)

# ==============================
# 2. 定义统一的入口函数
# ==============================
def main():
    """这是真正执行同步的入口"""
    print("🚀 启动数据同步引擎...")
    bs.login()
    
    try:
        stocks_df = get_all_stocks()
        stocks = stocks_df['code'].tolist()
        print("股票总数:", len(stocks))

        for code in tqdm(stocks, desc="同步行情"):
            market, symbol = code.split('.')
            path = DATA_DIR / market / f"{symbol}.parquet"
            
            # 断点续传逻辑
            if path.exists():
                continue
            
            download_and_save(code)
            time.sleep(0.05) # 稍微加速
            
    finally:
        bs.logout()
        print("✅ 数据引擎作业完成")

# ==============================
# 3. 关键保护锁：只有直接运行此脚本才会执行
# ==============================
if __name__ == "__main__":
    main()