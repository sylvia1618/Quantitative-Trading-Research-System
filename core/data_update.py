import baostock as bs  
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import datetime
import time

# --- 配置 ---
BASE_DIR = Path(r"D:\量化平台\QuantFlow_Lab")
DATA_DIR = BASE_DIR / "data"
TARGET_DATE = "2026-03-24"

def sync_and_standardize():
    # 1. 登录并增加超时重试逻辑
    print("🔐 正在连接 Baostock 服务器...")
    lg = bs.login()
    if lg.error_code != '0':
        print(f"❌ 登录失败: {lg.error_msg}")
        return

    # 2. 统计总文件数用于主进度条
    all_files = list(DATA_DIR.glob("sh/*.parquet")) + list(DATA_DIR.glob("sz/*.parquet"))
    total_count = len(all_files)
    print(f"📊 检测到本地共有 {total_count} 个股票文件，准备开始增量同步...")

    # 3. 使用单个大进度条遍历所有文件
    with tqdm(total=total_count, desc="🚀 总体同步进度", unit="股") as pbar:
        for market_prefix in ['sh', 'sz']:
            folder = DATA_DIR / market_prefix
            if not folder.exists(): 
                continue
            
            files = list(folder.glob("*.parquet"))
            for file_path in files:
                symbol = file_path.stem
                standard_code = f"{market_prefix}.{symbol}"
                
                # 更新进度条左侧的文字描述
                pbar.set_postfix_str(f"当前: {standard_code}")
                
                process_single_file(file_path, standard_code)
                
                # 每完成一只股，进度条前进一格
                pbar.update(1)

    bs.logout()
    print("\n✅ 所有个股文件已完成【代码注入】与【数据更新】！")

def process_single_file(path, standard_code):
    try:
        # 1. 读取旧数据
        df_old = pd.read_parquet(path)
        
        if df_old.index.name == 'date':
            df_old = df_old.reset_index()
        
        # 统一代码格式
        df_old['code'] = standard_code
        df_old['date'] = pd.to_datetime(df_old['date'])
        last_date = df_old['date'].max()
        
        # 检查是否需要更新
        if last_date >= pd.to_datetime(TARGET_DATE):
            # 即使不需要更新日期，如果没转过 category 也要转一下存回去
            if df_old['code'].dtype.name != 'category':
                df_old['code'] = df_old['code'].astype('category')
                df_old.to_parquet(path, index=False, compression='snappy')
            return

        # 2. 增量下载
        start_date = (last_date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        fields = "date,open,high,low,close,volume,amount,turn,pctChg,isST,pbMRQ,peTTM"
        
        rs = bs.query_history_k_data_plus(
            standard_code, fields,
            start_date=start_date, end_date=TARGET_DATE,
            frequency="d", adjustflag="2"
        )
        
        new_rows = []
        if rs is not None:
            while rs.next():
                new_rows.append(rs.get_row_data())
            
        # 3. 合并与保存
        if new_rows:
            df_new = pd.DataFrame(new_rows, columns=fields.split(','))
            df_new['code'] = standard_code
            
            # 类型转换
            f32_cols = ['open', 'high', 'low', 'close', 'turn', 'pctChg', 'pbMRQ', 'peTTM']
            df_new[f32_cols] = df_new[f32_cols].apply(pd.to_numeric, errors='coerce').astype('float32')
            df_new[['volume', 'amount']] = df_new[['volume', 'amount']].apply(pd.to_numeric, errors='coerce').astype('float64')
            df_new['isST'] = pd.to_numeric(df_new['isST'], errors='coerce').fillna(0).astype('int8')
            df_new['date'] = pd.to_datetime(df_new['date'])

            df_final = pd.concat([df_old, df_new], ignore_index=True).drop_duplicates('date')
        else:
            df_final = df_old

        # 强制转为 category 节省空间
        df_final['code'] = df_final['code'].astype('category')
        df_final.to_parquet(path, index=False, compression='snappy')

    except Exception as e:
        # 如果报错，不中断程序，只记录
        with open("error_log.txt", "a") as f:
            f.write(f"{datetime.datetime.now()} - {standard_code}: {str(e)}\n")

if __name__ == "__main__":
    sync_and_standardize()