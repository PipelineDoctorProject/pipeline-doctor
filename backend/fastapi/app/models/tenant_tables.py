from app.models.pipeline_run import PipelineRun
from app.models.prediction_log import PredictionLog
from app.models.incident import Incident
from app.models.drift_finding import DriftFinding
from app.models.data_quality import DataQualityFinding
from app.models.ml_model import MLModel
from app.models.baseline import Baseline
from app.models.schema_change_event import SchemaChangeEvent
from app.models.agent_run import AgentRun
from app.models.agent_step_log import AgentStepLog
from app.models.remediation_run import RemediationRun
from app.models.remediation_action_log import RemediationActionLog

TENANT_MODELS = [
    MLModel,
    PipelineRun,
    PredictionLog,
    Incident,
    DriftFinding,
    DataQualityFinding,
    Baseline,
    SchemaChangeEvent,
    AgentRun,
    AgentStepLog,
    RemediationRun,
    RemediationActionLog,
]
