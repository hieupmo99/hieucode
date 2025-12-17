# Local CI/CD Pipeline Setup

This repository uses a **local CI/CD pipeline** where:
- **CI (Continuous Integration)**: Tests run in GitHub Actions cloud
- **CD (Continuous Deployment)**: Automatically deploys to your local Mac

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  GitHub Repository (hieupmo99/hieucode)                     │
│  ~/Documents/hieucode/                                       │
│  - Source code (Kafka, Spark, Airflow, Crawler)            │
│  - Dashboard code (Flask app)                               │
│  - DAGs, configurations                                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ git push
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  GitHub Actions (Cloud)                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Build Images │→ │ Run Tests    │→ │ Deploy Local │     │
│  │ (ubuntu)     │  │ (ubuntu)     │  │ (self-hosted)│     │
│  └──────────────┘  └──────────────┘  └──────┬───────┘     │
└────────────────────────────────────────────────┼────────────┘
                                                 │
                      Runs on your Mac ─────────┘
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Production Folder (~/Documents/GitHub/action/)             │
│  - server.py (Dashboard)                                    │
│  - templates/                                               │
│  - docker-compose.yml                                       │
│  - app/ (crawler & Spark)                                   │
│  - dags/ (Airflow DAGs)                                     │
│                                                              │
│  📊 Dashboard: http://localhost:5000                        │
│  🌬️  Airflow:  http://localhost:8081                       │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Setup Instructions

### 1. Configure GitHub Self-Hosted Runner

First, set up the runner on your Mac:

```bash
cd ~/actions-runner

# Configure the runner (get token from GitHub)
./config.sh --url https://github.com/hieupmo99/hieucode --token YOUR_TOKEN

# Install as a service (runs automatically on boot)
./svc.sh install
./svc.sh start
```

**Get the token from:** https://github.com/hieupmo99/hieucode/settings/actions/runners/new

### 2. Verify Runner Status

Check that your runner is online:

```bash
# Check service status
./svc.sh status

# Or visit GitHub:
# https://github.com/hieupmo99/hieucode/settings/actions/runners
```

You should see your Mac listed as an online runner.

### 3. Test the Pipeline

Make a simple change and push:

```bash
cd ~/Documents/hieucode

# Make a change
echo "# Test deployment" >> README.md

# Commit and push
git add .
git commit -m "test: CI/CD pipeline"
git push
```

### 4. Watch the Deployment

1. Go to: https://github.com/hieupmo99/hieucode/actions
2. You'll see the workflow running with 4 jobs:
   - ✅ Build Images (cloud)
   - ✅ Deploy & Test Pipeline (cloud)
   - ✅ **Deploy to Local Production** (your Mac)
   - ✅ Notify Deployment Status (cloud)

3. The deployment will automatically:
   - Copy code to `~/Documents/GitHub/action/`
   - Restart the dashboard
   - Update Docker containers

## 📁 Folder Structure

```
~/Documents/
├── hieucode/                    # Development (git repository)
│   ├── .github/workflows/       # CI/CD configuration
│   ├── dashboard/               # Dashboard source code
│   │   ├── server.py
│   │   ├── templates/
│   │   └── requirements.txt
│   ├── app/                     # Crawler & Spark
│   ├── dags/                    # Airflow DAGs
│   ├── scripts/
│   │   └── deploy.sh           # Deployment script
│   └── docker-compose.yml
│
└── GitHub/action/               # Production (deployed automatically)
    ├── server.py                # ← Deployed from hieucode/dashboard/
    ├── templates/               # ← Deployed from hieucode/dashboard/
    ├── docker-compose.yml       # ← Deployed from hieucode/
    ├── app/                     # ← Deployed from hieucode/app/
    └── dags/                    # ← Deployed from hieucode/dags/
```

## 🔄 How It Works

### When you push code to GitHub:

1. **CI Stage (Cloud)**
   - GitHub Actions builds Docker images
   - Runs tests in isolated environment
   - Validates Kafka, Spark, and crawler

2. **CD Stage (Your Mac)**
   - If tests pass, triggers deployment
   - Self-hosted runner executes `scripts/deploy.sh`
   - Copies files from `hieucode/` to `GitHub/action/`
   - Restarts services automatically

### What Gets Deployed:

- ✅ Dashboard code (`server.py`, templates)
- ✅ Docker configurations
- ✅ Crawler and Spark code
- ✅ Airflow DAGs
- ❌ Git history (production folder is not a git repo)

## 🎯 Deployment Script

The deployment is handled by `scripts/deploy.sh`:

```bash
# Manual deployment (if needed)
cd ~/Documents/hieucode
./scripts/deploy.sh
```

This script:
1. Copies updated files to production
2. Restarts the dashboard
3. Updates Docker containers
4. Shows deployment summary

## 🔧 Managing the Runner

```bash
cd ~/actions-runner

# Start the runner
./svc.sh start

# Stop the runner
./svc.sh stop

# Check status
./svc.sh status

# Uninstall (if needed)
./svc.sh uninstall
```

## 📊 Monitoring

### Check Pipeline Status
- **GitHub Actions**: https://github.com/hieupmo99/hieucode/actions
- **Dashboard**: http://localhost:5000
- **Airflow**: http://localhost:8081

### View Deployment Logs
```bash
# Check runner logs
cd ~/actions-runner
tail -f _diag/Runner_*.log

# Check dashboard logs
tail -f ~/Documents/GitHub/action/dashboard.log
```

## 🐛 Troubleshooting

### Runner Not Picking Up Jobs

```bash
cd ~/actions-runner
./svc.sh status

# If stopped, start it:
./svc.sh start
```

### Deployment Failed

```bash
# Check deploy script permissions
ls -la ~/Documents/hieucode/scripts/deploy.sh

# Should be executable (rwxr-xr-x)
chmod +x ~/Documents/hieucode/scripts/deploy.sh

# Test deployment manually
cd ~/Documents/hieucode
./scripts/deploy.sh
```

### Dashboard Not Restarting

```bash
cd ~/Documents/GitHub/action

# Check if running
ps aux | grep server.py

# Restart manually
./dashboard.sh restart
```

## 🎓 Benefits of This Setup

✅ **Automatic Deployment**: Push code → Tests run → Auto-deploy to local
✅ **No Server Costs**: Your Mac is the "production server"
✅ **Safe Testing**: Tests run in cloud before deploying locally
✅ **Fast Deployment**: No SSH, no remote servers, just local file copy
✅ **Version Control**: Source code is tracked in git
✅ **Rollback Capable**: Can revert commits and redeploy

## 🔒 Security Notes

- The self-hosted runner has access to your local filesystem
- Only trusted team members should have push access to the repository
- The runner runs with your user permissions
- Consider using a dedicated Mac user account for the runner

## 📚 Additional Resources

- [GitHub Self-Hosted Runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- Project architecture: `ARCHITECTURE.md`
- Airflow auto-start: `AIRFLOW_AUTO_START.md`
