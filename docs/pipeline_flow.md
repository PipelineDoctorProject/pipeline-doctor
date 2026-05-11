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