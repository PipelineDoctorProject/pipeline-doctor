from app.models.pipeline_run import PipelineRun
from app.models.prediction_log import PredictionLog
from app.models.incident_group import IncidentGroup
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
from app.models.slack_channel import SlackChannel
from app.models.slack_workspace import SlackWorkspace


TENANT_MODELS = [
    MLModel,
    PipelineRun,
    PredictionLog,
    IncidentGroup,
    Incident,
    DriftFinding,
    DataQualityFinding,
    Baseline,
    SchemaChangeEvent,
    AgentRun,
    AgentStepLog,
    RemediationRun,
    RemediationActionLog,
    SlackChannel,
    SlackWorkspace
]
