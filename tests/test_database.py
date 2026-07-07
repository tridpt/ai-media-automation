"""Test ghi/đọc log vào database, dùng file DB tạm để không đụng DB thật."""
import importlib
from datetime import date


def test_log_and_read_back(tmp_path, monkeypatch):
    # Trỏ DB sang file tạm trước khi import module database
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(db_file))

    # Reload config + database để nhận DB_PATH mới
    import config
    importlib.reload(config)
    from src import database
    importlib.reload(database)

    database.init_db()
    database.log_task("1", "desc a", "openai", "PNG", "success", "link-a")
    database.log_task("2", "desc b", "claude", "MP3", "failed", "some error")

    logs = database.get_logs_for_day(date.today())
    assert len(logs) == 2

    statuses = {r["task_id"]: r["status"] for r in logs}
    assert statuses["1"] == "success"
    assert statuses["2"] == "failed"


def test_get_logs_empty_for_other_day(tmp_path, monkeypatch):
    from datetime import timedelta

    db_file = tmp_path / "test2.db"
    monkeypatch.setenv("DB_PATH", str(db_file))

    import config
    importlib.reload(config)
    from src import database
    importlib.reload(database)

    database.init_db()
    database.log_task("1", "desc", "openai", "PNG", "success", "link")

    # Ngày hôm qua chưa có log nào
    yesterday = date.today() - timedelta(days=1)
    assert database.get_logs_for_day(yesterday) == []
