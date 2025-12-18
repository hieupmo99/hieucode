# CI/CD Pipeline - Setup Complete! 🎉

## ✅ What We've Accomplished

Your local CI/CD pipeline is now fully operational! Here's what's been set up:

### 1. **GitHub Self-Hosted Runner** ✅
- Installed on your Mac at `~/actions-runner/`
- Running as a service (auto-starts on boot)
- Connected to GitHub repository: `hieupmo99/hieucode`
- Current version: 2.329.0
- Status: **Listening for Jobs**

### 2. **Deployment Script** ✅
- Location: `~/Documents/hieucode/scripts/deploy.sh`
- Automatically copies code from development to production
- Restarts services after deployment
- Updates Docker containers

### 3. **CI/CD Workflow** ✅
- Updated `.github/workflows/build-deploy.yml`
- **4 Jobs in pipeline:**
  1. **Build Images** (Cloud) - Builds Docker images
  2. **Deploy & Test** (Cloud) - Tests Kafka, Spark, Crawler
  3. **Deploy Production** (Your Mac) - Deploys to local production
  4. **Notify** (Cloud) - Summary and status

### 4. **Fixed Flake8 Workflow** ✅
- Added `flake8-html` package
- Fixed "No files were found" error
- Conditional artifact upload

### 5. **Dashboard Code in Repository** ✅
- Moved dashboard code into `hieucode/dashboard/`
- Now version controlled in git
- Automatically deploys to production

## 📁 Current Folder Structure

```
~/Documents/
├── hieucode/                          # 🔧 Development (Git Repository)
│   ├── .github/workflows/
│   │   ├── build-deploy.yml          # Main CI/CD pipeline
│   │   └── flake8.yml                # Code linting
│   ├── dashboard/                     # Dashboard source (NEW!)
│   │   ├── server.py
│   │   ├── templates/
│   │   ├── dashboard.sh
│   │   └── requirements.txt
│   ├── app/                          # Crawler & Spark
│   ├── dags/                         # Airflow DAGs
│   ├── scripts/
│   │   └── deploy.sh                 # Deployment script
│   ├── docker-compose.yml
│   ├── LOCAL_CICD_SETUP.md          # Setup guide
│   └── ARCHITECTURE.md
│
├── GitHub/action/                     # 📊 Production (Auto-deployed)
│   ├── server.py                     # ← Deployed automatically
│   ├── templates/                    # ← Deployed automatically
│   ├── dashboard.sh                  # Dashboard startup script
│   └── (other deployed files)
│
└── actions-runner/                    # 🤖 GitHub Runner
    ├── config.sh
    ├── run.sh
    └── action/                       # Workflow work directory
```

## 🔄 How Your CI/CD Works

### When you push code to GitHub:

```
┌─────────────────────────────────────────────────────────────┐
│  1. Developer pushes code                                    │
│     cd ~/Documents/hieucode                                  │
│     git add .                                                │
│     git commit -m "feature: Add new functionality"          │
│     git push                                                 │
└─────────────────┬────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  2. GitHub Actions CI (Cloud)                                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Job 1: Build Images (ubuntu-latest)                  │  │
│  │ - Build crawler Docker image                         │  │
│  │ - Build Spark Docker image                           │  │
│  │ - Build Airflow Docker image                         │  │
│  │ - Validate docker-compose.yml                        │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                      │
│                       ▼                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Job 2: Deploy & Test (ubuntu-latest)                 │  │
│  │ - Start Kafka cluster                                │  │
│  │ - Create topics                                      │  │
│  │ - Start Spark streaming                              │  │
│  │ - Run test crawler                                   │  │
│  │ - Verify database results                            │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                      │
│                       ▼ Tests Passed? ✅                    │
└───────────────────────┼──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  3. GitHub Actions CD (Your Mac - Self-Hosted)              │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Job 3: Deploy Production (self-hosted runner)        │  │
│  │ - Checkout code to ~/actions-runner/action/          │  │
│  │ - Run ~/Documents/hieucode/scripts/deploy.sh         │  │
│  │ - Copy dashboard/ → ~/Documents/GitHub/action/       │  │
│  │ - Copy app/ → ~/Documents/GitHub/action/app/         │  │
│  │ - Copy dags/ → ~/Documents/GitHub/action/dags/       │  │
│  │ - Restart dashboard service                          │  │
│  │ - Update Docker containers                           │  │
│  └────────────────────┬─────────────────────────────────┘  │
└───────────────────────┼──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Production Updated! 🎉                                  │
│     📊 Dashboard: http://localhost:5000                     │
│     🌬️  Airflow:  http://localhost:8081                    │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 What Gets Deployed

When `scripts/deploy.sh` runs:

- ✅ `dashboard/server.py` → `~/Documents/GitHub/action/server.py`
- ✅ `dashboard/templates/` → `~/Documents/GitHub/action/templates/`
- ✅ `dashboard/requirements.txt` → `~/Documents/GitHub/action/requirements.txt`
- ✅ `docker-compose.yml` → `~/Documents/GitHub/action/docker-compose.yml`
- ✅ `app/` → `~/Documents/GitHub/action/app/`
- ✅ `dags/` → `~/Documents/GitHub/action/dags/`
- 🔄 Dashboard restarts automatically
- 🐳 Docker containers rebuild if needed

## 🧪 Testing Your Pipeline

### Make a test change:

```bash
cd ~/Documents/hieucode

# Create a test file
echo "# CI/CD Test $(date)" >> TEST_DEPLOYMENT.md

# Commit and push
git add .
git commit -m "test: Verify CI/CD pipeline deployment"
git push
```

### Watch the deployment:

1. **GitHub Actions**: https://github.com/hieupmo99/hieucode/actions
   - You'll see "Build and Deploy Pipeline" running
   - 4 jobs will execute in sequence

2. **Runner Logs** (optional):
   ```bash
   tail -f ~/Library/Logs/actions.runner*/stdout.log
   ```

3. **Production Folder**:
   ```bash
   ls -la ~/Documents/GitHub/action/
   # You should see TEST_DEPLOYMENT.md after deployment
   ```

## 📊 Monitoring

### Check Runner Status
```bash
cd ~/actions-runner
./svc.sh status
```

### View Runner Logs
```bash
cat ~/Library/Logs/actions.runner*/stdout.log
```

### Check Recent Deployments
```bash
ls -lt ~/Documents/GitHub/action/ | head -10
```

### Dashboard Status
```bash
ps aux | grep server.py
tail -f ~/Documents/GitHub/action/dashboard.log
```

## 🔧 Managing the Runner

### Start Runner
```bash
cd ~/actions-runner
./svc.sh start
```

### Stop Runner
```bash
cd ~/actions-runner
./svc.sh stop
```

### Restart Runner
```bash
cd ~/actions-runner
./svc.sh stop
./svc.sh start
```

### Check Connection
```bash
open "https://github.com/hieupmo99/hieucode/settings/actions/runners"
```

You should see:
- 🟢 **MacBook-Pro-cua-OP-LT-0378** - Idle

## 🐛 Troubleshooting

### Runner Not Picking Up Jobs

**Problem**: Jobs are queued but not running

**Solution**:
```bash
cd ~/actions-runner
./svc.sh status

# If not running:
./svc.sh start

# Check logs:
cat ~/Library/Logs/actions.runner*/stdout.log
```

### Deployment Script Fails

**Problem**: deploy.sh exits with error

**Solution**:
```bash
# Test manually:
cd ~/Documents/hieucode
./scripts/deploy.sh

# Check permissions:
chmod +x scripts/deploy.sh

# Check paths:
ls -la ~/Documents/GitHub/action/
```

### Dashboard Not Restarting

**Problem**: Dashboard doesn't restart after deployment

**Solution**:
```bash
cd ~/Documents/GitHub/action

# Check if running:
ps aux | grep server.py

# Restart manually:
./dashboard.sh restart

# Check logs:
tail -50 dashboard.log
```

### Workflow Stuck on "Waiting for runner"

**Problem**: Deploy production job waiting

**Solution**:
1. Check runner is online: https://github.com/hieupmo99/hieucode/settings/actions/runners
2. Should show 🟢 Idle status
3. If offline, restart: `cd ~/actions-runner && ./svc.sh start`

## 📚 Key Files

| File | Purpose |
|------|---------|
| `.github/workflows/build-deploy.yml` | Main CI/CD pipeline |
| `.github/workflows/flake8.yml` | Code linting workflow |
| `scripts/deploy.sh` | Local deployment script |
| `dashboard/server.py` | Dashboard source code |
| `LOCAL_CICD_SETUP.md` | Complete setup guide |
| `ARCHITECTURE.md` | System architecture docs |

## 🎓 Benefits

✅ **Automated Testing**: Every push triggers tests in cloud  
✅ **Automated Deployment**: Tests pass → auto-deploy to local  
✅ **Version Control**: All code tracked in git  
✅ **No Server Costs**: Your Mac is the "production server"  
✅ **Fast Deployment**: No SSH, just local file copy  
✅ **Rollback Capable**: Can revert commits and redeploy  
✅ **Service Management**: Auto-restarts services after deploy  

## 🔒 Security

- Runner has access to your local filesystem
- Only runs jobs from `hieupmo99/hieucode` repository
- Runs with your user permissions
- Consider limiting GitHub push access to trusted users

## 📈 What's Next?

### Optional Enhancements:

1. **Version Control Production Folder** (Optional)
   ```bash
   cd ~/Documents/GitHub/action
   git init
   git add .
   git commit -m "Initial production snapshot"
   ```

2. **Add Deployment Notifications**
   - Slack notifications on deploy success/failure
   - Email alerts for pipeline failures

3. **Add Rollback Script**
   ```bash
   # In scripts/rollback.sh
   git checkout HEAD~1
   git push -f
   # Triggers redeploy of previous version
   ```

4. **Environment Variables**
   - Use GitHub Secrets for sensitive config
   - Different settings for dev vs production

## 🎉 Success Metrics

Your pipeline is working when:

- ✅ Runner shows "Idle" on GitHub
- ✅ Pushing code triggers workflow
- ✅ All 4 jobs complete successfully
- ✅ Files appear in `~/Documents/GitHub/action/`
- ✅ Dashboard accessible at http://localhost:5000
- ✅ Airflow accessible at http://localhost:8081

## 📞 Quick Reference

```bash
# Check everything is running:
cd ~/actions-runner && ./svc.sh status           # Runner
docker ps                                         # Containers
ps aux | grep server.py                          # Dashboard
curl http://localhost:5000                        # Dashboard endpoint
curl http://localhost:8081                        # Airflow endpoint

# Deploy changes:
cd ~/Documents/hieucode
git add .
git commit -m "your changes"
git push

# Watch deployment:
open "https://github.com/hieupmo99/hieucode/actions"

# Manual deployment:
cd ~/Documents/hieucode
./scripts/deploy.sh
```

---

## 🏆 Congratulations!

You now have a **fully automated CI/CD pipeline** that:
1. Tests your code in the cloud
2. Automatically deploys to your local Mac
3. Keeps production and development separate
4. Version controls all changes
5. Runs completely free (no server costs!)

**Next commit you push will automatically deploy!** 🚀
