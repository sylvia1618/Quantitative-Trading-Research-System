import baostock as bs
import pandas as pd
from pathlib import Path

class IndustryLabeler:
    def __init__(self, raw_path):
        self.raw_path = Path(raw_path)
        # 这里会自动创建 data 文件夹，如果不存在的话
        self.raw_path.mkdir(parents=True, exist_ok=True)

    def get_industry_mapping(self):
        print("🚀 正在连接 Baostock 获取行业分类...")
        lg = bs.login()
        if lg.error_code != '0':
            print(f"❌ 登录失败: {lg.error_msg}")
            return None

        rs = bs.query_stock_industry()
        industry_list = []
        while (rs.error_code == '0') & rs.next():
            industry_list.append(rs.get_row_data())
        bs.logout()

        df = pd.DataFrame(industry_list, columns=rs.fields)
        df['industry'] = df['industry'].replace('', 'Unknown')
        
        # 只取核心两列并去重
        df_clean = df[['code', 'industry']].copy()
        df_clean = df_clean.drop_duplicates(subset=['code'], keep='last')
        
        print(f"📊 标注完成。总数: {len(df_clean)}")
        return df_clean

    def save_mapping(self):
        df = self.get_industry_mapping()
        if df is not None:
            save_file = self.raw_path / "industry_mapping.csv"
            df.to_csv(save_file, index=False, encoding='utf-8-sig')
            print(f"✅ 行业映射表已保存至: {save_file}")

if __name__ == "__main__":
    # 无论脚本在哪里，都寻找名为 QuantFlow_Lab 的根目录，或根据当前深度回溯
    # 假设你的项目文件夹叫 QuantFlow_Lab
    BASE_DIR = Path(__file__).resolve().parent
    while BASE_DIR.name != 'QuantFlow_Lab' and BASE_DIR.parent != BASE_DIR:
        BASE_DIR = BASE_DIR.parent
        
    print(f"📍 项目根目录确认: {BASE_DIR}")
    labeler = IndustryLabeler(raw_path=BASE_DIR / "data")
    labeler.save_mapping()