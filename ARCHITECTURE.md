# VnExpress Crawler System Architecture

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [File Structure](#file-structure)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [File Relationships](#file-relationships)

---

## 🎯 System Overview

This is a **distributed web crawler and streaming data pipeline** that:
1. **Crawls** VnExpress news articles using Selenium
2. **Streams** data through Kafka (3-broker cluster)
3. **Processes** with Spark Streaming
4. **Stores** in SQLite database
5. **Monitors** via Flask dashboard
6. **Orchestrates** with Airflow

```
VnExpress Website
      ↓
[Crawler (Selenium)]
      ↓
[Kafka Cluster (3 brokers)]
      ↓
[Spark Streaming]
      ↓
[SQLite Database]
      ↓
[Flask Dashboard]
      
[Airflow] ← Orchestrates everything
```

---

## 📁 File Structure

```
hieucode/
├── app/                          # Main application directory
│   ├── Dockerfile                # Crawler container image
│   ├── entrypoint.sh            # Container startup script
│   ├── hieudb.db                # SQLite database (articles storage)
│   ├── mass_crawling.py         # Main crawler script
│   ├── producer.py              # Kafka producer (sends data to Kafka)
│   ├── spark_app.py             # Spark streaming consumer
│   ├── requirements.txt         # Python dependencies
│   └── sqlite-jdbc.jar          # JDBC driver for Spark-SQLite connection
│
├── dags/                         # Airflow DAG definitions
│   └── daily_crawler.py         # Automated daily crawler DAG
│
├── spark/                        # Spark configuration
│   └── Dockerfile               # Spark container image
│
├── airflow/                      # Airflow configuration
│   └── Dockerfile               # Airflow container image
│
├── docker-compose.yml           # Main orchestration file (all services)
├── crawling.py                  # Standalone crawler (for testing)
├── requirements.txt             # Root level dependencies
│
└── Documentation:
    ├── DASHBOARD_USAGE.md       # Dashboard user guide
    ├── AIRFLOW_AUTO_START.md    # Airflow auto-start feature guide
    └── ARCHITECTURE.md          # This file
```

---

## 🔧 Core Components

### 1️⃣ **Crawler Layer**

#### `app/mass_crawling.py` ⭐ MAIN CRAWLER
**Purpose**: Crawls VnExpress articles using Selenium and sends to Kafka

**What it does**:
- Opens Chrome browser with Selenium WebDriver
- Navigates to VnExpress category pages
- Scrolls down to load more articles (infinite scroll)
- Extracts: title, URL, image, description, category, timestamp
- Sends each article to Kafka topic `vnexpress_topic`
- Runs continuously until stopped

**Key Features**:
```python
# Crawls these categories
CATEGORIES = {
    'thoi-su': 'https://vnexpress.net/thoi-su',
    'giai-tri': 'https://vnexpress.net/giai-tri',
    'the-thao': 'https://vnexpress.net/the-thao',
    # ... more categories
}
```

**Selenium Configuration**:
- Headless Chrome (no UI)
- Disable images for speed
- User-agent randomization
- Auto-scroll for infinite loading

**Output**: JSON messages to Kafka
```json
{
  "title": "Article title",
  "link": "https://...",
  "image": "https://...",
  "description": "...",
  "category": "thoi-su",
  "timestamp": 1702809600
}
```

#### `app/producer.py` 
**Purpose**: Kafka producer helper (used by mass_crawling.py)

**What it does**:
- Creates Kafka producer connection
- Handles message serialization (JSON)
- Manages connection to Kafka brokers
- Error handling for failed sends

**Configuration**:
```python
bootstrap_servers = ['kafka-1:9092', 'kafka-2:9092', 'kafka-3:9092']
topic = 'vnexpress_topic'
```

#### `crawling.py`
**Purpose**: Standalone crawler for testing (NOT used in production)

**What it does**:
- Same crawling logic as mass_crawling.py
- Saves directly to CSV file instead of Kafka
- Used for local testing without Kafka

**Output**: `hieu.csv`, `trunghieu.csv`

---

### 2️⃣ **Message Queue Layer (Kafka)**

#### Defined in: `docker-compose.yml` (lines 5-79)

**3 Kafka Brokers** (KRaft mode - no Zookeeper needed):

**kafka-1** (Port 19092):
```yaml
container_name: kafka-1
ports: "19092:19092"  # External access
KAFKA_NODE_ID: 1
```

**kafka-2** (Port 29092):
```yaml
container_name: kafka-2  
ports: "29092:29092"
KAFKA_NODE_ID: 2
```

**kafka-3** (Port 39092):
```yaml
container_name: kafka-3
ports: "39092:39092"
KAFKA_NODE_ID: 3
```

**Why 3 brokers?**
- **Fault tolerance**: If 1 broker fails, others continue
- **Load balancing**: Distribute topic partitions across brokers
- **Replication**: Data replicated across brokers for safety

**Topic Configuration**:
- **Topic name**: `vnexpress_topic`
- **Partitions**: 3 (one per broker)
- **Replication**: Automatic across brokers

---

### 3️⃣ **Stream Processing Layer**

#### `app/spark_app.py` ⭐ STREAMING PROCESSOR
**Purpose**: Consumes from Kafka, processes, and saves to database

**What it does**:
```python
# 1. Read from Kafka
spark.readStream
  .format("kafka")
  .option("kafka.bootstrap.servers", "kafka-1:9092,kafka-2:9092,kafka-3:9092")
  .option("subscribe", "vnexpress_topic")
  
# 2. Parse JSON messages
parse JSON → extract fields

# 3. Write to SQLite
foreach batch:
  INSERT INTO articles (title, link, image, description, category, timestamp)
```

**Key Features**:
- **Streaming**: Processes data in real-time as it arrives
- **Micro-batches**: Processes every 10 seconds
- **Deduplication**: Checks if article already exists (by link)
- **SQLite JDBC**: Uses `sqlite-jdbc.jar` to write to database

**Database Schema**:
```sql
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    link TEXT UNIQUE,
    image TEXT,
    description TEXT,
    category TEXT,
    timestamp INTEGER
)
```

#### `spark/Dockerfile`
**Purpose**: Builds Spark container image

**What it includes**:
- Apache Spark 3.5.0
- Python 3.11
- Kafka integration JARs
- SQLite JDBC driver

---

### 4️⃣ **Storage Layer**

#### `app/hieudb.db` ⭐ MAIN DATABASE
**Purpose**: SQLite database storing all crawled articles

**Schema**:
- **id**: Auto-incrementing primary key
- **title**: Article title
- **link**: Article URL (UNIQUE constraint - prevents duplicates)
- **image**: Image URL
- **description**: Article summary
- **category**: News category (thoi-su, giai-tri, etc.)
- **timestamp**: Unix timestamp (seconds since epoch)

**Current Stats** (as of Dec 17, 2025):
- Total articles: **7,534**
- Today's crawl: **2,457 articles**
- This week: **2,457 articles**

**Queried by**:
- Spark (writes)
- Dashboard (reads)

---

### 5️⃣ **Orchestration Layer (Airflow)**

#### `dags/daily_crawler.py` ⭐ AUTOMATION DAG
**Purpose**: Automated daily crawling workflow with service auto-start

**DAG Schedule**: `'0 6 * * *'` (Every day at 6:00 AM)

**Task Flow**:
```
Step 1: Start Services (parallel)
├─ start_kafka           → Start Kafka brokers if not running
├─ start_spark           → Start Spark if not running  
└─ start_crawler_container → Start crawler container if not running
        ↓
Step 2: check_kafka_health → Verify Kafka cluster is healthy (3 retries)
        ↓
Step 3: crawl_vnexpress    → Execute crawler script
        ↓
Step 4: check_spark_processing → Verify Spark is processing data
        ↓
Step 5: log_completion     → Log success message
```

**Key Functions**:

1. **start_kafka_if_needed()**:
   ```python
   # Checks running brokers
   # If < 3 running → start all brokers
   # Wait 20 seconds for startup
   ```

2. **start_spark_if_needed()**:
   ```python
   # Check if Spark container running
   # If not → start spark
   # Wait 10 seconds
   ```

3. **ensure_crawler_container()**:
   ```python
   # Check crawler container
   # If not running → start it
   # Wait 5 seconds
   ```

4. **check_kafka_health()**:
   ```python
   # Try to connect to Kafka
   # 3 retries with 10-second delays
   # Raise exception if fails
   ```

5. **run_crawler()**:
   ```python
   # Execute mass_crawling.py inside crawler container
   # Crawls all categories
   # Sends to Kafka
   ```

**Default Arguments**:
```python
default_args = {
    'owner': 'hieucode',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}
```

#### `airflow/Dockerfile`
**Purpose**: Custom Airflow image with dependencies

**Includes**:
- Airflow 2.8.0
- PostgreSQL adapter
- Kafka Python library
- Selenium
- Docker CLI (for service management)

---

### 6️⃣ **Monitoring Layer (Dashboard)**

#### `~/Documents/GitHub/action/server.py` ⭐ FLASK API
**Purpose**: Backend API for dashboard

**Endpoints**:

1. **GET /api/stats**
   ```python
   # Returns article statistics
   {
     "total": 7534,
     "today": 2457,
     "week": 2457,
     "running_containers": 11
   }
   ```

2. **POST /api/crawler/start**
   ```python
   # Starts crawler process
   # Executes: docker exec crawler python mass_crawling.py
   ```

3. **POST /api/crawler/stop**
   ```python
   # Stops crawler (kills Chrome processes)
   ```

4. **GET /api/crawler/status**
   ```python
   # Returns crawler status
   {
     "is_running": true,
     "chrome_count": 1,
     "process_count": 3
   }
   ```

5. **POST /api/open-browser**
   ```python
   # Opens URL in system browser
   # Uses macOS 'open' command
   ```

6. **POST /api/service/start/<service>**
   ```python
   # Starts Docker service
   # docker-compose up -d <service>
   ```

7. **GET /api/logs/<container>**
   ```python
   # Fetches last 200 lines of container logs
   ```

**Database Queries**:
```python
# Total articles
SELECT COUNT(*) FROM articles

# Today's articles (Unix timestamp conversion)
SELECT COUNT(*) FROM articles 
WHERE date(timestamp, 'unixepoch', 'localtime') = date('now', 'localtime')

# This week
SELECT COUNT(*) FROM articles 
WHERE date(timestamp, 'unixepoch', 'localtime') >= date('now', '-7 days', 'localtime')
```

#### `~/Documents/GitHub/action/templates/dashboard_enhanced.html`
**Purpose**: Interactive web dashboard UI

**Features**:

**Tab 1: Overview**
- Real-time statistics (total, today, week)
- Service status indicators (green/red dots)
- Docker, Kafka, Spark, Airflow status cards

**Tab 2: Services Control**
- Crawler: Start/Stop/Logs + Chrome instances count
- Kafka: Start/Stop/Logs + Start UI + Open UI buttons
- Spark: Start/Stop/Logs
- Airflow: Start/Stop/Logs + Open UI button

**Tab 3: Logs Viewer**
- Dropdown to select container
- Refresh button
- Auto-refresh toggle (every 10 seconds)
- Displays last 200 lines

**Tab 4: Articles Browser**
- Latest 20 articles
- Shows: image, title, description, category
- Click to open full article

**JavaScript Functions**:
```javascript
updateStatus()        // Refresh every 5 seconds
startCrawler()        // POST /api/crawler/start
stopCrawler()         // POST /api/crawler/stop
openAirflowUI()       // Open localhost:8081
openKafkaUI()         // Open localhost:8080
loadLogs(container)   // GET /api/logs/<container>
```

---

### 7️⃣ **Container Orchestration**

#### `docker-compose.yml` ⭐ MAIN ORCHESTRATION FILE
**Purpose**: Defines and manages all Docker services

**Services** (11 total):

1. **kafka-1, kafka-2, kafka-3** (Kafka cluster)
   - Network: kafka-net
   - Volumes: kafka-data-1/2/3 (persistent storage)
   - KRaft mode (no Zookeeper)

2. **crawler**
   - Build: ./app/Dockerfile
   - Command: `tail -f /dev/null` (stays alive, wait for commands)
   - Volumes: ./app → /opt/app (live code sync)
   - Depends on: All 3 Kafka brokers

3. **spark**
   - Build: ./spark/Dockerfile
   - Runs: spark_app.py (streaming processor)
   - Volumes: ./app → /opt/app (access to database and JARs)
   - Depends on: Kafka cluster

4. **postgres-airflow**
   - PostgreSQL database for Airflow metadata
   - Volume: postgres-airflow-data (persistent)

5. **airflow-webserver**
   - Port: 8081 → 8080 (UI)
   - Volumes: 
     - ./dags → /opt/airflow/dags
     - ./app → /opt/airflow/app
     - /var/run/docker.sock (Docker control)
   - Command: Runs DB migration + creates admin user + starts webserver

6. **airflow-scheduler**
   - Executes DAG tasks
   - Same volumes as webserver
   - Docker socket access for service management

7. **kafka-ui**
   - Port: 8080
   - Web UI for Kafka monitoring
   - Shows topics, partitions, messages

**Networks**:
```yaml
kafka-net:
  driver: bridge  # All containers can communicate
```

**Volumes** (Persistent data):
- kafka-data-1/2/3: Kafka message storage
- postgres-airflow-data: Airflow metadata
- airflow-logs: Task execution logs

---

### 8️⃣ **Configuration Files**

#### `app/requirements.txt`
**Purpose**: Python dependencies for crawler and Spark

```
selenium          # Web scraping
kafka-python      # Kafka producer/consumer
pyspark           # Spark streaming
beautifulsoup4    # HTML parsing
requests          # HTTP requests
```

#### `requirements.txt` (root)
**Purpose**: Root level dependencies (for local testing)

#### `app/Dockerfile`
**Purpose**: Builds crawler container

**Steps**:
1. Base: python:3.11-slim
2. Install: Chrome, ChromeDriver, dependencies
3. Copy: requirements.txt → install packages
4. Working directory: /opt/app
5. Entry point: entrypoint.sh

#### `app/entrypoint.sh`
**Purpose**: Container startup script

**What it does**:
```bash
#!/bin/bash
# Wait for Kafka to be ready
# Then execute whatever command is passed
exec "$@"
```

---

## 🔄 Data Flow (Complete Journey)

### **Step-by-Step Process**:

```
1. USER TRIGGERS
   ├─ Manual: Dashboard → Click "Start Crawler"
   ├─ Automatic: Airflow DAG runs at 6 AM
   └─ Command: docker exec crawler python mass_crawling.py

2. CRAWLER (mass_crawling.py)
   ├─ Opens Chrome with Selenium
   ├─ Navigates to VnExpress categories
   ├─ Scrolls and loads articles
   └─ For each article:
       ├─ Extract: title, link, image, description, category
       ├─ Add timestamp
       └─ Send to Kafka → vnexpress_topic

3. KAFKA CLUSTER
   ├─ Receives JSON message from producer
   ├─ Distributes to 3 partitions (across 3 brokers)
   ├─ Replicates for fault tolerance
   └─ Holds in queue for consumers

4. SPARK STREAMING (spark_app.py)
   ├─ Subscribes to vnexpress_topic
   ├─ Reads messages in micro-batches (every 10 seconds)
   ├─ Parses JSON → DataFrame
   ├─ For each batch:
   │   ├─ Connect to SQLite (hieudb.db)
   │   ├─ Check if article exists (by link)
   │   ├─ INSERT new articles
   │   └─ Skip duplicates
   └─ Commit batch

5. SQLITE DATABASE (hieudb.db)
   ├─ Stores articles in 'articles' table
   ├─ UNIQUE constraint on 'link' prevents duplicates
   └─ Indexed by timestamp for fast queries

6. DASHBOARD (server.py + dashboard_enhanced.html)
   ├─ Every 5 seconds: Query database for stats
   ├─ Display: total, today, week counts
   ├─ Show: latest 20 articles with images
   └─ Monitor: service statuses

7. MONITORING
   ├─ Airflow UI: DAG execution history, logs
   ├─ Kafka UI: Topics, messages, partitions
   └─ Dashboard: Real-time stats, logs, controls
```

---

## 🔗 File Relationships Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    docker-compose.yml                            │
│  (Orchestrates everything - defines all services and networks)  │
└───┬─────────────┬──────────────┬──────────────┬────────────────┘
    │             │              │              │
    ▼             ▼              ▼              ▼
┌─────────┐  ┌─────────┐  ┌──────────┐  ┌────────────┐
│ Kafka   │  │Crawler  │  │  Spark   │  │  Airflow   │
│Cluster  │  │Container│  │ Container│  │ Container  │
└────┬────┘  └────┬────┘  └────┬─────┘  └─────┬──────┘
     │            │             │               │
     │            │             │               │
     │    ┌───────┴────────┐    │               │
     │    │                │    │               │
     ▼    ▼                ▼    ▼               ▼
┌─────────────────────────────────────────────────────┐
│                 app/ directory                       │
│  ┌──────────────────┐  ┌────────────────┐          │
│  │mass_crawling.py  │  │  spark_app.py  │          │
│  │  (producer.py)   │  │                │          │
│  └────────┬─────────┘  └───────┬────────┘          │
│           │                    │                    │
│           │      ┌─────────────▼────────┐          │
│           └─────→│     hieudb.db        │◄─────┐   │
│                  │   (SQLite Database)  │      │   │
│                  └──────────────────────┘      │   │
└─────────────────────────────────────────────────┼──┘
                                                  │
                                                  │
┌─────────────────────────────────────────────────┼──┐
│           Dashboard (GitHub/action/)            │  │
│  ┌──────────────┐         ┌──────────────────┐ │  │
│  │  server.py   │ Reads   │dashboard_enhanced│ │  │
│  │ (Flask API)  ├────────→│     .html        │ │  │
│  └──────┬───────┘         └──────────────────┘ │  │
│         │ Queries                               │  │
│         └───────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│              dags/daily_crawler.py                   │
│  (Airflow DAG - orchestrates entire workflow)       │
│                                                      │
│  Controls: Kafka start/stop                         │
│            Spark start/stop                         │
│            Crawler start/stop                       │
│            Executes mass_crawling.py                │
└─────────────────────────────────────────────────────┘
```

---

## 🔍 Detailed File Dependencies

### **Crawler Dependencies**:
```
mass_crawling.py
    ├─ Imports: producer.py (Kafka producer)
    ├─ Uses: selenium, beautifulsoup4, kafka-python
    ├─ Writes to: Kafka topic 'vnexpress_topic'
    └─ Controlled by: 
        ├─ Dashboard (server.py)
        └─ Airflow DAG (daily_crawler.py)
```

### **Spark Dependencies**:
```
spark_app.py
    ├─ Reads from: Kafka topic 'vnexpress_topic'
    ├─ Uses: pyspark, kafka integration JARs
    ├─ JDBC: sqlite-jdbc.jar
    ├─ Writes to: hieudb.db (SQLite)
    └─ Triggered by:
        ├─ Auto-start on container launch
        └─ Airflow DAG checks it's running
```

### **Database Dependencies**:
```
hieudb.db
    ├─ Written by: spark_app.py (Spark streaming)
    ├─ Read by: server.py (Dashboard API)
    └─ Location: /opt/app/hieudb.db (shared volume)
```

### **Airflow DAG Dependencies**:
```
daily_crawler.py
    ├─ Imports: subprocess, datetime, airflow modules
    ├─ Controls: Docker containers via docker socket
    ├─ Executes: mass_crawling.py in crawler container
    ├─ Checks: Kafka health, Spark processing
    └─ Schedule: Cron '0 6 * * *' (6 AM daily)
```

### **Dashboard Dependencies**:
```
server.py
    ├─ Imports: Flask, sqlite3, subprocess
    ├─ Reads: hieudb.db (SQLite queries)
    ├─ Controls: Docker services (docker-compose)
    ├─ Serves: dashboard_enhanced.html
    └─ Port: 5000

dashboard_enhanced.html
    ├─ Calls: server.py API endpoints
    ├─ JavaScript: Fetch API for async requests
    ├─ Updates: Every 5 seconds (auto-refresh)
    └─ Features: 4 tabs (Overview, Services, Logs, Articles)
```

---

## 🚀 How They Work Together

### **Scenario 1: Automatic Daily Crawl**

```
06:00 AM → Airflow DAG triggers
    ↓
daily_crawler.py executes:
    1. start_kafka_if_needed()     → Ensures Kafka running
    2. start_spark_if_needed()     → Ensures Spark running
    3. ensure_crawler_container()  → Ensures crawler running
    ↓
    4. check_kafka_health()        → Verifies Kafka ready
    ↓
    5. run_crawler()               → Executes mass_crawling.py
        ↓
        mass_crawling.py runs:
            • Opens Chrome
            • Crawls VnExpress
            • Sends to Kafka → vnexpress_topic
    ↓
Kafka stores messages in 3 partitions
    ↓
spark_app.py (already running):
    • Reads from Kafka every 10 seconds
    • Parses JSON
    • Inserts into hieudb.db
    ↓
    6. check_spark_processing()    → Verifies Spark working
    ↓
    7. log_completion()            → Logs success
    ↓
Dashboard (server.py):
    • Queries hieudb.db every 5 seconds
    • Updates statistics
    • Shows new articles
```

### **Scenario 2: Manual Dashboard Control**

```
User opens: http://localhost:5000
    ↓
dashboard_enhanced.html loads
    ↓
JavaScript calls: GET /api/stats
    ↓
server.py queries hieudb.db:
    • SELECT COUNT(*) FROM articles  → Total: 7534
    • SELECT COUNT(*) WHERE today    → Today: 2457
    • Returns JSON to frontend
    ↓
User clicks: "Start Crawler"
    ↓
JavaScript calls: POST /api/crawler/start
    ↓
server.py executes:
    docker exec crawler python /opt/app/mass_crawling.py
    ↓
Crawler starts → Sends to Kafka → Spark processes → DB updates
    ↓
Dashboard refreshes stats every 5 seconds
User sees: article count increasing in real-time
```

### **Scenario 3: Monitoring via UIs**

```
User opens: http://localhost:5000 (Dashboard)
    • Overview tab: See total articles, service status
    • Services tab: Control all services
    • Logs tab: View container logs
    • Articles tab: Browse latest articles
    ↓
User clicks: "Open Airflow UI"
    ↓
Opens: http://localhost:8081
    • Login: admin/admin
    • View: DAG execution history
    • Check: Task logs, success/failure
    • Trigger: Manual DAG run
    ↓
User clicks: "Open Kafka UI"
    ↓
Opens: http://localhost:8080
    • View: vnexpress_topic
    • See: 3 partitions across 3 brokers
    • Monitor: Message count, lag
    • Inspect: Individual messages (JSON)
```

---

## 📊 Data Flow Timeline

```
T+0s    Crawler starts browsing VnExpress
T+2s    First article found, sent to Kafka
T+2.1s  Kafka receives, stores in partition
T+10s   Spark reads first batch (10-second window)
T+10.5s Spark writes to SQLite database
T+15s   Dashboard queries DB, updates stats
T+20s   Spark reads second batch
T+30s   Dashboard refreshes again
...     (Continues until crawler stopped)
```

---

## 🎓 Key Concepts

### **Why Kafka?**
- **Decoupling**: Crawler and Spark don't directly communicate
- **Buffering**: If Spark is slow, Kafka holds messages
- **Scalability**: Can add more consumers easily
- **Fault tolerance**: 3 brokers, replication

### **Why Spark Streaming?**
- **Real-time**: Process data as it arrives
- **Scalable**: Can handle high throughput
- **Integration**: Easy Kafka and SQLite connection
- **Processing**: Can add transformations, filtering

### **Why Docker Compose?**
- **Isolation**: Each service in its own container
- **Networking**: Services communicate via container names
- **Volumes**: Shared data (database, code, logs)
- **Orchestration**: Start/stop all services together

### **Why Airflow?**
- **Scheduling**: Automated daily crawls
- **Dependencies**: Tasks run in order
- **Monitoring**: Track success/failure
- **Retry logic**: Auto-retry failed tasks

### **Why Flask Dashboard?**
- **Visibility**: Real-time monitoring
- **Control**: Start/stop services manually
- **Debugging**: View logs, check status
- **User-friendly**: Web UI instead of command line

---

## 🔧 Common Operations

### **Start Everything**:
```bash
cd /Users/op-lt-0378/Documents/hieucode
docker-compose up -d
```
**Files involved**:
- docker-compose.yml → Starts all services
- app/Dockerfile → Builds crawler
- spark/Dockerfile → Builds Spark
- airflow/Dockerfile → Builds Airflow

### **Trigger Crawl**:
```bash
# Option 1: Via Airflow
docker exec airflow-scheduler airflow dags trigger vnexpress_daily_crawler

# Option 2: Via Dashboard
# Open localhost:5000 → Click "Start Crawler"

# Option 3: Direct command
docker exec crawler python /opt/app/mass_crawling.py
```
**Files involved**:
- daily_crawler.py → DAG orchestration
- mass_crawling.py → Actual crawler
- producer.py → Kafka producer

### **Check Status**:
```bash
# Option 1: Dashboard
# Open localhost:5000 → Overview tab

# Option 2: Docker
docker ps --format "table {{.Names}}\t{{.Status}}"

# Option 3: Database
sqlite3 app/hieudb.db "SELECT COUNT(*) FROM articles"
```
**Files involved**:
- server.py → API for dashboard
- dashboard_enhanced.html → UI display
- hieudb.db → Database queries

### **View Logs**:
```bash
# Option 1: Dashboard
# Open localhost:5000 → Logs tab

# Option 2: Docker
docker logs crawler
docker logs spark
docker logs kafka-1

# Option 3: Airflow
# Open localhost:8081 → DAG → Task logs
```
**Files involved**:
- server.py → /api/logs/<container>
- All containers → stdout/stderr

---

## 📝 Summary

**Main Flow**:
1. **mass_crawling.py** (Crawler) → Scrapes VnExpress
2. **producer.py** (Kafka Producer) → Sends to Kafka
3. **Kafka Cluster** (Message Queue) → Buffers messages
4. **spark_app.py** (Spark Streaming) → Processes & saves
5. **hieudb.db** (SQLite) → Stores articles
6. **server.py** (Flask API) → Provides data to dashboard
7. **dashboard_enhanced.html** (Web UI) → Displays to user
8. **daily_crawler.py** (Airflow DAG) → Orchestrates everything

**Key Integration Points**:
- Crawler → Kafka: `vnexpress_topic`
- Kafka → Spark: Subscription to topic
- Spark → Database: JDBC via `sqlite-jdbc.jar`
- Database → Dashboard: SQLite queries
- Airflow → All services: Docker socket control
- Dashboard → Services: Docker Compose commands

**All files work together** to create a complete, automated, monitored web crawling and data pipeline system! 🎉

---

**Created**: December 17, 2025  
**Author**: GitHub Copilot  
**Version**: 1.0
