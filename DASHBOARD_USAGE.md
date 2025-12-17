# Hieucode Pipeline Dashboard - Usage Guide

## 🚀 Quick Start

### Starting the Dashboard
```bash
cd ~/Documents/GitHub/action
./dashboard.sh start
```

Access at: **http://localhost:5000**

## 📊 Dashboard Features

### **Overview Tab**
Real-time statistics and service status:
- Total articles crawled
- Today's articles
- This week's articles  
- Running services count
- Docker, Kafka, Spark, Airflow status cards

### **Services Control Tab**
Control all pipeline services:

#### 🕷️ Crawler Control
- **▶️ Start** - Starts the web crawler
- **⏹️ Stop** - Stops the crawler
- **📋 Logs** - View crawler logs
- Shows: Status, Chrome instances, Process count

#### 📊 Kafka Cluster
- **▶️ Start** - Starts Kafka brokers
- **⏹️ Stop** - Stops Kafka
- **📋 Logs** - View Kafka logs
- **▶️ Start Kafka UI** - Starts the Kafka web UI
- **🌐 Open UI** - Opens Kafka UI in system browser
- Shows: Broker count (X/3), Topics, UI status

#### ⚡ Spark Streaming
- **▶️ Start** - Starts Spark
- **⏹️ Stop** - Stops Spark
- **📋 Logs** - View Spark logs
- Shows: Running status, Streaming state

#### 🔄 Airflow
- **▶️ Start** - Starts Airflow services
- **⏹️ Stop** - Stops Airflow
- **📋 Logs** - View Airflow logs
- **🌐 Open Airflow UI** - Opens Airflow in system browser
- Shows: Container count, Status, Port 8081

### **Logs Tab**
View real-time container logs:
- Select container from dropdown
- View last 200 lines
- 🔄 Refresh button
- ⏱️ Auto-refresh toggle (every 5 seconds)
- Available containers:
  - crawler
  - spark
  - kafka-1, kafka-2, kafka-3
  - airflow-webserver
  - airflow-scheduler

### **Articles Tab**
Browse crawled articles:
- Latest 20 articles
- Article images
- Title and link
- Auto-refresh with stats

## 🔄 Airflow Integration

### Opening Airflow UI
1. Go to **Services Control** tab
2. Click **🌐 Open Airflow UI** button
3. Airflow opens in your **system browser** (Chrome/Safari)
4. Login credentials: **admin / admin**

### Running the Daily Crawler DAG
1. Open Airflow UI (http://localhost:8081)
2. Find **vnexpress_daily_crawler** DAG
3. Toggle it **ON** (switch on the left)
4. The DAG will:
   - ✅ Ensure crawler is ready
   - ✅ Check Kafka health
   - ✅ Run the crawler (starts crawling automatically)
   - ✅ Check Spark processing
   - ✅ Log completion

### DAG Schedule
- Runs **daily at 6:00 AM**
- Can be triggered manually from Airflow UI
- Automatically handles retries (2 attempts, 5-minute delay)

### Important: Service Management
**When you turn on the Airflow DAG:**
- The DAG will start the crawler automatically
- Kafka and Spark should already be running (start them first if not)
- Check dashboard to see crawler status change to "Running"
- Chrome instances will appear (10+)
- Articles will start flowing into the database

**If services are not running:**
1. Start Kafka: Click **▶️ Start** in Kafka card
2. Start Spark: Click **▶️ Start** in Spark card  
3. Then enable the Airflow DAG
4. The DAG will handle starting the crawler

## 📝 Tips & Troubleshooting

### Dashboard Not Updating?
- Check if dashboard is running: `./dashboard.sh status`
- Restart: `./dashboard.sh restart`
- Auto-refresh runs every 5 seconds

### Crawler Not Starting from Airflow?
- Ensure Kafka is running (3/3 brokers)
- Ensure Spark is running
- Check Airflow logs in the Logs tab
- Manually trigger DAG from Airflow UI

### Kafka/Airflow UI Opens in Dashboard?
- Fixed! Now uses `/api/open-browser` endpoint
- Opens in **system default browser**
- If fails, URL is copied to clipboard
- Check your browser tabs (Chrome/Safari/Firefox)

### CSRF Errors?
- Fixed! CSRF is disabled for API endpoints
- CORS headers added for cross-origin requests

### Services Not Starting?
- Check Docker Desktop is running
- Verify containers: `docker ps`
- Check logs in Logs tab
- Restart services using control buttons

## 🛠️ Dashboard Commands

```bash
# Start dashboard
./dashboard.sh start

# Stop dashboard
./dashboard.sh stop

# Restart dashboard
./dashboard.sh restart

# Check status
./dashboard.sh status

# View logs
./dashboard.sh logs

# Open in browser
./dashboard.sh open
```

## 📊 Current Statistics
- **Total Articles**: Check Overview tab
- **Today's Crawl**: Updates in real-time
- **Crawler Status**: See in Services Control
- **Service Health**: All status cards update every 5 seconds

## 🎯 Workflow

### Manual Crawling
1. Go to **Services Control** tab
2. Click **▶️ Start** on Crawler card
3. Monitor status and Chrome instances
4. View logs in **Logs** tab
5. Check articles in **Articles** tab

### Automated Daily Crawling (Airflow)
1. Ensure Kafka and Spark are running
2. Open **Airflow UI** (🌐 button)
3. Enable **vnexpress_daily_crawler** DAG
4. DAG runs daily at 6 AM automatically
5. Monitor in dashboard

## 🔗 Quick Links
- **Dashboard**: http://localhost:5000
- **Airflow UI**: http://localhost:8081 (admin/admin)
- **Kafka UI**: http://localhost:8080
- **GitHub Repo**: https://github.com/hieupmo99/hieucode

## ✅ Success Indicators
- Kafka: 3/3 brokers ✅
- Spark: Running, Active streaming ✅
- Crawler: Running, 10+ Chrome instances ✅
- Airflow: 3 containers (webserver, scheduler, postgres) ✅
- Articles: Increasing count in Overview ✅

---

**Dashboard Version**: Enhanced Control Center v2.0
**Last Updated**: December 17, 2025
