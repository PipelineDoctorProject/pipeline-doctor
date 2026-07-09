from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.dependencies.auth import require_tenant_user
from app.db.session import get_db
from app.models.drift_finding import DriftFinding
from app.models.pipeline_run import PipelineRun

from app.schemas.drift import DriftResponse
from app.schemas.explanations import InsightExplanationResponse
from app.services.ai_explanations import build_drift_explanation
from app.services.access_control import require_accessible_model

router = APIRouter(prefix="/drift-findings", tags=["Drift Findings"])


@router.get("/")
def list_drift_findings(
    model_id: int | None = Query(default=None),
    run_id: int | None = Query(default=None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):
    if model_id is not None:
        require_accessible_model(db, model_id, current_user.tenant_id)

    runs_query = db.query(DriftFinding.run_id).distinct()
    if run_id is not None:
        runs_query = runs_query.filter(DriftFinding.run_id == run_id)
        
    if model_id is not None:
        runs_query = (
            runs_query
            .join(PipelineRun, DriftFinding.run_id == PipelineRun.id)
            .filter(PipelineRun.model_id == model_id)
        )
        
    total_count = runs_query.count()
    run_ids_result = runs_query.order_by(DriftFinding.run_id.desc()).offset(skip).limit(limit).all()
    run_ids = [r[0] for r in run_ids_result]
    
    findings = []
    if run_ids:
        findings = db.query(DriftFinding).filter(DriftFinding.run_id.in_(run_ids)).order_by(DriftFinding.id.desc()).all()
        
    items = [_serialize_drift_finding(finding) for finding in findings]
    
    # Recreate the base query for finding-level stats
    query = db.query(DriftFinding)
    if run_id is not None:
        query = query.filter(DriftFinding.run_id == run_id)
    if model_id is not None:
        query = (
            query
            .join(PipelineRun, DriftFinding.run_id == PipelineRun.id)
            .filter(PipelineRun.model_id == model_id)
        )

    # Compute global stats
    drift_detected_count = query.filter(DriftFinding.drift_detected == True).count()
    average_score = db.query(func.avg(DriftFinding.drift_score)).select_from(query.subquery()).scalar() or 0
    severity_counts_query = db.query(DriftFinding.severity, func.count(DriftFinding.id)).select_from(query.subquery()).group_by(DriftFinding.severity).all()
    severity_counts = {sev: count for sev, count in severity_counts_query if sev}
    
    stats = {
        "drift_detected": drift_detected_count,
        "average_score": float(average_score),
        "severity_counts": severity_counts
    }
    
    return {
        "items": items,
        "total_count": total_count,
        "stats": stats
    }


@router.post("/backfill/{run_id}")
def backfill_drift_findings(
    run_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user)
):
    from app.services.drift.drift_service import run_drift_checks

    run = db.get(PipelineRun, run_id)
    if not run:
        return {
            "run_id": run_id,
            "saved": 0,
            "reason": "Pipeline run not found",
        }

    existing_count = (
        db.query(DriftFinding)
        .filter(DriftFinding.run_id == run_id)
        .count()
    )
    if existing_count:
        return {
            "run_id": run_id,
            "saved": existing_count,
            "reason": "Drift findings already exist for this run",
        }

    result = run_drift_checks(db, run)
    return {
        "run_id": run_id,
        **(result or {"saved": 0, "reason": "Drift did not return a result"}),
    }


@router.get("/explain", response_model=InsightExplanationResponse)
def explain_drift_run(
    run_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    findings = (
        db.query(DriftFinding)
        .filter(DriftFinding.run_id == run_id)
        .order_by(DriftFinding.id.asc())
        .all()
    )

    if not findings:
        raise HTTPException(status_code=404, detail="No drift findings found for this run")

    return build_drift_explanation(run_id, findings)


def _serialize_drift_finding(finding: DriftFinding):
    return {
        "id": finding.id,
        "run_id": finding.run_id,
        "feature_name": finding.feature_name,
        "drift_score": finding.drift_score,
        "drift_detected": finding.drift_detected,
        "psi_score": finding.psi_score,
        "ks_score": finding.ks_score,
        "ks_pvalue": finding.ks_pvalue,
        "severity": finding.severity,
        "created_at": finding.created_at,
        "interpretation": _build_drift_interpretation(finding),
    }


def _build_drift_interpretation(finding: DriftFinding):
    feature = finding.feature_name or "Feature"

    if not finding.drift_detected:
        return {
            "title": f"{feature} is stable",
            "cause": "Current values are close to the active baseline distribution.",
            "action": "Keep monitoring future runs.",
        }

    psi = finding.psi_score or 0
    ks = finding.ks_score or 0
    pvalue = finding.ks_pvalue
    score = finding.drift_score or 0
    strength = "strong" if psi >= 0.3 else "moderate" if psi >= 0.2 else "minor"
    significance = (
        "The KS p-value supports a statistically significant distribution shift."
        if pvalue is not None and pvalue < 0.05
        else "The KS p-value is not significant, so treat this as monitoring evidence and confirm with source context."
    )

    return {
        "title": f"{feature} shows {strength} population drift",
        "cause": (
            f"{feature} no longer matches the baseline distribution. "
            f"PSI={psi:.4f}, KS={ks:.4f}, drift score={score:.4f}. {significance}"
        ),
        "action": (
            f"Check whether {feature}'s source, business mix, or time window changed. "
            "Fix upstream data if unexpected; refresh the baseline or retrain only if the shift is valid."
        ),
    }
