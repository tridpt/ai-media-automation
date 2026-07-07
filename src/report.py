"""Tổng hợp log trong ngày, vẽ biểu đồ và gửi email tổng kết cho admin."""
import os
from datetime import date

import matplotlib

matplotlib.use("Agg")  # không cần màn hình, chỉ render ra file
import matplotlib.pyplot as plt

from config import CONFIG
from src.database import get_logs_for_day
from src.notify import send_email


def _build_chart(logs, out_path: str):
    """Vẽ biểu đồ cột số task thành công / thất bại."""
    success = sum(1 for r in logs if r["status"] == "success")
    failed = sum(1 for r in logs if r["status"] == "failed")

    fig, ax = plt.subplots(figsize=(5, 4))
    bars = ax.bar(
        ["Thành công", "Thất bại"],
        [success, failed],
        color=["#2e7d32", "#c62828"],
    )
    ax.set_title(f"Kết quả task ngày {date.today().isoformat()}")
    ax.set_ylabel("Số lượng")
    for b in bars:
        ax.text(
            b.get_x() + b.get_width() / 2,
            b.get_height(),
            str(int(b.get_height())),
            ha="center",
            va="bottom",
        )
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return success, failed


def _build_text_report(logs, success, failed) -> str:
    total = len(logs)
    rate = (success / total * 100) if total else 0
    lines = [
        f"BÁO CÁO TỔNG KẾT NGÀY {date.today().isoformat()}",
        "=" * 40,
        f"Tổng số task : {total}",
        f"Thành công   : {success}",
        f"Thất bại     : {failed}",
        f"Tỷ lệ thành công: {rate:.1f}%",
        "",
        "CHI TIẾT:",
    ]
    for r in logs:
        lines.append(
            f"- [{r['status'].upper()}] Task {r['task_id']} "
            f"({r['output_format']}/{r['model']}): {r['detail']}"
        )
    return "\n".join(lines)


def build_and_send_daily_report(day: date = None):
    """Điểm vào chính: tổng hợp -> chart -> email admin."""
    day = day or date.today()
    logs = get_logs_for_day(day)
    if not logs:
        print("[report] Không có log nào trong ngày, bỏ qua báo cáo.")
        return

    os.makedirs(CONFIG.OUTPUT_DIR, exist_ok=True)
    chart_path = os.path.join(CONFIG.OUTPUT_DIR, f"report_{day.isoformat()}.png")
    success, failed = _build_chart(logs, chart_path)
    body = _build_text_report(logs, success, failed)

    subject = f"[AI Automation] Báo cáo ngày {day.isoformat()}"
    try:
        send_email(subject, body, to=CONFIG.ADMIN_EMAIL, attachment=chart_path)
        print("[report] Đã gửi báo cáo cho admin.")
    except Exception as e:  # noqa: BLE001
        print(f"[report] Lỗi gửi báo cáo: {e}")


if __name__ == "__main__":
    build_and_send_daily_report()
