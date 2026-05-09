PipelineDoctor Architecture

Components:
- ML Layer (MLflow)
- Backend (FastAPI + PostgreSQL)
- Pipeline Simulator

Flow:
1. Model trained and registered in MLflow
2. Pipeline loads model using alias (champion)
3. Data is generated (normal / drift / bad)
4. Predictions are made
5. Results stored in DB
6. Drift & data quality checks run
7. Incidents are created if issues found