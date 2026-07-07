"""Đọc cấu hình từ file .env. Import CONFIG ở các module khác."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # AI models
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

    # Google
    GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv(
        "GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json"
    )
    SHEET_ID = os.getenv("SHEET_ID", "")
    SHEET_TAB = os.getenv("SHEET_TAB", "Sheet1")
    DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "")

    # Email
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM = os.getenv("EMAIL_FROM", "")
    EMAIL_TO = os.getenv("EMAIL_TO", "")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")

    # Slack
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

    # Local
    DB_PATH = os.getenv("DB_PATH", "automation.db")
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")

    # Chế độ chạy thử: True = giả lập mọi thứ, không gọi API thật.
    # Có thể bật bằng biến môi trường MOCK=1 hoặc cờ --mock khi chạy main.py
    MOCK = os.getenv("MOCK", "0") in ("1", "true", "True")

    # Google API scopes
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]


CONFIG = Config()
