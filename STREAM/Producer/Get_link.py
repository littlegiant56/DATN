import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()

# Bật chế độ headless nếu muốn (bỏ comment dòng dưới)
# chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/113.0.0.0 Safari/537.36"
)

driver = webdriver.Chrome(options=chrome_options)

url = "https://www.vietnamworks.com/viec-lam?sorting=lasted"

SCROLL_PAUSE_TIME = 1

crawled_jobs = set()  # lưu link job đã crawl vòng trước

try:
    while True:
        driver.get(url)
        time.sleep(2)  # chờ trang load

        # Scroll đến cuối trang để load hết job
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Lấy tất cả thẻ a có class 'img_job_card'
        job_elements = driver.find_elements("css selector", "a.img_job_card")

        # Lấy link tất cả job hiện tại trên trang
        current_job_links = set()
        for elem in job_elements:
            href = elem.get_attribute("href")
            if href:
                current_job_links.add(href)

        # Tìm job mới: link chưa có trong crawled_jobs
        new_jobs = [job for job in current_job_links if job not in crawled_jobs]

        if new_jobs:
            print(f"Tìm thấy {len(new_jobs)} job mới:")
            for job_link in new_jobs:
                print(job_link)
        else:
            print("Không có job mới.")

        # Cập nhật crawled_jobs thành toàn bộ job hiện tại (xóa dữ liệu cũ)
        crawled_jobs = current_job_links

        print("Chờ 3 giây trước khi kiểm tra lại...")
        time.sleep(3)

except KeyboardInterrupt:
    print("Dừng crawl theo yêu cầu người dùng.")
finally:
    driver.quit()
