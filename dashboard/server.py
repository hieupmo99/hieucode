#!/usr/bin/env python3
"""
Hieucode Data Pipeline Dashboard
Real-time monitoring dashboard for the data crawling pipeline
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
import json
from datetime import datetime
import os
import subprocess

app = Flask(__name__)

# Disable CSRF for API endpoints
app.config['WTF_CSRF_ENABLED'] = False
app.config['WTF_CSRF_CHECK_DEFAULT'] = False

# Configuration
HIEUCODE_DIR = os.path.expanduser('~/Documents/hieucode')
DB_PATH = os.path.join(HIEUCODE_DIR, 'app', 'hieudb.db')
SYNC_INFO_PATH = os.path.join(os.path.dirname(__file__), 'sync-info.json')

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods',
                         'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Load sync info
def get_sync_info():
    """Get information about last sync from GitHub"""
    try:
        if os.path.exists(SYNC_INFO_PATH):
            with open(SYNC_INFO_PATH, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading sync info: {e}")
    return {
        'last_sync': 'Never',
        'commit_sha': 'N/A',
        'commit_message': 'N/A',
        'branch': 'N/A',
        'author': 'N/A'
    }


@app.route('/')
def dashboard():
    """Main dashboard page - Enhanced Control Center"""
    return render_template('dashboard_enhanced.html')


@app.route('/old')
def old_dashboard():
    """Old dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/stats')
def get_stats():
    """Get statistics from the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total articles
        cursor.execute("SELECT COUNT(*) FROM vnexpress")
        total = cursor.fetchone()[0]
        
        # Articles today
        cursor.execute("""
            SELECT COUNT(*) FROM vnexpress 
            WHERE date(timestamp, 'unixepoch', 'localtime') = date('now', 'localtime')
        """)
        today = cursor.fetchone()[0]
        
        # Articles this week
        cursor.execute("""
            SELECT COUNT(*) FROM vnexpress 
            WHERE date(timestamp, 'unixepoch', 'localtime') >= date('now', 'localtime', '-7 days')
        """)
        week = cursor.fetchone()[0]
        
        # Recent articles
        cursor.execute("""
            SELECT title, link, src, timestamp 
            FROM vnexpress 
            ORDER BY timestamp DESC 
            LIMIT 20
        """)
        recent = cursor.fetchall()
        
        # Articles by date (last 7 days)
        cursor.execute("""
            SELECT date(timestamp, 'unixepoch', 'localtime') as day, COUNT(*) as count
            FROM vnexpress 
            WHERE date(timestamp, 'unixepoch', 'localtime') >= date('now', 'localtime', '-7 days')
            GROUP BY date(timestamp, 'unixepoch', 'localtime')
            ORDER BY day DESC
        """)
        by_date = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'total': total,
            'today': today,
            'week': week,
            'recent': [
                {
                    'title': r[0], 
                    'link': r[1], 
                    'src': r[2],
                    'timestamp': r[3]
                }
                for r in recent
            ],
            'by_date': [
                {'date': d[0], 'count': d[1]}
                for d in by_date
            ]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Database not accessible. Is the pipeline running?'
        }), 500


@app.route('/api/kafka/status')
def kafka_status():
    """Check Kafka cluster status"""
    try:
        from kafka import KafkaConsumer
        from kafka.errors import NoBrokersAvailable
        
        try:
            consumer = KafkaConsumer(
                bootstrap_servers=['localhost:19092', 'localhost:29092', 'localhost:39092'],
                consumer_timeout_ms=2000
            )
            topics = consumer.topics()
            
            # Get topic info
            topic_info = {}
            for topic in topics:
                partitions = consumer.partitions_for_topic(topic)
                if partitions:
                    topic_info[topic] = {
                        'partitions': len(partitions)
                    }
            
            consumer.close()
            
            return jsonify({
                'status': 'healthy',
                'topics': list(topics),
                'topic_count': len(topics),
                'topic_info': topic_info
            })
        except NoBrokersAvailable:
            return jsonify({
                'status': 'down',
                'error': 'Kafka brokers not available',
                'message': 'Start Kafka with: docker-compose up -d'
            }), 503
    except ImportError:
        return jsonify({
            'status': 'unknown',
            'error': 'kafka-python not installed',
            'message': 'Install with: pip install kafka-python'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/spark/metrics')
def spark_metrics():
    """Get Spark processing metrics"""
    try:
        # Check if Spark container is running
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=spark', '--format', '{{.Names}}\t{{.Status}}'],
            capture_output=True,
            text=True,
            cwd=HIEUCODE_DIR
        )
        
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            containers = []
            for line in lines:
                if '\t' in line:
                    name, status = line.split('\t', 1)
                    containers.append({
                        'name': name,
                        'status': status
                    })
            
            return jsonify({
                'status': 'running',
                'containers': containers,
                'count': len(containers)
            })
        else:
            return jsonify({
                'status': 'stopped',
                'message': 'Spark container not running',
                'hint': 'Start with: docker-compose up spark -d'
            })
    except FileNotFoundError:
        return jsonify({
            'status': 'error',
            'error': 'Docker not found',
            'message': 'Is Docker installed and running?'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/docker/status')
def docker_status():
    """Get overall Docker containers status"""
    try:
        result = subprocess.run(
            ['docker-compose', 'ps', '--format', 'json'],
            capture_output=True,
            text=True,
            cwd=HIEUCODE_DIR
        )
        
        if result.returncode == 0 and result.stdout.strip():
            # Parse each line as JSON
            containers = []
            for line in result.stdout.strip().split('\n'):
                try:
                    container = json.loads(line)
                    containers.append({
                        'name': container.get('Name', 'unknown'),
                        'service': container.get('Service', 'unknown'),
                        'state': container.get('State', 'unknown'),
                        'status': container.get('Status', 'unknown')
                    })
                except json.JSONDecodeError:
                    continue
            
            running = sum(1 for c in containers if c['state'] == 'running')
            
            return jsonify({
                'status': 'ok',
                'containers': containers,
                'total': len(containers),
                'running': running
            })
        else:
            return jsonify({
                'status': 'no_containers',
                'message': 'No containers running',
                'hint': 'Start with: docker-compose up -d'
            })
    except FileNotFoundError:
        return jsonify({
            'status': 'error',
            'error': 'docker-compose not found'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/sync/info')
def sync_info():
    """Get GitHub sync information"""
    return jsonify(get_sync_info())


@app.route('/api/health')
def health_check():
    """Overall health check"""
    health = {
        'dashboard': 'healthy',
        'timestamp': datetime.now().isoformat()
    }
    
    # Check database
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.close()
        health['database'] = 'accessible'
    except:
        health['database'] = 'not_accessible'
    
    # Check sync info
    sync = get_sync_info()
    health['last_sync'] = sync.get('last_sync', 'Never')
    
    return jsonify(health)


@app.route('/api/airflow/status')
def airflow_status():
    """Get Airflow status"""
    try:
        # Check Airflow containers
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=airflow',
             '--format', '{{.Names}}\t{{.Status}}'],
            capture_output=True,
            text=True,
            cwd=HIEUCODE_DIR
        )
        
        containers = {}
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) == 2:
                        name, status = parts
                        containers[name] = {
                            'status': status,
                            'healthy': 'healthy' in status.lower() or
                                      'up' in status.lower()
                        }
        
        # Check if we can reach Airflow API
        try:
            import requests
            response = requests.get(
                'http://localhost:8081/health', timeout=2)
            api_available = response.status_code == 200
        except Exception:
            api_available = False
        
        return jsonify({
            'success': True,
            'containers': containers,
            'webserver_url': 'http://localhost:8081',
            'api_available': api_available,
            'total_containers': len(containers),
            'healthy_containers': sum(
                1 for c in containers.values() if c['healthy'])
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'containers': {}
        })


@app.route('/api/crawler/status')
def crawler_status():
    """Get crawler status"""
    try:
        # Check crawler container
        result = subprocess.run(
            ['docker', 'exec', 'crawler', 'ps', 'aux'],
            capture_output=True,
            text=True,
            cwd=HIEUCODE_DIR
        )
        
        running = False
        process_count = 0
        chrome_count = 0
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'mass_crawling.py' in line:
                    running = True
                    process_count += 1
                if 'chromium' in line or 'chrome' in line:
                    chrome_count += 1
        
        return jsonify({
            'success': True,
            'running': running,
            'process_count': process_count,
            'chrome_instances': chrome_count,
            'container': 'crawler'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'running': False
        })


@app.route('/api/crawler/start', methods=['POST'])
def start_crawler():
    """Start the crawler"""
    try:
        result = subprocess.run(
            ['docker', 'exec', '-d', 'crawler',
             'python3', 'mass_crawling.py'],
            capture_output=True,
            text=True,
            cwd=HIEUCODE_DIR
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Crawler started successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.stderr
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/crawler/stop', methods=['POST'])
def stop_crawler():
    """Stop the crawler"""
    try:
        # Kill mass_crawling.py process
        result = subprocess.run(
            ['docker', 'exec', 'crawler', 'pkill', '-f',
             'mass_crawling.py'],
            capture_output=True,
            text=True,
            cwd=HIEUCODE_DIR
        )
        
        return jsonify({
            'success': True,
            'message': 'Crawler stopped successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/open-browser')
def open_browser():
    """Open URL in system default browser"""
    try:
        url = request.args.get('url', 'http://localhost:8081')
        # Use macOS 'open' command to open in default browser
        subprocess.run(['open', url], check=True)
        return jsonify({
            'success': True,
            'message': f'Opening {url} in default browser'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/service/start/<service>', methods=['POST'])
def start_service(service):
    """Start a docker-compose service"""
    try:
        result = subprocess.run(
            ['docker-compose', 'up', '-d', service],
            capture_output=True,
            text=True,
            cwd=HIEUCODE_DIR
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': f'{service} started successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.stderr
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/logs/<container>')
def get_container_logs(container):
    """Get logs from a specific container"""
    try:
        result = subprocess.run(
            ['docker', 'logs', '--tail', '200', container],
            capture_output=True,
            text=True,
            cwd=HIEUCODE_DIR,
            timeout=10
        )
        
        logs = result.stdout + result.stderr
        
        return jsonify({
            'success': True,
            'logs': logs,
            'container': container
        })
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Timeout reading logs'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Hieucode Data Pipeline Dashboard")
    print("="*60)
    print(f"📊 Database: {DB_PATH}")
    print(f"📁 Hieucode Directory: {HIEUCODE_DIR}")
    print(f"🔄 Sync Info: {SYNC_INFO_PATH}")
    print(f"🌐 Dashboard URL: http://localhost:5000")
    print("="*60 + "\n")
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print("⚠️  WARNING: Database not found!")
        print(f"   Expected at: {DB_PATH}")
        print("   The dashboard will start but stats won't work until the pipeline runs.\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
