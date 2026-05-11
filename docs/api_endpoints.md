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