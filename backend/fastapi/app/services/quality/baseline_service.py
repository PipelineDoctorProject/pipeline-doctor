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


def create_baseline_version(
    db: Session,
    model_id: int,
    schema: dict,
    profile: dict,
    approved: bool = False
):

    # latest version
    latest = (
        db.query(Baseline)
        .filter(Baseline.model_id == model_id)
        .order_by(Baseline.version.desc())
        .first()
    )

    version = 1 if not latest else latest.version + 1

    # active approved baseline
    active_baseline = (
        db.query(Baseline)
        .filter(
            Baseline.model_id == model_id,
            Baseline.is_active == True,
            Baseline.status == "approved"
        )
        .first()
    )

    # FIRST BASELINE
    if not active_baseline:
        status = "approved"
        is_active = True

    # APPROVAL FLOW
    elif approved:
        status = "approved"
        is_active = False

    # NORMAL NEW UPLOAD
    else:
        status = "draft"
        is_active = False

    baseline = Baseline(
        model_id=model_id,
        version=version,
        schema=schema,
        profile=profile,
        status=status,
        is_active=is_active
    )

    db.add(baseline)
    db.commit()
    db.refresh(baseline)

    # ensure only one active
    if is_active:
        db.query(Baseline).filter(
            Baseline.model_id == model_id,
            Baseline.id != baseline.id
        ).update({"is_active": False})

        db.commit()

    return baseline


def activate_baseline(db: Session, baseline_id: int):
    baseline = db.get(Baseline, baseline_id)

    if not baseline:
        raise Exception("Baseline not found")

    if baseline.status != "approved":
        raise Exception("Baseline must be approved first")

    # deactivate others
    db.query(Baseline).filter(
        Baseline.model_id == baseline.model_id,
        Baseline.is_active == True
    ).update({"is_active": False})

    baseline.is_active = True

    db.commit()
    db.refresh(baseline)

    return baseline