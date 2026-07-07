# Chạy tự động hằng ngày (Windows Task Scheduler)

Đề bài yêu cầu "compile **daily** logs into a report" — tức pipeline nên chạy tự động
mỗi ngày. Trên Windows, cách chuẩn là dùng **Task Scheduler** gọi file `run_daily.bat`.

File `run_daily.bat` (đã có sẵn ở thư mục gốc) sẽ:
- Chuyển vào đúng thư mục dự án
- Ép Python xuất UTF-8 (tránh lỗi encoding)
- Chạy `python main.py`
- Ghi toàn bộ output ra `logs\run_YYYY-MM-DD.log`

---

## Cách 1 — Tạo bằng giao diện (dễ nhất)

1. Mở **Task Scheduler** (gõ "Task Scheduler" ở menu Start).
2. Bên phải bấm **Create Basic Task...**
3. **Name**: `AI Media Automation` → Next.
4. **Trigger**: chọn **Daily** → Next → chọn giờ chạy (ví dụ 23:00 mỗi ngày) → Next.
5. **Action**: chọn **Start a program** → Next.
6. **Program/script**: bấm **Browse...** và trỏ tới:
   ```
   d:\App\ai-media-automation\run_daily.bat
   ```
7. **Start in (optional)**: điền thư mục gốc dự án (quan trọng):
   ```
   d:\App\ai-media-automation
   ```
8. Next → tick **Open the Properties dialog** → Finish.
9. Trong Properties, tab **General**:
   - Tick **Run whether user is logged on or not** (để chạy cả khi chưa đăng nhập).
   - Tick **Run with highest privileges** nếu cần.

---

## Cách 2 — Tạo bằng dòng lệnh (nhanh)

Mở PowerShell (Admin) và chạy (đổi giờ `23:00` nếu muốn):

```powershell
$action  = New-ScheduledTaskAction -Execute "d:\App\ai-media-automation\run_daily.bat" -WorkingDirectory "d:\App\ai-media-automation"
$trigger = New-ScheduledTaskTrigger -Daily -At 23:00
Register-ScheduledTask -TaskName "AI Media Automation" -Action $action -Trigger $trigger -Description "Chay pipeline AI Media Automation moi ngay"
```

Xóa task khi không cần nữa:

```powershell
Unregister-ScheduledTask -TaskName "AI Media Automation" -Confirm:$false
```

---

## Gợi ý về lịch chạy

Có 2 kiểu thiết kế:

- **Đơn giản (mặc định hiện tại):** chạy `main.py` 1 lần/ngày. Nó xử lý hết task đang
  chờ rồi tạo báo cáo luôn ở cuối. Phù hợp nếu task được thêm vào sheet trong ngày và
  xử lý gộp vào buổi tối.

- **Nâng cao:** chạy `main.py` nhiều lần trong ngày (ví dụ mỗi giờ) để xử lý task ngay
  khi có, và chạy `main.py report` **một lần** vào cuối ngày để tổng hợp. Khi đó tạo
  **2 task** trong Task Scheduler:
  - Task A: `run_daily.bat` mỗi giờ (cần sửa bat bỏ phần report — xem ghi chú dưới).
  - Task B: chạy `python main.py report` lúc 23:59.

> Ghi chú: hiện `main.py` luôn kèm báo cáo ở cuối. Nếu muốn tách hẳn, bạn có thể bỏ
> dòng `build_and_send_daily_report()` trong hàm `run()` và để việc báo cáo cho lệnh
> `python main.py report` chạy riêng theo lịch.

---

## Kiểm tra

- Chạy thử file bat một lần bằng tay để chắc chắn hoạt động:
  ```
  run_daily.bat
  ```
  Sau đó mở `logs\run_YYYY-MM-DD.log` xem kết quả.
- Trong Task Scheduler, chuột phải task → **Run** để chạy thử ngay không cần đợi tới giờ.
