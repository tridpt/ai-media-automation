"""Ghi và đọc log của mỗi task vào SQLite."""
import sqlite3
from datetime import datetime, date
from contextlib import contextmanager

from config import CONFIG


@contextmanager
def _conn():
    conn = sqlite3.connect(CONFIG.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Tạo bảng log nếu chưa có."""
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS task_logs (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id       TEXT,
                description   TEXT,
                model         TEXT,
                output_format TEXT,
                status        TEXT,          -- 'success' | 'failed'
                detail        TEXT,          -- link file hoặc thông báo lỗi
                created_at    TEXT
            )
            """
        )


def log_task(task_id, description, model, output_format, status, detail):
    """Ghi 1 dòng log."""
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO task_logs
                (task_id, description, model, output_format, status, detail, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(task_id),
                description,
                model,
                output_format,
                status,
                detail,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )


def get_logs_for_day(day: date = None):
    """Lấy toàn bộ log trong 1 ngày (mặc định hôm nay)."""
    day = day or date.today()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM task_logs WHERE date(created_at) = ? ORDER BY id",
            (day.isoformat(),),
        ).fetchall()
    return [dict(r) for r in rows]
