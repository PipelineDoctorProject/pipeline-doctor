# ML Layer Integration

## MLflow Connectivity
The system supports multi-tenant MLflow environments. Each model can point to its own tracking server.
- **Tracking URI**: Dynamically set per model from the database.
- **Model Loading**: Uses the `models:/NAME@ALIAS` format for production robustness.
- **Caching**: Models are cached in-memory to optimize performance.

## Feature Engineering & Enforced Schema
To prevent pipeline crashes, the system enforces a strict feature contract:
- **Expected Features**: The database stores exactly which columns the model requires.
- **Dynamic Slicing**: The pipeline automatically extracts and reorders features from the CSV to match the model's training signature.
- **Case Insensitivity**: Supports matching "Age" in DB to "age" in CSV.
- **Dtype Enforcement**: Automatically casts inputs to `float64` to satisfy MLflow's signature requirements.