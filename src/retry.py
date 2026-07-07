"""Tiện ích retry: thử lại một hàm vài lần khi gặp lỗi tạm thời.

Dùng cho các lời gọi API mạng (OpenAI, Claude, Google, Slack...) vì các lỗi
như rate limit, timeout, sự cố mạng thường chỉ tạm thời và sẽ hết khi thử lại.

Cách dùng:
    from src.retry import with_retry

    @with_retry()                      # dùng cấu hình mặc định
    def call_api(...): ...

    @with_retry(max_attempts=5, base_delay=2.0)
    def call_api(...): ...
"""
import time
import functools


# Các loại lỗi KHÔNG nên retry (lỗi do cấu hình/đầu vào, thử lại cũng vô ích).
# So khớp theo tên class hoặc chuỗi trong thông báo lỗi.
_NON_RETRYABLE_KEYWORDS = (
    "authentication",       # sai key
    "invalid_api_key",
    "invalid x-api-key",
    "billing_hard_limit",   # hết hạn mức chi tiêu
    "insufficient_quota",   # hết quota
    "permission",           # 403 thiếu quyền
    "not_found",            # 404 sai id
    "unsupported",          # định dạng không hỗ trợ (ValueError của ta)
    "không hỗ trợ",
)


def _is_retryable(exc: Exception) -> bool:
    """Quyết định có nên thử lại với lỗi này không."""
    text = f"{type(exc).__name__} {exc}".lower()
    for kw in _NON_RETRYABLE_KEYWORDS:
        if kw in text:
            return False
    return True


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    backoff: float = 2.0,
    what: str = None,
):
    """Decorator: thử lại hàm tối đa max_attempts lần với delay tăng dần.

    - max_attempts: tổng số lần thử (kể cả lần đầu).
    - base_delay: thời gian chờ trước lần thử lại đầu tiên (giây).
    - backoff: hệ số nhân delay sau mỗi lần thất bại (exponential backoff).
    - what: tên dễ đọc của thao tác, dùng trong log (mặc định là tên hàm).

    Lỗi không thể retry (sai key, hết tiền, sai quyền...) sẽ raise ngay,
    không phí thời gian thử lại.
    """

    def decorator(func):
        label = what or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    # Lỗi do cấu hình/đầu vào: dừng ngay, không thử lại.
                    if not _is_retryable(exc):
                        raise
                    # Đã hết số lần thử: raise lỗi cuối cùng.
                    if attempt == max_attempts:
                        raise
                    print(
                        f"[retry] {label} lỗi lần {attempt}/{max_attempts}: "
                        f"{type(exc).__name__}. Thử lại sau {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay *= backoff
            # Không bao giờ tới đây, nhưng để an toàn:
            raise last_exc

        return wrapper

    return decorator
