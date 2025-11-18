from re import A
from bs4 import BeautifulSoup
from pandas.core.dtypes.common import is_1d_only_ea_dtype
import requests
import pandas as pd
import sqlite3
import selenium
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
# from webdriver_manager.chrome import ChromeDriverManager

from producer import send_crawled_item


# Kafka producer configuration is handled in producer.send_crawled_item
# chrome_driver_path = shutil.which("chromedriver")
# if chrome_driver_path:
#     print(f"Chrome driver path: {chrome_driver_path}")
# else:
#     print("Chrome driver not found")

url = "https://vnexpress.net/"

# Find ChromeDriver in common locations
import os
chromedriver_paths = [
    "/opt/homebrew/bin/chromedriver",
    "/usr/bin/chromedriver",
    "/usr/local/bin/chromedriver",
    os.environ.get("CHROMEDRIVER_PATH", "")
]

chromedriver_path = None
for path in chromedriver_paths:
    if path and os.path.exists(path) and os.access(path, os.X_OK):
        chromedriver_path = path
        break

# If not found, try to copy from /usr/bin to /opt/homebrew/bin
if not chromedriver_path:
    if os.path.exists("/usr/bin/chromedriver"):
        os.makedirs("/opt/homebrew/bin", exist_ok=True)
        import shutil
        shutil.copy("/usr/bin/chromedriver", "/opt/homebrew/bin/chromedriver")
        os.chmod("/opt/homebrew/bin/chromedriver", 0o755)
        chromedriver_path = "/opt/homebrew/bin/chromedriver"
    elif os.path.exists("/usr/local/bin/chromedriver"):
        os.makedirs("/opt/homebrew/bin", exist_ok=True)
        import shutil
        shutil.copy("/usr/local/bin/chromedriver", "/opt/homebrew/bin/chromedriver")
        os.chmod("/opt/homebrew/bin/chromedriver", 0o755)
        chromedriver_path = "/opt/homebrew/bin/chromedriver"

if not chromedriver_path:
    raise FileNotFoundError("ChromeDriver not found in any expected location")

print(f"Using ChromeDriver at: {chromedriver_path}")
service = Service(chromedriver_path)

# Configure Chrome options for Docker (headless mode)
chrome_options = Options()
if os.path.exists("/.dockerenv") or os.environ.get('DOCKER_ENV'):
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    print("Running in Docker - using headless mode")

driver = webdriver.Chrome(service=service, options=chrome_options)
driver.implicitly_wait(10)
print("Driver initialized")
print(f"Driver path: {driver.service.path}")
driver.get(url)


try:
    revealed = driver.find_element(By.CLASS_NAME, "hamburger")
    driver.find_element(By.XPATH, "//span[@class='hamburger']").click()
    WebDriverWait(driver, timeout=10).until(lambda _ : revealed.is_displayed())
except Exception as e:
    print(f"Error: {e}")


page_source = driver.page_source

soup = BeautifulSoup(page_source, "html.parser")
# print(soup.prettify())
link_list = []
menu_list = soup.find(class_ = "wrap-all-menu")
menu_links = menu_list.find_all("a")

for link in menu_links:
    click_link = link["href"]
    link_list.append(click_link)
    print(f"Link: {click_link}")
print(link_list)

tuple_data = set()
list_data = []
paper_count = 0
for A_link in link_list:
    print(f"Link: {A_link}")
    try:
        driver.set_page_load_timeout(15)
        driver.get(A_link)
        WebDriverWait(driver, timeout=3).until(lambda _ :(driver.find_element(By.TAG_NAME, "body")).is_displayed())
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        a_list = soup.find_all("a")
        for a in a_list:
            img = a.find("img")
            if img:
                src = img.get("src")
                title = a.get("title")
                link = a.get("href")
                if src:
                    msg ={
                        "title": title,
                        "link": link,
                        "src": src,
                        "timestamp": time.time()
                    }
                    send_crawled_item(msg)
                 
                    print(f'Sent to Kafka: {msg}')
                    tuple_data.add((title, link, src))
                    list_data.append({"title": title, "link": link, "src": src})
                    print(f" title: {title}, link: {link}, src: {src}")
                    paper_count += 1
                    print(f"Paper count: {paper_count}")
    except TimeoutException as e:
        print(f"Timeout: {e}")
        continue
    except Exception as e:
        print(f"Error: {e}")
        continue


driver.quit()


tuple_list = list(tuple_data)
def divide_data(tuple_list, batch_size):
    for i in range(0, len(tuple_list), batch_size):
        yield tuple_list[i:i+batch_size]

divided_data_batch = divide_data(tuple_list, 10)

# Insert data in batches
if divided_data_batch:
    with sqlite3.connect("hieudb.db", timeout=10) as conn:
        try:
            print("Inserting data...")
            cursor = conn.cursor()
            insert_query = (
                "INSERT OR IGNORE INTO vnexpress(title, link, src) VALUES (?, ?, ?)"
            )
            for data in divided_data_batch:
                cursor.executemany(insert_query, data)
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error inserting data: {e}")

csv_path = Path("/app/masscrawling.csv")
if not csv_path.exists():
    with open(csv_path, "w") as f:
        if list_data:
            df = pd.DataFrame(list_data)
            df = df.drop_duplicates()
            df.to_csv(csv_path, index=False, encoding="utf-8")
    print("Data saved to CSV")
else:
    print("CSV file already exists")



print("Done")

