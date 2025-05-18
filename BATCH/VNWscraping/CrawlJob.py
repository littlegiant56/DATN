import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os 
from datetime import datetime, timedelta
from selenium.common.exceptions import StaleElementReferenceException

yesterday = datetime.now() #- timedelta(1)

input_csv_filename = "Rawdata/Links/" + yesterday.strftime("%d-%m-%Y") + "_links.csv"
output_csv_filename = yesterday.strftime("%d-%m-%Y") + "_jobs.csv"

# Cấu hình Chrome driver
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
driver.get('https://www.vietnamworks.com/')
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.TAG_NAME, 'body'))
)
time.sleep(2)

def read_job_links_from_csv(filename=input_csv_filename):
    job_links = []
    with open(filename, mode='r', encoding='utf-8') as file:
        for row in file:
            link = row.strip()
            if link and not link.lower().startswith('job link'):  # bỏ header nếu có
                job_links.append(link)
    return job_links

# Mảng các link cần crawl
job_links = read_job_links_from_csv(input_csv_filename)

# Hàm crawl thông tin công việc
def try_click(keyword):
    xpath = (
        f"//button[contains(normalize-space(text()), '{keyword}')"
        f" or contains(@aria-label, '{keyword}')]"
    )
    buttons = driver.find_elements(By.XPATH, xpath)
    if not buttons:
        print(f"⚠️ Không tìm thấy nút nào với từ khóa: '{keyword}'")
        return
    for idx, btn in enumerate(buttons, start=1):
        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", btn
            )
            time.sleep(0.2)
            btn.click()
            time.sleep(0.5)

        except StaleElementReferenceException:
            fresh = driver.find_elements(By.XPATH, xpath)
            if idx-1 < len(fresh):
                try:
                    btn2 = fresh[idx-1]
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", btn2
                    )
                    time.sleep(0.2)
                    btn2.click()
                    print(f"🔄 Retry click nút {idx} thành công")
                    time.sleep(1)
                except Exception as e2:
                    print(f"❌ Retry thất bại nút {idx}: {e2}")
            else:
                print(f"⚠️ Không tìm lại được nút {idx} để retry")
        except Exception as e:
            print(f"❌ Lỗi khi click nút thứ {idx} '{keyword}': {e}")
    try:
        buttons = driver.find_elements(By.XPATH, xpath)
        if buttons:
            driver.execute_script("arguments[0].scrollIntoView(true);", buttons[0])
            buttons[0].click()
        else:
            print(f"⚠️ Không tìm thấy nút: {xpath}")
    except Exception as e:
        print(f"❌ Lỗi khi bấm nút {xpath}: {e}")

# Hàm lấy text không cần wait
def get_text_safe(xpath):
    try:
        labels = driver.find_elements(By.XPATH, xpath)
        if labels:
            sibling = labels[0].find_element(By.XPATH, "following-sibling::p")
            return sibling.text.strip()
    except:
        return None
    return None

def get_locations():
    try:
        # Giới hạn phạm vi tìm kiếm: chỉ lấy các <p name="paragraph"> trong khối "Địa điểm làm việc"
        location_elements = driver.find_elements(By.XPATH, "//h2[text()='Địa điểm làm việc']/following::p[@name='paragraph']")
        locations = [el.text.strip() for el in location_elements if el.text.strip()]
        return ", ".join(locations)
    except Exception as e:
        print(f"❌ Lỗi khi lấy địa điểm: {e}")
        return None
    
def get_keywords():
    try:
        # Xác định phần bắt đầu từ khóa: tiêu đề "Từ khoá:"
        keyword_block = driver.find_elements(By.XPATH, "//div[contains(text(),'Từ khoá')]")
        if not keyword_block:
            return None

        # Tìm tất cả span trong button phía sau khối "Từ khoá"
        keyword_buttons = driver.find_elements(By.XPATH, "//div[contains(@class, 'sc-a3652268-3')]//button/span")
        keywords = [el.text.strip() for el in keyword_buttons if el.text.strip()]
        return ", ".join(keywords)
    except Exception as e:
        print(f"❌ Lỗi khi lấy từ khóa: {e}")
        return None

# Hàm crawl thông tin
def crawl_job_details(url):
    driver.get(url)

    try:
        # Bấm các nút nếu có
        try_click("Xem đầy đủ mô tả công việc")
        try_click("Xem thêm")
        time.sleep(0.5)

        # Lấy thông tin chính
        title = driver.find_element(By.CSS_SELECTOR, "h1[name='title']").text
        company = driver.find_element(By.XPATH, "/html/body/main/div/main/div[2]/div/div/div/div[2]/div/div[1]/div[2]/a").text.strip()
        salary = driver.find_element(By.CSS_SELECTOR, "span[name='label']").text
        location = get_locations()
        job_description = driver.find_element(By.XPATH, "/html/body/main/div/main/div[2]/div/div/div/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div").text.strip()
        job_requirements = driver.find_element(By.XPATH, "/html/body/main/div/main/div[2]/div/div/div/div[1]/div/div[1]/div/div[3]/div/div/div[2]/div").text.strip()

        # Lấy thông tin thêm
        date_posted = get_text_safe("//label[text()='NGÀY ĐĂNG']")
        industry = get_text_safe("//label[text()='NGÀNH NGHỀ']")
        field = get_text_safe("//label[text()='LĨNH VỰC']")
        experience = get_text_safe("//label[text()='SỐ NĂM KINH NGHIỆM TỐI THIỂU']")
        education = get_text_safe("//label[text()='TRÌNH ĐỘ HỌC VẤN TỐI THIỂU']")
        age = get_text_safe("//label[text()='ĐỘ TUỔI MONG MUỐN']")
        vacancy = get_text_safe("//label[text()='SỐ LƯỢNG TUYỂN DỤNG']")
        work_time = get_text_safe("//label[text()='GIỜ LÀM VIỆC']")
        level = get_text_safe("//label[text()='CẤP BẬC']")
        skills = get_text_safe("//label[text()='KỸ NĂNG']")
        language = get_text_safe("//label[text()='NGÔN NGỮ TRÌNH BÀY HỒ SƠ']")
        nationality = get_text_safe("//label[text()='QUỐC TỊCH']")
        gender = get_text_safe("//label[text()='GIỚI TÍNH']")
        marital_status = get_text_safe("//label[text()='TÌNH TRẠNG HÔN NHÂN']")
        work_date = get_text_safe("//label[text()='NGÀY LÀM VIỆC']")
        work_type = get_text_safe("//label[text()='LOẠI HÌNH LÀM VIỆC']")
        keyword = get_keywords()

        return [title, company, salary, location, job_description, job_requirements, date_posted, industry, field,
                experience, education, age, vacancy, work_time, level, skills, language, nationality, gender,
                marital_status, work_date, work_type, keyword ]
    except Exception as e:
        print(f"❌ Lỗi khi crawl job từ {url}: {e}")
        return None

# Lưu vào CSV
def save_to_csv(data, filename=output_csv_filename):
    headers = ["Title", "Company", "Salary", "Location", "Job Description", "Job Requirements", "Date Posted", "Industry", "Field",
               "Experience", "Education", "Age", "Vacancy", "Work Time", "Level", "Skills", "Language",
               "Nationality", "Gender", "Marital Status", "Work Date", "Work Type", "Keyword"]
    
    file_exists = os.path.isfile(filename)
    
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(headers)  # Ghi tiêu đề nếu file chưa có
        writer.writerow(data)

# Thực thi crawl
counter = 0
for link in job_links:
    data = crawl_job_details(link)
    if data:
        save_to_csv(data)
        counter += 1
        print(f"✅ Đã lưu {counter} job.")

driver.quit()
