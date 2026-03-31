import baostock as bs
import pandas as pd
from tqdm import tqdm
from pathlib import Path
import time
import random

# --- 路径配置 ---
BASE_DIR = Path(__file__).resolve().parent.parent
SAVE_PATH = BASE_DIR / "data" / "raw"
SAVE_PATH.mkdir(parents=True, exist_ok=True)

# --- 抓取配置 ---
START_DATE = "2020-01-01"
END_DATE = "2026-03-12"
EXTRA_FIELDS = "date,code,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST"

def download_chunk(stock_list):
    """尝试下载一小批数据"""
    chunk_results = []
    # 每一批开始前都重新登录，确保连接新鲜
    bs.login()
    
    for code in stock_list:
        try:
            rs = bs.query_history_k_data_plus(
                code, EXTRA_FIELDS,
                start_date=START_DATE, end_date=END_DATE,
                frequency="d", adjustflag="2"
            )
            
            if rs.error_code == "0":
                rows = []
                while rs.next():
                    rows.append(rs.get_row_data())
                if rows:
                    chunk_results.append(pd.DataFrame(rows, columns=rs.fields))
            # 哪怕是单线程，每只票也必须歇一下，防止触发防火墙
            time.sleep(0.5) 
        except Exception:
            continue
            
    bs.logout()
    return chunk_results

def main():
    print(f"🛠️ 启动「超稳健」下载模式 | 目标: {SAVE_PATH}")
    
    # 1. 获取名单
    bs.login()
    hs300 = bs.query_hs300_stocks().get_data()
    zz500 = bs.query_zz500_stocks().get_data()
    stocks = pd.concat([hs300, zz500])["code"].drop_duplicates().tolist()
    bs.logout()
    
    print(f"📋 待处理股票总数: {len(stocks)}")
import baostock as bs
import pandas as pd
from tqdm import tqdm
from pathlib import Path
import time

# --- 配置 ---
START_DATE = "2020-01-01"
END_DATE = "2026-03-12"
BASE_DIR = Path(__file__).resolve().parent.parent
SAVE_PATH = BASE_DIR / "data" / "raw"
SAVE_PATH.mkdir(parents=True, exist_ok=True)

# 将字段拆开，降低服务器单次查询压力
# 我们先尝试获取最核心的三个：涨跌幅、PE、PB
CORE_FIELDS = "date,code,pctChg,peTTM,pbMRQ"

def download_safe(code):
    """极致稳定的单只下载逻辑"""
    # 失败重试次数
    for attempt in range(2):
        try:
            rs = bs.query_history_k_data_plus(
                code, CORE_FIELDS,
                start_date=START_DATE, end_date=END_DATE,
                frequency="d", adjustflag="2"
            )
            if rs.error_code == "0":
                data = []
                while rs.next():
                    data.append(rs.get_row_data())
                if data:
                    return pd.DataFrame(data, columns=rs.fields)
            # 如果报错，多歇会儿
            time.sleep(1)
        except:
            time.sleep(2)
    return None

def main():
    print(f"🛠️ 进入「极限稳定模式」下载")
    bs.login()
    
    try:
        # 获取股票池
        stocks = bs.query_hs300_stocks().get_data()["code"].tolist()
        stocks += bs.query_zz500_stocks().get_data()["code"].tolist()
        stocks = list(set(stocks))
        
        print(f"📋 目标股票: {len(stocks)} 只")
        
        results = []
        # 强制单线程运行，并且每 50 只股票重新登录一次
        for i, code in enumerate(tqdm(stocks, desc="📥 进度")):
            if i % 50 == 0 and i > 0:
                bs.logout()
                time.sleep(2)
                bs.login()
                
            df = download_safe(code)
            if df is not None:
                results.append(df)
            
            # 关键：每只股票下载完强制休息，给服务器喘气时间
            time.sleep(0.2)

        if results:
            final_df = pd.concat(results, ignore_index=True)
            # 转换格式
            for col in ["pctChg", "peTTM", "pbMRQ"]:
                final_df[col] = pd.to_numeric(final_df[col], errors="coerce")
            
            output_file = SAVE_PATH / "extra_valuation_data.parquet"
            final_df.to_parquet(output_file, index=False)
            print(f"\n✅ 成功保存至: {output_file}")
        else:
            print("❌ 未能获取任何有效数据。")

    finally:
        bs.logout()

if __name__ == "__main__":
    main()