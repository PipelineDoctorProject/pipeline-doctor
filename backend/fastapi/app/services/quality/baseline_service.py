from sqlalchemy.orm import Session
from app.models.baseline import Baseline


def get_active_baseline(db: Session, model_id: int):
    baseline = (
        db.query(Baseline)
        .filter(
            Baseline.model_id == model_id,
            Baseline.is_active == True,
            Baseline.status == "approved"
        )
        .first()
    )

    if not baseline:
        raise Exception("No active baseline found")

    return baseline


def create_baseline_version(db: Session, model_id: int, schema: dict, profile: dict):
    latest = (
        db.query(Baseline)
        .filter(Baseline.model_id == model_id)
        .order_by(Baseline.version.desc())
        .first()
    )

    version = 1 if not latest else latest.version + 1

    baseline = Baseline(
        model_id=model_id,
        version=version,
        schema=schema,
        profile=profile,
        status="draft",
        is_active=False
    )

    db.add(baseline)
    db.commit()
    db.refresh(baseline)

    return baseline


def activate_baseline(db: Session, baseline_id: int):
    baseline = db.query(Baseline).get(baseline_id)

    if baseline.status != "approved":
        raise Exception("Baseline must be approved first")

    # deactivate others
    db.query(Baseline).filter(
        Baseline.model_id == baseline.model_id
    ).update({"is_active": False})

    baseline.is_active = True
    db.commit()