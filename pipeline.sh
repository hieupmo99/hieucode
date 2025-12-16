#!/bin/bash

# Hieucode Pipeline Management Script
# Manage all services: Kafka, Spark, Crawler, Airflow

ACTION="${1:-status}"

show_usage() {
    echo "Hieucode Pipeline Management"
    echo ""
    echo "Usage: ./pipeline.sh {start|stop|restart|status|logs|airflow}"
    echo ""
    echo "Commands:"
    echo "  start        - Start all services"
    echo "  stop         - Stop all services"
    echo "  restart      - Restart all services"
    echo "  status       - Show service status"
    echo "  logs         - Show logs (all services)"
    echo "  airflow      - Open Airflow UI in browser"
    echo "  kafka-ui     - Open Kafka UI in browser"
    echo "  dashboard    - Open dashboard in browser"
    echo ""
    echo "Service-specific commands:"
    echo "  ./pipeline.sh start kafka      - Start only Kafka"
    echo "  ./pipeline.sh start spark      - Start only Spark"
    echo "  ./pipeline.sh start airflow    - Start only Airflow"
    echo "  ./pipeline.sh logs airflow     - Show Airflow logs"
    echo ""
}

case "$ACTION" in
    start)
        SERVICE="${2:-all}"
        if [ "$SERVICE" == "all" ]; then
            echo "🚀 Starting all services..."
            docker-compose up -d
            echo ""
            echo "✅ All services started!"
            echo ""
            echo "🌐 Access Points:"
            echo "   • Kafka UI:    http://localhost:8080"
            echo "   • Airflow UI:  http://localhost:8081"
            echo "   • Dashboard:   http://localhost:5000"
            echo ""
        elif [ "$SERVICE" == "kafka" ]; then
            echo "🚀 Starting Kafka cluster..."
            docker-compose up -d kafka-1 kafka-2 kafka-3 kafka-ui
            echo "✅ Kafka started! UI: http://localhost:8080"
        elif [ "$SERVICE" == "spark" ]; then
            echo "🚀 Starting Spark..."
            docker-compose up -d spark
            echo "✅ Spark started!"
        elif [ "$SERVICE" == "airflow" ]; then
            echo "🚀 Starting Airflow..."
            docker-compose up -d postgres-airflow airflow-webserver airflow-scheduler
            echo "✅ Airflow started! UI: http://localhost:8081"
        else
            echo "❌ Unknown service: $SERVICE"
            show_usage
        fi
        ;;
        
    stop)
        echo "🛑 Stopping all services..."
        docker-compose down
        echo "✅ All services stopped"
        ;;
        
    restart)
        echo "🔄 Restarting all services..."
        docker-compose restart
        echo "✅ All services restarted"
        ;;
        
    status)
        echo "📊 Service Status:"
        echo ""
        docker-compose ps
        echo ""
        echo "🔍 Health Check:"
        
        # Check Kafka
        if docker ps | grep -q kafka-1; then
            echo "  ✅ Kafka: Running"
        else
            echo "  ❌ Kafka: Not running"
        fi
        
        # Check Spark
        if docker ps | grep -q spark; then
            echo "  ✅ Spark: Running"
        else
            echo "  ❌ Spark: Not running"
        fi
        
        # Check Airflow
        if docker ps | grep -q airflow-webserver; then
            echo "  ✅ Airflow: Running"
        else
            echo "  ❌ Airflow: Not running"
        fi
        
        # Check Dashboard
        if lsof -ti:5000 >/dev/null 2>&1; then
            echo "  ✅ Dashboard: Running"
        else
            echo "  ❌ Dashboard: Not running"
        fi
        ;;
        
    logs)
        SERVICE="${2:-}"
        if [ -z "$SERVICE" ]; then
            echo "📋 Showing all logs (Ctrl+C to exit)..."
            docker-compose logs -f
        else
            echo "📋 Showing logs for $SERVICE (Ctrl+C to exit)..."
            docker-compose logs -f "$SERVICE"
        fi
        ;;
        
    airflow)
        if docker ps | grep -q airflow-webserver; then
            echo "🌐 Opening Airflow UI..."
            open http://localhost:8081
        else
            echo "❌ Airflow is not running"
            echo "💡 Start with: ./pipeline.sh start airflow"
        fi
        ;;
        
    kafka-ui)
        if docker ps | grep -q kafka-ui; then
            echo "🌐 Opening Kafka UI..."
            open http://localhost:8080
        else
            echo "❌ Kafka UI is not running"
            echo "💡 Start with: ./pipeline.sh start kafka"
        fi
        ;;
        
    dashboard)
        if lsof -ti:5000 >/dev/null 2>&1; then
            echo "🌐 Opening Dashboard..."
            open http://localhost:5000
        else
            echo "❌ Dashboard is not running"
            echo "💡 Start with: /Users/op-lt-0378/Documents/GitHub/action/dashboard.sh start"
        fi
        ;;
        
    help|--help|-h)
        show_usage
        ;;
        
    *)
        echo "❌ Unknown command: $ACTION"
        echo ""
        show_usage
        exit 1
        ;;
esac
