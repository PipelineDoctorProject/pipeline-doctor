from celery.utils.log import get_task_logger

from app.core.celery_app import celery
from app.utils.email_utils import (
    send_otp_email,
    send_invite_email
)

logger = get_task_logger(__name__)


@celery.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
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
