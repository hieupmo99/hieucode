# 🚀 Airflow Setup Guide

## Overview

Airflow is configured to run the VnExpress crawler automatically every day at 6 AM.

## 📋 Quick Start

### 1. Setup Airflow (First Time Only)

```bash
cd ~/Documents/hieucode
./setup-airflow.sh
```

This will:
- Build Airflow Docker image with Chrome/Selenium
- Initialize PostgreSQL database
- Create admin user (username: `admin`, password: `admin`)
- Start Airflow webserver and scheduler

### 2. Access Airflow UI

Open: **http://localhost:8081**

- **Username**: `admin`
- **Password**: `admin`

### 3. View DAGs

The `vnexpress_daily_crawler` DAG should appear in the UI:
- Schedule: Every day at 6:00 AM
- Tasks: Check Kafka → Crawl VnExpress → Check Spark → Log Completion

## 🎯 Using the Pipeline Management Script

```bash
# Start all services (Kafka, Spark, Airflow)
./pipeline.sh start

# Start only Airflow
./pipeline.sh start airflow

# Check status
./pipeline.sh status

# View Airflow logs
./pipeline.sh logs airflow-webserver
./pipeline.sh logs airflow-scheduler

# Open Airflow UI
./pipeline.sh airflow

# Stop all services
./pipeline.sh stop
```

## 📊 DAG Details

### vnexpress_daily_crawler

**Schedule**: `0 6 * * *` (Every day at 6 AM)

**Tasks**:
1. **check_kafka_health**: Verifies Kafka cluster is healthy
2. **crawl_vnexpress**: Runs Selenium crawler, scrapes articles, sends to Kafka
3. **check_spark_processing**: Verifies Spark is processing the data
4. **log_completion**: Logs completion timestamp

**Flow**:
```
Check Kafka → Crawl VnExpress → Check Spark → Log Complete
```

## 🔧 Manual DAG Trigger

1. Go to http://localhost:8081
2. Find `vnexpress_daily_crawler` in the DAG list
3. Click the ▶️ Play button to trigger manually
4. View progress in the Graph or Grid view

## 📁 File Structure

```
hieucode/
├── airflow/
│   ├── Dockerfile          # Custom Airflow image with Chrome
│   └── requirements.txt    # Python dependencies
├── dags/
│   └── daily_crawler.py    # Main DAG definition
├── logs/                   # Airflow logs
├── setup-airflow.sh        # Setup script
└── pipeline.sh             # Management script
```

## 🐛 Troubleshooting

### Airflow UI not accessible

```bash
# Check if services are running
docker-compose ps

# Restart Airflow
./pipeline.sh restart

# Check logs
./pipeline.sh logs airflow-webserver
```

### DAG not appearing

```bash
# Check for Python syntax errors
docker-compose exec airflow-webserver airflow dags list

# View DAG-specific errors
docker-compose exec airflow-webserver airflow dags list-import-errors
```

### DAG fails during execution

```bash
# View task logs in Airflow UI
# OR check logs directly:
docker-compose logs -f airflow-scheduler

# Check specific task instance logs
docker-compose exec airflow-webserver airflow tasks test vnexpress_daily_crawler crawl_vnexpress 2025-12-16
```

### Chrome/Selenium issues

```bash
# Enter Airflow container
docker-compose exec airflow-webserver bash

# Test Chrome
google-chrome --version

# Test ChromeDriver
chromedriver --version

# Test Selenium
python3 -c "from selenium import webdriver; print('Selenium OK')"
```

## 🔄 Workflow

### Daily Automated Flow

```
6:00 AM
  ↓
Airflow Triggers DAG
  ↓
Check Kafka Healthy
  ↓
Run Crawler (Selenium + Chrome)
  ↓
Scrape VnExpress Articles
  ↓
Send to Kafka Topic (vnexpress_topic)
  ↓
Spark Consumes from Kafka
  ↓
Spark Writes to SQLite
  ↓
Dashboard Auto-Refreshes (shows new articles)
```

## 📈 Monitoring

### View Execution History
- Go to Airflow UI → DAGs → vnexpress_daily_crawler
- Click on "Graph" or "Grid" view
- See all past runs with success/failure status

### Check Article Count
1. Open dashboard: http://localhost:5000
2. See "Articles Today" count increase after DAG runs

### View Logs
```bash
# Real-time logs
./pipeline.sh logs airflow-scheduler

# Or in Airflow UI: Click on task → View Log
```

## ⚙️ Configuration

### Change Schedule

Edit `dags/daily_crawler.py`:

```python
schedule_interval='0 6 * * *',  # Change this line
```

Examples:
- `'0 */6 * * *'` - Every 6 hours
- `'0 0 * * *'` - Midnight daily
- `'0 9,18 * * *'` - 9 AM and 6 PM daily
- `'@hourly'` - Every hour
- `None` - Manual trigger only

### Change Crawler Settings

Edit the `run_crawler()` function in `dags/daily_crawler.py`:
- Modify URL
- Change scroll count
- Adjust wait times
- Update parsing logic

## 🔐 Security

**Default credentials**:
- Airflow username: `admin`
- Airflow password: `admin`
- PostgreSQL username: `airflow`
- PostgreSQL password: `airflow`

**⚠️ Change these for production!**

## 📞 Commands Reference

```bash
# Setup (first time)
./setup-airflow.sh

# Start all services
./pipeline.sh start

# Start only Airflow
./pipeline.sh start airflow

# Stop all services
./pipeline.sh stop

# Check status
./pipeline.sh status

# View logs
./pipeline.sh logs airflow-webserver
./pipeline.sh logs airflow-scheduler

# Open UIs
./pipeline.sh airflow      # Airflow at :8081
./pipeline.sh kafka-ui     # Kafka UI at :8080
./pipeline.sh dashboard    # Dashboard at :5000

# Docker commands
docker-compose ps                    # Service status
docker-compose logs -f airflow-*     # All Airflow logs
docker-compose exec airflow-webserver bash  # Enter container

# Airflow CLI (inside container)
airflow dags list                    # List all DAGs
airflow dags trigger vnexpress_daily_crawler  # Trigger DAG
airflow tasks list vnexpress_daily_crawler    # List tasks
```

## 🎉 Success Indicators

After setup, you should see:
- ✅ Airflow UI accessible at http://localhost:8081
- ✅ DAG `vnexpress_daily_crawler` visible in UI
- ✅ DAG can be triggered manually
- ✅ Tasks complete successfully (green in Graph view)
- ✅ Dashboard shows new articles after DAG runs

## 📚 Resources

- Airflow Docs: https://airflow.apache.org/docs/
- DAG Writing: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html
- Operators: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/operators.html
