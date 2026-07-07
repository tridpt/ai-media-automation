# AI Media Automation

Automation workflow: đọc task từ Google Sheets → sinh media bằng AI (OpenAI/Claude) →
lưu Google Drive → thông báo Email + Slack → ghi log vào database → cuối ngày tổng hợp
báo cáo + biểu đồ và gửi email cho admin.

## Luồng hoạt động

```
Google Sheets (input)
      │  đọc từng task (description, asset URLs, format, model)
      ▼
Gọi AI tạo file (PNG/JPG/GIF/MP3)
      │
   ┌──┴───────────┐
   ▼              ▼
Thành công      Thất bại
   │              │
Upload Drive      │
   └──────┬───────┘
          ▼
 Email + Slack notify
          ▼
 Ghi log vào SQLite
          ▼
 (cuối ngày) python main.py report → chart + email admin
```

## Cấu trúc thư mục

```
ai-media-automation/
├── main.py              # chạy pipeline xử lý toàn bộ task + báo cáo cuối ngày
├── config.py            # đọc cấu hình từ .env
├── requirements.txt
├── .env.example         # copy thành .env rồi điền key
├── run_daily.bat        # script cho Windows Task Scheduler (chạy tự động hằng ngày)
├── check_setup.py       # kiểm tra credentials trước khi chạy thật
├── docs/
│   ├── SETUP_GOOGLE.md  # hướng dẫn tạo Service Account + bật API
│   ├── SCHEDULE.md      # hướng dẫn lên lịch chạy tự động
│   └── sample_tasks.csv # dữ liệu mẫu để import vào Google Sheets
└── src/
    ├── sheets.py        # đọc Google Sheets
    ├── generator.py     # gọi OpenAI / Claude sinh media
    ├── drive.py         # upload file lên Google Drive
    ├── notify.py        # gửi Email + Slack
    ├── database.py      # ghi/đọc log SQLite
    ├── retry.py         # tiện ích retry cho các lời gọi API (backoff)
    └── report.py        # dựng báo cáo + vẽ biểu đồ (matplotlib)
```

## Cài đặt

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env        # rồi điền các key vào .env
```

## Cấu trúc Google Sheets (input)

| id | description | example_asset_urls | output_format | model | status |
|----|-------------|--------------------|---------------|-------|--------|
| 1  | a cat astronaut | https://... | PNG | openai | |
| 2  | relaxing intro voice | | MP3 | openai | |

- `output_format`: PNG, JPG, GIF, MP3
- `model`: openai hoặc claude
- Cột `status` do script tự cập nhật (done/failed)

## Chạy

```bash
# Xử lý toàn bộ task đang chờ trong sheet (kèm báo cáo cuối ngày)
python main.py

# Chỉ tổng hợp báo cáo trong ngày và gửi cho admin
python main.py report
```

## Chạy thử offline (chế độ MOCK) — không cần API key

Muốn xem toàn bộ pipeline hoạt động ngay mà chưa cần đăng ký Google/OpenAI/Slack?
Dùng chế độ mock. Nó giả lập mọi dịch vụ bên ngoài:

- Đọc task: trả về vài task mẫu (PNG, JPG, MP3, GIF + 1 task lỗi để test nhánh thất bại)
- Sinh file: tạo file thật trong `outputs/` bằng Pillow (không gọi API AI)
- Upload Drive: trả về link giả
- Email + Slack: in nội dung ra console thay vì gửi thật
- Ghi log + vẽ biểu đồ báo cáo: chạy thật như bình thường

```bash
python main.py --mock
```

Hoặc bật bằng biến môi trường:

```bash
set MOCK=1        # Windows (cmd)
python main.py
```

Sau khi chạy, mở thư mục `outputs/` để xem các file được tạo và
`outputs/report_<ngày>.png` để xem biểu đồ thống kê thành công/thất bại.

Ở chế độ mock chỉ cần cài 3 thư viện nhẹ: `python-dotenv`, `Pillow`, `matplotlib`
(không bắt buộc cài `openai`, `google-api-python-client`...).

> Lưu ý: database lưu log tích lũy theo ngày. Nếu muốn chạy lại từ đầu sạch sẽ,
> xóa file `automation.db` trước khi chạy.

## Thiết lập Google API (tóm tắt)

1. Vào Google Cloud Console → tạo project.
2. Bật **Google Sheets API** và **Google Drive API**.
3. Tạo **Service Account**, tải file JSON key về đặt tên `service_account.json`.
4. Share Google Sheet + folder Drive cho email của service account (quyền Editor).

## Chạy tự động hằng ngày

Đề bài yêu cầu "compile **daily** logs into a report". Để pipeline tự chạy mỗi ngày
mà không phải gõ tay, dùng `run_daily.bat` + Windows Task Scheduler.
Xem hướng dẫn chi tiết trong `docs/SCHEDULE.md`.

Tóm tắt: `run_daily.bat` tự chuyển đúng thư mục, ép UTF-8, và ghi toàn bộ output ra
`logs/run_<ngày>.log` để tiện kiểm tra sau này.

## Các quyết định thiết kế (vì sao làm như vậy)

**1. OpenAI tạo media, Claude tinh chỉnh prompt.**
Đề cho chọn "OpenAI or Claude", nhưng Claude chỉ sinh text — không tạo được ảnh/audio.
Vì output yêu cầu là PNG/JPG/GIF/MP3, phần render media bắt buộc dùng OpenAI
(`images.generate` cho ảnh, TTS cho audio). Khi task chọn `model=claude`, hệ thống dùng
Claude để viết lại mô tả thành prompt chi tiết hơn (`_refine_prompt_with_claude`), rồi
vẫn render bằng OpenAI. Nhờ vậy vừa dùng cả hai model đúng thế mạnh, vừa ra được media thật.

**2. GIF ghép từ nhiều khung ảnh.** Không có API tạo GIF trực tiếp, nên sinh nhiều ảnh
rồi ghép bằng Pillow — đơn giản và không phụ thuộc dịch vụ ngoài.

**3. Cô lập lỗi theo từng task.** Mỗi task bọc trong try/except riêng: một task lỗi
(sai định dạng, API chết...) được log + thông báo nhưng **không làm dừng** các task khác.
Đây là phần "unsuccessful completion" của đề.

**4. Retry có phân loại lỗi.** `src/retry.py` tự thử lại các lời gọi API khi gặp lỗi
tạm thời (timeout, rate limit, sự cố mạng) với exponential backoff. Nhưng lỗi do cấu hình
(sai key, hết quota, sai quyền) thì raise ngay — thử lại cũng vô ích, chỉ tốn thời gian.

**5. Chế độ MOCK.** Cho phép chạy và kiểm chứng toàn bộ pipeline offline, không tốn tiền
API và không cần credentials — hữu ích để review code và demo nhanh.

**6. Báo cáo theo ngày, cộng dồn.** Log lưu trong SQLite; báo cáo gộp toàn bộ log trong
ngày (kể cả nhiều lần chạy) — đúng nghĩa "daily report".

## Lưu ý

Một số phần gọi API AI cần bạn điền API key thật trong `.env` (và tài khoản OpenAI cần
có credit để tạo ảnh/audio). Chế độ `--mock` chạy được ngay không cần key. Trước khi
chạy thật, chạy `python check_setup.py` để kiểm tra mọi credentials đã đúng.
