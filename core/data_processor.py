import pandas as pd
import numpy as np
from pathlib import Path

def clean_factor_pipeline(input_file, output_file):
    print(f"🚀 开始执行私募级因子清洗流水线...")
    
    # 1. 读取数据
    df = pd.read_parquet(input_file)
    df['date'] = pd.to_datetime(df['date'])
    
    # 2. 基础过滤：剔除停牌与 ST
    # 停牌和ST的数据会严重污染因子的截面分布
    if 'volume' in df.columns:
        df = df[df['volume'] > 0]
    if 'isst' in df.columns:
        df = df[df['isst'] == 0]

    # 3. 预处理：处理负 PE 和 无穷值
    # 逻辑：亏损公司的 PE (pettm) 为负，直接做 Z-score 会误认为“极度低估”。
    # 做法：将负 PE 设为 NaN，后续用中位数填充。
    if 'pettm' in df.columns:
        df.loc[df['pettm'] <= 0, 'pettm'] = np.nan
        
    # 处理所有数值列的 inf
    num_cols = df.select_dtypes(include=[np.number]).columns
    df[num_cols] = df[num_cols].replace([np.inf, -np.inf], np.nan)

    # 4. 定义横截面处理函数 (去极值 + 标准化)
    # 使用 Pandas 原生 clip 替代 Scipy，性能提升 5-10 倍
    def cross_section_process(group):
        factor_cols = [c for c in ["pbmrq", "pettm", "turn", "amount"] if c in group.columns]
        
        for col in factor_cols:
            # a. 缺失值填充 (用当天该因子的中位数)
            group[col] = group[col].fillna(group[col].median())
            
            # b. 极值处理 (Winsorize: 1% - 99%)
            ql, qu = group[col].quantile(0.01), group[col].quantile(0.99)
            group[col] = group[col].clip(ql, qu)
            
            # c. 标准化 (Z-score)
            std = group[col].std()
            if std > 0:
                group[f"{col}_z"] = (group[col] - group[col].mean()) / std
            else:
                group[f"{col}_z"] = 0.0
                
        return group

    # 5. 执行横截面计算
    print("⏳ 正在逐日执行去极值与标准化 (Groupby Date)...")
    df = df.groupby("date", group_keys=False).apply(cross_section_process)

    # 6. 清理并排序
    # 剔除无法计算出 Z-score 的行（通常是数据严重缺失的）
    z_cols = [c for c in df.columns if c.endswith('_z')]
    df = df.dropna(subset=z_cols)
    df = df.sort_values(["date", "code"]).reset_index(drop=True)

    # 7. 保存
    df.to_parquet(output_file, index=False, compression='snappy')
    
    print(f"✅ 清洗完成！")
    print(f"📊 最终可用样本量: {len(df)}")
    print(f"📅 日期范围: {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"📁 输出路径: {output_file}")

if __name__ == "__main__":
    IN = r"D:\量化平台\QuantFlow_Lab\data\derived\universe_v1.parquet"
    OUT = r"D:\量化平台\QuantFlow_Lab\data\derived\clean_factor_data.parquet"
    clean_factor_pipeline(IN, OUT)