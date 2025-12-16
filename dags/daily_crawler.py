"""
Daily VnExpress Crawler DAG
Runs every day at 6 AM to crawl new articles
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
import sys
import os

# Add app directory to Python path
sys.path.insert(0, '/opt/airflow/app')

# Default arguments
default_args = {
    'owner': 'hieucode',
    'depends_on_past': False,
    'start_date': datetime(2025, 12, 16),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG
dag = DAG(
    'vnexpress_daily_crawler',
    default_args=default_args,
    description='Crawl VnExpress articles daily',
    schedule_interval='0 6 * * *',  # Every day at 6 AM
    catchup=False,
    tags=['crawler', 'vnexpress', 'daily'],
)


def check_kafka_health():
    """Check if Kafka cluster is healthy"""
    from kafka import KafkaConsumer
    from kafka.errors import NoBrokersAvailable
    
    try:
        consumer = KafkaConsumer(
            bootstrap_servers=['kafka-1:9092', 'kafka-2:9092', 'kafka-3:9092'],
            consumer_timeout_ms=5000
        )
        topics = consumer.topics()
        consumer.close()
        print(f"✅ Kafka is healthy. Topics: {topics}")
        return True
    except NoBrokersAvailable:
        print("❌ Kafka brokers not available")
        raise Exception("Kafka cluster is not healthy")
    except Exception as e:
        print(f"❌ Kafka health check failed: {e}")
        raise


def run_crawler():
    """Run the VnExpress crawler"""
    import sys
    import os
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from bs4 import BeautifulSoup
    import time
    from kafka import KafkaProducer
    import json
    
    # Kafka producer setup
    producer = KafkaProducer(
        bootstrap_servers=['kafka-1:9092', 'kafka-2:9092', 'kafka-3:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all',
        retries=3
    )
    
    # Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Initialize driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🚀 Starting VnExpress crawler...")
        url = 'https://vnexpress.net/'
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "title-news"))
        )
        
        # Scroll to load more content
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        articles = soup.find_all('article', class_='item-news')
        
        count = 0
        for article in articles:
            try:
                title_elem = article.find('h3', class_='title-news')
                if not title_elem:
                    continue
                
                link_elem = title_elem.find('a')
                if not link_elem:
                    continue
                
                title = link_elem.get('title', '').strip()
                link = link_elem.get('href', '').strip()
                
                # Get image
                img_elem = article.find('img')
                img_src = img_elem.get('data-src', '') if img_elem else ''
                if not img_src and img_elem:
                    img_src = img_elem.get('src', '')
                
                if title and link:
                    data = {
                        'title': title,
                        'link': link,
                        'src': img_src,
                        'timestamp': int(time.time())
                    }
                    
                    # Send to Kafka
                    producer.send('vnexpress_topic', value=data)
                    count += 1
                    
                    if count % 10 == 0:
                        print(f"📊 Crawled {count} articles...")
            
            except Exception as e:
                print(f"⚠️  Error processing article: {e}")
                continue
        
        producer.flush()
        print(f"✅ Successfully crawled {count} articles")
        return count
        
    except Exception as e:
        print(f"❌ Crawler failed: {e}")
        raise
    
    finally:
        driver.quit()
        producer.close()


def check_spark_processing():
    """Verify Spark is processing the data"""
    import subprocess
    import time
    
    print("🔍 Checking Spark processing...")
    time.sleep(10)  # Wait for Spark to process
    
    result = subprocess.run(
        ['docker', 'exec', 'spark', 'ps', 'aux'],
        capture_output=True,
        text=True
    )
    
    if 'spark-submit' in result.stdout:
        print("✅ Spark is processing data")
    else:
        print("⚠️  Spark might not be running")


# Task 1: Check Kafka health
check_kafka = PythonOperator(
    task_id='check_kafka_health',
    python_callable=check_kafka_health,
    dag=dag,
)

# Task 2: Run crawler
crawl_vnexpress = PythonOperator(
    task_id='crawl_vnexpress',
    python_callable=run_crawler,
    dag=dag,
)

# Task 3: Check Spark
check_spark = PythonOperator(
    task_id='check_spark_processing',
    python_callable=check_spark_processing,
    dag=dag,
)

# Task 4: Log completion
log_completion = BashOperator(
    task_id='log_completion',
    bash_command='echo "✅ Daily crawl completed at $(date)"',
    dag=dag,
)

# Set task dependencies
check_kafka >> crawl_vnexpress >> check_spark >> log_completion
