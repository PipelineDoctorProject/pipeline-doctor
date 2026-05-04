import mlflow
import mlflow.sklearn

from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


mlflow.set_tracking_uri("http://127.0.0.1:5000")
mlflow.set_experiment("PipelineDoctor Demo Model")


def train_and_register_model():
    X, y = make_classification(
        n_samples=1000,
        n_features=3,
        n_informative=2,
        n_redundant=0,
        random_state=42,
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)

    with mlflow.start_run():
        model.fit(X_train, y_train) 

        preds = model.predict(X_test) 
        accuracy = accuracy_score(y_test, preds) 

        mlflow.log_param("model_type", "RandomForestClassifier")
        mlflow.log_param("n_estimators", 100)
        mlflow.log_metric("accuracy", accuracy)

        mlflow.sklearn.log_model(
            sk_model=model,
            name="model",
            registered_model_name="PipelineDoctorDemoModel",
            input_example=X_test[:2],
        )

        print("Model registered successfully")
        print("Accuracy:", accuracy)


if __name__ == "__main__":
    train_and_register_model()