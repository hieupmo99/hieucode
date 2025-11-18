from bs4 import BeautifulSoup
import requests
import pandas as pd
import sqlite3
from more_itertools import chunked

url = "https://vnexpress.net/"

response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

a_list = soup.find_all("a")
tuple_data = set()
list_data = []

for a in a_list:
    img = a.find("img")
    if img:
        src = img.get("src")
        title = a.get("title")
        link = a.get("href")

        # Only process if we have all required data
        if src:
            tuple_data.add((title, link, src))
            list_data.append({"title": title, "link": link, "src": src})
            print(f" title: {title}, link: {link}, src: {src}")

tuple_list = list(tuple_data)
def divide_data(tuple_list, batch_size):
    for i in range(0, len(tuple_list), batch_size):
        yield tuple_list[i:i+batch_size]
        
divided_data_batch = divide_data(tuple_list, 10)

# Insert data in batches
if divided_data_batch:
    with sqlite3.connect("app/hieudb.db", timeout=10) as conn:
        try:
            print("Inserting data...")
            cursor = conn.cursor()
            insert_query = (
                "INSERT OR IGNORE INTO vnexpress(title, link, src) VALUES (?, ?, ?)"
            )
            # Use chunked to divide into batches of 10
            for data in divided_data_batch:
                cursor.executemany(insert_query, data)
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error inserting data: {e}")


# Create DataFrame and save to CSV
if list_data:
    df = pd.DataFrame(list_data)
    df = df.drop_duplicates()
    df.to_csv("/Users/op-lt-0378/Documents/hieucode/hieu.csv", index=False, encoding="utf-8")
    
print("Done")

