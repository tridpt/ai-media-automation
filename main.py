"""Điểm chạy chính của workflow tự động hoá.

Luồng xử lý:
1. Đọc task chưa xử lý từ Google Sheets
2. Với mỗi task: gọi AI sinh file -> upload Drive -> thông báo -> ghi log
3. Cập nhật trạng thái ngược lại Sheets
4. Cuối cùng: tổng hợp log trong ngày, vẽ chart, email admin

Cách dùng:
    python main.py            # chạy toàn bộ workflow (xử lý task + báo cáo)
    python main.py report     # chỉ tạo và gửi báo cáo tổng kết trong ngày
"""
import os
import sys

# Ép stdout/stderr sang UTF-8 để không crash khi in tiếng Việt/emoji
# lúc output bị pipe hoặc ghi ra file (Windows mặc định dùng cp1252).
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# Bật chế độ mock TRƯỚC khi import CONFIG nếu có cờ --mock hoặc MOCK=1.
# Vì CONFIG đọc biến môi trường ngay lúc import, phải set os.environ sớm.
if "--mock" in sys.argv:
    os.environ["MOCK"] = "1"

from config import CONFIG
from src.database import init_db, log_task
from src.sheets import read_tasks, update_status
from src.generator import generate
from src.drive import upload
from src.notify import notify_task_result
from src.report import build_and_send_daily_report


def process_task(task: dict):
    """Xử lý 1 task từ đầu đến cuối. Trả về (success, detail)."""
    task_id = task.get("id") or task.get("_row")
    try:
        # 1. Sinh file bằng AI
        local_path = generate(task)
        # 2. Upload lên Google Drive
        link = upload(local_path)
        # 3. Ghi log thành công
        log_task(
            task_id,
            task.get("description", ""),
            task.get("model", ""),
            task.get("output_format", ""),
            "success",
            link,
        )
        # 4. Thông báo + cập nhật sheet
        notify_task_result(task, True, link)
        update_status(task["_row"], "success")
        print(f"[main] Task {task_id} OK -> {link}")
        return True, link
    except Exception as e:  # noqa: BLE001
        detail = f"{type(e).__name__}: {e}"
        log_task(
            task_id,
            task.get("description", ""),
            task.get("model", ""),
            task.get("output_format", ""),
            "failed",
            detail,
        )
        notify_task_result(task, False, detail)
        try:
            update_status(task["_row"], "failed")
        except Exception:  # noqa: BLE001
            pass
        print(f"[main] Task {task_id} FAILED -> {detail}")
        return False, detail


def run():
    """Chạy toàn bộ workflow."""
    init_db()
    if CONFIG.MOCK:
        print("[main] === CHẾ ĐỘ MOCK: giả lập mọi dịch vụ, không gọi API thật ===")
    print("[main] Đọc task từ Google Sheets...")
    tasks = read_tasks()
    print(f"[main] Có {len(tasks)} task cần xử lý.")

    for task in tasks:
        process_task(task)

    # Tổng hợp và gửi báo cáo cuối ngày
    build_and_send_daily_report()
    print("[main] Hoàn tất.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        init_db()
        build_and_send_daily_report()
    else:
        run()
