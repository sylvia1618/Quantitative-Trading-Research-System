import baostock as bs
import pandas as pd
from pathlib import Path

def sync_all_stock_names(data_path="data"):
    # 1. 路径准备
    raw_path = Path(data_path) / "raw"
    raw_path.mkdir(parents=True, exist_ok=True)

    # 2. 登录 Baostock
    lg = bs.login()
    if lg.error_code != "0":
        print(f"Baostock 登录失败: {lg.error_msg}")
        return

    print("🔍 正在抓取全 A 股最新名称映射表...")
    
    # 3. 尝试回溯抓取（处理周末或节假日无数据的情况）
    found_data = False
    for i in range(10):  # 增加到10天回溯，更稳健
        target_date = (pd.Timestamp.now() - pd.Timedelta(days=i)).strftime("%Y-%m-%d")
        # query_all_stock 默认获取该日所有股票/指数信息
        rs = bs.query_all_stock(day=target_date)
        
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        if data_list:
            df = pd.DataFrame(data_list, columns=rs.fields)
            
            # 4. 关键过滤：仅保留股票，剔除指数
            # Baostock 中，股票代码通常以 sh.6 或 sz.0/sz.3/bj 开头
            # 我们通过 tradeStatus 判断（1为正常交易，0为停牌，但也属于股票）
            # 或者通过 code 判断不包含 'sh.000' (上证指数等)
            df = df[df['code'].str.contains(r'sh\.6|sz\.0|sz\.3|sz\.0|bj\.', regex=True)]
            
            # 5. 格式清洗
            df = df[['code', 'code_name']].rename(columns={'code_name': 'display_name'})
            
            output_file = raw_path / "all_stock_info.csv"
            df.to_csv(output_file, index=False, encoding="utf-8-sig")
            
            print(f"✨ 成功获取 {target_date} 的全 A 股数据")
            print(f"🚀 同步完成！共计 {len(df)} 只个股，已保存至: {output_file}")
            found_data = True
            break
            
    if not found_data:
        print("⚠️ 未能抓取到名称数据，请检查网络或 Baostock 状态。")

    bs.logout()

if __name__ == "__main__":
    # 根据你的项目目录结构调整路径
    sync_all_stock_names(data_path="data")