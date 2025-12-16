#!/bin/bash

# Airflow Setup Script
# Builds and starts Airflow services

set -e

echo "============================================"
echo "🚀 Setting up Airflow"
echo "============================================"

# Check if running from correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found"
    echo "Please run this script from the hieucode directory"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p dags logs airflow/dags

# Set permissions for Airflow
echo "🔐 Setting permissions..."
chmod -R 777 logs 2>/dev/null || sudo chmod -R 777 logs

# Build Airflow image
echo "🔨 Building Airflow image (this may take a few minutes)..."
docker-compose build airflow-webserver airflow-scheduler

# Start PostgreSQL first
echo "🗄️  Starting PostgreSQL..."
docker-compose up -d postgres-airflow

# Wait for PostgreSQL to be healthy
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Initialize Airflow database
echo "📊 Initializing Airflow database..."
docker-compose run --rm airflow-webserver airflow db migrate || echo "Database already initialized"

# Create admin user
echo "👤 Creating Airflow admin user..."
docker-compose run --rm airflow-webserver airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@hieucode.com || echo "Admin user already exists"

# Start Airflow services
echo "🚀 Starting Airflow services..."
docker-compose up -d airflow-webserver airflow-scheduler

# Wait for services to be ready
echo "⏳ Waiting for Airflow to be ready..."
sleep 15

# Check status
echo ""
echo "============================================"
echo "✅ Airflow Setup Complete!"
echo "============================================"
echo ""
echo "📊 Airflow Web UI: http://localhost:8081"
echo "👤 Username: admin"
echo "🔑 Password: admin"
echo ""
echo "📋 DAGs Location: ./dags/"
echo "📜 Logs Location: ./logs/"
echo ""
echo "🔍 Check status with:"
echo "   docker-compose ps"
echo ""
echo "📖 View logs with:"
echo "   docker-compose logs -f airflow-webserver"
echo "   docker-compose logs -f airflow-scheduler"
echo ""
