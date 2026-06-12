import sqlite3
import pandas as pd
from snownlp import SnowNLP

# -------------------------- 路径 --------------------------
DB_PATH = r"D:\aoe\arknights_taptap.db"

# --------------------------  连接数据库 --------------------------
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
print("✅ 数据库连接成功")

# -------------------------- 去重+过滤 --------------------------
# 先统计原始数据量
cursor.execute("SELECT COUNT(*) FROM taptap_reviews")
raw_count = cursor.fetchone()[0]
print(f"📊 原始数据：{raw_count} 条")

# 去重+过滤SQL（去掉中文别名，避免SQLite列名问题）
clean_sql = """
CREATE TABLE IF NOT EXISTS taptap_reviews_clean AS
SELECT DISTINCT *
FROM taptap_reviews
WHERE
    col3 IN ('0','1','2','3','4','5')
    AND col4 IS NOT NULL
    AND TRIM(col4) != ''
"""
cursor.execute(clean_sql)

# 统计清洗后的数据量
cursor.execute("SELECT COUNT(*) FROM taptap_reviews_clean")
clean_count = cursor.fetchone()[0]
print(f"✅ 去重+过滤完成，剩余有效数据：{clean_count} 条")

# --------------------------  情感分析 --------------------------
# 读取干净表
df = pd.read_sql("SELECT * FROM taptap_reviews_clean", conn)

def get_sentiment(text):
    text = str(text).strip()
    if not text:
        return "无内容"
    s = SnowNLP(text)
    score = s.sentiments
    if score > 0.6:
        return "好评"
    elif score < 0.4:
        return "差评"
    else:
        return "中评"

# 关键修复：用 iloc 按位置取评论内容（第4列，索引为3）
df["情感标签"] = df.iloc[:, 3].astype(str).apply(get_sentiment)
print("✅ 情感分析完成！")

# -------------------------- 4. 把结果写回数据库，生成最终分析表 --------------------------
df.to_sql("taptap_sentiment_final", conn, if_exists="replace", index=False)
print("✅ 情感分析结果已存入数据库！")

# -------------------------- 5. 快速统计结果 --------------------------
print("\n📊 数据清洗&情感分析结果：")
print(f"清洗前：{raw_count} 条 → 清洗后：{clean_count} 条")
print("\n情感分布：")
print(df["情感标签"].value_counts())

conn.commit()
conn.close()
print("\n🎉 全部流程跑完！")