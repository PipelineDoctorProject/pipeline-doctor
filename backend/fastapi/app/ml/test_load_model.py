import mlflow.pyfunc
import numpy as np

mlflow.set_tracking_uri("http://127.0.0.1:5000")

model = mlflow.pyfunc.load_model("models:/PipelineDoctorDemoModel/1")

X = np.random.normal(0.5, 0.1, (5, 3))
preds = model.predict(X)

print(preds)