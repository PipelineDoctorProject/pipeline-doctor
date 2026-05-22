import os
import random
from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.utils.schema_utils import set_schema
from app.models.tenant import Tenant
from app.models.ml_model import MLModel
from app.models.pipeline_run import PipelineRun
from app.models.data_quality import DataQualityFinding
from app.models.drift_finding import DriftFinding
from app.models.incident import Incident

def seed_data(email: str):
    db = SessionLocal()
    try:
        # 1. Find User/Tenant
        from app.models.user import User
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.tenant_id:
            print(f"User {email} not found or has no workspace.")
            return

        tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
        if not tenant:
            print("Tenant not found.")
            return

        schema_name = tenant.schema_name
        print(f"Using workspace schema: {schema_name}")
        set_schema(db, schema_name)

        # 2. Check if a model exists, if not create a dummy one
        model = db.query(MLModel).first()
        if not model:
            model = MLModel(
                name="Fraud_Detection_XGBoost",
                version="1.2.0",
                framework="xgboost",
                mlflow_model_name="fraud-detect",
                mlflow_alias="production",
                mlflow_run_id="dummy-run-id-123",
                mlflow_tracking_uri=os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
            )
            db.add(model)
            db.commit()
            db.refresh(model)
            print(f"Created Mock Model: {model.name}")

        # 3. Create a Pipeline Run
        run = PipelineRun(
            model_id=model.id,
            baseline_version=1,
            status="success",
            schema_changed=False,
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        print(f"Created Pipeline Run #{run.id}")

        # 4. Create Data Quality Findings
        dq1 = DataQualityFinding(
            model_id=model.id,
            pipeline_run_id=run.id,
            column_name="transaction_amount",
            check_type="not_null",
            success=True,
            created_at=datetime.utcnow() - timedelta(hours=1, minutes=50)
        )
        dq2 = DataQualityFinding(
            model_id=model.id,
            pipeline_run_id=run.id,
            column_name="user_age",
            check_type="type_match",
            success=False,
            details={"expected": "integer", "found": "string"},
            created_at=datetime.utcnow() - timedelta(hours=1, minutes=50)
        )
        db.add_all([dq1, dq2])

        # 5. Create Drift Finding
        drift = DriftFinding(
            run_id=run.id,
            feature_name="transaction_amount",
            drift_score=0.85,  # High drift
            drift_detected=True,
            psi_score=0.25,
            ks_score=0.45,
            ks_pvalue=0.01,
            severity="high",
            created_at=datetime.utcnow() - timedelta(hours=1, minutes=45)
        )
        db.add(drift)

        # 6. Create Incident
        incident = Incident(
            run_id=run.id,
            title="High Drift on Transaction Amount",
            description="The distribution of transaction_amount has shifted significantly compared to the baseline (PSI: 0.25).",
            failure_type="Data Drift",
            severity="high",
            status="open",
        )
        db.add(incident)

        db.commit()
        print("\n✅ Successfully seeded dummy data! Go check your UI now.")

    except Exception as e:
        print("Error:", e)
    finally:
        db.close()

if __name__ == "__main__":
    email = input("Enter your login email address: ")
    seed_data(email)
