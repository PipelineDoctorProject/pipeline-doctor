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

    if baseline:
        return baseline

    # fallback
    baseline = (
        db.query(Baseline)
        .filter(
            Baseline.model_id == model_id,
            Baseline.status == "approved"
        )
        .order_by(Baseline.version.desc())
        .first()
    )

    if baseline:
        return baseline

    raise Exception("No approved baseline found")


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
    baseline = db.get(Baseline, baseline_id)

    if not baseline:
        raise Exception("Baseline not found")

    if baseline.status != "approved":
        raise Exception("Baseline must be approved first")

    db.query(Baseline).filter(
        Baseline.model_id == baseline.model_id,
        Baseline.is_active == True
    ).update({"is_active": False})

    baseline.is_active = True
    db.commit()