import sqlite3
import pandas as pd
from snownlp import SnowNLP

# -------------------------- 只改这里的路径 --------------------------
DB_PATH = r"D:\aoe\arknights_taptap.db"

# -------------------------- 1. 连接数据库 --------------------------
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
print("✅ 数据库连接成功")

# -------------------------- 2. 去重+过滤，生成干净表 --------------------------
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

# -------------------------- 3. 情感分析（给评论打标签） --------------------------
# 读取干净表
df = pd.read_sql("SELECT * FROM taptap_reviews_clean", conn)

def get_sentiment(text):
    text = str(text).strip()
    if not text:
        return "无内容"
    s = SnowNLP(text)
    score = s.sentiments
    if score > 0.45:
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

# ====================== 【新增】导出CSV文件 ======================
df.to_csv(r"D:\aoe\final_analysis_data.csv", index=False, encoding="utf-8-sig")
print("✅ CSV文件已导出：D:\\aoe\\final_analysis_data.csv")
# =================================================================

# -------------------------- 5. 快速统计结果 --------------------------
print("\n📊 数据清洗&情感分析结果：")
print(f"清洗前：{raw_count} 条 → 清洗后：{clean_count} 条")
print("\n情感分布：")
print(df["情感标签"].value_counts())

conn.commit()
conn.close()
print("\n🎉 全部流程跑完！")
# 加在代码末尾、关闭数据库之前
from snownlp import SnowNLP

# 批量算出每条评论真实分数
def get_score(text):
    text = str(text).strip()
    if not text:
        return 0.0
    return SnowNLP(text).sentiments

df["情绪分数"] = df.iloc[:,3].apply(get_score)

# 统计区间
print("\n==== 情绪分数区间统计 ====")
print("大于0.45（应是好评）：", (df["情绪分数"]>0.45).sum())
print("0.4~0.45（中评）：", ((df["情绪分数"]>=0.4) & (df["情绪分数"]<=0.45)).sum())
print("小于0.4（差评）：", (df["情绪分数"]<0.4).sum())