from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime
import os
import shutil
import requests

INCOMING_DIR = "/opt/airflow/project/uploads/incoming"
PROCESSED_DIR = "/opt/airflow/project/uploads/processed"

FASTAPI_URL = "http://host.docker.internal:8000/data-quality/validate?model_id=1"


def process_incoming_files():

    files = os.listdir(INCOMING_DIR)

    csv_files = [
        f for f in files
        if f.endswith(".csv")
    ]

    if not csv_files:
        print("No files found")
        return

    for file_name in csv_files:

        file_path = os.path.join(
            INCOMING_DIR,
            file_name
        )

        print(f"Processing: {file_name}")

        with open(file_path, "rb") as f:

            response = requests.post(
                FASTAPI_URL,
                files={
                    "file": (
                        file_name,
                        f,
                        "text/csv"
                    )
                }
            )

        print(response.status_code)
        print(response.text)

        destination = os.path.join(
            PROCESSED_DIR,
            file_name
        )

        shutil.move(file_path, destination)

        print(f"Moved to processed: {file_name}")


default_args = {
    "owner": "pipeline-doctor"
}

with DAG(
    dag_id="data_quality_pipeline",
    default_args=default_args,
    start_date=datetime(2026, 5, 1),
    schedule_interval="*/1 * * * *",
    catchup=False
) as dag:

    run_pipeline = PythonOperator(
        task_id="process_incoming_files",
        python_callable=process_incoming_files
    )