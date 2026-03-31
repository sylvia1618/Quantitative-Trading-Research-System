import os
import dai
import pandas as pd

# 假设你已在环境变量中设置好 BQ_API_KEY（或 SDK 要求的其他变量）
os.environ['BQ_API_KEY'] = 'FaTVcvPbKi6C.tJq1LzNxHsO3o8HN43AcD0yaDRsOp2YYPJN6MmqSA0rlvsftaIZqJa9gXDGk0Cbh'

# 查询 cn_stock_static_data 表在指定日期范围内的流通股本
start_date = "2020-01-01"
end_date = "2026-03-24"

sql = """
SELECT
    date,
    instrument,
    name,
    public_float_share
FROM
    cn_stock_static_data
WHERE
    date BETWEEN '{s}' AND '{e}'
""".format(s=start_date, e=end_date)

# filters 参数通常也可用来限制日期范围，示例如下二选一：使用 SQL WHERE 或 filters
result = dai.query(sql).df()

# 如需按交易日/股票分片下载以防单次过大，可分批查询并合并
# 示例：按年份分批（伪代码）
# all_dfs = []
# for year in range(2020, 2027):
#     s = f"{year}-01-01"
#     e = f"{year}-12-31" if year < 2026 else end_date
#     chunk_sql = sql.replace(start_date, s).replace(end_date, e)
#     df_chunk = dai.query(chunk_sql).df()
#     all_dfs.append(df_chunk)
# df = pd.concat(all_dfs, ignore_index=True)

# 存为本地 CSV
result.to_csv("cn_stock_static_data_public_float_share_20200101_20260324.csv", index=False)
print("保存完成，记录数：", len(result))