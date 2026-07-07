"""Đọc danh sách task từ Google Sheets và cập nhật trạng thái ngược lại."""
from config import CONFIG

# Thứ tự cột kỳ vọng trong sheet (hàng đầu tiên là header)
EXPECTED_HEADERS = [
    "id",
    "description",
    "example_asset_urls",
    "output_format",
    "model",
    "status",
]


# Dữ liệu task mẫu dùng khi chạy chế độ mock (không cần Google Sheets thật)
_MOCK_TASKS = [
    {
        "id": "1",
        "description": "a cat astronaut floating in space, orange fur",
        "example_asset_urls": "",
        "output_format": "PNG",
        "model": "openai",
        "status": "",
        "_row": 2,
    },
    {
        "id": "2",
        "description": "a serene lake at sunrise, watercolor style",
        "example_asset_urls": "",
        "output_format": "JPG",
        "model": "claude",
        "status": "",
        "_row": 3,
    },
    {
        "id": "3",
        "description": "relaxing intro voice welcoming listeners to a podcast",
        "example_asset_urls": "",
        "output_format": "MP3",
        "model": "openai",
        "status": "",
        "_row": 4,
    },
    {
        "id": "4",
        "description": "a bouncing ball animation loop",
        "example_asset_urls": "",
        "output_format": "GIF",
        "model": "openai",
        "status": "",
        "_row": 5,
    },
    {
        # Task cố tình lỗi: định dạng không được hỗ trợ -> để test nhánh THẤT BẠI
        "id": "5",
        "description": "an example task with an unsupported output format",
        "example_asset_urls": "",
        "output_format": "MP4",
        "model": "openai",
        "status": "",
        "_row": 6,
    },
]


def _service():
    # Import "lười" để chế độ mock không cần cài thư viện google.
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_file(
        CONFIG.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=CONFIG.SCOPES
    )
    return build("sheets", "v4", credentials=creds)


def read_tasks():
    """Trả về list dict các task chưa xử lý (status trống).

    Mỗi dict kèm khóa _row (số hàng thực trong sheet) để cập nhật lại sau.
    Ở chế độ mock, trả về danh sách task mẫu, không gọi Google.
    """
    if CONFIG.MOCK:
        print("[sheets][MOCK] Trả về", len(_MOCK_TASKS), "task mẫu")
        # trả về bản sao để không ảnh hưởng dữ liệu gốc
        return [dict(t) for t in _MOCK_TASKS]

    svc = _service()
    rng = f"{CONFIG.SHEET_TAB}!A1:F"
    result = (
        svc.spreadsheets()
        .values()
        .get(spreadsheetId=CONFIG.SHEET_ID, range=rng)
        .execute()
    )
    values = result.get("values", [])
    if not values:
        return []

    headers = values[0]
    tasks = []
    for i, row in enumerate(values[1:], start=2):  # hàng 2 trở đi
        # pad cho đủ số cột
        row = row + [""] * (len(headers) - len(row))
        record = dict(zip(headers, row))
        record["_row"] = i
        # bỏ qua task đã xử lý
        if str(record.get("status", "")).strip():
            continue
        if not record.get("description", "").strip():
            continue
        tasks.append(record)
    return tasks


def update_status(row_number: int, status: str):
    """Cập nhật cột status (cột F) cho hàng cụ thể."""
    if CONFIG.MOCK:
        print(f"[sheets][MOCK] Cập nhật hàng {row_number} -> {status}")
        return
    svc = _service()
    rng = f"{CONFIG.SHEET_TAB}!F{row_number}"
    svc.spreadsheets().values().update(
        spreadsheetId=CONFIG.SHEET_ID,
        range=rng,
        valueInputOption="RAW",
        body={"values": [[status]]},
    ).execute()
