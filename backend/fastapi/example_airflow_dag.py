from datetime import datetime, timedelta
import os
import requests
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable

# ==========================================
# CONFIGURATION
# ==========================================
# In a real Airflow setup, these would be stored in Airflow Variables/Connections
OPSSIGHT_API_URL = "http://host.docker.internal:8000" # URL to your FastAPI backend
MODEL_ID = 1

# NOTE: In production, never hardcode tokens. Use Airflow Connections or Secrets.
# For local testing, paste a Bearer token you get from logging into your React UI.
API_TOKEN = "paste_your_jwt_token_here" 

def extract_data_from_db(**kwargs):
    """
    Step 1: Extract data from the company's primary database.
    (Simulated here by creating a quick Pandas DataFrame)
    """
    print("Extracting data from Snowflake/Postgres...")
    
    # Simulating a database pull of the last 24 hours of transactions
    data = {
        "transaction_amount": [120.50, 45.00, 3000.00, None, 15.99],
        "user_age": [25, 42, "thirty", 55, 19], # "thirty" is a deliberate dirty value
        "merchant_category": ["retail", "food", "electronics", "retail", "food"]
    }
    df = pd.DataFrame(data)
    
    # Save temporarily for the next task to pick up
    file_path = "/tmp/daily_transactions.csv"
    df.to_csv(file_path, index=False)
    print(f"Data saved to {file_path}")
    
    # Push file path to Airflow XComs so the next task can find it
    return file_path


def push_to_opssight(**kwargs):
    """
    Step 2: Send the extracted data to OpsSight (PipelineDoctor) 
    for cleaning, validation, and inference.
    """
    ti = kwargs['ti']
    file_path = ti.xcom_pull(task_ids='extract_data')
    
    print(f"Sending {file_path} to OpsSight for processing...")
    
    url = f"{OPSSIGHT_API_URL}/data-quality/validate?model_id={MODEL_ID}"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json"
    }
    
    with open(file_path, "rb") as f:
        files = {"file": ("daily_transactions.csv", f, "text/csv")}
        
        # POST the file to your FastAPI backend
        response = requests.post(url, headers=headers, files=files)
        
    if response.status_code == 200:
        result = response.json()
        print("✅ OpsSight Processing Successful!")
        print(f"Run ID: {result.get('run_id')}")
        print(f"Schema Changed: {result.get('schema_change_detected')}")
        
        # In a real setup, OpsSight would return the cleaned predictions here,
        # and Airflow would save them to a reporting database.
    else:
        print(f"❌ OpsSight Failed: {response.text}")
        raise Exception("OpsSight Monitoring Pipeline Failed")


# ==========================================
# DAG DEFINITION
# ==========================================
default_args = {
    'owner': 'data_engineering_team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'daily_fraud_detection_pipeline',
    default_args=default_args,
    description='Pulls daily transactions and sends to OpsSight for inference and monitoring',
    schedule_interval=timedelta(days=1), # Runs once a day
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['opssight', 'ml_inference'],
) as dag:

    # Define tasks
    t1_extract = PythonOperator(
        task_id='extract_data',
        python_callable=extract_data_from_db,
    )

    t2_process_and_monitor = PythonOperator(
        task_id='push_to_opssight',
        python_callable=push_to_opssight,
    )

    # Set dependencies (T1 runs, then T2)
    t1_extract >> t2_process_and_monitor
