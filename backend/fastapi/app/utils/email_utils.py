import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config.settings import (
    MAIL_FROM,
    MAIL_PASSWORD,
    MAIL_PORT,
    MAIL_SERVER,
    MAIL_USERNAME,
)


def _build_server():
    missing = [
        name
        for name, value in {
            "MAIL_USERNAME": MAIL_USERNAME,
            "MAIL_PASSWORD": MAIL_PASSWORD,
            "MAIL_FROM": MAIL_FROM,
            "MAIL_SERVER": MAIL_SERVER,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Email service is not configured. Missing: {', '.join(missing)}")

    server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
    server.starttls()
    server.login(MAIL_USERNAME, MAIL_PASSWORD)
    return server


def _send_html_email(email: str, subject: str, body: str):
    msg = MIMEMultipart()
    msg["From"] = MAIL_FROM
    msg["To"] = email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    server = _build_server()
    server.sendmail(MAIL_FROM, email, msg.as_string())
    server.quit()


def send_otp_email(email: str, otp: str):

    subject = "PipelineDoctor OTP Verification"

    body = f"""
    <h2>PipelineDoctor Verification</h2>

    <p>Your OTP is:</p>

    <h1>{otp}</h1>

    <p>This code expires in 10 minutes.</p>
    """

    try:
        _send_html_email(email, subject, body)
        print("OTP email sent")
    except Exception as e:
        print("Email error:", e)


# ==========================================
# SEND INVITE EMAIL
# ==========================================
def send_invite_email(
    email: str,
    invite_link: str
):

    subject = "PipelineDoctor Workspace Invitation"

    body = f"""
    <h2>You are invited to PipelineDoctor</h2>

    <p>
        You have been invited to join a workspace.
    </p>

    <p>
        Click below to accept invitation:
    </p>

    <a href="{invite_link}">
        Accept Invitation
    </a>

    <br><br>

    <p>
        If you did not expect this email,
        you can ignore it.
    </p>
    """

    try:
        _send_html_email(email, subject, body)
        print("Invite email sent")
    except Exception as e:
        print("Email error:", e)


def send_incident_alert_email(
    *,
    email: str,
    incident_title: str,
    severity: str,
    run_id: int,
    failure_type: str,
    status: str,
    description: str,
    delivery_reason: str,
):
    subject = f"PipelineDoctor Alert: {severity.upper()} incident detected"

    body = f"""
    <h2>PipelineDoctor Incident Alert</h2>

    <p>{delivery_reason}</p>

    <p><strong>Title:</strong> {incident_title}</p>
    <p><strong>Severity:</strong> {severity}</p>
    <p><strong>Failure Type:</strong> {failure_type}</p>
    <p><strong>Run ID:</strong> {run_id}</p>
    <p><strong>Status:</strong> {status}</p>

    <h3>Summary</h3>
    <p>{description}</p>

    <p>Please review the incident in PipelineDoctor as soon as possible.</p>
    """

    try:
        _send_html_email(email, subject, body)
        print(f"Incident alert email sent to {email}")
    except Exception as e:
        print("Email error:", e)
