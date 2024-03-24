from email.message import EmailMessage

import aiosmtplib


async def send_email(
    subject: str,
    recipient: str,
    body: str,
    smtp_server: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
):
    message = EmailMessage()
    message["From"] = smtp_username
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=smtp_server,
        port=smtp_port,
        username=smtp_username,
        password=smtp_password,
        use_tls=True,
    )
