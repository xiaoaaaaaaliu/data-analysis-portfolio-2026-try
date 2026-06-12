from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
import time
import pandas as pd
#导入os模块用于文件判断
import os

# 初始化浏览器
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
driver = webdriver.Edge(options=options)
wait = WebDriverWait(driver, 30)

url = "https://www.taptap.cn/app/70253/review?os=pc&sort=newest"
driver.get(url)
print("请手动登录TapTap，登录后回车继续...")
input()

# -------------------------- 容器 selector（去掉nth-child） --------------------------
# 去掉nth-child后匹配所有评论
review_container_selector = "#all-app-reviews > div.reviews-list__wrap > div > div > div"

# 子 selector
SELECTORS_INSIDE = {
    "用户名": "div.review-item--in-app-tab__content.review-item__content > div.review-item__header.flex-center--y > div",
    "游戏状态/时长": "div.review-item--in-app-tab__content.review-item__content > div.review-item__rating.flex-center--y.caption-m12-w12.gray-06 > div.tap-text.tap-text__one-line.review-item__time-label",
    "评分星星": "div.review-item--in-app-tab__content.review-item__content > div.review-item__rating.flex-center--y.caption-m12-w12.gray-06 > div.review-rate.review-item__time-label > div.review-rate__highlight",
    "评论内容": "div.review-item--in-app-tab__content.review-item__content > div.review-item__body.flex-center--y > div > div > div > a > div > span",
    "发布时间": "div.review-item--in-app-tab__content.review-item__content > div.review-item__footer.flex-center--y > div > div.flex-center--y.caption-m12-w12.gray-04 > span",
    "设备信息": "div.review-item--in-app-tab__content.review-item__content > div.review-item__footer.flex-center--y > div > div.review-item__device > div"
}

# -------------------------- 断点续爬逻辑 --------------------------
csv_path = "明日方舟评论.csv"  #保存路径一致
all_reviews = []
last_comment_count = 0  # 记录已爬取的评论数

# 1. 检查是否有已保存的CSV文件，恢复断点
if os.path.exists(csv_path):
    # 读取已有数据
    df_exist = pd.read_csv(csv_path, encoding="utf-8-sig")
    all_reviews = df_exist.to_dict("records")
    last_saved_count = len(all_reviews)
    print(f"✅ 发现已有爬取数据，共 {last_saved_count} 条，将从断点继续爬取")
    
    # 滚动到之前的位置（模拟已爬取的滚动次数）
    print("🔄 正在滚动到上次爬取的位置...")
    scroll_to_restore = min(last_saved_count // 10, 250)  # 最多滚动250次快速定位
    for _ in range(scroll_to_restore):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # 快速滚动间隔等待2秒
    
    # 更新当前页面的评论总数（作为断点起点）
    review_items = driver.find_elements(By.CSS_SELECTOR, review_container_selector)
    last_comment_count = len(review_items)
else:
    print("🆕 未发现已有数据，将从头开始爬取")

# -------------------------- 滚动加载逻辑（完全不变） --------------------------
scroll_times = 20  # 滚动次数
scroll_wait = 6   # 每次等待6秒

for scroll_idx in range(1, scroll_times + 1):
    print(f"\n===== 第 {scroll_idx} 次滚动加载 =====")
    
    # 滚动到底部触发加载
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    print(f"🔄 已滚动到底部，等待 {scroll_wait} 秒加载新评论...")
    time.sleep(scroll_wait)
    
    try:
        # 等待评论容器加载
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, review_container_selector)))
        review_items = driver.find_elements(By.CSS_SELECTOR, review_container_selector)
        current_count = len(review_items)
        print(f"✅ 当前页面累计 {current_count} 条评论项")
        
        # 只处理新增评论
        new_review_items = review_items[last_comment_count:]
        if not new_review_items:
            print("🔚 无新增评论，已滚动到底部，提前结束")
            break
        
        # 提取新增评论字段
        for idx, item in enumerate(new_review_items, 1):
            try:
                username_elem = item.find_elements(By.CSS_SELECTOR, SELECTORS_INSIDE["用户名"])
                username = username_elem[0].text.strip() if username_elem else "未知用户"

                status_elem = item.find_elements(By.CSS_SELECTOR, SELECTORS_INSIDE["游戏状态/时长"])
                status = status_elem[0].text.strip() if status_elem else "未知状态"

                try:
                    star_elem = item.find_element(By.CSS_SELECTOR, SELECTORS_INSIDE["评分星星"])
                    # 从 style 里拿到宽度，比如 "width: 36px;" → 36
                    style = star_elem.get_attribute("style")
                    width_str = style.split("width: ")[1].split("px")[0]
                    highlight_width = int(float(width_str))  # 处理可能的小数
                    # 每颗星 18px，计算星级（四舍五入到整数）
                    stars = round(highlight_width / 18)
                except:
                    stars = 0  # 提取失败时默认 0 星

                content_elem = item.find_elements(By.CSS_SELECTOR, SELECTORS_INSIDE["评论内容"])
                content = content_elem[0].text.strip().replace("\n", " ") if content_elem else "无内容"

                post_time_elem = item.find_elements(By.CSS_SELECTOR, SELECTORS_INSIDE["发布时间"])
                post_time = post_time_elem[0].text.strip() if post_time_elem else "未知时间"

                device_elem = item.find_elements(By.CSS_SELECTOR, SELECTORS_INSIDE["设备信息"])
                device = device_elem[0].text.strip() if device_elem else "未知设备"

                all_reviews.append({
                    "用户名": username,
                    "游戏状态": status,
                    "评分": stars,
                    "评论内容": content,
                    "发布时间": post_time,
                    "设备信息": device
                })
                print(f"✅ 新增第{idx}条: {username} - {stars}星 | 设备: {device}")

            except Exception as e:
                print(f"⚠️ 新增第{idx}条提取失败: {str(e)[:50]}")
                continue
        
        # 更新评论计数
        last_comment_count = current_count
        
    except Exception as e:
        print(f"❌ 第{scroll_idx}次滚动加载失败: {e}")
        continue

# -------------------------- 保存结果 --------------------------
if all_reviews:
    df = pd.DataFrame(all_reviews)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"\n🎉 爬取完成！累计保存 {len(all_reviews)} 条有效评论")  #累计
else:
    print("\n❌ 未提取到任何评论")

driver.quit()