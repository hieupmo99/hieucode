# 🚀 Airflow Setup - Complete!

## ✅ What Was Created

### 1. Airflow Docker Image
- **Location**: `airflow/Dockerfile`
- **Features**: 
  - Apache Airflow 2.8.0
  - Chrome + ChromeDriver for Selenium
  - Python packages: selenium, beautifulsoup4, kafka-python, pandas

### 2. Daily Crawler DAG
- **Location**: `dags/daily_crawler.py`
- **Schedule**: Every day at 6:00 AM
- **Tasks**:
  1. Check Kafka health
  2. Run VnExpress crawler (Selenium)
  3. Verify Spark processing
  4. Log completion

### 3. Docker Compose Updates
- **PostgreSQL**: Database for Airflow metadata
- **Airflow Webserver**: UI at http://localhost:8081
- **Airflow Scheduler**: Runs DAGs on schedule

### 4. Management Scripts
- `setup-airflow.sh` - Initialize Airflow (one-time)
- `pipeline.sh` - Manage all services

## 🚀 How to Start

### Step 1: Start Docker Desktop
**⚠️ Docker must be running first!**

1. Open **Docker Desktop** app
2. Wait for it to start (whale icon in menu bar)
3. Verify: `docker ps` should work

### Step 2: Setup Airflow

```bash
cd ~/Documents/hieucode
./setup-airflow.sh
```

This will take **5-10 minutes** first time (building image with Chrome).

### Step 3: Access Airflow UI

Open: **http://localhost:8081**

- Username: `admin`
- Password: `admin`

### Step 4: Trigger DAG

1. Find `vnexpress_daily_crawler` in DAG list
2. Toggle it ON (switch on left)
3. Click ▶️ to trigger manually
4. Watch it run in Graph view!

## 📊 Complete Pipeline Flow

```
Airflow (6 AM) 
    ↓
Run Crawler
    ↓
Scrape VnExpress Articles
    ↓
Send to Kafka (vnexpress_topic)
    ↓
Spark Consumes & Processes
    ↓
Write to SQLite
    ↓
Dashboard Shows New Articles (auto-refresh)
```

## 🎮 Quick Commands

```bash
# ============================================
# START EVERYTHING
# ============================================
cd ~/Documents/hieucode
./pipeline.sh start

# ============================================
# CHECK STATUS
# ============================================
./pipeline.sh status

# ============================================
# OPEN UIs
# ============================================
./pipeline.sh airflow     # http://localhost:8081
./pipeline.sh kafka-ui    # http://localhost:8080
./pipeline.sh dashboard   # http://localhost:5000

# ============================================
# VIEW LOGS
# ============================================
./pipeline.sh logs airflow-webserver
./pipeline.sh logs airflow-scheduler

# ============================================
# STOP EVERYTHING
# ============================================
./pipeline.sh stop
```

## 📈 What You'll See

### After DAG Runs:

1. **Airflow UI** (http://localhost:8081)
   - DAG run shows green (success)
   - Each task shows duration and logs

2. **Kafka UI** (http://localhost:8080)
   - New messages in `vnexpress_topic`
   - Partition consumption stats

3. **Dashboard** (http://localhost:5000)
   - "Articles Today" count increases
   - New articles appear in "Recent Articles"
   - Charts update with today's data

## 🔧 Services Overview

| Service | Port | Purpose |
|---------|------|---------|
| Kafka UI | 8080 | Monitor Kafka topics |
| Airflow UI | 8081 | Manage DAGs & schedules |
| Dashboard | 5000 | View pipeline results |
| Kafka Brokers | 19092, 29092, 39092 | Message queue |
| PostgreSQL | 5432 | Airflow metadata |

## 🎯 Testing the Setup

### Test 1: Manual DAG Run

```bash
# 1. Start services
./pipeline.sh start

# 2. Wait 2 minutes for everything to start

# 3. Open Airflow UI
./pipeline.sh airflow

# 4. Find vnexpress_daily_crawler
# 5. Click play button ▶️
# 6. Watch it run!
```

### Test 2: Check Results

```bash
# View crawled articles
sqlite3 app/hieudb.db "SELECT COUNT(*) FROM vnexpress WHERE date(timestamp) = date('now');"

# Check dashboard
open http://localhost:5000

# See "Articles Today" number
```

### Test 3: View Logs

```bash
# Real-time Airflow logs
./pipeline.sh logs airflow-scheduler

# Or in UI: Click task → View Log
```

## 🐛 Troubleshooting

### "Cannot connect to Docker daemon"
**Solution**: Start Docker Desktop app first

### Airflow UI shows 502 Bad Gateway
**Solution**: Wait 2-3 minutes, services are still starting

### DAG not appearing
**Solution**:
```bash
# Check for errors
docker-compose logs airflow-webserver | grep ERROR
docker-compose logs airflow-scheduler | grep ERROR

# Restart
./pipeline.sh restart
```

### DAG fails with "No module named 'selenium'"
**Solution**: Rebuild Airflow image
```bash
docker-compose build airflow-webserver airflow-scheduler --no-cache
./pipeline.sh restart airflow
```

### Chrome/Selenium errors
**Solution**: Image includes Chrome. Check logs:
```bash
docker-compose exec airflow-webserver google-chrome --version
docker-compose exec airflow-webserver chromedriver --version
```

## 📅 Schedule Details

**Default**: 6:00 AM daily (`0 6 * * *`)

**To change** - Edit `dags/daily_crawler.py`:

```python
schedule_interval='0 6 * * *',  # <-- Change this
```

**Examples**:
- `'0 */4 * * *'` - Every 4 hours
- `'0 9,18 * * *'` - 9 AM and 6 PM
- `'@hourly'` - Every hour
- `'@daily'` - Midnight daily
- `None` - Manual trigger only

## ✅ Success Checklist

After running `./setup-airflow.sh`:

- [ ] Docker is running
- [ ] Airflow UI accessible at http://localhost:8081
- [ ] Can login with admin/admin
- [ ] DAG `vnexpress_daily_crawler` appears
- [ ] Can toggle DAG ON
- [ ] Can trigger DAG manually
- [ ] DAG runs successfully (all green)
- [ ] Dashboard shows new articles
- [ ] Kafka UI shows messages

## 🎉 You're All Set!

Your automated crawling pipeline is ready:

✅ **Airflow** will run crawler every day at 6 AM
✅ **Kafka** will queue all scraped articles
✅ **Spark** will process and store in SQLite
✅ **Dashboard** will show results in real-time

**Just keep Docker running!**

## 📚 Next Steps

1. **Monitor daily runs** in Airflow UI
2. **Check dashboard** after 6 AM to see new articles
3. **Review logs** if any DAG fails
4. **Adjust schedule** if needed
5. **Add more DAGs** for other news sources

---

**Questions?** Check `AIRFLOW_GUIDE.md` for detailed docs!
