import csv
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta

# Tính toán ngày hôm qua
yesterday = datetime.now() #- timedelta(1)
target_date = yesterday.strftime("%d/%m/%Y")  # Định dạng ngày theo "Ngày/Tháng/Năm"

# Tạo tên file CSV với định dạng "ngày/tháng/năm_links.csv"
csv_filename ="VNW_" + yesterday.strftime("%d-%m-%Y") + "_links.csv"

# Tạo file CSV nếu chưa tồn tại và ghi header
if not os.path.exists(csv_filename):
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Job Link"])

# Đọc các link đã lưu để tránh trùng
with open(csv_filename, mode='r', encoding='utf-8') as file:
    existing_links = set(row.strip() for row in file if row.strip() and not row.startswith("Job Link"))

chrome_options = Options()

# Bật chế độ headless
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

# Giúp chạy ổn định trên Linux/AWS
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Tắt các cảnh báo automation để giả lập trình duyệt thật hơn
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# Thiết lập User-Agent giống trình duyệt thật (bạn có thể thay user-agent phù hợp)
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/113.0.0.0 Safari/537.36"
)

# Khởi tạo trình duyệt với options đã cấu hình
driver = webdriver.Chrome(options=chrome_options)

# Base URL
base_url = "https://www.vietnamworks.com/viec-lam"
sort_param = "sorting=lasted"

page = 1
found_target_date = False 
while True:
    if page == 1:
        url = f"{base_url}?{sort_param}"
    else:
        url = f"{base_url}?page={page}&{sort_param}"

    print(f"\n➡️  Đang crawl trang {page}: {url}")
    driver.get(url)

    # Scroll hết trang
    SCROLL_PAUSE_TIME = 1
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Chờ load xong job
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.view_job_item'))
        )
    except:
        print(f"⛔ Không tìm thấy job nào ở trang {page}, dừng.")
        break

    # Tìm tất cả job link
    job_links = driver.find_elements(By.CSS_SELECTOR, 'div.view_job_item a[href*="?source=searchResults"]')
    if not job_links:
        print(f"⛔ Trang {page} không còn job.")
        break

    new_links = []
    for link_element in job_links:
        href = link_element.get_attribute('href')
        
        # Lấy ngày cập nhật từ DOM
        try:
            job_date_element = link_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'view_job_item')]//div[contains(text(),'Cập nhật:')]")
            job_date_text = job_date_element.text.strip().replace("Cập nhật: ", "")  # Lấy ngày từ text
            date_elements = driver.find_elements(By.XPATH, "./ancestor::div[contains(@class, 'view_job_item')]//div[contains(text(),'Hôm nay')]")
            if date_elements == 'Hôm nay':
                continue
            # Kiểm tra nếu ngày cập nhật trùng với ngày hôm qua
            if job_date_text == target_date:
                found_target_date = True
                # Nếu href bắt đầu bằng '/', ta sẽ thêm "https://www.vietnamworks.com" vào đầu href
                if href.startswith('/'):
                    href = "https://www.vietnamworks.com" + href

                # Kiểm tra nếu liên kết chưa tồn tại trong existing_links
                if href not in existing_links:
                    new_links.append(href)  # Thêm vào danh sách các liên kết mới
                    existing_links.add(href)  # Thêm vào existing_links để tránh trùng lặp
        except Exception as e:
            print(f"Error retrieving date for job link: {href} - Error: {e}")

    # Kiểm tra nếu không có link mới nào thỏa mãn điều kiện
    if not new_links:
        if found_target_date:
            # Đã từng tìm thấy job ngày mục tiêu trước đó, giờ không còn nữa -> dừng
            print(f"⛔ Đã từng tìm thấy job ngày {target_date} trước đó, nhưng trang {page} không có job nào ngày này nữa. Dừng.")
            break
        else:
            # Chưa tìm thấy ngày mục tiêu nào, tiếp tục sang trang kế tiếp
            print(f"⚠️ Trang {page} không có job ngày {target_date}. Tiếp tục sang trang kế tiếp.")
            page += 1
            continue

    # Lưu link mới vào CSV
    with open(csv_filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for link in new_links:
            writer.writerow([link])

    print(f"✅ Trang {page}: thêm {len(new_links)} link mới vào CSV.")

    page += 1  # Sang trang tiếp theo

# Kết thúc
print(f"\n📄 Tổng số link đã lưu: {len(existing_links)}")
print(f"📥 File CSV: {csv_filename}")
driver.quit()
