import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

chrome_options = Options()

chrome_options.add_argument("--headless=new")
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
driver.get('https://www.vietnamworks.com/')
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.TAG_NAME, 'body'))
)
time.sleep(2)


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

def get_text_safe(xpath):
    try:
        labels = driver.find_elements(By.XPATH, xpath)
        if labels:
            sibling = labels[0].find_element(By.XPATH, "following-sibling::p")
            return sibling.text.strip()
    except:
        return None
    return None

def get_skills():
    try:
        p = driver.find_element(By.XPATH, "//label[text()='KỸ NĂNG']/following-sibling::p")
        text = p.text.strip()
        skills = [s.strip() for s in text.split(",") if s.strip()]
        return skills
    except Exception as e:
        print(f"❌ Lỗi khi lấy ký năng: {e}")
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
        return keywords
    except Exception as e:
        print(f"❌ Lỗi khi lấy từ khóa: {e}")
        return None
    
def crawl_job_details(url):
    driver.get(url)

    try:
        # Bấm các nút nếu có
        try_click("Xem đầy đủ mô tả công việc")
        try_click("Xem thêm")
        time.sleep(1)

        # Lấy thông tin chính
        title = driver.find_element(By.CSS_SELECTOR, "h1[name='title']").text
        company = driver.find_element(By.XPATH, "/html/body/main/div/main/div[2]/div/div/div/div[2]/div/div[1]/div[2]/a").text.strip()
        salary = driver.find_element(By.CSS_SELECTOR, "span[name='label']").text
        location = get_locations()
        job_description = driver.find_element(By.XPATH, "/html/body/main/div/main/div[2]/div/div/div/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div").text.strip()
        job_requirements = driver.find_element(By.XPATH, "/html/body/main/div/main/div[2]/div/div/div/div[1]/div/div[1]/div/div[3]/div/div/div[2]/div").text.strip()

        # Lấy thông tin thêm
        data = {
            "title": title,
            "company": company,
            "salary": salary,
            "location": location,
            "job_description": job_description,
            "job_requirements": job_requirements,
            "date_posted": get_text_safe("//label[text()='NGÀY ĐĂNG']"),
            "industry": get_text_safe("//label[text()='NGÀNH NGHỀ']"),
            "field": get_text_safe("//label[text()='LĨNH VỰC']"),
            "experience": get_text_safe("//label[text()='SỐ NĂM KINH NGHIỆM TỐI THIỂU']"),
            "education": get_text_safe("//label[text()='TRÌNH ĐỘ HỌC VẤN TỐI THIỂU']"),
            "age": get_text_safe("//label[text()='ĐỘ TUỔI MONG MUỐN']"),
            "vacancy": get_text_safe("//label[text()='SỐ LƯỢNG TUYỂN DỤNG']"),
            "work_time": get_text_safe("//label[text()='GIỜ LÀM VIỆC']"),
            "level": get_text_safe("//label[text()='CẤP BẬC']"),
            "skills": get_skills(),
            "language": get_text_safe("//label[text()='NGÔN NGỮ TRÌNH BÀY HỒ SƠ']"),
            "nationality": get_text_safe("//label[text()='QUỐC TỊCH']"),
            "gender": get_text_safe("//label[text()='GIỚI TÍNH']"),
            "marital_status": get_text_safe("//label[text()='TÌNH TRẠNG HÔN NHÂN']"),
            "work_date": get_text_safe("//label[text()='NGÀY LÀM VIỆC']"),
            "work_type": get_text_safe("//label[text()='LOẠI HÌNH LÀM VIỆC']"),
            "keywords": get_keywords()
        }
        return data

    except Exception as e:
        print(f"❌ Lỗi khi crawl job từ {url}: {e}")
        return None
    
def crawl_job_details_json(url):
    result = crawl_job_details(url)
    if result is None:
        return None
    return json.dumps(result, ensure_ascii=False, indent=4)

def close_driver():
    try:
        driver.quit()
    except Exception:
        pass

if __name__ == "__main__":
    url = "https://www.vietnamworks.com/technical-sales-manager-pharmaceutical-and-nutraceutical-ingredients-1909695-jv?source=searchResults&searchType=2&placement=1909695&sortBy=latest"
    json_str = crawl_job_details_json(url)
    if json_str:
        print(json_str)
    else:
        print("❌ Crawl thất bại, không có dữ liệu JSON")