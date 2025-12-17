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
    schedule_interval='0 4 * * *',  # Every day at 11 AM GMT+7 (4 AM UTC)
    catchup=False,
    tags=['crawler', 'vnexpress', 'daily'],
)


def start_kafka_if_needed():
    """Start Kafka brokers if not running"""
    import subprocess
    import time
    
    print("🔍 Checking Kafka brokers status...")
    
    # Check if Kafka containers are running
    result = subprocess.run(
        ['docker', 'ps', '--filter', 'name=kafka', '--format', '{{.Names}}'],
        capture_output=True,
        text=True
    )
    
    running_brokers = result.stdout.strip().split('\n')
    running_count = len([b for b in running_brokers if b])
    
    if running_count < 3:
        print(f"⚠️  Only {running_count}/3 Kafka brokers running. Starting...")
        for broker in ['kafka-1', 'kafka-2', 'kafka-3']:
            subprocess.run(['docker', 'start', broker], check=False)
        print("⏳ Waiting 20 seconds for Kafka to start...")
        time.sleep(20)
        print("✅ Kafka brokers started")
    else:
        print(f"✅ All Kafka brokers already running ({running_count}/3)")


def start_spark_if_needed():
    """Start Spark streaming if not running"""
    import subprocess
    import time
    
    print("🔍 Checking Spark status...")
    
    # Check if Spark container is running
    result = subprocess.run(
        ['docker', 'ps', '--filter', 'name=spark', '--format', '{{.Names}}'],
        capture_output=True,
        text=True
    )
    
    if 'spark' not in result.stdout:
        print("⚠️  Spark not running. Starting...")
        subprocess.run(['docker', 'start', 'spark'], check=False)
        print("⏳ Waiting 10 seconds for Spark to start...")
        time.sleep(10)
        print("✅ Spark started")
    else:
        print("✅ Spark already running")


def ensure_crawler_container():
    """Ensure crawler container is running"""
    import subprocess
    import time
    
    print("🔍 Checking crawler container...")
    
    result = subprocess.run(
        ['docker', 'ps', '--filter', 'name=crawler', '--format', '{{.Names}}'],
        capture_output=True,
        text=True
    )
    
    if 'crawler' not in result.stdout:
        print("⚠️  Crawler container not running. Starting...")
        subprocess.run(['docker', 'start', 'crawler'], check=False)
        print("⏳ Waiting 5 seconds for crawler to start...")
        time.sleep(5)
        print("✅ Crawler container started")
    else:
        print("✅ Crawler container already running")


def check_kafka_health():
    """Check if Kafka cluster is healthy with retry logic"""
    import time
    from kafka import KafkaConsumer
    from kafka.errors import NoBrokersAvailable
    
    max_retries = 3
    retry_delay = 10
    
    for attempt in range(max_retries):
        print(f"🔍 Kafka health check (attempt {attempt + 1}/{max_retries})...")
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
            if attempt < max_retries - 1:
                print(f"⚠️  Kafka not ready. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print("❌ Kafka brokers not available after retries")
                raise Exception("Kafka cluster is not healthy")
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️  Health check failed: {e}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print(f"❌ Kafka health check failed after retries: {e}")
                raise


def run_crawler():
    """Run the VnExpress crawler in the crawler container"""
    import subprocess
    import time
    
    print("🚀 Starting VnExpress crawler in crawler container...")
    
    # Execute the crawler script inside the crawler container
    # This runs in background and we monitor it
    result = subprocess.Popen(
        ['docker', 'exec', 'crawler', 'python', '/opt/app/mass_crawling.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait a bit to ensure crawler starts
    time.sleep(5)
    
    # Check if process is still running (crawler started successfully)
    poll = result.poll()
    if poll is not None:
        # Process ended quickly, likely an error
        stdout, stderr = result.communicate()
        print(f"❌ Crawler failed to start:\nSTDOUT: {stdout}\nSTDERR: {stderr}")
        raise Exception("Crawler failed to start")
    
    print("✅ Crawler started successfully in container")
    print("📊 Crawler will run and send articles to Kafka")
    print("⏱️  Letting crawler run for 60 seconds...")
    
    # Let crawler run for a while (adjust duration as needed)
    time.sleep(60)
    
    # Stop the crawler after 60 seconds
    print("⏹️  Stopping crawler...")
    subprocess.run(['docker', 'exec', 'crawler', 'pkill', '-f', 'mass_crawling.py'],
                   check=False)
    
    print("✅ Crawler execution completed")


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


# Task 0: Start required services (run in parallel)
start_kafka = PythonOperator(
    task_id='start_kafka',
    python_callable=start_kafka_if_needed,
    dag=dag,
)

start_spark = PythonOperator(
    task_id='start_spark',
    python_callable=start_spark_if_needed,
    dag=dag,
)

start_crawler_container = PythonOperator(
    task_id='start_crawler_container',
    python_callable=ensure_crawler_container,
    dag=dag,
)

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
# Start all services in parallel, then check health, crawl, verify, and complete
[start_kafka, start_spark, start_crawler_container] >> check_kafka >> \
    crawl_vnexpress >> check_spark >> log_completion
