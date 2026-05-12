from app.db.session import engine
from app.models.base import Base
from app.models.user import User
from app.models.tenant import Tenant
from app.models.ml_model import MLModel
from app.models.pipeline_run import PipelineRun
from app.models.prediction_log import PredictionLog
from app.models.incident import Incident
from app.models.drift_finding import DriftFinding
from app.models.data_quality import DataQualityFinding
from app.models.baseline import Baseline

def init_public_db():
    print("Initializing public schema tables...")
    Base.metadata.create_all(bind=engine)
    print("Done!")

if __name__ == "__main__":
    init_public_db()
