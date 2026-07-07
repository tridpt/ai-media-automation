"""Test logic sinh file ở chế độ MOCK (không gọi API AI).

conftest.py đã bật MOCK=1 nên generate() sẽ tạo file giả bằng Pillow.
"""
import os

import pytest

from src.generator import generate, _wrap


def _task(task_id, fmt, model="openai"):
    return {
        "id": str(task_id),
        "description": "a test description for generation",
        "example_asset_urls": "",
        "output_format": fmt,
        "model": model,
        "_row": task_id,
    }


@pytest.mark.parametrize(
    "fmt,expected_ext",
    [
        ("PNG", ".png"),
        ("JPG", ".jpg"),
        ("GIF", ".gif"),
        ("MP3", ".mp3"),
    ],
)
def test_generate_creates_file_with_correct_ext(fmt, expected_ext):
    path = generate(_task(100, fmt))
    assert path.endswith(expected_ext)
    assert os.path.exists(path)
    assert os.path.getsize(path) > 0


def test_generate_unsupported_format_raises():
    with pytest.raises(ValueError):
        generate(_task(101, "MP4"))


def test_wrap_breaks_long_text():
    wrapped = _wrap("word " * 30, width=20)
    # mỗi dòng không vượt quá width nhiều
    for line in wrapped.split("\n"):
        assert len(line) <= 24
