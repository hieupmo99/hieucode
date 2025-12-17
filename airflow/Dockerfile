FROM apache/airflow:2.8.0-python3.11

USER airflow

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy DAGs and scripts
COPY dags/ ${AIRFLOW_HOME}/dags/
COPY app/ /opt/airflow/app/
