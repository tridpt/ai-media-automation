"""Cấu hình logging dùng chung cho toàn dự án.

Ghi log ra cả 2 nơi:
- Console (stdout) — để theo dõi khi chạy tay.
- File `logs/app_<ngày>.log` — để lưu lại bằng chứng chạy, tiện debug sau này.

Cách dùng ở các module khác:
    from src.logger import get_logger
    log = get_logger(__name__)
    log.info("thông điệp")
"""
import os
import sys
import logging
from datetime import date

_LOG_DIR = "logs"
_configured = False


def setup_logging(level: int = logging.INFO) -> None:
    """Cấu hình root logger (gọi 1 lần lúc khởi động). Gọi nhiều lần vẫn an toàn."""
    global _configured
    if _configured:
        return

    os.makedirs(_LOG_DIR, exist_ok=True)
    log_file = os.path.join(_LOG_DIR, f"app_{date.today().isoformat()}.log")

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler ghi ra file (UTF-8 để không lỗi tiếng Việt).
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(fmt)

    # Handler ra console.
    stream = sys.stdout
    try:
        stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    console_handler = logging.StreamHandler(stream)
    console_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(level)
    # Tránh thêm handler trùng nếu bị gọi lại.
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    _configured = True


def get_logger(name: str = "app") -> logging.Logger:
    """Lấy logger theo tên; tự cấu hình nếu chưa."""
    if not _configured:
        setup_logging()
    return logging.getLogger(name)
