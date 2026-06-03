# ML Integration

OpsSight integrates with MLflow for model loading, candidate logging, model versioning, and alias-based promotion. The platform is model-aware but deployment-safe: it can stage a candidate, but production deployment should be confirmed only after the serving system has actually deployed and passed checks.

---

## Model Registry Fields

Models are registered inside OpsSight through the `ml_models` table and UI.

Important fields:

| Field | Purpose |
|---|---|
| `name` | Human-readable model name in OpsSight |
| `version` | Current OpsSight version label, normally aligned with the deployed champion version |
| `framework` | Framework type such as `sklearn` |
| `mlflow_model_name` | Registered model name in MLflow |
| `mlflow_alias` | Alias used for live loading, usually `champion` |
| `mlflow_tracking_uri` | MLflow server for this model |
| `mlflow_run_id` | Run id for the current deployed champion version |
| `expected_features` | Ordered list of features the model expects |
| `training_mode` | Supervised or unsupervised behavior |

Each tenant can register different models, and each model can point to a different MLflow tracking server.

---

## Runtime Model Loading

During prediction, OpsSight loads the configured model from MLflow.

```text
Pipeline run starts
    |
Resolve tenant and model
    |
Read model record from tenant schema
    |
Build MLflow model URI
    |
models:/<mlflow_model_name>@<mlflow_alias>
    |
Load with mlflow.pyfunc.load_model
    |
Cache model in memory
    |
Run prediction on accepted feature frame
```

Default live alias:

```text
champion
```

Example live model URI:

```text
models:/spotify-kmeans-recommender@champion
```

---

## Feature Selection

OpsSight never sends all CSV columns blindly into a model. It resolves a feature list using this priority:

1. `ml_models.expected_features`
2. active baseline fields when model features are missing
3. safe numeric fallback only for legacy/demo compatibility

Feature matching is case-insensitive, but the final model input frame is ordered according to the resolved expected feature list.

---

## Why Numeric Features Are Preferred

Most scikit-learn estimators operate on numeric arrays. String columns such as names, categories, and free text cannot be used directly by most models unless they are transformed.

Examples:

| Raw string column | Production transformation |
|---|---|
| `country` | one-hot encoding, ordinal encoding, target encoding |
| `mood` | approved categorical encoder |
| `artist` | hashing encoder, embedding, or excluded high-cardinality feature |
| `review_text` | text embedding or TF-IDF |

OpsSight should not guess this transformation automatically for production models. If a new string column becomes important, it should go through schema evolution approval and then be added to a controlled preprocessing pipeline.

---

## Supervised vs Unsupervised Models

### Supervised

Supervised models need:

- feature columns
- target column
- enough clean rows
- valid labels

Examples:

- classifier
- regressor

During retraining, OpsSight validates that the target column exists and is suitable.

### Unsupervised

Unsupervised models need:

- feature columns only
- no target column

Examples:

- KMeans clustering
- segmentation

During remediation, OpsSight can refit the estimator using accepted features. Review focuses on cluster quality, feature correctness, and business meaning.

---

## Candidate Model Logging

When remediation retraining succeeds, OpsSight logs a candidate model to MLflow.

Candidate URI format:

```text
runs:/<candidate_run_id>/candidate_model
```

Example:

```text
runs:/bb00b5d16c147088e9d7f8082568398/candidate_model
```

The candidate run stores:

- candidate artifact
- metrics
- feature columns
- source model id
- source model name
- source model version
- pipeline run id
- remediation candidate tag

At this point, the candidate is not live.

---

## MLflow Aliases

OpsSight uses aliases to describe lifecycle state.

| Alias | Meaning |
|---|---|
| `staging` | Candidate has been reviewed and is ready for deployment validation |
| `champion` | Current production/live model used by OpsSight monitoring |

Recommended production rule:

- `Stage candidate` updates only `staging`.
- `Confirm deployment` updates `champion`.

---

## Local Development Flow

For local development, you can create a demo MLflow source model with a bootstrap script. The exact command depends on the container path, but the goal is:

1. train or load the demo estimator
2. log it to local MLflow
3. register it as `spotify-kmeans-recommender`
4. assign `champion`
5. register the matching model record in OpsSight

After that, Airflow or UI uploads can run monitoring against the local champion model.

---

## Production Flow

In production, the customer's real training pipeline usually creates the source model. OpsSight does not need to train the first production model.

Recommended production setup:

1. Customer training pipeline logs model to MLflow.
2. Customer assigns `champion` to the deployed version.
3. Admin registers the model in OpsSight.
4. OpsSight monitors batches against the champion model.
5. Incidents can create remediation candidates.
6. Admin stages a candidate after review.
7. Customer deployment pipeline deploys `staging`.
8. Admin confirms deployment.
9. OpsSight updates `champion` tracking and monitors the new version.

---

## Cache Behavior

Loaded models are cached in the API process to avoid repeated downloads.

Cache key shape:

```text
<mlflow_model_name>@<alias>
```

Cache should be cleared when:

- a model alias changes
- candidate is staged
- deployment is confirmed
- model metadata is edited
- API is restarted

---

## Related Code

- `backend/fastapi/app/services/quality/pipeline.py`
- `backend/fastapi/app/services/remediation/retraining_service.py`
- `backend/fastapi/app/services/remediation/promotion_service.py`
- `backend/fastapi/app/api/routes/ml_models.py`
- `backend/fastapi/app/ml/bootstrap_spotify_kmeans_model.py`

---

## Related Docs

- [model_lifecycle.md](./model_lifecycle.md)
- [remediation.md](./remediation.md)
- [schema_evolution.md](./schema_evolution.md)
- [automation_and_scheduler.md](./automation_and_scheduler.md)
