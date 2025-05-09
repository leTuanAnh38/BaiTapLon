from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import schedule
import datetime

def crawl_data():
    print(f"Bắt đầu chạy lúc {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    options = Options()
    options.add_experimental_option("detach", True)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 15)

    # --- Bước 1: Mở trang chủ ---
    driver.get("https://alonhadat.com.vn/")
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "province")))

    # --- Bước 2: Chọn tỉnh/thành phố ---
    province_select = Select(driver.find_element(By.CLASS_NAME, "province"))
    province_select.select_by_visible_text("Đà Nẵng")

    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "property-type")))
    property_select = Select(driver.find_element(By.CLASS_NAME, "property-type"))
    property_select.select_by_visible_text("Phòng trọ, nhà trọ")

    # --- Bước 3: Click nút tìm kiếm ---
    search_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btnsearch")))
    search_button.click()

    # --- Bước 4,5: Bắt đầu thu thập dữ liệu các trang ---
    data = []
    page = 1
    while True:
        print(f"\nĐang thu thập trang {page}")
        start_time = datetime.datetime.now()
        print(f"Bắt đầu lúc {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".content-item.item")))
        except:
            print("Không tìm thấy dữ liệu hoặc hết trang.")
            break

        listings = driver.find_elements(By.CSS_SELECTOR, ".content-item.item")
        if not listings:
            print("Không có dữ liệu, hoặc đã hết các trang.")
            break

        for listing in listings:
            try:
                title = listing.find_element(By.CSS_SELECTOR, ".ct_title").text.strip()
                description = listing.find_element(By.CSS_SELECTOR, ".ct_brief").text.strip()

                try:
                    area = listing.find_element(By.CSS_SELECTOR, ".road-width").text.strip()
                except:
                    area = "Không có thông tin"

                try:
                    price = listing.find_element(By.CSS_SELECTOR, ".ct_price").text.strip()
                except:
                    price = "Không có giá"

                try:
                    address = listing.find_element(By.CSS_SELECTOR, ".ct_dis").text.strip()
                except:
                    address = "Không có địa chỉ"

                data.append([title, description, area, price, address])
            except Exception as e:
                print(f"Lỗi lấy tin: {e}")
                continue

        # --- Xử lý phân trang ---
        try:
            pagination_links = driver.find_elements(By.CSS_SELECTOR, "div.page a")
            current_index = -1
            next_page_url = None

            for i, link in enumerate(pagination_links):
                if "active" in link.get_attribute("class"):
                    current_index = i
                    break

            if 0 <= current_index < len(pagination_links) - 1:
                next_page_url = pagination_links[current_index + 1].get_attribute("href")
                print(f"Chuyển sang trang kế tiếp: {next_page_url}")
                driver.get(next_page_url)
                WebDriverWait(driver, 10).until(EC.staleness_of(listings[0]))
                page += 1
            else:
                print("Đã đến trang cuối hoặc không có trang kế tiếp.")
                break
        except Exception as e:
            print(f"Lỗi phân trang: {e}")
            break

    driver.quit()

    # --- Bước 6: Ghi ra Excel ---
    df = pd.DataFrame(data, columns=["Tiêu đề", "Mô tả", "Diện tích", "Giá", "Địa chỉ"])
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"alonhadat_danang_{today}.xlsx"
    df.to_excel(filename, index=False)
    print(f"\nĐã lưu dữ liệu vào: {filename}")

# --- Bước 7: Lên lịch chạy tự động ---
schedule.every().day.at("10:44").do(crawl_data)

print("Đang chờ đến 06:00 mỗi ngày để thu thập dữ liệu... Nhấn Ctrl+C để dừng.")
while True:
    schedule.run_pending()
    time.sleep(60)
