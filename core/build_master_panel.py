import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import re

def load_single_parquet(path):
    """高效读取单个文件并实施物理隔绝"""
    try:
        df = pd.read_parquet(path)
        if df.empty: return None

        # 1. 物理隔绝
        code_sample = str(df['code'].iloc[0])
        if not re.match(r'^(sh\.6|sz\.[03])', code_sample):
            return None

        # 2. 🚀 强制类型对齐 (解决报错的关键)
        # 对成交量和成交额强制转为 float64 (避免科学计数法导致的 str 误判)
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce').astype('float64')
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').astype('float64')

        # 对其他列强制转为 float32
        f32_cols = ['open', 'high', 'low', 'close', 'turn', 'pctChg', 'pbMRQ', 'peTTM']
        for col in f32_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('float32')

        # 对 isST 强制转为 int8
        if 'isST' in df.columns:
            df['isST'] = pd.to_numeric(df['isST'], errors='coerce').fillna(0).astype('int8')

        # 确保日期格式
        df['date'] = pd.to_datetime(df['date'])
        
        # 3. 确保 code 列是字符串/分类
        df['code'] = df['code'].astype('category')
        
        return df
    except Exception as e:
        print(f"⚠️ 文件 {path} 加载出错: {e}")
        return None

def build_master_panel():
    DATA_DIR = Path(r"D:\量化平台\QuantFlow_Lab\data")
    # 扫描所有文件
    all_files = list(DATA_DIR.glob("sh/*.parquet")) + list(DATA_DIR.glob("sz/*.parquet"))
    
    print(f"📦 正在筛选并准备合并 {len(all_files)} 个文件...")
    
    # 利用多线程读取
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(tqdm(executor.map(load_single_parquet, all_files), 
                           total=len(all_files), desc="读取与清洗"))
    
    # 过滤掉 None (指数和空文件)
    df_list = [r for r in results if r is not None]
    
    print(f"🔗 筛选完成，剩余个股: {len(df_list)}。正在进行全量拼接...")
    
    # 拼接
    full_df = pd.concat(df_list, ignore_index=True)
    
    # 排序：这是量化计算的生命线
    print("⏳ 正在进行全局排序 (Date & Code)...")
    full_df = full_df.sort_values(['date', 'code'])
    
    # 最终输出
    output_path = DATA_DIR / "derived" / "clean_factor_data.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"💾 正在写入磁盘 (使用 zstd 高级压缩)...")
    full_df.to_parquet(output_path, compression='zstd', index=False)
    
    print(f"✅ 合成成功！")
    print(f"📊 最终记录数: {len(full_df)}")
    print(f"📉 包含个股数: {full_df['code'].nunique()}")

if __name__ == "__main__":
    build_master_panel()