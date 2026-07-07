@echo off
REM ============================================================
REM  Chạy pipeline AI Media Automation tự động (dùng cho Task Scheduler)
REM  - Đặt đúng thư mục làm việc rồi gọi python main.py
REM  - Ghi toàn bộ output ra file log theo ngày trong thư mục logs\
REM ============================================================

REM Chuyển tới thư mục chứa file .bat này (thư mục gốc dự án)
cd /d "%~dp0"

REM Ép Python xuất UTF-8 để không lỗi khi ghi log tiếng Việt
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

REM Tạo thư mục logs nếu chưa có
if not exist "logs" mkdir "logs"

REM Lấy ngày theo định dạng YYYY-MM-DD cho tên file log
for /f "tokens=1-3 delims=/- " %%a in ("%date%") do set TODAY=%%c-%%b-%%a

REM Nếu có virtualenv thì ưu tiên dùng python trong đó
set PY=python
if exist ".venv\Scripts\python.exe" set PY=.venv\Scripts\python.exe

echo [%date% %time%] Bat dau chay pipeline >> "logs\run_%TODAY%.log"
"%PY%" main.py >> "logs\run_%TODAY%.log" 2>&1
echo [%date% %time%] Ket thuc, exit code=%errorlevel% >> "logs\run_%TODAY%.log"
