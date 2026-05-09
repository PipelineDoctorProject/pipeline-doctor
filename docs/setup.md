Setup Instructions

1. Start MLflow server:
   mlflow server --host 127.0.0.1 --port 5000

2. Train model:
   python app/ml/train_register_model.py

3. Run FastAPI:
   uvicorn app.main:app --reload

4. Open API docs:
   http://127.0.0.1:8000/docs