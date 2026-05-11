# ML Integration — MLflow Dynamic Model Loading

PipelineDoctor integrates with MLflow to dynamically load, cache, and run ML models for inference. The system is model-agnostic and supports multiple models on different MLflow servers simultaneously.

---

## 🔄 Model Loading Flow

```
Pipeline Run starts (model_id passed in)
        ↓
get_mlflow_model(db, model_id)
        ↓
Query `ml_models` table for model config
        ↓
Check in-memory _model_cache
        ↓ (cache miss)
Set mlflow.set_tracking_uri(db_model.mlflow_tracking_uri)
        ↓
Load model: mlflow.pyfunc.load_model("models:/NAME@ALIAS")
        ↓
Cache model in _model_cache[cache_key]
        ↓ (cache hit on next run — fast)
Return model object + db_model config
```

---

## 📋 Model Registration

Before the pipeline can load a model, it must be registered in the **`ml_models`** database table via the API.

**Endpoint:** `POST /ml-models/`

```json
{
  "name": "Production Fraud Model",
  "version": "1.0",
  "framework": "sklearn",
  "mlflow_model_name": "PipelineDoctorDemoModel",
  "mlflow_alias": "champion",
  "mlflow_tracking_uri": "http://127.0.0.1:5000",
  "expected_features": ["age", "salary", "bonus"]
}
```

| Field | Required | Description |
|---|---|---|
| `name` | ✅ | Friendly display name |
| `version` | ✅ | Your version label |
| `mlflow_model_name` | ✅ | Exact name in MLflow registry |
| `mlflow_alias` | Optional | Alias (default: `champion`) |
| `mlflow_tracking_uri` | Optional | Custom MLflow server (default: `localhost:5000`) |
| `expected_features` | Optional | Column names the model needs (in correct order) |

---

## 🧠 Feature Filtering & Enforcement

**File:** `app/services/quality/pipeline.py`

Before passing data to the model, the pipeline applies a strict filtering process:

### 1. Case-Insensitive Matching
The system maps database feature names to actual CSV column names case-insensitively.
```
DB config:  ["Age", "Salary", "Bonus"]
CSV headers: ["age", "salary", "bonus"]
Result:     ✅ Matched correctly
```

### 2. Column Selection & Reordering
Only the `expected_features` columns are extracted from the CSV, in the exact order specified. This prevents shape mismatch errors.

### 3. Type Casting
All selected columns are cast to `float64` before being sent to MLflow. This is required because MLflow validates dtypes strictly against the model signature.

```python
X_for_prediction = df[safe_features].fillna(0.0).astype(numpy.float64)
```

### 4. Fallback Mode
If `expected_features` is not set in the database, the system falls back to using the first 3 numeric columns. This ensures backward compatibility.

---

## ⚡ In-Memory Caching

**File:** `app/services/quality/pipeline.py → _model_cache`

Loading an MLflow model requires a network call and artifact download. To avoid doing this on every pipeline run, models are cached in memory.

```python
_model_cache = {}
cache_key = f"{model_name}@{alias}"
# e.g., "PipelineDoctorDemoModel@champion"
```

- **First run:** Downloads from MLflow, stores in `_model_cache`.
- **Subsequent runs:** Returns instantly from memory.
- **Cache invalidation:** Restart the FastAPI server to clear the cache and force a re-download.

---

## 🌐 Multi-Tenant MLflow Support

Each registered model can point to a **different MLflow tracking server**. This supports users who host their own private MLflow instances.

| Model | Tracking URI |
|---|---|
| Company A's model | `http://mlflow.companya.com:5000` |
| Company B's model | `http://mlflow.companyb.com:5000` |
| Local demo model | `http://127.0.0.1:5000` |

The pipeline calls `mlflow.set_tracking_uri()` right before loading each model to switch the active context.

---

## 📦 Training & Registering a Model

**File:** `app/ml/train_register_model.py`

```python
import mlflow
import mlflow.sklearn
mlflow.set_tracking_uri("http://127.0.0.1:5000")
mlflow.set_experiment("PipelineDoctor Demo")

with mlflow.start_run():
    model.fit(X_train, y_train)
    mlflow.sklearn.log_model(
        sk_model=model,
        name="model",
        registered_model_name="PipelineDoctorDemoModel"
    )
```

After training, assign the `champion` alias in the MLflow UI, or via code:
```python
from mlflow import MlflowClient
client = MlflowClient()
client.set_registered_model_alias("PipelineDoctorDemoModel", "champion", "1")
```
