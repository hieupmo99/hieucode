#!/bin/bash

# Dashboard Control Script

ACTION="${1:-status}"
DASHBOARD_DIR="/Users/op-lt-0378/Documents/GitHub/action"
PID_FILE="$DASHBOARD_DIR/dashboard.pid"
LOG_FILE="$DASHBOARD_DIR/dashboard.log"

cd "$DASHBOARD_DIR" || exit 1

get_pid() {
    lsof -ti:5000 2>/dev/null
}

case "$ACTION" in
    start)
        if PID=$(get_pid); then
            echo "❌ Dashboard already running (PID: $PID)"
            echo "   Use './dashboard.sh stop' first"
            exit 1
        fi
        
        echo "🚀 Starting dashboard..."
        nohup python3 server.py > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        sleep 2
        
        if PID=$(get_pid); then
            echo "✅ Dashboard started successfully (PID: $PID)"
            echo "🌐 Open: http://localhost:5000"
        else
            echo "❌ Failed to start dashboard"
            echo "📋 Check logs: tail -f $LOG_FILE"
            exit 1
        fi
        ;;
        
    stop)
        if PID=$(get_pid); then
            echo "🛑 Stopping dashboard (PID: $PID)..."
            kill $PID 2>/dev/null
            sleep 1
            if ! get_pid >/dev/null 2>&1; then
                echo "✅ Dashboard stopped"
                rm -f "$PID_FILE"
            else
                echo "⚠️  Force killing..."
                kill -9 $PID 2>/dev/null
                rm -f "$PID_FILE"
                echo "✅ Dashboard force stopped"
            fi
        else
            echo "ℹ️  Dashboard is not running"
        fi
        ;;
        
    restart)
        echo "🔄 Restarting dashboard..."
        "$0" stop
        sleep 1
        "$0" start
        ;;
        
    status)
        if PID=$(get_pid); then
            echo "✅ Dashboard is running (PID: $PID)"
            echo "🌐 URL: http://localhost:5000"
            echo "📁 Directory: $DASHBOARD_DIR"
            echo "📋 Logs: $LOG_FILE"
        else
            echo "❌ Dashboard is not running"
            echo "💡 Start with: $0 start"
        fi
        ;;
        
    logs)
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            echo "❌ No log file found"
        fi
        ;;
        
    open)
        if get_pid >/dev/null 2>&1; then
            echo "🌐 Opening dashboard in browser..."
            open http://localhost:5000
        else
            echo "❌ Dashboard is not running"
            echo "💡 Start with: $0 start"
            exit 1
        fi
        ;;
        
    *)
        echo "Dashboard Control Script"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|open}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the dashboard"
        echo "  stop     - Stop the dashboard"
        echo "  restart  - Restart the dashboard"
        echo "  status   - Show dashboard status"
        echo "  logs     - Show live logs (Ctrl+C to exit)"
        echo "  open     - Open dashboard in browser"
        echo ""
        echo "Examples:"
        echo "  $0 start         # Start dashboard"
        echo "  $0 status        # Check if running"
        echo "  $0 logs          # View logs"
        echo "  $0 restart       # Restart dashboard"
        exit 1
        ;;
esac
