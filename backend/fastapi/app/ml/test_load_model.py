import mlflow.pyfunc
import numpy as np
import os

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000"))

model = mlflow.pyfunc.load_model("models:/PipelineDoctorDemoModel/1")

X = np.random.normal(0.5, 0.1, (5, 3))
preds = model.predict(X)

print(preds)
