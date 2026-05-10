from sqlalchemy.orm import Session
from app.models.drift_finding import DriftFinding
from app.models.incident import Incident

def save_drift_finding_and_incident(
    db: Session, 
    run_id: int, 
    feature_name: str, 
    psi_score: float, 
    ks_score: float, 
    ks_pvalue: float, 
    drift_score: float, 
    severity: str,
    finding_type_name: str = "data_drift"
):
    drift_detected = drift_score > 0.2
    
    finding = DriftFinding(
        run_id=run_id,
        feature_name=feature_name,
        psi_score=psi_score,
        ks_score=ks_score,
        ks_pvalue=ks_pvalue,
        drift_score=drift_score,
        drift_detected=drift_detected,
        severity=severity
    )
    db.add(finding)
    db.flush() # To get finding.id

    if severity in ["high", "critical"]:
        if finding_type_name == "concept_drift":
            title = "Concept Drift Detected: Prediction Output"
            desc = f"Model output distribution shifted significantly. Severity '{severity}'. PSI: {psi_score:.3f}, KS: {ks_score:.3f}"
        else:
            title = f"Data Drift Detected: {feature_name}"
            desc = f"Drift detected on feature '{feature_name}' with severity '{severity}'. PSI: {psi_score:.3f}, KS: {ks_score:.3f}"

        incident = Incident(
            run_id=run_id,
            title=title,
            description=desc,
            failure_type=finding_type_name,
            finding_type="drift",
            finding_id=finding.id,
            severity=severity
        )
        db.add(incident)
