from celery.utils.log import get_task_logger

from app.core.celery_app import celery
from app.utils.email_utils import (
    send_otp_email,
    send_invite_email,
    send_incident_alert_email,
)

logger = get_task_logger(__name__)


@celery.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    ignore_result=True,  # fire-and-forget: no result backend subscription needed
)
def send_otp_email_task(
    self,
    email: str,
    otp: str
):

    logger.info(f"Sending OTP email to {email}")

    send_otp_email(email, otp)

    logger.info(f"OTP email sent to {email}")


@celery.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    ignore_result=True,
)
def send_invite_email_task(
    self,
    email: str,
    invite_link: str
):

    logger.info(f"Sending invite email to {email}")

    send_invite_email(email, invite_link)

    logger.info(f"Invite email sent to {email}")
    logger.info(f"Invite email sent to {email}")


@celery.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    ignore_result=True,
)
def send_incident_alert_email_task(
    self,
    email: str,
    incident_title: str,
    severity: str,
    run_id: int,
    failure_type: str,
    status: str,
    description: str,
    delivery_reason: str,
):
    logger.info(f"Sending incident alert email to {email}")

    send_incident_alert_email(
        email=email,
        incident_title=incident_title,
        severity=severity,
        run_id=run_id,
        failure_type=failure_type,
        status=status,
        description=description,
        delivery_reason=delivery_reason,
    )

    logger.info(f"Incident alert email sent to {email}")
