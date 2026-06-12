import sqlite3
import pandas as pd

# =================自己改路径=================
csv_path = r"D:\aoe\Online_Retail.csv"
db_path = r"D:\aoe\retail.db"
# ============================================

# 1、读取原始数据，先把日期格式处理好
df_raw = pd.read_csv(csv_path, encoding="latin1")
# 关键修正：提前把InvoiceDate转为标准日期格式，SQLite才能正确识别
df_raw["InvoiceDate"] = pd.to_datetime(df_raw["InvoiceDate"])

# 2、入库到sqlite
conn = sqlite3.connect(db_path)
df_raw.to_sql("retail", conn, if_exists="replace", index=False)
print(f"入库完毕，原始数据共 {len(df_raw)} 行")

# 筛选条件：有效订单（剔除退货、负数数量、空用户ID）
base_where = "WHERE CustomerID IS NOT NULL AND Quantity > 0 AND InvoiceNo NOT LIKE 'C%'"

# 2、SQL提取三张表
# ①月度营收+环比（现在strftime可以正常识别日期了）
sql_month = f'''
WITH month_data AS(
SELECT
strftime('%Y-%m',InvoiceDate) as month,
SUM(Quantity*UnitPrice) as sales,
COUNT(DISTINCT CustomerID) as user_count,
COUNT(DISTINCT InvoiceNo) as order_count,
SUM(Quantity*UnitPrice)/COUNT(DISTINCT InvoiceNo) as avg_order_price
FROM retail {base_where}
GROUP BY month
)
SELECT *,
ROUND((sales-LAG(sales,1)OVER(ORDER BY month))*100.0/LAG(sales,1)OVER(ORDER BY month),2) as sales_growth_rate
FROM month_data
ORDER BY month;
'''
df_month = pd.read_sql(sql_month, conn)

# ②RFM基础用户数据（first_buy/last_buy会是标准日期格式）
sql_rfm_base = f'''
SELECT
CustomerID,
MIN(InvoiceDate) as first_buy,
MAX(InvoiceDate) as last_buy,
COUNT(DISTINCT InvoiceNo) as F_freq,
SUM(Quantity*UnitPrice) as M_money
FROM retail {base_where}
GROUP BY CustomerID;
'''
df_rfm_base = pd.read_sql(sql_rfm_base, conn)

# ③各国销售
sql_country = f'''
SELECT
Country,
SUM(Quantity*UnitPrice) as total_sales,
COUNT(DISTINCT CustomerID) as user_cnt
FROM retail {base_where}
GROUP BY Country
ORDER BY total_sales DESC;
'''
df_country = pd.read_sql(sql_country, conn)

# 3、导出csv（后续RFM、PowerBI用）
df_month.to_csv("月度指标.csv", index=False, encoding="utf-8-sig")
df_rfm_base.to_csv("RFM基础数据.csv", index=False, encoding="utf-8-sig")
df_country.to_csv("国别销售.csv", index=False, encoding="utf-8-sig")

print("三张汇总csv导出完成！")
print(f"月度表行数: {len(df_month)}")  # 正常应该是37行
print(f"RFM基础表行数: {len(df_rfm_base)}")
print(f"国别销售表行数: {len(df_country)}")

conn.close()
