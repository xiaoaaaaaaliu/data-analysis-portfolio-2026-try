import pandas as pd
from datetime import datetime

# 读取上一步导出的RFM基础表
df = pd.read_csv(r"C:\Users\32717\RFM基础数据.csv", encoding="utf-8-sig")

# 1、日期转换，数据集截止日期：2011-12-09（全量订单最后一天）
df["last_buy"] = pd.to_datetime(df["last_buy"])
cutoff_day = datetime(2011, 12, 9)

# 计算R：距离末次消费的天数
df["R"] = (cutoff_day - df["last_buy"]).dt.days

# F、M直接复用原有字段
df["F"] = df["F_freq"]
df["M"] = df["M_money"]

# 2、RFM四分位打分（R越小得分越高；F/M越大得分越高 1~5分）
# F做rank避免同分报错
df["R_score"] = pd.qcut(df["R"], q=5, labels=[5,4,3,2,1])
df["F_score"] = pd.qcut(df["F"].rank(method="first"), q=5, labels=[1,2,3,4,5])
df["M_score"] = pd.qcut(df["M"], q=5, labels=[1,2,3,4,5])

# 总分求和
df["RFM总得分"] = df["R_score"].astype(int) + df["F_score"].astype(int) + df["M_score"].astype(int)

# 3、用户分层规则（对标原论文四类客户）
def user_class(score):
    if score >= 12:
        return "高价值客户"
    elif score >= 9:
        return "忠实复购客户"
    elif score >= 6:
        return "沉睡预警客户"
    else:
        return "流失低价值客户"

df["用户分层标签"] = df["RFM总得分"].apply(user_class)

# 4、导出最终结果（给PowerBI用）
result_df = df[["CustomerID","R","F","M","R_score","F_score","M_score","RFM总得分","用户分层标签"]]
result_df.to_csv("RFM分层结果.csv", index=False, encoding="utf-8-sig")

# 控制台输出分层统计（项目结论）
print("====用户分层数量统计====")
print(result_df["用户分层标签"].value_counts())
print("\nRFM分层结果.csv 导出完毕！")
