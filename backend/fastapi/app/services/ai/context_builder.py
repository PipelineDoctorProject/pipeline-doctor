from app.models.pipeline_run import PipelineRun
from app.models.drift_finding import DriftFinding
from app.models.data_quality import DataQualityFinding
from app.models.schema_change_event import SchemaChangeEvent


def _serialize_schema_change(event: SchemaChangeEvent):
    entries = []

    for column in event.new_columns or []:
        entries.append({
            "column": column,
            "change_type": "new_column",
        })

    for column in event.missing_columns or []:
        entries.append({
            "column": column,
            "change_type": "missing_column",
        })

    return entries


def build_pipeline_context(db, pipeline_run_id: int):

    pipeline_run = (
        db.query(PipelineRun)
        .filter(PipelineRun.id == pipeline_run_id)
        .first()
    )

    drift_findings = (
        db.query(DriftFinding)
        .filter(DriftFinding.run_id == pipeline_run_id)
        .all()
    )

    quality_findings = (
        db.query(DataQualityFinding)
        .filter(DataQualityFinding.pipeline_run_id == pipeline_run_id)
        .all()
    )

    schema_changes = (
        db.query(SchemaChangeEvent)
        .filter(SchemaChangeEvent.pipeline_run_id == pipeline_run_id)
        .all()
    )

    return {

        "pipeline_run": {
            "id": pipeline_run.id,
            "status": pipeline_run.status,
        },

        "drift_findings": [
            {
                "feature": d.feature_name,
                "score": d.drift_score,
                "severity": d.severity,
            }
            for d in drift_findings
        ],

        "quality_findings": [
            {
                "column": q.column_name,
                "issue": q.check_type,
            }
            for q in quality_findings
        ],

        "schema_changes": [
            item
            for change in schema_changes
            for item in _serialize_schema_change(change)
        ]
    }
