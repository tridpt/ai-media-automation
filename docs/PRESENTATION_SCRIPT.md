# Script thuyết trình video (Assignment 3)

Thời lượng mục tiêu: **10 phút**. Script chia theo mốc thời gian. Chữ *in nghiêng*
là ghi chú thao tác (bấm gì, mở gì), chữ thường là lời nói gợi ý.

> Phần Assignment 2 (prompt engineering) bạn tự điền vào mốc [4:00–5:30] — tôi đã
> chừa sẵn chỗ và gợi ý cấu trúc.

---

## [0:00 – 0:45] Mở đầu — giới thiệu bài toán

Chào thầy/cô và mọi người. Em xin trình bày Assignment 1 và 2.

Assignment 1 là một **quy trình tự động hóa (automation pipeline)**: người dùng chỉ
cần điền một dòng vào Google Sheets mô tả nội dung muốn tạo, hệ thống sẽ tự động:
sinh media bằng AI, lưu lên Google Drive, gửi thông báo qua Email và Slack, ghi log
vào database, và cuối ngày tổng hợp thành báo cáo kèm biểu đồ gửi cho admin.

Toàn bộ viết bằng **Python**, chia module rõ ràng, và em đã đưa lên GitHub.

*(Mở trang GitHub repo cho thấy)*

---

## [0:45 – 2:00] Kiến trúc & luồng hoạt động

*(Mở README, cuộn tới sơ đồ luồng)*

Luồng gồm 6 bước, khớp đúng 6 yêu cầu của đề:

1. **Đọc task** từ Google Sheets — mỗi hàng là một task gồm: mô tả, URL asset mẫu,
   định dạng output (PNG/JPG/GIF/MP3), và model (OpenAI/Claude).
2. **Sinh media** bằng AI theo định dạng yêu cầu.
3. **Upload** file lên Google Drive, sắp xếp theo folder ngày.
4. **Thông báo** Email + Slack cho từng task (thành công hoặc thất bại).
5. **Ghi log** mỗi task vào database SQLite.
6. **Báo cáo cuối ngày**: tổng hợp log → vẽ biểu đồ tỷ lệ thành công/thất bại →
   email cho admin.

*(Mở thư mục src/ cho thấy cách chia module: sheets, generator, drive, notify,
database, report, retry, logger — mỗi việc một file)*

Mỗi bước là một module riêng, dễ đọc và dễ bảo trì.

---

## [2:00 – 4:00] Demo chạy thật

*(Mở terminal)*

Em demo bằng chế độ mock — chạy toàn bộ pipeline offline, không tốn tiền API:

*(Gõ: `python main.py --mock` và để chạy)*

Có thể thấy hệ thống: đọc 5 task mẫu, tạo file cho từng cái, một task định dạng sai
thì bị đánh dấu thất bại nhưng **không làm dừng** các task khác, cuối cùng tổng hợp
báo cáo.

*(Mở thư mục outputs/ cho thấy file ảnh, gif, và report_<ngày>.png)*

Đây là biểu đồ báo cáo tự sinh — cột thành công và thất bại.

Và đây là các phần em đã chạy **thật** với dịch vụ thật, không phải mock:

*(Mở Gmail cho thấy email báo cáo kèm biểu đồ)*
- Email báo cáo thật, có file chart đính kèm.

*(Mở Slack cho thấy tin nhắn)*
- Thông báo Slack thật.

*(Mở link Google Drive của file đã upload)*
- File thật trên Google Drive, mở xem được.

---

## [4:00 – 5:30] Assignment 2 — Prompt Engineering Strategy

> **(PHẦN BẠN TỰ ĐIỀN)** Gợi ý cấu trúc trình bày:
>
> - Chiến lược prompt bạn dùng là gì (ví dụ: vai trò/role, few-shot, ràng buộc
>   định dạng output, chain-of-thought...)
> - Ví dụ 1–2 prompt cụ thể trước/sau khi tối ưu, cho thấy khác biệt
> - Kết quả cải thiện thế nào
> - Liên hệ với Assignment 1: trong code, khi task chọn `model=claude`, hệ thống
>   dùng Claude để **viết lại mô tả thành prompt chi tiết hơn** trước khi render ảnh
>   (hàm `_refine_prompt_with_claude`) — đây chính là prompt engineering áp dụng thực tế.

---

## [5:30 – 7:30] Kết quả đạt được

*(Quay lại bảng trạng thái trong README)*

5 trên 6 chức năng đã chạy thật với dịch vụ thật:
- Đọc Google Sheets ✅
- Upload Google Drive ✅ (qua OAuth)
- Email thông báo ✅
- Slack thông báo ✅
- Ghi log database ✅
- Báo cáo + biểu đồ + email admin ✅

Ngoài yêu cầu đề, em làm thêm: cơ chế **retry** khi API lỗi, **logging** ra file,
**16 unit test**, **chế độ mock** để demo/kiểm thử, và script **chạy tự động hằng ngày**
qua Windows Task Scheduler.

---

## [7:30 – 9:00] Thách thức và cách xử lý

Em gặp mấy thách thức thật và cách giải quyết:

**1. Claude không tạo được ảnh/audio.** Đề cho chọn OpenAI hoặc Claude, nhưng Claude
chỉ sinh text. Em xử lý bằng cách: dùng OpenAI để render media, còn Claude thì đảm
nhiệm việc tinh chỉnh prompt — mỗi model đúng thế mạnh.

**2. Service account không upload được lên Drive.** Ban đầu em dùng service account,
nhưng nó báo lỗi `storageQuotaExceeded` — vì service account không có dung lượng lưu
trữ trên Drive cá nhân. Em chuyển sang **OAuth**, upload bằng tài khoản người dùng
(quota 15GB) — và khâu lưu trữ chạy thật được.

**3. Rào cản credit API.** OpenAI hết credit, thử Gemini thì free tier bị giới hạn.
Em xử lý bằng **chế độ mock** để kiểm chứng toàn bộ logic mà không phụ thuộc credit,
và thiết kế code tách biệt để chỉ cần điền key có credit là chạy ra media thật ngay,
không phải sửa code.

**4. Một task lỗi không được làm sập cả pipeline.** Em bọc mỗi task trong try/except
riêng + ghi log lỗi + vẫn gửi thông báo thất bại — đúng yêu cầu "unsuccessful completion".

---

## [9:00 – 10:00] Đề xuất cải tiến & kết luận

Hướng cải tiến nếu có thêm thời gian:
- Thêm hàng đợi (queue) để xử lý số lượng task lớn song song.
- Dashboard web xem log và báo cáo trực quan thay vì chỉ email.
- Hỗ trợ thêm nhà cung cấp AI (đã thiết kế sẵn để dễ cắm thêm).
- Convert audio sang MP3 chuẩn bằng ffmpeg nếu dùng nguồn TTS khác.

Tổng kết: pipeline đáp ứng đầy đủ yêu cầu đề, phần lớn đã chạy thật, có xử lý lỗi và
tài liệu đầy đủ. Em cảm ơn thầy/cô đã lắng nghe.

---

## Checklist quay video

- [ ] Mở sẵn: GitHub repo, README, terminal, Gmail, Slack, 1 link file Drive
- [ ] Chạy thử `python main.py --mock` một lần trước khi quay cho mượt
- [ ] Quay màn hình + giọng nói, kiểm tra mic
- [ ] Giữ dưới 10 phút — nếu thiếu giờ, rút gọn phần demo
- [ ] Đính kèm khi nộp: link GitHub (Assignment 1), file Assignment 2, video
