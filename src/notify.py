"""Gửi thông báo qua Email (SMTP) và Slack (webhook)."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

import requests

from config import CONFIG
from src.retry import with_retry


def send_email(subject: str, body: str, to: str = None, attachment: str = None):
    """Gửi email dạng text, có thể kèm 1 file đính kèm."""
    if CONFIG.MOCK:
        att = f" (đính kèm: {attachment})" if attachment else ""
        print(f"[email][MOCK] To: {to or CONFIG.EMAIL_TO} | {subject}{att}")
        print("  " + body.replace("\n", "\n  "))
        return
    if not CONFIG.SMTP_USER:
        print("[notify] SMTP chưa cấu hình, bỏ qua email")
        return
    to = to or CONFIG.EMAIL_TO
    msg = MIMEMultipart()
    msg["From"] = CONFIG.EMAIL_FROM or CONFIG.SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    if attachment:
        with open(attachment, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={attachment.split('/')[-1]}",
        )
        msg.attach(part)

    with smtplib.SMTP(CONFIG.SMTP_HOST, CONFIG.SMTP_PORT) as server:
        server.starttls()
        server.login(CONFIG.SMTP_USER, CONFIG.SMTP_PASSWORD)
        server.send_message(msg)


def send_slack(text: str):
    """Gửi tin nhắn tới Slack qua Incoming Webhook."""
    if CONFIG.MOCK:
        print(f"[slack][MOCK] {text.splitlines()[0] if text else ''}")
        return
    if not CONFIG.SLACK_WEBHOOK_URL:
        print("[notify] Slack webhook chưa cấu hình, bỏ qua")
        return
    _post_slack(text)


@with_retry(what="Slack webhook")
def _post_slack(text: str):
    resp = requests.post(CONFIG.SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
    resp.raise_for_status()


def notify_task_result(task, success: bool, detail: str):
    """Gửi cả email + slack cho kết quả của 1 task."""
    status = "✅ THÀNH CÔNG" if success else "❌ THẤT BẠI"
    desc = task.get("description", "")
    subject = f"[AI Automation] Task {task.get('id', task.get('_row'))} {status}"
    body = (
        f"Trạng thái: {status}\n"
        f"Mô tả: {desc}\n"
        f"Model: {task.get('model')}\n"
        f"Định dạng: {task.get('output_format')}\n"
        f"Chi tiết: {detail}\n"
    )
    try:
        send_email(subject, body)
    except Exception as e:  # noqa: BLE001
        print(f"[notify] lỗi gửi email: {e}")
    try:
        send_slack(f"{subject}\n{body}")
    except Exception as e:  # noqa: BLE001
        print(f"[notify] lỗi gửi slack: {e}")
