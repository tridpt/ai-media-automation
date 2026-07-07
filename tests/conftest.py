"""Cấu hình chung cho test: đảm bảo import được từ thư mục gốc dự án
và bật chế độ MOCK để test không gọi API thật."""
import os
import sys

# Bật MOCK TRƯỚC khi bất kỳ module nào đọc CONFIG (CONFIG đọc env lúc import).
os.environ["MOCK"] = "1"

# Thêm thư mục gốc dự án vào sys.path để `import config`, `import src...` chạy được
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Ép CONFIG.MOCK=True phòng trường hợp CONFIG đã được import ở đâu đó trước.
from config import CONFIG  # noqa: E402

CONFIG.MOCK = True
