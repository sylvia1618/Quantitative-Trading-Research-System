import pandas as pd
import os
import glob
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm

class ParquetInspector:
    def __init__(self, data_path='data/raw/'):
        self.data_path = data_path
        # 获取所有 .parquet 文件路径
        self.files = glob.glob(os.path.join(data_path, '*.parquet'))
        print(f"📂 找到 {len(self.files)} 个数据文件")

    def _check_single_file(self, file_path):
        """单文件检查逻辑"""
        try:
            df = pd.read_parquet(file_path)
            # 基础信息检查
            info = {
                'file': os.path.basename(file_path),
                'count': len(df),
                'start': df['date'].min() if 'date' in df.columns else None,
                'end': df['date'].max() if 'date' in df.columns else None,
                'has_nan': df.isnull().values.any(),
                'cols': list(df.columns)
            }
            return info
        except Exception as e:
            return {'file': os.path.basename(file_path), 'error': str(e)}

    def audit_all(self, sample_size=100):
        """抽取部分样本进行深度体检"""
        samples = self.files[:sample_size]
        results = []
        
        print(f"🧪 正在对 {sample_size} 个样本进行健康审计...")
        with ProcessPoolExecutor() as executor:
            results = list(tqdm(executor.map(self._check_single_file, samples), total=sample_size))
            
        audit_df = pd.DataFrame([r for r in results if 'error' not in r])
        
        # 打印审计报告
        print("\n" + "="*50)
        print("📊 数据健康审计报告")
        print("="*50)
        print(f"✅ 平均数据行数: {audit_df['count'].mean():.2f}")
        print(f"✅ 日期覆盖: {audit_df['start'].min()} 至 {audit_df['end'].max()}")
        print(f"✅ 包含字段: {audit_df['cols'].iloc[0]}")
        
        nan_files = audit_df[audit_df['has_nan'] == True]
        if not nan_files.empty:
            print(f"⚠️ 警告: 有 {len(nan_files)} 个文件存在缺失值 (NaN)")
        else:
            print("💎 完美: 抽样文件中未发现缺失值")
        
        # 展示其中一个的具体长相
        print("\n👀 数据样例 (前 5 行):")
        display_df = pd.read_parquet(samples[0])
        print(display_df.head())

if __name__ == "__main__":
    inspector = ParquetInspector(data_path='data/raw/')
    inspector.audit_all(sample_size=50) # 审计 50 只股票作为代表