"""
opssight_pipeline_dag.py
========================
A real Apache Airflow DAG that:
  1. Reads a CSV file from the /data directory (which can come from S3, a DB, etc.)
  2. POSTs it to OpsSight (PipelineDoctor) FastAPI backend for validation,
     cleaning, prediction, drift detection, and incident creation.

Airflow UI: http://localhost:8080
Login:      admin / admin

Place this file in the airflow-setup/dags/ directory.
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# =============================================
# READ CONFIG FROM AIRFLOW ENVIRONMENT
# =============================================
# These are set in docker-compose.yml under 'environment'
OPSSIGHT_API_URL = os.environ.get("OPSSIGHT_API_URL", "http://host.docker.internal:8000")
OPSSIGHT_MODEL_ID = int(os.environ.get("OPSSIGHT_MODEL_ID", "1"))
OPSSIGHT_API_TOKEN = os.environ.get("OPSSIGHT_API_TOKEN", "")

# Directory inside the container where CSV files are placed
DATA_DIR = "/opt/airflow/data"


# =============================================
# TASK 1: LOAD DATA
# This simulates pulling from a real source.
# In production, replace this with:
#   - pd.read_sql(...) for PostgreSQL/Snowflake
#   - pd.read_parquet("s3://...") for AWS S3
#   - pd.read_json(api_response) for external API
# =============================================
def load_data(**kwargs):
    print("=" * 60)
    print("TASK 1: Loading data from source...")
    print("=" * 60)

    # Look for the most recent CSV in the data directory
    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {DATA_DIR}. "
            "Please place your CSV file in the airflow-setup/data/ folder."
        )

    # Pick the latest file
    latest_file = sorted(csv_files)[-1]
    file_path = os.path.join(DATA_DIR, latest_file)
    
    df = pd.read_csv(file_path)
    print(f"  -> Loaded file: {latest_file}")
    print(f"  -> Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"  -> Columns: {list(df.columns)}")

    # Pass file path to next task via XCom
    return file_path


# =============================================
# TASK 2: PUSH TO OPSSIGHT
# =============================================
def push_to_opssight(**kwargs):
    ti = kwargs['ti']
    file_path = ti.xcom_pull(task_ids='load_data')

    print("=" * 60)
    print("TASK 2: Pushing to OpsSight backend for processing...")
    print("=" * 60)

    if not OPSSIGHT_API_TOKEN or OPSSIGHT_API_TOKEN == "REPLACE_WITH_YOUR_JWT_TOKEN":
        raise ValueError(
            "OPSSIGHT_API_TOKEN is not set! "
            "Update it in docker-compose.yml and restart Docker."
        )

    url = f"{OPSSIGHT_API_URL}/data-quality/validate?model_id={OPSSIGHT_MODEL_ID}"
    headers = {
        "Authorization": f"Bearer {OPSSIGHT_API_TOKEN}",
        "Accept": "application/json",
    }

    print(f"  -> URL      : {url}")
    print(f"  -> Model ID : {OPSSIGHT_MODEL_ID}")
    print(f"  -> File     : {file_path}")
    print()

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "text/csv")}
        response = requests.post(url, headers=headers, files=files, timeout=120)

    print(f"  -> HTTP Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print()
        print("✅ OpsSight processed successfully!")
        print(f"   Run ID          : {result.get('run_id')}")
        print(f"   Baseline Version: {result.get('baseline_version')}")
        print(f"   Schema Changed  : {result.get('schema_change_detected')}")
        print()
        print("👉 Check your OpsSight Dashboard at http://localhost:5173")
        return result
    else:
        raise Exception(
            f"OpsSight returned error {response.status_code}: {response.text}"
        )


# =============================================
# DAG DEFINITION
# =============================================
default_args = {
    'owner': 'opssight',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    dag_id='opssight_daily_pipeline',
    default_args=default_args,
    description='Sends daily inference data to OpsSight for monitoring',
    # Runs every day at 2 AM. Change to timedelta(hours=1) for hourly, etc.
    schedule_interval='0 2 * * *',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['opssight', 'ml-monitoring'],
) as dag:

    task_load = PythonOperator(
        task_id='load_data',
        python_callable=load_data,
    )

    task_push = PythonOperator(
        task_id='push_to_opssight',
        python_callable=push_to_opssight,
    )

    # Task dependency: load first, then push
    task_load >> task_push
