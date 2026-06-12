import sqlite3
import pandas as pd
from pathlib import Path

# -------------------------- 1. 只改这两个路径 --------------------------
CSV_PATH = r"D:\aoe\taptap_reviews.csv"
DB_PATH = r"D:\aoe\arknights_taptap.db"

# -------------------------- 2. 连接数据库 --------------------------
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
print(f"✅ 数据库连接成功，存放位置：{DB_PATH}")

# -------------------------- 3. 建表：改成 6 个字段 --------------------------
create_raw_table_sql = """
CREATE TABLE IF NOT EXISTS taptap_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    col1 TEXT,
    col2 TEXT,
    col3 TEXT,
    col4 TEXT,
    col5 TEXT,
    col6 TEXT,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""
cursor.execute(create_raw_table_sql)
print("✅ 原始数据表创建完成")

# -------------------------- 4. 读取CSV并批量插入 --------------------------
if not Path(CSV_PATH).exists():
    raise FileNotFoundError("❌ 你的CSV路径写错了，检查一下！")

df = pd.read_csv(CSV_PATH)
print(f"✅ 读取到原始评论数据：一共 {len(df)} 条，列数：{len(df.columns)}")

df = df.fillna("")
df = df.astype(str)
data_list = df.values.tolist()

# -------------------------- 5. 插入语句适配 6 列 --------------------------
insert_sql = """
INSERT INTO taptap_reviews (col1, col2, col3, col4, col5, col6)
VALUES (?, ?, ?, ?, ?, ?)
"""
cursor.executemany(insert_sql, data_list)

print("✅ CSV 全部导入数据库成功")

# -------------------------- 6. 清洗（保留全部6列） --------------------------
clean_sql = """
CREATE TABLE IF NOT EXISTS taptap_reviews_clean AS
SELECT DISTINCT *
FROM taptap_reviews
WHERE
    col3 IN ('1','2','3','4','5')
    AND col4 IS NOT NULL
    AND TRIM(col4) != ''
"""
cursor.execute(clean_sql)

cnt = cursor.execute("SELECT COUNT(*) FROM taptap_reviews_clean").fetchone()[0]
print(f"✅ 清洗完毕！干净有效数据剩余：{cnt} 条")

# -------------------------- 收尾 --------------------------
conn.commit()
conn.close()
print("\n🎉 全部流程跑完，自动生成了 arknights_taptap.db 文件！")