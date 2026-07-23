"""메일 발송 (SMTP). GitHub Secrets의 환경변수로 자격증명 주입."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_digest(mail, subject, body_text, body_html):
    if not mail or not mail.get("enabled"):
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = mail["user"]
    msg["To"] = mail["to"]
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))
    with smtplib.SMTP(mail["smtp_host"], int(mail["smtp_port"]), timeout=30) as s:
        s.starttls()
        s.login(mail["user"], mail["password"])
        s.sendmail(mail["user"], [mail["to"]], msg.as_string())
    return True
