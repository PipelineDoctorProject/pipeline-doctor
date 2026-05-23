import json
from celery.utils.log import get_task_logger
from datetime import datetime

import redis

from app.config.settings import REDIS_URL
from app.core.celery_app import celery
from app.models.agent_run import AgentRun
from app.models.agent_step_log import AgentStepLog
from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.utils.schema_utils import set_schema
from app.services.ai.context_builder import build_pipeline_context
from app.services.ai_orchestration.supervisor import run_root_cause_analysis
from app.services.incidents.report_builder import build_final_incident_report
from app.services.incidents import persist_root_cause_incident
from app.models.pipeline_run import PipelineRun
from app.services.remediation import decide_remediation

logger = get_task_logger(__name__)

STEP_NAMES = {
    0: "detection",
    1: "reasoning",
    2: "parser",
    3: "reporting",
}


def _publish_step(run_id: int, step_index: int, status: str, message: str, payload: dict = None):
    """Synchronously publish a step event to the Redis pub/sub channel."""
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        event = {
            "event":      "step_update",
            "run_id":     str(run_id),
            "step_index": step_index,
            "step_name":  STEP_NAMES.get(step_index, f"step_{step_index}"),
            "status":     status,
            "message":    message,
            "payload":    payload or {},
        }
        r.publish(f"agent_trace:{run_id}", json.dumps(event))
        r.close()
    except Exception as pub_err:
        logger.warning(f"Redis publish failed (non-critical): {pub_err}")


def _publish_terminal(run_id: int, event_type: str, message: str):
    """Publish a run_complete or run_failed terminal event."""
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        r.publish(f"agent_trace:{run_id}", json.dumps({
            "event":   event_type,
            "run_id":  str(run_id),
            "message": message,
        }))
        r.close()
    except Exception as pub_err:
        logger.warning(f"Redis terminal publish failed (non-critical): {pub_err}")


@celery.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 2},
)
def run_doctor_agent_task(
    self,
    pipeline_run_id: int,
    tenant_id: str,
    agent_type: str = "doctor"
):
    """
    Run the Doctor AI agent for incident analysis and RCA generation.
    """

    db = SessionLocal()
    agent_run = None

    try:
        logger.info(
            f"Starting {agent_type} agent "
            f"for pipeline_run_id={pipeline_run_id}, "
            f"tenant_id={tenant_id}"
        )

        # ==========================================
        # SET TENANT SCHEMA
        # ==========================================
        if tenant_id:
            tenant = (
                db.query(Tenant)
                .filter(Tenant.id == tenant_id)
                .first()
            )

            if tenant and tenant.schema_name:
                set_schema(db, tenant.schema_name)

        pipeline_run = (
            db.query(PipelineRun)
            .filter(PipelineRun.id == pipeline_run_id)
            .first()
        )

        if not pipeline_run:
            logger.warning(
                "Skipping doctor agent because pipeline run %s was not found in tenant %s",
                pipeline_run_id,
                tenant_id,
            )
            _publish_terminal(
                pipeline_run_id,
                "run_failed",
                f"Pipeline run {pipeline_run_id} was not found for tenant {tenant_id}",
            )
            return

        existing_run = (
            db.query(AgentRun)
            .filter(
                AgentRun.pipeline_run_id == pipeline_run_id,
                AgentRun.agent_name == agent_type,
            )
            .order_by(AgentRun.id.desc())
            .first()
        )

        if existing_run and existing_run.status in {"running", "completed"}:
            logger.info(
                "Skipping duplicate %s agent task for pipeline_run_id=%s because AgentRun %s is already %s",
                agent_type,
                pipeline_run_id,
                existing_run.id,
                existing_run.status,
            )
            return

        # ==========================================
        # CREATE AGENT RUN
        # ==========================================
        agent_run = AgentRun(
            agent_name=agent_type,
            tenant_id=tenant_id,
            pipeline_run_id=pipeline_run_id,
            status="running",
            started_at=datetime.utcnow()
        )

        db.add(agent_run)
        db.commit()
        db.refresh(agent_run)

        logger.info(f"Created AgentRun record: id={agent_run.id}")

        # ==========================================
        # BUILD AI CONTEXT
        # ==========================================
        context = build_pipeline_context(
            db=db,
            pipeline_run_id=pipeline_run_id
        )

        logger.info(f"Built AI context: {context}")

        # ==========================================
        # STEP 0 — DETECTION (context built)
        # ==========================================
        _publish_step(
            pipeline_run_id, 0, "running",
            "Fetching drift and data quality findings"
        )

        step_1 = AgentStepLog(
            agent_run_id=agent_run.id,
            step_index=0,
            log_type="context_build",
            message="Collected monitoring findings for AI analysis",
            payload=context
        )
        db.add(step_1)
        db.commit()

        _publish_step(
            pipeline_run_id, 0, "done",
            "Detection complete — findings loaded"
        )

        # ==========================================
        # STEP 1 — REASONING (LLM about to run)
        # ==========================================
        _publish_step(
            pipeline_run_id, 1, "running",
            "LLM is analysing root cause"
        )

        logger.info(f"Logged step 0 (detection) for AgentRun {agent_run.id}")

        # ==========================================
        # RUN REAL AI RCA ANALYSIS
        # ==========================================
        analysis_state = run_root_cause_analysis(
            db=db,
            run=pipeline_run
        )

        logger.info(f"AI RCA Analysis Complete: {analysis_state}")

        # STEP 1 done — STEP 2 parser
        _publish_step(
            pipeline_run_id, 1, "done",
            "AI reasoning complete"
        )
        _publish_step(
            pipeline_run_id, 2, "running",
            "Structuring RCA output"
        )

        step_2 = AgentStepLog(
            agent_run_id=agent_run.id,
            step_index=1,
            log_type="rca_result",
            message="AI Root Cause Analysis completed",
            payload=analysis_state.get("report", {})
        )
        db.add(step_2)
        db.commit()

        _publish_step(
            pipeline_run_id, 2, "done",
            "Parsing complete"
        )

        step_3 = AgentStepLog(
            agent_run_id=agent_run.id,
            step_index=2,
            log_type="parser",
            message="Structured AI reasoning into an RCA report",
            payload=analysis_state.get("report", {})
        )
        db.add(step_3)
        db.commit()

        _publish_step(
            pipeline_run_id, 3, "running",
            "Writing incident report to database"
        )

        logger.info(f"Logged RCA result for AgentRun {agent_run.id}")

        remediation_policy = decide_remediation(
            analysis_state.get("report", {}),
            analysis_state,
        )
        final_report = build_final_incident_report(
            analysis_state,
            remediation_policy,
        )

        step_4 = AgentStepLog(
            agent_run_id=agent_run.id,
            step_index=3,
            log_type="reporting",
            message="Completed RCA reporting for this run",
            payload={
                "run_id": pipeline_run_id,
                "status": "completed",
                "report_status": final_report.get("report_status"),
                "action_type": remediation_policy.get("action_type"),
                "requires_approval": remediation_policy.get("requires_approval"),
            }
        )
        db.add(step_4)
        db.commit()

        persist_root_cause_incident(db, pipeline_run_id, analysis_state)

        # ==========================================
        # COMPLETE AGENT RUN
        # ==========================================
        agent_run.status = "completed"
        agent_run.finished_at = datetime.utcnow()
        agent_run.result_summary = "Doctor analysis complete"
        db.commit()

        _publish_step(
            pipeline_run_id, 3, "done",
            "Reporting complete — incident saved"
        )
        _publish_terminal(
            pipeline_run_id, "run_complete",
            "Agent run finished successfully"
        )

        logger.info(f"Completed AgentRun {agent_run.id}")

    except Exception as exc:
        logger.error(
            f"Error in run_doctor_agent_task: {exc}",
            exc_info=True
        )

        if agent_run:
            agent_run.status = "failed"
            agent_run.finished_at = datetime.utcnow()
            agent_run.result_summary = f"Failed with error: {str(exc)}"

            try:
                db.commit()
            except Exception:
                db.rollback()

        _publish_terminal(
            pipeline_run_id, "run_failed",
            f"Agent run failed: {str(exc)}"
        )

        raise

    finally:
        db.close()
