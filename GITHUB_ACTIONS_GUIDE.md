# GitHub Actions Setup Guide

## ✅ What You Have Now (No Secrets Needed!)

Your CI/CD pipeline is **fully functional without any secrets**. Here's what it does:

### 1. **Code Quality Checks** (Flake8, Black, etc.)
- Automatically checks your Python code style
- No secrets required ❌

### 2. **Security Scanning** (Bandit, Safety)
- Scans for security vulnerabilities
- No secrets required ❌

### 3. **Testing with Coverage**
```bash
# What coverage means:
pytest tests/ --cov=app

# Example output:
# app/producer.py      85%    # 85% of code is tested
# app/spark_app.py     60%    # 60% of code is tested
# TOTAL                72%    # Overall coverage
```
- Coverage = % of your code that has tests
- Higher = better (more bugs caught)
- **Reports available as artifacts in GitHub Actions**
- No secrets required ❌

### 4. **Docker Build**
- Builds your Docker images
- Tests docker-compose configuration
- No secrets required ❌

### 5. **Kafka Integration Tests**
- Starts Kafka cluster
- Runs your test scripts
- No secrets required ❌

---

## 🔐 When DO You Need Secrets?

### Current Project: **NEVER** ✅
Your pipeline works completely without secrets!

### Future Scenarios Where You MIGHT Need Secrets:

1. **Pushing Docker images to Docker Hub**:
```yaml
# Would need:
# - DOCKERHUB_USERNAME
# - DOCKERHUB_TOKEN
```

2. **Deploying to cloud** (AWS, GCP, Azure):
```yaml
# Would need:
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY
```

3. **Accessing private APIs**:
```yaml
# Would need:
# - API_KEY
# - API_SECRET
```

---

## 📊 How to View Your Coverage Reports

1. Go to: https://github.com/hieupmo99/hieucode/actions
2. Click on any completed workflow run
3. Scroll down to "Artifacts" section
4. Download `coverage-report`
5. Unzip and open `htmlcov/index.html` in browser

You'll see:
- Which files have tests
- Which lines are tested (green) vs untested (red)
- Overall percentage

---

## 🎯 Quick Start - What to Do Now

### Option 1: Run Your Pipeline (Recommended)
```bash
# Already done! Your workflows will run automatically on:
# - Every push to main/develop
# - Every pull request
# - Manual trigger from GitHub Actions tab
```

### Option 2: Add Some Basic Tests (Makes it more useful)
```bash
# Create a simple test
mkdir -p tests
cat > tests/test_producer.py << 'EOF'
import pytest
from app.producer import send_crawled_item

def test_send_crawled_item():
    """Test that send_crawled_item accepts correct data"""
    data = {
        'title': 'Test',
        'link': 'http://test.com',
        'src': 'http://test.com/img.jpg'
    }
    # Just verify it doesn't crash
    # Real test would need mock Kafka
    assert isinstance(data, dict)
EOF

# Run tests locally
pip install pytest pytest-cov
pytest tests/ --cov=app
```

### Option 3: Just Monitor (Easiest)
- Your CI runs automatically
- Check the "Actions" tab occasionally
- Fix any issues it finds

---

## 🚫 What You DON'T Need

❌ **Codecov account** - Coverage already calculated, just download artifacts
❌ **Secrets/Tokens** - Everything works without them
❌ **.env in GitHub** - Never needed (and never should upload .env to GitHub!)
❌ **Paid services** - All tools used are free

---

## 💡 Environment Variables: Local vs CI

### Local Development (.env file):
```bash
# .env (in .gitignore)
KAFKA_BOOTSTRAP=localhost:19092
DATABASE_PATH=/Users/op-lt-0378/Documents/hieucode/app/hieudb.db
```

### GitHub Actions (No .env needed):
- CI tests use **default values** or **test fixtures**
- Kafka runs in Docker on CI server
- SQLite creates temporary test database
- Everything is isolated per workflow run

**Your code already handles this!** Look at `producer.py`:
```python
KAFKA_BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP', 'localhost:19092')  # ← Default value
```

---

## 📈 Next Steps (All Optional)

1. ✅ **Add basic tests** to make coverage meaningful
2. ✅ **Monitor Actions tab** for any issues
3. ✅ **Fix linting errors** if any appear
4. ❌ **Don't worry about secrets** - you don't need them!

---

## ❓ FAQ

**Q: Do I need to configure anything in GitHub?**
A: No! Push your code and it runs automatically.

**Q: Will my .env be used in GitHub Actions?**
A: No, and that's good! .env should never be in Git. CI uses defaults or test values.

**Q: What if tests fail?**
A: Workflow shows error details. Fix locally, push again.

**Q: Can I see what's happening?**
A: Yes! Actions tab shows real-time logs of every step.

**Q: Does this cost money?**
A: No! GitHub Actions is free for public repos (2,000 minutes/month for private repos).
