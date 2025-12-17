# Quick Reference: File Relationships

## 🎯 One-Line Summaries

| File | What It Does |
|------|--------------|
| **mass_crawling.py** | Selenium crawler that scrapes VnExpress and sends to Kafka |
| **producer.py** | Kafka producer helper (creates connection, sends messages) |
| **spark_app.py** | Reads from Kafka, processes, saves to SQLite database |
| **daily_crawler.py** | Airflow DAG that auto-starts services and runs crawler daily |
| **server.py** | Flask API backend for dashboard (stats, controls, logs) |
| **dashboard_enhanced.html** | Web UI with 4 tabs (Overview, Services, Logs, Articles) |
| **docker-compose.yml** | Orchestrates all 11 containers (Kafka, Spark, Airflow, etc.) |
| **hieudb.db** | SQLite database storing 7,534+ crawled articles |
| **Dockerfiles** | Build images for crawler, Spark, and Airflow containers |

---

## 🔄 Data Flow (Simplified)

```
VnExpress.net
     ↓
mass_crawling.py (Selenium scraper)
     ↓
producer.py (Kafka producer)
     ↓
Kafka Cluster (3 brokers, vnexpress_topic)
     ↓
spark_app.py (Spark Streaming)
     ↓
hieudb.db (SQLite database)
     ↓
server.py (Flask API)
     ↓
dashboard_enhanced.html (Web UI)
     ↓
👤 You see articles in browser
```

---

## 🎭 Who Talks to Who?

### **mass_crawling.py** talks to:
- ✅ VnExpress website (scrapes)
- ✅ producer.py (imports)
- ✅ Kafka cluster (sends messages)

### **spark_app.py** talks to:
- ✅ Kafka cluster (reads messages)
- ✅ hieudb.db (writes articles)

### **daily_crawler.py** (Airflow DAG) talks to:
- ✅ Docker (starts containers)
- ✅ Kafka (health checks)
- ✅ mass_crawling.py (executes)

### **server.py** talks to:
- ✅ hieudb.db (queries)
- ✅ Docker (starts/stops services)
- ✅ dashboard_enhanced.html (serves page)

### **dashboard_enhanced.html** talks to:
- ✅ server.py (API calls)
- ✅ Your browser (displays UI)

### **docker-compose.yml** talks to:
- ✅ All Dockerfiles (builds images)
- ✅ All services (orchestrates)

---

## 🏗️ Component Ownership

```
Crawler Layer:
├── mass_crawling.py        (main crawler script)
├── producer.py             (Kafka producer helper)
├── crawling.py             (standalone test version)
└── app/Dockerfile          (builds crawler container)

Streaming Layer:
├── spark_app.py            (Spark streaming processor)
├── spark/Dockerfile        (builds Spark container)
└── sqlite-jdbc.jar         (JDBC driver for SQLite)

Storage Layer:
└── hieudb.db              (SQLite database)

Orchestration Layer:
├── daily_crawler.py        (Airflow DAG)
├── airflow/Dockerfile      (builds Airflow container)
└── docker-compose.yml      (all services)

Monitoring Layer:
├── server.py               (Flask API)
└── dashboard_enhanced.html (Web UI)

Documentation:
├── ARCHITECTURE.md         (detailed guide)
├── DASHBOARD_USAGE.md      (dashboard guide)
├── AIRFLOW_AUTO_START.md   (DAG guide)
└── QUICK_REFERENCE.md      (this file)
```

---

## 🚦 Execution Paths

### **Path 1: Automatic Daily Crawl**
```
06:00 AM
  ↓
Airflow Scheduler wakes up
  ↓
daily_crawler.py triggers
  ↓
Starts: Kafka, Spark, Crawler (parallel)
  ↓
Checks: Kafka health
  ↓
Executes: mass_crawling.py
  ↓
Crawls VnExpress → Kafka → Spark → Database
  ↓
Done! ✅
```

### **Path 2: Manual Dashboard Start**
```
You click "Start Crawler" in Dashboard
  ↓
dashboard_enhanced.html → POST /api/crawler/start
  ↓
server.py → docker exec crawler python mass_crawling.py
  ↓
Crawls VnExpress → Kafka → Spark → Database
  ↓
Dashboard refreshes stats every 5 seconds
  ↓
You see article count increasing ✅
```

### **Path 3: Manual Command**
```
You run: docker exec crawler python /opt/app/mass_crawling.py
  ↓
Crawls VnExpress → Kafka → Spark → Database
  ↓
Check dashboard to see new articles ✅
```

---

## 🔌 Ports Reference

| Service | Port | Purpose |
|---------|------|---------|
| Kafka-1 | 19092 | Kafka broker 1 (external) |
| Kafka-2 | 29092 | Kafka broker 2 (external) |
| Kafka-3 | 39092 | Kafka broker 3 (external) |
| Kafka UI | 8080 | Web UI for Kafka monitoring |
| Airflow | 8081 | Airflow web UI (admin/admin) |
| Dashboard | 5000 | Flask dashboard UI |

---

## 📦 Container Network

All containers are on `kafka-net` network:

```
kafka-net (bridge network)
├── kafka-1          (hostname: kafka-1)
├── kafka-2          (hostname: kafka-2)
├── kafka-3          (hostname: kafka-3)
├── crawler          (hostname: crawler)
├── spark            (hostname: spark)
├── airflow-webserver
├── airflow-scheduler
├── postgres-airflow
└── kafka-ui
```

Services communicate using container names:
- `kafka-1:9092` instead of `localhost:19092`
- `spark` instead of `localhost`

---

## 🗄️ Database Schema

```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    link TEXT UNIQUE,              -- Prevents duplicates
    image TEXT,
    description TEXT,
    category TEXT,                  -- thoi-su, giai-tri, etc.
    timestamp INTEGER               -- Unix timestamp
);
```

**Current Stats**:
- Total: 7,534 articles
- Today: 2,457 articles
- This week: 2,457 articles

---

## 🎯 Key Kafka Details

**Topic**: `vnexpress_topic`
**Partitions**: 3 (distributed across 3 brokers)
**Format**: JSON messages

**Message Structure**:
```json
{
  "title": "Article title",
  "link": "https://vnexpress.net/...",
  "image": "https://...",
  "description": "Article summary",
  "category": "thoi-su",
  "timestamp": 1702809600
}
```

---

## 🔧 Common Commands

### Start Everything:
```bash
cd ~/Documents/hieucode
docker-compose up -d
```

### Stop Everything:
```bash
docker-compose down
```

### Start Crawler:
```bash
# Option 1: Dashboard (http://localhost:5000)
# Option 2: Airflow (http://localhost:8081)
# Option 3: Command
docker exec crawler python /opt/app/mass_crawling.py
```

### Check Logs:
```bash
docker logs crawler --tail 50
docker logs spark --tail 50
docker logs kafka-1 --tail 50
```

### Check Database:
```bash
sqlite3 ~/Documents/hieucode/app/hieudb.db
.tables                         # Show tables
SELECT COUNT(*) FROM articles;  # Total count
SELECT * FROM articles LIMIT 5; # Show recent
.quit
```

### Trigger Airflow DAG:
```bash
docker exec airflow-scheduler airflow dags trigger vnexpress_daily_crawler
```

---

## 🎬 What Happens When...

### **...you run `docker-compose up -d`:**
1. Starts Kafka cluster (3 brokers)
2. Starts PostgreSQL for Airflow
3. Starts Airflow webserver & scheduler
4. Starts Kafka UI
5. Starts Spark (begins streaming immediately)
6. Starts Crawler container (idle, waits for commands)

### **...you start the crawler:**
1. Chrome browser launches (headless)
2. Navigates to VnExpress categories
3. Scrolls down to load more articles
4. Extracts article data
5. Sends each article to Kafka
6. Continues until stopped

### **...Kafka receives a message:**
1. Assigns to one of 3 partitions
2. Replicates across brokers
3. Stores in partition log
4. Waits for consumers

### **...Spark reads from Kafka:**
1. Consumes messages in 10-second batches
2. Parses JSON to DataFrame
3. Checks if article already exists (by link)
4. Inserts new articles to SQLite
5. Skips duplicates

### **...you open the dashboard:**
1. Browser requests `http://localhost:5000`
2. server.py serves dashboard_enhanced.html
3. JavaScript loads and calls `/api/stats`
4. server.py queries hieudb.db
5. Returns JSON with counts
6. Dashboard displays stats
7. Refreshes every 5 seconds

---

## 🎓 Learning Path

**If you want to understand**:

**1. How scraping works** → Read `mass_crawling.py`
- See Selenium usage
- Understand scroll and extract logic

**2. How Kafka works** → Check `producer.py` and Kafka UI
- See producer configuration
- View topics and partitions at http://localhost:8080

**3. How Spark processes data** → Read `spark_app.py`
- See Kafka integration
- Understand streaming batches
- Check SQLite write logic

**4. How automation works** → Read `daily_crawler.py`
- See Airflow task definitions
- Understand DAG dependencies
- Check service startup logic

**5. How monitoring works** → Read `server.py` and `dashboard_enhanced.html`
- See Flask API endpoints
- Check database queries
- Understand JavaScript fetch calls

**6. How everything connects** → Read `docker-compose.yml`
- See all service definitions
- Understand networks and volumes
- Check environment variables

---

## 🏆 Success Indicators

**✅ Everything is working when**:
- Dashboard shows increasing article count
- `docker ps` shows 11 containers running
- Airflow UI shows green DAG runs
- Kafka UI shows messages in `vnexpress_topic`
- Database grows: `SELECT COUNT(*) FROM articles`
- No errors in logs: `docker logs <container>`

---

**Quick Reference Created**: December 17, 2025
