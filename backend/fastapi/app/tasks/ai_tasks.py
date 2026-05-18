from celery.utils.log import get_task_logger
from datetime import datetime

from app.core.celery_app import celery
from app.models.agent_run import AgentRun
from app.models.agent_step_log import AgentStepLog
from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.utils.schema_utils import set_schema
from app.services.ai.context_builder import build_pipeline_context
from app.services.ai_orchestration.supervisor import run_root_cause_analysis
from app.models.pipeline_run import PipelineRun

logger = get_task_logger(__name__)


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
        # SAVE STEP 1 LOG
        # ==========================================
        step_1 = AgentStepLog(
            agent_run_id=agent_run.id,
            step_index=1,
            log_type="context_build",
            message="Collected monitoring findings for AI analysis",
            payload=context
        )

        db.add(step_1)
        db.commit()

        logger.info(f"Logged step 1 for AgentRun {agent_run.id}")

        # ==========================================
        # FETCH PIPELINE RUN
        # ==========================================
        pipeline_run = (
            db.query(PipelineRun)
            .filter(PipelineRun.id == pipeline_run_id)
            .first()
        )

        # ==========================================
        # RUN REAL AI RCA ANALYSIS
        # ==========================================
        analysis_state = run_root_cause_analysis(
            db=db,
            run=pipeline_run
        )

        logger.info(f"AI RCA Analysis Complete: {analysis_state}")

        # ==========================================
        # SAVE STEP 2 LOG
        # ==========================================
        step_2 = AgentStepLog(
            agent_run_id=agent_run.id,
            step_index=2,
            log_type="rca_result",
            message="AI Root Cause Analysis completed",
            payload=analysis_state.get("report", {})
        )

        db.add(step_2)
        db.commit()

        logger.info(f"Logged RCA result for AgentRun {agent_run.id}")

        # ==========================================
        # COMPLETE AGENT RUN
        # ==========================================
        agent_run.status = "completed"
        agent_run.finished_at = datetime.utcnow()
        agent_run.result_summary = "Doctor analysis complete"

        db.commit()

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

        raise

    finally:
        db.close()