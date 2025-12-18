#!/bin/bash

# CI/CD Deployment Script
# Deploys from ~/Documents/hieucode to ~/Documents/GitHub/action/

set -e  # Exit on error

echo "🚀 Starting deployment to production..."

# Define paths
SOURCE_DIR="$HOME/Documents/hieucode"
PROD_DIR="$HOME/Documents/GitHub/action"

# Ensure production directory exists
mkdir -p "$PROD_DIR"

echo "📦 Copying application files..."

# Copy server.py (dashboard)
if [ -f "$SOURCE_DIR/dashboard/server.py" ]; then
    cp "$SOURCE_DIR/dashboard/server.py" "$PROD_DIR/server.py"
    echo "✅ Copied server.py"
fi

# Copy templates if they exist
if [ -d "$SOURCE_DIR/dashboard/templates" ]; then
    mkdir -p "$PROD_DIR/templates"
    cp -r "$SOURCE_DIR/dashboard/templates/"* "$PROD_DIR/templates/"
    echo "✅ Copied templates"
fi

# Copy static files if they exist
if [ -d "$SOURCE_DIR/dashboard/static" ]; then
    mkdir -p "$PROD_DIR/static"
    cp -r "$SOURCE_DIR/dashboard/static/"* "$PROD_DIR/static/"
    echo "✅ Copied static files"
fi

# Copy requirements.txt
if [ -f "$SOURCE_DIR/dashboard/requirements.txt" ]; then
    cp "$SOURCE_DIR/dashboard/requirements.txt" "$PROD_DIR/requirements.txt"
    echo "✅ Copied requirements.txt"
fi

# Copy docker-compose.yml (pipeline configuration)
if [ -f "$SOURCE_DIR/docker-compose.yml" ]; then
    cp "$SOURCE_DIR/docker-compose.yml" "$PROD_DIR/docker-compose.yml"
    echo "✅ Copied docker-compose.yml"
fi

# Copy app directory (crawler and spark)
if [ -d "$SOURCE_DIR/app" ]; then
    mkdir -p "$PROD_DIR/app"
    cp -r "$SOURCE_DIR/app/"* "$PROD_DIR/app/"
    echo "✅ Copied app directory"
fi

# Copy dags directory (Airflow DAGs)
if [ -d "$SOURCE_DIR/dags" ]; then
    mkdir -p "$PROD_DIR/dags"
    cp -r "$SOURCE_DIR/dags/"* "$PROD_DIR/dags/"
    echo "✅ Copied dags directory"
fi

echo "🔄 Restarting services..."

# Check if dashboard is running and restart it
cd "$PROD_DIR"

if [ -f "dashboard.pid" ]; then
    PID=$(cat dashboard.pid)
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Stopping dashboard (PID: $PID)..."
        kill "$PID"
        sleep 2
    fi
fi

# Start dashboard
if [ -f "dashboard.sh" ]; then
    echo "Starting dashboard..."
    ./dashboard.sh restart
else
    echo "⚠️  dashboard.sh not found, you may need to start manually"
fi

# Update Docker containers if they're running
cd "$SOURCE_DIR"
if docker ps 2>/dev/null | grep -q "kafka-1"; then
    echo "🐳 Updating Docker containers..."
    if docker-compose up -d --no-deps --build crawler spark 2>&1; then
        echo "✅ Docker containers updated"
    else
        echo "⚠️  Warning: Docker container update had issues (this is non-critical)"
        echo "   You may need to restart containers manually with: docker-compose restart crawler spark"
    fi
else
    echo "ℹ️  Docker containers not running, skipping container update"
fi

echo ""
echo "✅ Deployment completed successfully!"
echo "📊 Dashboard: http://localhost:5000"
echo "🌬️  Airflow: http://localhost:8081"
echo ""
echo "📝 Deployment log:"
echo "  - Timestamp: $(date)"
echo "  - Source: $SOURCE_DIR"
echo "  - Target: $PROD_DIR"
