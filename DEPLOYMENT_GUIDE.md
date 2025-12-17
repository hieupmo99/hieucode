# Deployment Guide: Local vs GitHub Actions

## 🎯 Understanding Your Setup

### **You Have TWO Separate Environments**

```
┌─────────────────────────────────────────────────────────────┐
│  GITHUB ACTIONS (Cloud - Testing Only)                      │
│  ─────────────────────────────────────────                  │
│  - Runs on GitHub's servers                                 │
│  - Triggered by: git push                                   │
│  - Purpose: Test that code works                            │
│  - Lifespan: ~5 minutes, then destroyed                     │
│  - NOT visible in your dashboard                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  LOCAL DEVELOPMENT (Your Mac - Production)                  │
│  ────────────────────────────────────────                   │
│  - Runs on: localhost                                       │
│  - Started by: docker-compose up                            │
│  - Purpose: Your actual working pipeline                    │
│  - Lifespan: Until you stop it                              │
│  - Dashboard shows THIS environment                          │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 What Happens When You Commit

### **Step-by-Step Flow**:

```
1. You make changes in VS Code
   └─> Files: dags/daily_crawler.py, etc.

2. You run: git add, git commit, git push
   └─> Code uploaded to GitHub

3. GitHub Actions STARTS (in cloud)
   ├─> Builds Docker images
   ├─> Starts temporary Kafka/Spark/Crawler
   ├─> Runs test crawl
   ├─> Verifies everything works
   └─> DESTROYS all containers (cleanup)
   
   ⚠️  Your dashboard CANNOT see this!
   ⚠️  This is just testing, not production!

4. Your Local Machine (UNCHANGED)
   ├─> Still running old containers
   ├─> Old code in memory
   └─> No automatic sync!
```

## 📊 Why Dashboard Doesn't Show GitHub Actions

The dashboard (`http://localhost:5000`) ONLY shows:
- ✅ Docker containers running on YOUR Mac
- ✅ Database file: `~/Documents/hieucode/app/hieudb.db`
- ✅ Airflow DAGs in YOUR local Airflow

The dashboard CANNOT show:
- ❌ GitHub Actions test runs (they're in the cloud)
- ❌ Temporary test data (it's deleted after tests)
- ❌ Build logs from GitHub servers

## 🔄 How Files Sync to Local

### **Files That Auto-Sync (Volume Mounts)**

These files update **immediately** in running containers:

```yaml
# From docker-compose.yml:
volumes:
  - ./dags:/opt/airflow/dags          # ✅ DAG changes auto-reload
  - ./app:/opt/app                     # ✅ Crawler changes auto-reload
  - ./app:/opt/airflow/app             # ✅ App changes visible
```

**Example**: When you edit `dags/daily_crawler.py`:
1. File saved on disk
2. Docker container sees change immediately (volume mount)
3. Airflow detects change and reloads DAG
4. New schedule takes effect

**You can verify**:
```bash
# Check if local file matches container file
cd ~/Documents/hieucode
docker exec airflow-scheduler cat /opt/airflow/dags/daily_crawler.py | grep schedule_interval
```

### **Files That DON'T Auto-Sync (Built into Image)**

These require **rebuilding containers**:
- ❌ `Dockerfile` changes
- ❌ `requirements.txt` changes  
- ❌ System packages
- ❌ `docker-compose.yml` service definitions

**When to rebuild**:
```bash
# After changing Dockerfiles or requirements.txt:
docker-compose down
docker-compose build
docker-compose up -d
```

## 🎯 Current State of Your Environment

### **What's Running Right Now**:
```
Local Machine (localhost):
├─ Airflow (8081): ✅ Schedule updated to 11 AM GMT+7
├─ Kafka (19092, 29092, 39092): ✅ Running
├─ Spark: ✅ Running
├─ Crawler: ✅ Running
├─ Dashboard (5000): ✅ Running
└─ Database: ~/Documents/hieucode/app/hieudb.db (8650 articles)

GitHub Actions (cloud):
└─ Test run: Completed (see https://github.com/hieupmo99/hieucode/actions)
```

### **Your Airflow DAG**:
- ✅ Schedule: `0 4 * * *` (11 AM GMT+7)
- ✅ Auto-reload: Enabled (volume mount)
- ✅ Next run: Tomorrow at 11 AM

## 📝 Common Scenarios

### **Scenario 1: I changed a Python file (*.py)**

**What happens**:
- ✅ File saved to disk
- ✅ Container sees change via volume mount
- ✅ Airflow/Crawler uses new code immediately

**Action needed**: None (auto-synced)

**Example**:
```bash
# Edit dags/daily_crawler.py
# Save file
# Airflow automatically reloads within 30 seconds
```

### **Scenario 2: I changed Dockerfile or requirements.txt**

**What happens**:
- ❌ Container still uses old image
- ❌ New dependencies not installed

**Action needed**: Rebuild containers
```bash
cd ~/Documents/hieucode
docker-compose down
docker-compose build
docker-compose up -d
```

### **Scenario 3: I committed to GitHub**

**What happens**:
- ✅ GitHub Actions tests your code (in cloud)
- ❌ Your local containers unchanged
- ❌ Dashboard shows old data

**Action needed**: Nothing! (or rebuild if you want to be sure)
```bash
# Optional - to get absolutely latest:
git pull
docker-compose restart airflow-scheduler
```

## 🔍 How to Monitor Changes

### **Check if Airflow detected your DAG changes**:
```bash
cd ~/Documents/hieucode

# Check schedule in running container
docker exec airflow-scheduler airflow dags details vnexpress_daily_crawler | grep schedule

# Check last DAG file modification
docker exec airflow-scheduler stat /opt/airflow/dags/daily_crawler.py

# View scheduler logs for DAG reload messages
docker logs airflow-scheduler --tail 50 | grep daily_crawler
```

### **Check if Dashboard is showing latest data**:
```bash
# Check database directly
sqlite3 ~/Documents/hieucode/app/hieudb.db "SELECT COUNT(*) FROM vnexpress"

# Check what dashboard is reading
curl http://localhost:5000/api/stats

# Restart dashboard if needed
pkill -f server.py
cd ~/Documents/GitHub/action
python3 server.py &
```

### **Check GitHub Actions results**:
```bash
# Open in browser
open https://github.com/hieupmo99/hieucode/actions

# Or use GitHub CLI (if installed)
gh run list --repo hieupmo99/hieucode
```

## 🚀 Deployment Workflow (Recommended)

### **Daily Development**:
```bash
# 1. Make changes in VS Code
# 2. Save files (auto-synced via volumes)
# 3. Test locally
# 4. When satisfied:
git add -A
git commit -m "your changes"
git push

# GitHub Actions will test automatically
# No need to update local (already synced)
```

### **After Major Changes (Dockerfile, dependencies)**:
```bash
# 1. Make changes
# 2. Commit and push
git add -A
git commit -m "updated dependencies"
git push

# 3. Rebuild local containers
cd ~/Documents/hieucode
docker-compose down
docker-compose build
docker-compose up -d

# 4. Verify everything works
docker ps
curl http://localhost:5000/api/stats
open http://localhost:8081  # Check Airflow
```

## 🎯 Your Questions Answered

### **Q: When I commit, nothing reflects in dashboard?**
**A**: Correct! Because:
- Commit → GitHub Actions (cloud testing)
- Dashboard → Your local containers
- They're separate environments
- Your local containers already have the code (volume mount)

### **Q: How do GitHub Actions sync to local folder?**
**A**: They don't! 
- GitHub Actions runs in cloud
- Your local folder is updated by `git pull` (if needed)
- But Python files are already volume-mounted, so containers see changes immediately

### **Q: Do I need to rebuild after every commit?**
**A**: No!
- ✅ Python files (*.py): Auto-synced, no rebuild needed
- ✅ YAML configs: Auto-synced, no rebuild needed
- ❌ Dockerfiles: Need rebuild
- ❌ requirements.txt: Need rebuild

## 📋 Quick Reference

| Action | Updates Local? | Needs Rebuild? |
|--------|----------------|----------------|
| Edit `dags/daily_crawler.py` | ✅ Auto (volume) | ❌ No |
| Edit `app/mass_crawling.py` | ✅ Auto (volume) | ❌ No |
| Edit `docker-compose.yml` | ❌ Manual restart | ⚠️  Sometimes |
| Edit `Dockerfile` | ❌ Manual rebuild | ✅ Yes |
| Edit `requirements.txt` | ❌ Manual rebuild | ✅ Yes |
| `git commit && git push` | ❌ Tests in cloud | ❌ No |
| `git pull` | ✅ Updates files | ⚠️  Check above |

## 🎉 Current Status

Your setup is **working correctly**! 

- ✅ Airflow schedule updated to 11 AM GMT+7
- ✅ DAG file is volume-mounted (auto-synced)
- ✅ Dashboard showing local data
- ✅ GitHub Actions testing on commits
- ✅ Everything is as expected!

**Nothing is broken** - this is how it's supposed to work! 🚀

---

**Created**: December 17, 2025  
**Author**: GitHub Copilot
