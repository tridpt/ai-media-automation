"""Test logic retry: phân loại lỗi và cơ chế thử lại (không gọi API thật)."""
from src.retry import with_retry, _is_retryable


def test_retryable_error_transient():
    """Lỗi tạm thời (timeout, rate limit) nên được coi là có thể retry."""
    assert _is_retryable(TimeoutError("connection timed out")) is True
    assert _is_retryable(Exception("rate limit exceeded, try again")) is True


def test_non_retryable_errors():
    """Lỗi cấu hình/đầu vào KHÔNG nên retry."""
    assert _is_retryable(Exception("authentication failed")) is False
    assert _is_retryable(Exception("invalid_api_key provided")) is False
    assert _is_retryable(Exception("billing_hard_limit reached")) is False
    assert _is_retryable(Exception("insufficient_quota")) is False
    assert _is_retryable(ValueError("Định dạng không hỗ trợ: mp4")) is False


def test_retry_succeeds_after_failures():
    """Hàm lỗi vài lần rồi thành công thì with_retry phải trả về kết quả."""
    calls = {"n": 0}

    @with_retry(max_attempts=3, base_delay=0, backoff=1)
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise TimeoutError("tạm thời")
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 3


def test_retry_stops_immediately_on_non_retryable():
    """Lỗi không thể retry phải raise ngay, chỉ gọi 1 lần."""
    calls = {"n": 0}

    @with_retry(max_attempts=5, base_delay=0, backoff=1)
    def bad_key():
        calls["n"] += 1
        raise Exception("authentication error")

    try:
        bad_key()
        assert False, "phải raise"
    except Exception:
        pass
    assert calls["n"] == 1


def test_retry_exhausts_and_raises():
    """Lỗi tạm thời liên tục: thử đủ max_attempts rồi raise."""
    calls = {"n": 0}

    @with_retry(max_attempts=3, base_delay=0, backoff=1)
    def always_timeout():
        calls["n"] += 1
        raise TimeoutError("mãi lỗi")

    try:
        always_timeout()
        assert False, "phải raise"
    except TimeoutError:
        pass
    assert calls["n"] == 3
