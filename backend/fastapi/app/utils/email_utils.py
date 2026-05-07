import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config.settings import (
    MAIL_USERNAME,
    MAIL_PASSWORD,
    MAIL_FROM,
)


def send_otp_email(email: str, otp: str):

    subject = "PipelineDoctor OTP Verification"

    body = f"""
    <h2>PipelineDoctor Verification</h2>

    <p>Your OTP is:</p>

    <h1>{otp}</h1>

    <p>This code expires in 10 minutes.</p>
    """

    msg = MIMEMultipart()

    msg["From"] = MAIL_FROM
    msg["To"] = email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)

        server.starttls()

        server.login(MAIL_USERNAME, MAIL_PASSWORD)

        server.sendmail(
            MAIL_FROM,
            email,
            msg.as_string()
        )

        server.quit()

        print("✅ OTP email sent")

    except Exception as e:
        print("❌ Email error:", e)