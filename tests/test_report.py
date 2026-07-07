"""Test logic tổng hợp báo cáo (không gửi email, không vẽ file)."""
from src.report import _build_text_report


def _make_logs():
    return [
        {"task_id": "1", "status": "success", "output_format": "PNG",
         "model": "openai", "detail": "link1"},
        {"task_id": "2", "status": "success", "output_format": "MP3",
         "model": "openai", "detail": "link2"},
        {"task_id": "3", "status": "failed", "output_format": "MP4",
         "model": "openai", "detail": "ValueError: unsupported"},
    ]


def test_report_counts_and_rate():
    logs = _make_logs()
    text = _build_text_report(logs, success=2, failed=1)
    assert "Tổng số task : 3" in text
    assert "Thành công   : 2" in text
    assert "Thất bại     : 1" in text
    # 2/3 = 66.7%
    assert "66.7%" in text


def test_report_lists_each_task():
    logs = _make_logs()
    text = _build_text_report(logs, success=2, failed=1)
    assert "[SUCCESS] Task 1" in text
    assert "[FAILED] Task 3" in text


def test_report_empty_rate_zero():
    text = _build_text_report([], success=0, failed=0)
    assert "Tổng số task : 0" in text
    assert "0.0%" in text
