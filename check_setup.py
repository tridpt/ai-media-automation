"""Kiểm tra cấu hình trước khi chạy pipeline thật.

Chạy:  python check_setup.py

Script kiểm tra lần lượt:
- File .env và các biến bắt buộc
- File service_account.json
- Kết nối Google Sheets (đọc được tab task)
- Kết nối Google Drive (truy cập được folder đích)
- API key OpenAI / Claude có được điền chưa
- Cấu hình Email (SMTP) và Slack

Mỗi mục in ✅ (ok) / ⚠️ (thiếu, không bắt buộc) / ❌ (lỗi cần sửa).
Script KHÔNG gửi email/slack hay tạo file thật, chỉ kiểm tra kết nối.
"""
import os
import sys

from config import CONFIG

OK = "[OK]  "
WARN = "[WARN]"
ERR = "[ERR] "

_errors = 0
_warns = 0


def ok(msg):
    print(f"{OK} {msg}")


def warn(msg):
    global _warns
    _warns += 1
    print(f"{WARN} {msg}")


def err(msg):
    global _errors
    _errors += 1
    print(f"{ERR} {msg}")


def check_env_file():
    print("\n== 1. File .env ==")
    if os.path.exists(".env"):
        ok("Tìm thấy file .env")
    else:
        warn("Chưa có file .env (đang dùng giá trị mặc định). "
             "Chạy: copy .env.example .env rồi điền thông tin.")


def check_service_account():
    print("\n== 2. Google service account ==")
    path = CONFIG.GOOGLE_SERVICE_ACCOUNT_FILE
    if not os.path.exists(path):
        err(f"Không tìm thấy '{path}'. Xem docs/SETUP_GOOGLE.md bước 4.")
        return False
    ok(f"Tìm thấy file key: {path}")
    return True


def check_sheets():
    print("\n== 3. Google Sheets ==")
    if not CONFIG.SHEET_ID:
        err("SHEET_ID trống trong .env. Xem SETUP_GOOGLE.md bước 6.")
        return
    try:
        from src.sheets import read_tasks

        tasks = read_tasks()
        ok(f"Kết nối Sheets thành công. Có {len(tasks)} task đang chờ xử lý.")
    except Exception as e:  # noqa: BLE001
        err(f"Không đọc được Sheets: {type(e).__name__}: {e}")


def check_drive():
    print("\n== 4. Google Drive ==")
    if not CONFIG.DRIVE_FOLDER_ID:
        err("DRIVE_FOLDER_ID trống trong .env. Xem SETUP_GOOGLE.md bước 7.")
        return
    try:
        from src.drive import _service

        svc = _service()
        # thử truy cập metadata của folder đích
        svc.files().get(
            fileId=CONFIG.DRIVE_FOLDER_ID, fields="id, name"
        ).execute()
        ok("Kết nối Drive thành công và truy cập được folder đích.")
    except Exception as e:  # noqa: BLE001
        err(f"Không truy cập được Drive/folder: {type(e).__name__}: {e}")


def check_ai_keys():
    print("\n== 5. AI model keys ==")
    if CONFIG.OPENAI_API_KEY:
        ok("OPENAI_API_KEY đã được điền.")
    else:
        warn("OPENAI_API_KEY trống. Cần cho tạo ảnh/audio bằng OpenAI.")
    if CONFIG.ANTHROPIC_API_KEY:
        ok("ANTHROPIC_API_KEY đã được điền.")
    else:
        warn("ANTHROPIC_API_KEY trống. Chỉ cần nếu dùng model=claude.")


def check_email():
    print("\n== 6. Email (SMTP) ==")
    if CONFIG.SMTP_USER and CONFIG.SMTP_PASSWORD:
        ok(f"SMTP đã cấu hình cho {CONFIG.SMTP_USER}")
    else:
        warn("SMTP_USER/SMTP_PASSWORD trống. Sẽ không gửi được email thật.")
    if CONFIG.ADMIN_EMAIL:
        ok(f"ADMIN_EMAIL: {CONFIG.ADMIN_EMAIL}")
    else:
        warn("ADMIN_EMAIL trống. Báo cáo cuối ngày sẽ không có người nhận.")


def check_slack():
    print("\n== 7. Slack ==")
    if CONFIG.SLACK_WEBHOOK_URL:
        ok("SLACK_WEBHOOK_URL đã được điền.")
    else:
        warn("SLACK_WEBHOOK_URL trống. Sẽ không gửi được thông báo Slack.")


def main():
    print("=" * 55)
    print(" KIỂM TRA CẤU HÌNH - AI Media Automation")
    print("=" * 55)

    check_env_file()
    has_sa = check_service_account()
    if has_sa:
        check_sheets()
        check_drive()
    else:
        print("\n(Bỏ qua kiểm tra Sheets/Drive vì thiếu service_account.json)")
    check_ai_keys()
    check_email()
    check_slack()

    print("\n" + "=" * 55)
    if _errors:
        print(f" KẾT QUẢ: {_errors} lỗi cần sửa, {_warns} cảnh báo.")
        print(" Sửa các mục [ERR] rồi chạy lại. Xem docs/SETUP_GOOGLE.md.")
        sys.exit(1)
    if _warns:
        print(f" KẾT QUẢ: OK phần bắt buộc, còn {_warns} cảnh báo (không chặn).")
        print(" Bạn có thể chạy: python main.py")
    else:
        print(" KẾT QUẢ: Tất cả sẵn sàng! Chạy: python main.py")
    print("=" * 55)


if __name__ == "__main__":
    main()
