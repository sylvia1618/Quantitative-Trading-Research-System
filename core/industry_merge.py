import pandas as pd
from pathlib import Path

# --- 配置 ---
BASE_DIR = Path(r"D:\量化平台\QuantFlow_Lab")
DATA_DIR = BASE_DIR / "data"
MASTER_PATH = DATA_DIR / "derived" / "clean_factor_data.parquet"
INDUSTRY_PATH = BASE_DIR / "data" / "industry_mapping.csv" # 请确认你的映射表路径D:\量化平台\QuantFlow_Lab\data\industry_mapping.csv

def merge_industry_info():
    print("📖 正在加载全市场大表...")
    df = pd.read_parquet(MASTER_PATH)
    
    print("📂 正在加载申万行业映射表...")
    # 假设 csv 包含列: code, industry_name
    df_ind = pd.read_csv(INDUSTRY_PATH)
    
    # 强制确保 code 列格式一致 (防止 sh.600000 和 600000 匹配不上)
    # 如果你的 csv 里只有 600000，需要补全前缀，但如果你之前存的就是标准格式则忽略
    
    print("🔗 正在执行行业挂载 (Merge)...")
    # 使用 left join，确保即使没行业信息的个股也不被删除（会被填为 NaN）
    df_final = pd.merge(df, df_ind[['code', 'industry']], on='code', how='left')
    
    # 填充缺失行业为 "未知"
    df_final['industry'] = df_final['industry'].fillna("未知")
    
    # 🚀 优化：行业名重复率极高，转为 category 节省内存
    df_final['industry'] = df_final['industry'].astype('category')
    
    output_path = DATA_DIR / "derived" / "clean_factor_data_with_ind.parquet"
    print(f"💾 正在保存带行业属性的新大表...")
    df_final.to_parquet(output_path, compression='zstd', index=False)
    
    print(f"✅ 挂载成功！")
    print(f"📊 覆盖率检查: {(df_final['industry'] != '未知').sum() / len(df_final):.2%} 的数据已匹配到行业")

if __name__ == "__main__":
    merge_industry_info()