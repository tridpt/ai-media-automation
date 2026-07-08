# Hướng dẫn thiết lập Google API (chi tiết)

Đây là phần tốn thời gian nhất. Làm đúng một lần rồi dùng mãi. Tổng thời gian khoảng 15–20 phút.

Ta cần 2 thứ từ Google:
1. Một **Service Account** (tài khoản máy) + file key JSON để code đăng nhập tự động.
2. Bật **Google Sheets API** và **Google Drive API** cho project.

Sau đó **share** Google Sheet và folder Drive cho email của service account.

---

## Bước 1 — Tạo project trên Google Cloud

1. Vào https://console.cloud.google.com/
2. Ở thanh trên cùng, bấm dropdown chọn project → **New Project**.
3. Đặt tên (ví dụ `ai-media-automation`) → **Create**.
4. Chờ vài giây, chọn đúng project vừa tạo ở dropdown.

## Bước 2 — Bật 2 API cần thiết

1. Menu trái → **APIs & Services** → **Library**.
2. Tìm **"Google Sheets API"** → bấm vào → **Enable**.
3. Quay lại Library, tìm **"Google Drive API"** → bấm vào → **Enable**.

## Bước 3 — Tạo Service Account

1. Menu trái → **APIs & Services** → **Credentials**.
2. Bấm **+ CREATE CREDENTIALS** → chọn **Service account**.
3. Đặt tên (ví dụ `automation-bot`) → **Create and Continue**.
4. Phần "Grant this service account access" có thể bỏ qua → **Continue** → **Done**.

## Bước 4 — Tải file key JSON

1. Ở trang **Credentials**, trong mục **Service Accounts**, bấm vào service account vừa tạo.
2. Sang tab **Keys** → **Add Key** → **Create new key**.
3. Chọn định dạng **JSON** → **Create**. File sẽ tự tải về máy.
4. Đổi tên file thành `service_account.json` và đặt vào thư mục gốc dự án
   (`d:\App\ai-media-automation\service_account.json`).

> ⚠️ File này là bí mật, đừng commit lên git. `.gitignore` đã loại trừ nó sẵn.

## Bước 5 — Lấy email của service account

1. Vẫn ở trang service account, copy giá trị **Email**.
   Dạng: `automation-bot@ten-project.iam.gserviceaccount.com`
2. Giữ email này để dùng ở bước share.

## Bước 6 — Tạo Google Sheet và share cho service account

1. Tạo một Google Sheet mới tại https://sheets.google.com
2. Import file mẫu `docs/sample_tasks.csv` (File → Import → Upload) hoặc tự tạo các cột:
   `id | description | example_asset_urls | output_format | model | status`
3. Bấm **Share** (góc trên phải) → dán **email service account** ở Bước 5 →
   chọn quyền **Editor** → **Send**.
4. Lấy **SHEET_ID** từ URL của sheet:
   `https://docs.google.com/spreadsheets/d/`**`SHEET_ID_NẰM_Ở_ĐÂY`**`/edit`

## Bước 7 — Tạo folder Google Drive và share

1. Tạo một folder mới trên https://drive.google.com (ví dụ `AI Outputs`).
2. Bấm chuột phải folder → **Share** → dán **email service account** → quyền **Editor**.
3. Mở folder, lấy **DRIVE_FOLDER_ID** từ URL:
   `https://drive.google.com/drive/folders/`**`DRIVE_FOLDER_ID_NẰM_Ở_ĐÂY`**

## Bước 8 — Điền vào file .env

Mở file `.env` (copy từ `.env.example` nếu chưa có) và điền:

```
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
SHEET_ID=<dán SHEET_ID ở bước 6>
SHEET_TAB=Sheet1
DRIVE_FOLDER_ID=<dán DRIVE_FOLDER_ID ở bước 7>
```

## Bước 9 — Kiểm tra kết nối

Chạy script kiểm tra:

```bash
python check_setup.py
```

Nếu thấy tất cả dòng đều ✅ là đã sẵn sàng chạy thật. Nếu có ❌, script sẽ báo rõ
thiếu cái gì để bạn sửa.

---

## Các lỗi thường gặp

| Lỗi | Nguyên nhân / cách sửa |
|-----|------------------------|
| `403 ... does not have permission` | Chưa share Sheet/folder cho email service account, hoặc share sai quyền. |
| `FileNotFoundError: service_account.json` | Chưa đặt file key đúng chỗ hoặc sai tên. |
| `HttpError 404 ... Requested entity was not found` | SHEET_ID hoặc DRIVE_FOLDER_ID sai. |
| `API has not been used ... disabled` | Chưa bật Sheets API hoặc Drive API ở Bước 2. |
| `Service Accounts do not have storage quota` | Đang upload Drive bằng service account. Với Gmail cá nhân phải dùng OAuth — xem phần dưới. |

---

## Upload Drive bằng OAuth (bắt buộc với Gmail cá nhân)

Service account **không có dung lượng lưu trữ riêng**, nên với Gmail cá nhân việc
upload file lên Drive sẽ báo `storageQuotaExceeded`. Cách đúng là dùng **OAuth** để
upload với tư cách chính bạn (dùng quota 15GB của tài khoản). Đọc Sheets vẫn dùng
service account như trên; chỉ khâu upload Drive cần OAuth.

### Bước A — Tạo OAuth Client ID

1. Google Cloud Console → **APIs & Services** → **Credentials**.
2. **+ CREATE CREDENTIALS** → **OAuth client ID**.
3. Nếu bị hỏi cấu hình **OAuth consent screen**:
   - User type: chọn **External** → Create.
   - Điền tên app + email bắt buộc → Save and Continue (bỏ qua Scopes).
   - **Test users** → Add users → thêm chính Gmail của bạn → Save.
4. Quay lại tạo OAuth client ID → Application type: **Desktop app** → Create.
5. Bấm **Download JSON**, đổi tên thành `oauth_client.json`, đặt ở thư mục gốc dự án.

### Bước B — Cấu hình .env

```
DRIVE_AUTH=oauth
OAUTH_CLIENT_FILE=oauth_client.json
```

### Bước C — Đăng nhập lần đầu

Lần chạy thật đầu tiên, trình duyệt sẽ tự mở để bạn đăng nhập Google và cấp quyền.
Gặp màn hình "Google chưa xác minh app này" (vì đây là app test của chính bạn):
bấm **Nâng cao (Advanced)** → **Chuyển tới ... (không an toàn)** → **Cho phép (Allow)**.

Sau khi cho phép, token được lưu vào `token.json` — các lần sau không phải đăng nhập
lại. Cả `oauth_client.json` và `token.json` đều đã nằm trong `.gitignore`.
