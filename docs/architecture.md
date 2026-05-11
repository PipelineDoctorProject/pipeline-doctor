# PipelineDoctor Architecture

## Core Components:
- **ML Layer (MLflow)**: Model registry and tracking. Supports dynamic model loading via URIs and specific tracking servers.
- **Backend (FastAPI + PostgreSQL)**: Core API and database for runs, baselines, and findings.
- **Data Quality Service**: Handles cleaning, schema validation, and threshold checks.
- **Drift Detection Service**: Modular service for Data Drift (Feature shifts) and Concept Drift (Prediction shifts).
- **Incident Escalation**: Automated creation of incidents based on critical quality or drift alerts.

# PipelineDoctor API Reference

## ML Models
- `POST /ml-models/`: Register a new model from MLflow with tracking URI and expected features.
- `GET /ml-models/`: List all registered models.

## Baselines
- `POST /baseline/upload`: Upload a CSV to establish a statistical baseline for a model.

## Data Quality & Schema
- `GET /schema-change-events`: View detected schema evolution events.
- `POST /schema/approve/{id}`: Approve a new schema version.

## Monitoring & Observability
- `GET /runs`: View history of pipeline runs.
- `GET /predictions`: View logged model inferences.
- `GET /drift-findings`: View statistical drift analysis (PSI, KS).
- `GET /incidents`: View escalated production issues.

# Pipeline Execution Flow

1. **Ingestion**: File detected in `uploads/incoming/`.
2. **Data Quality Layer**:
   - Cleaning and transformation.
   - **Schema Evolution Check**: Detects new/missing columns vs. Baseline.
   - **Baseline Validation**: Validates ranges, null ratios, and uniqueness.
3. **Storage**: Cleaned data saved to `cleaned/` folder.
4. **Dynamic Prediction Layer**:
   - Fetch model metadata (URI, Features) from database.
   - Connect to specific MLflow Tracking Server.
   - Filter input data to match `expected_features` (case-insensitive).
   - Generate and log model predictions.
5. **Drift Detection Layer**:
   - **Data Drift**: PSI & KS metrics for all numeric baseline features.
   - **Concept Drift**: Distribution shift analysis of model outputs.
6. **Escalation**:
   - Create `DriftFinding` records.
   - Trigger `Incident` creation if severity is critical.