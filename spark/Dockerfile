FROM apache/spark-py:latest

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Copy application files
COPY app/spark_app.py /opt/spark-app/spark_app.py
COPY app/sqlite-jdbc.jar /opt/spark-app/sqlite-jdbc.jar

WORKDIR /opt/spark-app

# Run Spark application with Kafka connector
CMD ["spark-submit", \
     "--jars", "/opt/spark-app/sqlite-jdbc.jar", \
     "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0", \
     "/opt/spark-app/spark_app.py"]