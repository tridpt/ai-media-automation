"""Upload file kết quả lên Google Drive, sắp xếp theo folder ngày."""
import os
from datetime import date

from config import CONFIG
from src.retry import with_retry

_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".mp3": "audio/mpeg",
}


def _service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

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
        print(f"[drive][MOCK] Giả lập upload {file_path} -> {fake}")
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
