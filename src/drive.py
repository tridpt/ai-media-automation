"""Upload file kết quả lên Google Drive, sắp xếp theo folder ngày."""
import os
from datetime import date

from config import CONFIG
from src.retry import with_retry
from src.logger import get_logger

log = get_logger("drive")

_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".mp3": "audio/mpeg",
}


def _oauth_credentials():
    """Lấy credentials OAuth (upload với tư cách tài khoản người dùng).

    - Lần đầu: mở trình duyệt cho bạn đăng nhập, rồi lưu token vào token.json.
    - Các lần sau: đọc lại token.json, tự refresh khi hết hạn (không phải đăng nhập lại).

    Cần file OAuth Client ID (tải từ Google Cloud) đặt tại CONFIG.OAUTH_CLIENT_FILE.
    """
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    creds = None
    token_path = CONFIG.OAUTH_TOKEN_FILE

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, CONFIG.SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CONFIG.OAUTH_CLIENT_FILE):
                raise RuntimeError(
                    f"Không tìm thấy '{CONFIG.OAUTH_CLIENT_FILE}'. "
                    "Tải OAuth Client ID (Desktop) từ Google Cloud về đặt tên này."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                CONFIG.OAUTH_CLIENT_FILE, CONFIG.SCOPES
            )
            creds = flow.run_local_server(port=0)
        # lưu token để lần sau không phải đăng nhập lại
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return creds


def _service():
    """Tạo Drive service.

    Ưu tiên OAuth nếu có OAuth Client file (upload bằng quota của bạn - 15GB).
    Nếu không, fallback về service account (lưu ý: service account không có
    quota lưu trữ với Drive cá nhân).
    """
    from googleapiclient.discovery import build

    if CONFIG.DRIVE_AUTH == "oauth" or os.path.exists(CONFIG.OAUTH_CLIENT_FILE):
        log.info("Drive dùng OAuth (tài khoản người dùng).")
        return build("drive", "v3", credentials=_oauth_credentials())

    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_file(
        CONFIG.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=CONFIG.SCOPES
    )
    return build("drive", "v3", credentials=creds)


def _get_or_create_day_folder(svc, parent_id: str) -> str:
    """Tạo (hoặc lấy) folder con theo ngày trong folder gốc."""
    name = date.today().isoformat()
    query = (
        f"name='{name}' and mimeType='application/vnd.google-apps.folder' "
        f"and '{parent_id}' in parents and trashed=false"
    )
    res = svc.files().list(q=query, fields="files(id)").execute()
    files = res.get("files", [])
    if files:
        return files[0]["id"]
    meta = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = svc.files().create(body=meta, fields="id").execute()
    return folder["id"]


def upload(file_path: str) -> str:
    """Upload file lên Drive, trả về link xem file."""
    if CONFIG.MOCK:
        fake = f"https://drive.google.com/mock/{os.path.basename(file_path)}"
        log.info("[MOCK] Giả lập upload %s -> %s", file_path, fake)
        return fake

    return _upload_to_drive(file_path)


@with_retry(what="Google Drive upload")
def _upload_to_drive(file_path: str) -> str:
    from googleapiclient.http import MediaFileUpload

    svc = _service()
    folder_id = _get_or_create_day_folder(svc, CONFIG.DRIVE_FOLDER_ID)

    ext = os.path.splitext(file_path)[1].lower()
    mime = _MIME.get(ext, "application/octet-stream")

    meta = {"name": os.path.basename(file_path), "parents": [folder_id]}
    media = MediaFileUpload(file_path, mimetype=mime, resumable=True)
    file = (
        svc.files()
        .create(body=meta, media_body=media, fields="id, webViewLink")
        .execute()
    )
    # cho phép ai có link đều xem được
    svc.permissions().create(
        fileId=file["id"], body={"role": "reader", "type": "anyone"}
    ).execute()
    return file.get("webViewLink", f"https://drive.google.com/file/d/{file['id']}/view")
