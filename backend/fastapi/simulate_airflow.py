"""
simulate_airflow.py
===================
This script simulates what Apache Airflow would do:
1. "Extract" data from a source database (simulated here)
2. POST it to your OpsSight FastAPI backend for processing

Run this AFTER your FastAPI backend is running locally.
Usage:
    python simulate_airflow.py
"""

import requests
import pandas as pd
import io
import json

# =============================================
# CONFIGURATION - Edit these values
# =============================================
OPSSIGHT_API_URL = "http://127.0.0.1:8000"
MODEL_ID = 1  # Change this to your actual model ID from the UI

# Your JWT token from the browser.
# See instructions below on how to get this.
API_TOKEN = "PASTE_YOUR_TOKEN_HERE"


# =============================================
# STEP 1: Simulate pulling data from a database
# (Replace this with pd.read_sql(...) for a real DB)
# =============================================
def extract_data():
    print("=" * 50)
    print("STEP 1: Extracting data from source database...")
    print("=" * 50)

    # Simulate a daily batch of incoming transaction data
    # Includes intentional issues to test your platform:
    #   - 'user_age' has a string value "thirty" (type error)
    #   - 'transaction_amount' has a None (missing value)
    data = {
        "transaction_amount": [120.50, 45.00, 3000.00, None, 15.99, 250.00, 88.40],
        "user_age":           [25,     42,    "thirty", 55,  19,    38,     61    ],
        "merchant_category":  ["retail","food","electronics","retail","food","travel","retail"],
    }

    df = pd.DataFrame(data)
    print(f"  -> Extracted {len(df)} rows from source.")
    print(df.to_string(index=False))
    print()
    return df


# =============================================
# STEP 2: Send data to OpsSight for processing
# =============================================
def push_to_opssight(df: pd.DataFrame):
    print("=" * 50)
    print("STEP 2: Pushing data to OpsSight backend...")
    print("=" * 50)

    url = f"{OPSSIGHT_API_URL}/data-quality/validate?model_id={MODEL_ID}"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json",
    }

    # Convert pandas DataFrame to an in-memory CSV (no file on disk needed)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    files = {
        "file": ("incoming_data.csv", csv_bytes, "text/csv")
    }

    print(f"  -> Sending to: {url}")
    print(f"  -> Model ID:   {MODEL_ID}")
    print()

    try:
        response = requests.post(url, headers=headers, files=files, timeout=60)
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to the FastAPI backend.")
        print("   Make sure your backend is running on http://127.0.0.1:8000")
        return

    print(f"  -> HTTP Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print()
        print("=" * 50)
        print("✅ SUCCESS! OpsSight processed the data.")
        print("=" * 50)
        print(f"  Run ID        : {result.get('run_id')}")
        print(f"  Baseline Ver  : {result.get('baseline_version')}")
        print(f"  Schema Changed: {result.get('schema_change_detected')}")
        print()
        print("  Validation Result Summary:")
        validation = result.get("result", {})
        print(f"    - Schema Errors : {validation.get('schema_errors', [])}")
        print(f"    - Type Errors   : {validation.get('type_errors', [])}")
        print(f"    - Missing Values: {validation.get('missing_values', {})}")
        print()
        print("👉 Now go to your OpsSight UI and check:")
        print("   - Dashboard   → Total Runs went up")
        print("   - Pipelines   → New run listed")
        print("   - Data Quality→ Type errors detected")
        print("   - Drift       → Drift scores calculated")
        print("   - Incidents   → Any alerts raised")
    elif response.status_code == 401:
        print("❌ ERROR: Authentication failed.")
        print("   Your API_TOKEN is expired or wrong.")
        print("   Follow the instructions at the top of this script to get a fresh token.")
    elif response.status_code == 404:
        print(f"❌ ERROR: Model ID {MODEL_ID} not found.")
        print("   Check the ML Models page in the UI to get the correct Model ID.")
    else:
        print(f"❌ ERROR: Unexpected response.")
        print(f"   {response.text}")


# =============================================
# MAIN
# =============================================
if __name__ == "__main__":
    if API_TOKEN == "PASTE_YOUR_TOKEN_HERE":
        print()
        print("⚠️  You haven't set your API_TOKEN yet!")
        print()
        print("To get your token:")
        print("  1. Open your browser and log in to http://localhost:5173")
        print("  2. Open DevTools (F12) → Application tab → Cookies")
        print("  3. Find the cookie named 'access_token'")
        print("  4. Copy its value and paste it into API_TOKEN in this script.")
        print()
        print("Alternatively, use Swagger at http://localhost:8000/docs:")
        print("  1. Call POST /auth/login with your credentials")
        print("  2. Copy the 'access_token' from the response body")
        print()
    else:
        df = extract_data()
        push_to_opssight(df)
