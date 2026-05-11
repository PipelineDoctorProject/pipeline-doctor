# Setup & Running

1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Environment**: Configure `.env` with Supabase and MLflow credentials.
3. **Database**: Run migrations using `alembic upgrade head`.
4. **MLflow**: Ensure your tracking server is running (default: `http://127.0.0.1:5000`).
5. **Register Model**: Use the `/ml-models/` endpoint to register your model.
6. **Upload Baseline**: Use the `/baseline/upload/` endpoint to initialize the data profile.
7. **Run Auto-Runner**: Start the ingestion loop:
   ```bash
   python run_auto_runner.py
   ```