import pandas as pd
import numpy as np
import os
from pathlib import Path

def factor_process_pro(df, factor_cols):
    """
    私募级标准化：自动剔除坏因子 + 强制二阶标准化
    """
    df = df.copy()
    
    # --- 第一步：剔除僵尸因子 ---
    # 计算非空比例，保留覆盖度 > 50% 的因子
    valid_cols = []
    for col in factor_cols:
        coverage = df[col].notnull().mean()
        if coverage > 0.5:
            valid_cols.append(col)
        else:
            print(f"🗑️ 剔除低质量因子: {col} (覆盖度仅 {coverage:.2%})")

    # --- 第二步：强制去重 ---
    # 如果同时存在 'bp' 和 'bp_zscore'，我们只选后缀带 zscore 的
    final_cols = []
    for col in valid_cols:
        if f"{col}_zscore" in valid_cols:
            continue
        final_cols.append(col)

    # --- 第三步：循环处理 ---
    for col in final_cols:
        # 数值转换
        df[col] = pd.to_numeric(df[col], errors='coerce').replace([np.inf, -np.inf], np.nan)
        
        # 1. 填充 (当天中位数 -> 全局中位数)
        global_med = df[col].median()
        df[col] = df.groupby('date')[col].transform(lambda x: x.fillna(x.median())).fillna(global_med)

        # 2. MAD 去极值
        def mad_clip(x):
            med = x.median()
            mad = (x - med).abs().median()
            limit = 3 * 1.4826 * mad
            return x.clip(med - limit, med + limit) if limit > 0 else x
        
        df[col] = df.groupby('date')[col].transform(mad_clip)

        # 3. 强制 Z-Score (确保 Mean=0, Std=1)
        def force_z(x):
            mu = x.mean()
            std = x.std(ddof=0)
            if std < 1e-8: 
                return x - mu # 即使标准差为0，也要把均值拉回到0
            return (x - mu) / std
            
        df[col] = df.groupby('date')[col].transform(force_z)

    # 只返回带 date, code 和 过滤后的因子列
    return df[['date', 'code'] + final_cols]

def aggregate_and_standardize(base_path, output_path):
    """
    自动化聚合 Parquet 因子并标准化
    """
    all_dfs = {}  # 使用字典通过 Key 去重
    base_dir = Path(base_path)
    
    print(f"🔍 正在扫描路径: {base_dir}")
    files = list(base_dir.rglob("*.parquet")) 
    
    if not files:
        print(f"❌ 错误：在目标路径下没找到任何 .parquet 文件！")
        return

    print(f"📂 发现 {len(files)} 个文件，开始去重读取...")
    
    for f in files:
        try:
            # 获取因子纯名称作为 Key，例如 BP_factors.parquet -> BP
            factor_name = f.name.replace("_factors.parquet", "").lower()
            
            # 如果字典里已经有这个因子了（比如同时存在于 valuation 和 fundamental），直接跳过
            if factor_name in all_dfs:
                print(f"  ⏩ 跳过重复因子: {f.name}")
                continue
                
            temp_df = pd.read_parquet(f)
            temp_df.columns = [c.lower() for c in temp_df.columns]
            
            if 'date' in temp_df.columns and 'code' in temp_df.columns:
                temp_df = temp_df.drop_duplicates(subset=['date', 'code'])
                # 设置索引，方便后面 concat 自动对齐
                all_dfs[factor_name] = temp_df.set_index(['date', 'code'])
                print(f"  ✅ 已加载: {f.name}")
        except Exception as e:
            print(f"  ❌ 读取 {f.name} 失败: {e}")

    if not all_dfs:
        print("❌ 无有效数据可聚合。")
        return

    # 🔗 横向合并
    print(f"🔗 正在合并 {len(all_dfs)} 个唯一因子列...")
    # join='outer' 保证时间序列不整齐时也能保留所有数据
    full_df = pd.concat(all_dfs.values(), axis=1, join='outer').reset_index()
    
# ⚡ 执行标准化
    factor_cols = [c for c in full_df.columns if c not in ['date', 'code']]
    print(f"⚡ 正在对 {len(factor_cols)} 个因子执行 MAD 标准化...")
    
    # 注意这里：要调用你新写的那个 _pro 版本的函数
    final_df = factor_process_pro(full_df, factor_cols) 
    
    # 💾 保存最终宽表
    final_df.to_parquet(output_path, index=False)

if __name__ == "__main__":
    # 路径配置
    BASE_DIR = r"D:\量化平台\QuantFlow_Lab\data\factors"
    OUTPUT_FILE = r"D:\量化平台\QuantFlow_Lab\data\final_standardized_pool.parquet"
    
    aggregate_and_standardize(BASE_DIR, OUTPUT_FILE)