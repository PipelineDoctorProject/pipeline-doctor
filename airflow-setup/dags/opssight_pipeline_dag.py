import os
from datetime import datetime, timedelta

import pandas as pd
import requests
from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.hooks.base import BaseHook
from airflow.models.param import Param
from airflow.models import Variable
from airflow.operators.python import PythonOperator

# Airflow connection/variable keys
OPSSIGHT_CONN_ID = os.environ.get("OPSSIGHT_CONN_ID", "opssight_api")
DEFAULT_OPSSIGHT_API_URL = os.environ.get("OPSSIGHT_API_URL", "http://api:8000")
OPSSIGHT_API_URL_VAR = "opssight_api_url"
OPSSIGHT_MODEL_ID_VAR = "opssight_model_id"
OPSSIGHT_MODEL_NAME_VAR = "opssight_model_name"

DATA_DIR = "/opt/airflow/data"


def _get_connection():
    try:
        return BaseHook.get_connection(OPSSIGHT_CONN_ID)
    except Exception as exc:
        raise AirflowException(
            f"Airflow connection '{OPSSIGHT_CONN_ID}' is not configured. "
            "Create an HTTP connection with login/password or extra.api_token."
        ) from exc


def _resolve_api_url(conn):
    extra = conn.extra_dejson or {}
    if extra.get("api_url"):
        return str(extra["api_url"]).rstrip("/")

    variable_url = Variable.get(OPSSIGHT_API_URL_VAR, default_var="").strip()
    if variable_url:
        return variable_url.rstrip("/")

    host = (conn.host or "").strip()
    if host:
        if host.startswith("http://") or host.startswith("https://"):
            base_url = host
        else:
            scheme = conn.conn_type if conn.conn_type in {"http", "https"} else "http"
            base_url = f"{scheme}://{host}"

        if conn.port and f":{conn.port}" not in base_url:
            base_url = f"{base_url}:{conn.port}"
        return base_url.rstrip("/")

    return DEFAULT_OPSSIGHT_API_URL.rstrip("/")


def _build_auth_headers(api_url, conn):
    extra = conn.extra_dejson or {}
    api_token = (extra.get("api_token") or "").strip()

    if api_token:
        return {
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json",
        }

    if conn.login and conn.password:
        login_url = f"{api_url}/auth/login"
        response = requests.post(
            login_url,
            json={"email": conn.login, "password": conn.password},
            headers={"Accept": "application/json"},
            timeout=(15, 120),
        )

        if response.status_code != 200:
            raise AirflowException(
                f"OpsSight login failed with {response.status_code}: {response.text}"
            )

        access_token = response.json().get("access_token")
        if not access_token:
            raise AirflowException(
                "OpsSight login succeeded but no access_token was returned."
            )

        return {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

    raise AirflowException(
        f"Connection '{OPSSIGHT_CONN_ID}' has no auth data. "
        "Set login/password or extra.api_token."
    )


def _lookup_model_id_by_name(api_url, headers, model_name):
    response = requests.get(
        f"{api_url}/ml-models/?limit=500",
        headers=headers,
        timeout=(15, 120),
    )
    if response.status_code != 200:
        raise AirflowException(
            f"Failed to list models ({response.status_code}): {response.text}"
        )

    items = response.json() or []
    name_key = model_name.strip().lower()
    matches = [
        item for item in items
        if str(item.get("name", "")).strip().lower() == name_key
    ]
    if not matches:
        raise AirflowException(
            f"Model name '{model_name}' not found in tenant model registry."
        )

    selected = sorted(matches, key=lambda item: item.get("id", 0), reverse=True)[0]
    return int(selected["id"])


def _resolve_model_id(kwargs, conn, api_url, headers):
    dag_conf = (kwargs.get("dag_run").conf if kwargs.get("dag_run") else {}) or {}
    params = kwargs.get("params") or {}
    extra = conn.extra_dejson or {}

    model_id_value = (
        dag_conf.get("model_id")
        or params.get("model_id")
        or Variable.get(OPSSIGHT_MODEL_ID_VAR, default_var="").strip()
        or extra.get("model_id")
    )

    if model_id_value not in (None, ""):
        try:
            return int(model_id_value)
        except (TypeError, ValueError) as exc:
            raise AirflowException(
                f"Invalid model_id value '{model_id_value}'. Must be an integer."
            ) from exc

    model_name = (
        dag_conf.get("model_name")
        or params.get("model_name")
        or Variable.get(OPSSIGHT_MODEL_NAME_VAR, default_var="").strip()
        or extra.get("model_name")
    )
    if model_name:
        return _lookup_model_id_by_name(api_url, headers, str(model_name))

    return None


def load_data(**_kwargs):
    print("=" * 60)
    print("TASK 1: Loading data from source...")
    print("=" * 60)

    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {DATA_DIR}. "
            "Place input CSV in airflow-setup/data/."
        )

    latest_file = sorted(csv_files)[-1]
    file_path = os.path.join(DATA_DIR, latest_file)
    df = pd.read_csv(file_path)

    print(f"  -> Loaded file: {latest_file}")
    print(f"  -> Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"  -> Columns: {list(df.columns)}")
    return file_path


def push_to_opssight(**kwargs):
    ti = kwargs["ti"]
    file_path = ti.xcom_pull(task_ids="load_data")

    conn = _get_connection()
    api_url = _resolve_api_url(conn)
    headers = _build_auth_headers(api_url, conn)
    model_id = _resolve_model_id(kwargs, conn, api_url, headers)

    print("=" * 60)
    print("TASK 2: Pushing to OpsSight backend for processing...")
    print("=" * 60)

    if model_id is None:
        url = f"{api_url}/data-quality/validate-auto"
    else:
        url = f"{api_url}/data-quality/validate?model_id={model_id}"

    print(f"  -> URL      : {url}")
    print(f"  -> Model ID : {model_id if model_id is not None else 'auto-detect'}")
    print(f"  -> File     : {file_path}")

    with open(file_path, "rb") as handle:
        files = {"file": (os.path.basename(file_path), handle, "text/csv")}
        response = requests.post(url, headers=headers, files=files, timeout=(30, 300))

    print(f"  -> HTTP Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("OpsSight processed successfully.")
        print(f"   Run ID          : {result.get('run_id')}")
        print(f"   Baseline Version: {result.get('baseline_version')}")
        print(f"   Schema Changed  : {result.get('schema_change_detected')}")
        print("Check your OpsSight Dashboard at http://localhost:5173")
        # Keep XCom payload compact for production logs and metadata storage.
        return {
            "run_id": result.get("run_id"),
            "pipeline_status": result.get("pipeline_status"),
            "schema_change_detected": result.get("schema_change_detected"),
        }

    raise AirflowException(
        f"OpsSight returned error {response.status_code}: {response.text}"
    )


default_args = {
    "owner": "opssight",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="opssight_daily_pipeline",
    default_args=default_args,
    description="Sends daily inference data to OpsSight for monitoring",
    schedule_interval="0 2 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    params={
        "model_id": Param(
            "",
            type=["null", "string", "integer"],
            title="Model ID",
            description="Optional. Use this when you know the OpsSight model id.",
        ),
        "model_name": Param(
            "",
            type=["null", "string"],
            title="Model name",
            description="Optional. Used only when model_id is empty.",
        ),
    },
    tags=["opssight", "ml-monitoring"],
) as dag:
    task_load = PythonOperator(
        task_id="load_data",
        python_callable=load_data,
    )

    task_push = PythonOperator(
        task_id="push_to_opssight",
        python_callable=push_to_opssight,
    )

    task_load >> task_push