Pipeline Flow

1. Start pipeline run
2. Generate data:
   - normal
   - drift
   - bad
3. Predict using MLflow model
4. Store prediction logs
5. Run:
   - Data quality check (NaN)
   - Drift check (mean shift)
6. Create incidents:
   - data_quality
   - drift
7. Update run status:
   - completed
   - completed_with_issues
   - failed