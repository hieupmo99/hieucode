from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json, col, window, count, from_unixtime, current_timestamp
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, TimestampType
)


spark = SparkSession.builder \
    .appName("vnexpress_crawler") \
    .config("spark.jars", "/opt/spark-app/sqlite-jdbc.jar") \
    .config("spark.driver.extraClassPath", "/opt/spark-app/sqlite-jdbc.jar") \
    .config("spark.executor.extraClassPath", "/opt/spark-app/sqlite-jdbc.jar") \
    .getOrCreate()

schema = StructType([
    StructField('title', StringType(), True),
    StructField('link', StringType(), True),
    StructField('src', StringType(), True),
    StructField('timestamp', DoubleType(), True)
])

# Read from Kafka
df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "kafka-1:9092,kafka-2:9092,kafka-3:9092") \
    .option("subscribe", "vnexpress_topic") \
    .option("startingOffsets", "latest") \
    .load()

# Parse JSON and add Kafka ingestion timestamp for speed metrics
json_df = df.selectExpr("CAST(value AS STRING) as json_value", "timestamp") \
    .select(
        from_json(col("json_value"), schema).alias("data"),
        col("timestamp").cast(TimestampType()).alias("kafka_timestamp")
    ) \
    .select("data.*", "kafka_timestamp")


def write_batch(batch_df, batch_id):
    """Process each batch: write to SQLite and show stats"""
    import sqlite3
    import time
    
    if batch_df.isEmpty():
        print(f"Batch {batch_id}: No data")
        return
    
    batch_size = batch_df.count()
    print("=" * 60)
    print(f"Batch {batch_id}: Processing {batch_size} records")
    print("=" * 60)
    
    # Show sample records
    print("Sample records:")
    batch_df.select("title", "link", "src").show(5, truncate=False)
    
    # Calculate crawl speed (items per second based on Kafka timestamp)
    speed_df = batch_df \
        .withWatermark("kafka_timestamp", "10 seconds") \
        .groupBy(window(col("kafka_timestamp"), "1 second")) \
        .agg(count("*").alias("items_per_sec"))
    
    print("📊 Crawl Speed Metrics (items per second):")
    speed_df.select("window.start", "window.end", "items_per_sec").show(
        truncate=False
    )
    
    # Write to SQLite using Python sqlite3
    start_time = time.time()
    try:
        conn = sqlite3.connect("/opt/app/hieudb.db")
        cursor = conn.cursor()
        
        # Insert records with timestamp
        records = batch_df.collect()
        inserted = 0
        duplicates = 0
        
        for row in records:
            try:
                cursor.execute(
                    "INSERT INTO vnexpress (title, link, src, timestamp) VALUES (?, ?, ?, ?)",
                    (row.title, row.link, row.src, str(row.timestamp))
                )
                inserted += 1
            except sqlite3.IntegrityError:
                # Skip duplicates (src is UNIQUE)
                duplicates += 1
        
        conn.commit()
        conn.close()
        
        write_time = time.time() - start_time
        write_speed = inserted / write_time if write_time > 0 else 0
        
        print(f"✓ Inserted {inserted} new, skipped {duplicates} duplicates")
        print(f"⚡ SQLite write speed: {write_speed:.1f} records/sec")
        print(f"⏱️  Write time: {write_time:.3f} seconds")
    except Exception as e:
        print(f"✗ Error writing to SQLite: {e}")
    
    print()


# Single streaming query with foreachBatch to handle everything
query = json_df.writeStream \
    .foreachBatch(write_batch) \
    .outputMode("append") \
    .option("checkpointLocation", "/tmp/spark-checkpoint") \
    .start()

query.awaitTermination()


