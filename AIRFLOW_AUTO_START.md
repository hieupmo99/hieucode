# Airflow DAG Auto-Start Feature

## Overview
The `vnexpress_daily_crawler` DAG now automatically starts all required services (Kafka, Spark, and Crawler) if they're not running when you trigger the DAG.

## How It Works

### DAG Task Flow
```
┌─────────────────┐
│  start_kafka    │ ──┐
└─────────────────┘   │
                      │
┌─────────────────┐   │
│  start_spark    │ ──┼──> ┌────────────────────┐
└─────────────────┘   │    │ check_kafka_health │
                      │    └────────────────────┘
┌─────────────────┐   │              │
│ start_crawler   │ ──┘              │
│   _container    │                  ▼
└─────────────────┘         ┌─────────────────┐
                            │ crawl_vnexpress │
                            └─────────────────┘
                                     │
                                     ▼
                            ┌────────────────────────┐
                            │ check_spark_processing │
                            └────────────────────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ log_completion  │
                            └─────────────────┘
```

### Service Startup Tasks (Run in Parallel)

1. **start_kafka**: Checks if all 3 Kafka brokers are running
   - If <3 brokers running: starts kafka-1, kafka-2, kafka-3
   - Waits 20 seconds for Kafka to be ready

2. **start_spark**: Checks if Spark container is running
   - If not running: starts the spark container
   - Waits 10 seconds for Spark to initialize

3. **start_crawler_container**: Ensures crawler container is running
   - If stopped: starts the crawler container
   - Waits 5 seconds for container to be ready

All three tasks run **in parallel** for faster startup, then the DAG proceeds to check Kafka health.

## Usage

### Automatic Execution (Scheduled)
The DAG runs automatically every day at 6:00 AM (schedule: `'0 6 * * *'`).

### Manual Trigger

#### From Airflow UI:
1. Open Airflow UI: http://localhost:8081
2. Login with: `admin` / `admin`
3. Find `vnexpress_daily_crawler` in the DAG list
4. Click the "Play" button (▶️) to trigger
5. Watch the Graph view to see services starting

#### From Command Line:
```bash
cd /Users/op-lt-0378/Documents/hieucode
docker exec airflow-scheduler airflow dags trigger vnexpress_daily_crawler
```

#### From Dashboard:
1. Open Dashboard: http://localhost:5000
2. Go to "Services Control" tab
3. Click "Open Airflow UI"
4. Trigger the DAG from Airflow

## Testing the Auto-Start Feature

### Stop all services and test:
```bash
cd /Users/op-lt-0378/Documents/hieucode

# Stop all pipeline services
docker-compose stop kafka-1 kafka-2 kafka-3 spark crawler

# Trigger DAG
docker exec airflow-scheduler airflow dags trigger vnexpress_daily_crawler

# Watch services start
watch -n 2 'docker ps --format "table {{.Names}}\t{{.Status}}"'
```

### Check logs:
```bash
# Watch DAG execution logs
docker logs airflow-scheduler --follow

# Check specific task logs
docker exec airflow-scheduler airflow tasks logs vnexpress_daily_crawler start_kafka 2025-12-17
```

## Important Notes

### Docker Socket Access
The Airflow containers need access to the Docker socket to start services:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

This is configured in `docker-compose.yml` for both `airflow-scheduler` and `airflow-webserver`.

### Permissions
Tasks run docker commands as root user from within the Airflow container to manage other containers.

### Service Dependencies
- **Kafka** must be healthy before crawling starts
- **Spark** processes the data after crawling
- **Crawler container** must be running to execute crawler scripts

### Retry Logic
- Service startup tasks: No retries (they handle their own checks)
- Health checks: 3 retry attempts with 10-second delays
- Crawler task: 2 retries with 5-minute delays (configured in `default_args`)

## Monitoring

### Check DAG Status:
```bash
# List all DAGs
docker exec airflow-scheduler airflow dags list

# Show DAG structure
docker exec airflow-scheduler airflow dags show vnexpress_daily_crawler

# List all tasks
docker exec airflow-scheduler airflow tasks list vnexpress_daily_crawler
```

### Check Service Status from Dashboard:
1. Open: http://localhost:5000
2. "Overview" tab shows all service statuses in real-time
3. Green dot (●) = running, Red dot (●) = stopped

## Troubleshooting

### Services don't start automatically:
1. Check Docker socket permissions:
   ```bash
   docker exec airflow-scheduler ls -l /var/run/docker.sock
   ```

2. Verify Docker CLI is available:
   ```bash
   docker exec airflow-scheduler which docker
   ```

3. Check task logs for errors:
   ```bash
   docker exec airflow-scheduler airflow tasks logs vnexpress_daily_crawler start_kafka latest
   ```

### DAG fails to parse:
```bash
# Check for syntax errors
docker logs airflow-scheduler 2>&1 | grep -i "SyntaxError\|daily_crawler"

# Manually test DAG file
docker exec airflow-scheduler python /opt/airflow/dags/daily_crawler.py
```

### Services start but crawler doesn't run:
- Check crawler container logs:
  ```bash
  docker logs crawler --tail 50
  ```
- Verify Kafka topic exists:
  ```bash
  docker exec kafka-1 kafka-topics.sh --list --bootstrap-server localhost:9092
  ```

## Configuration

### Change Schedule:
Edit `/Users/op-lt-0378/Documents/hieucode/dags/daily_crawler.py`:
```python
schedule_interval='0 6 * * *',  # Change time here (cron format)
```

### Adjust Wait Times:
If services need more time to start, increase sleep times in the service startup functions:
```python
time.sleep(20)  # Kafka startup wait
time.sleep(10)  # Spark startup wait
time.sleep(5)   # Crawler startup wait
```

### Disable Auto-Start:
To disable automatic service startup, pause the DAG in Airflow UI or remove the DAG file from `dags/` folder.

## Integration with Dashboard

The dashboard (http://localhost:5000) and Airflow DAG work independently:

- **Dashboard controls**: Manual start/stop for immediate testing
- **Airflow DAG**: Automated scheduling and orchestration with service auto-start

When you trigger the DAG, the dashboard will reflect service status changes automatically (refresh every 5 seconds).

## Benefits

✅ **Fully Automated**: No need to manually start services before crawling  
✅ **Reliable**: Services are checked and started every time  
✅ **Parallel Startup**: All services start simultaneously for speed  
✅ **Error Recovery**: Health checks with retry logic ensure reliability  
✅ **Scheduled**: Runs daily at 6 AM without intervention  
✅ **Manual Override**: Can still trigger manually anytime  

## Next Steps

1. Enable the DAG in Airflow UI (toggle switch)
2. Test manual trigger to verify auto-start works
3. Let it run on schedule and monitor the first automatic execution
4. Check database to verify articles are being collected
5. Monitor Airflow logs for any issues

## Support Files

- DAG file: `/Users/op-lt-0378/Documents/hieucode/dags/daily_crawler.py`
- Docker Compose: `/Users/op-lt-0378/Documents/hieucode/docker-compose.yml`
- Dashboard: `~/Documents/GitHub/action/server.py`
- Database: `/Users/op-lt-0378/Documents/hieucode/app/hieudb.db`

---
**Last Updated**: December 17, 2025  
**Author**: GitHub Copilot  
**Version**: 1.0
