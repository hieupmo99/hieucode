# CI/CD Pipeline Architecture

## 🎯 Current vs Proposed Setup

### **Current Setup (No CD)**:
```
~/Documents/hieucode/              (Development - where you edit code)
├─ Running containers
├─ Dashboard monitors THIS
└─ Manual git push

GitHub Actions (Cloud)
├─ Tests code
└─ No deployment
```

### **Proposed Setup (With CD)**:
```
~/Documents/hieucode/              (Development - where you edit code)
├─ Edit code here
├─ git push triggers CI/CD
└─ Local containers for testing

GitHub Actions (Cloud - CI)
├─ Runs tests
├─ Builds images
└─ If tests pass → Triggers deployment script

~/Documents/hieucode-production/   (Production - auto-deployed)
├─ Code auto-deployed from GitHub
├─ Production containers
├─ Dashboard monitors THIS
└─ Automatic updates
```

## 🏗️ Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│  DEVELOPER WORKFLOW                                          │
└──────────────────────────────────────────────────────────────┘

1. Developer edits code in:
   ~/Documents/hieucode/  (DEV)
   ↓
   
2. git commit && git push
   ↓
   
┌──────────────────────────────────────────────────────────────┐
│  CI PIPELINE (GitHub Actions - Cloud)                        │
├──────────────────────────────────────────────────────────────┤
│  ✅ Build Docker images                                      │
│  ✅ Run tests                                                │
│  ✅ Test crawler                                             │
│  ✅ Verify data in database                                  │
│  ✅ All checks pass?                                         │
└──────────────────────────────────────────────────────────────┘
   ↓ YES
   
┌──────────────────────────────────────────────────────────────┐
│  CD PIPELINE (Deployment - Local)                            │
├──────────────────────────────────────────────────────────────┤
│  1. GitHub Actions triggers deployment webhook               │
│  2. Local script pulls latest code                           │
│  3. Deploys to: ~/Documents/hieucode-production/             │
│  4. Runs: docker-compose down                                │
│  5. Runs: docker-compose build                               │
│  6. Runs: docker-compose up -d                               │
│  7. Verifies: All services healthy                           │
│  8. Notification: Deployment complete                        │
└──────────────────────────────────────────────────────────────┘
   ↓
   
┌──────────────────────────────────────────────────────────────┐
│  PRODUCTION ENVIRONMENT                                      │
├──────────────────────────────────────────────────────────────┤
│  ~/Documents/hieucode-production/                            │
│  ├─ Kafka cluster (19092, 29092, 39092)                     │
│  ├─ Spark streaming                                          │
│  ├─ Crawler (auto-scheduled via Airflow)                    │
│  ├─ Airflow (8081)                                           │
│  ├─ Database: hieudb.db                                      │
│  └─ Dashboard (5000) - Monitors THIS environment            │
└──────────────────────────────────────────────────────────────┘
```

## 🔧 Implementation Options

### **Option 1: Simple Local CD (Recommended for Local Use)**

**Pros**:
- ✅ Easy setup
- ✅ Runs on your Mac
- ✅ No external server needed
- ✅ Separate dev/prod folders

**Cons**:
- ⚠️ Only works on your machine
- ⚠️ Requires your Mac to be on
- ⚠️ Not accessible remotely

**How it works**:
```bash
# Setup
mkdir ~/Documents/hieucode-production
cd ~/Documents/hieucode-production
git clone https://github.com/hieupmo99/hieucode.git .

# Create auto-deploy script
~/deploy-production.sh
  ├─ Pulls latest code
  ├─ Rebuilds containers
  ├─ Restarts services
  └─ Logs deployment
```

### **Option 2: Self-Hosted Server CD (Professional)**

**Pros**:
- ✅ Always running
- ✅ Accessible from anywhere
- ✅ Real production environment
- ✅ Proper deployment pipeline

**Cons**:
- ⚠️ Requires server (VPS, cloud)
- ⚠️ More complex setup
- ⚠️ Costs money

**How it works**:
```bash
# On VPS/Cloud Server
Server (DigitalOcean/AWS/GCP)
  ├─ GitHub webhook listener
  ├─ Pulls code on webhook
  ├─ Rebuilds containers
  ├─ Production database
  └─ Public dashboard
```

### **Option 3: Docker Hub CD (Hybrid)**

**Pros**:
- ✅ Images built once, deployed anywhere
- ✅ Fast deployment (no rebuild)
- ✅ Version control for images

**Cons**:
- ⚠️ Need Docker Hub account
- ⚠️ More CI/CD complexity

**How it works**:
```
GitHub Actions:
  ├─ Builds images
  ├─ Pushes to Docker Hub
  └─ Tags with version

Local Production:
  ├─ Pulls images from Docker Hub
  ├─ docker-compose up
  └─ No rebuild needed
```

## 🎯 Recommended Solution: Simple Local CD

For your use case (local development + production separation), I recommend:

### **Setup**:

1. **Two separate folders**:
   - `~/Documents/hieucode/` → Development (where you edit)
   - `~/Documents/hieucode-production/` → Production (auto-deployed)

2. **Different ports** to avoid conflicts:
   - Dev: Airflow 8081, Dashboard 5000, Kafka 19092/29092/39092
   - Prod: Airflow 8091, Dashboard 5001, Kafka 19093/29093/39093

3. **Automatic deployment** via script triggered by GitHub webhook

4. **Dashboard** monitors production only

### **Workflow**:
```bash
# You work in development
cd ~/Documents/hieucode
vim dags/daily_crawler.py  # Edit code
git commit -m "fix: update schedule"
git push

# GitHub Actions tests
# ↓ Tests pass
# ↓ Triggers deployment

# Auto-deployment happens
cd ~/Documents/hieucode-production
git pull
docker-compose down
docker-compose build
docker-compose up -d

# Dashboard shows production
open http://localhost:5001  # Production dashboard
```

## 📊 Comparison Table

| Feature | Current Setup | Option 1: Local CD | Option 2: Server CD | Option 3: Docker Hub CD |
|---------|---------------|-------------------|--------------------|-----------------------|
| Dev/Prod Separation | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| Auto-deployment | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| Costs | $0 | $0 | $10-50/month | $0 (free tier) |
| Setup Complexity | Easy | Medium | Hard | Medium |
| Requires Server | ❌ No | ❌ No | ✅ Yes | ❌ No |
| Remote Access | ❌ No | ❌ No | ✅ Yes | ⚠️ Limited |
| Production Ready | ❌ No | ⚠️ Local only | ✅ Yes | ⚠️ Local only |

## 🚀 What I Recommend for You

Based on your question, I suggest **Option 1: Simple Local CD**:

```
Current folder structure (AFTER setup):

~/Documents/
├── hieucode/                      (DEVELOPMENT)
│   ├── Edit code here
│   ├── Test manually
│   ├── Git push from here
│   └── docker-compose.dev.yml (port 8081, 5000)
│
├── hieucode-production/           (PRODUCTION)
│   ├── Auto-deployed code
│   ├── Never edit directly
│   ├── Airflow runs here
│   └── docker-compose.yml (port 8091, 5001)
│
└── deploy-scripts/
    ├── deploy-production.sh       (Auto-deployment script)
    ├── check-health.sh            (Health checks)
    └── rollback.sh                (Rollback on failure)
```

## 🎯 Benefits You Get:

1. **✅ Separation**: Dev and prod are separate
2. **✅ Automatic**: Push code → auto-deployed to prod
3. **✅ Safe**: Test in dev before production
4. **✅ Dashboard**: Monitors production environment
5. **✅ Airflow**: Production DAG runs scheduled tasks
6. **✅ Rollback**: Easy to revert if something breaks
7. **✅ No costs**: Runs on your Mac

## 🤔 Do You Want Me To:

1. **Set up Option 1** (Local CD with separate folders)?
   - Create production folder
   - Set up auto-deployment script
   - Configure different ports
   - Update dashboard to monitor production

2. **Keep current setup** (just monitoring)?
   - Current dashboard is fine for development
   - Manually deploy when needed

3. **Plan for server deployment** (Option 2)?
   - Design VPS deployment
   - Set up proper CI/CD pipeline
   - Public production environment

**Which option do you prefer? Tell me and I'll implement it for you!** 🚀

---

**Created**: December 17, 2025  
**Author**: GitHub Copilot
