# Cài đặt và vận hành hệ thống hiện hữu

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

## Cài mới ở môi trường riêng

1. Tạo Python virtual environment, kích hoạt và cài `python -m pip install -r requirements.txt`; bản dependency hiện dùng >=, chưa lock phiên bản.
2. Tạo `.env` từ `.env.example` cục bộ. Điền DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME; SECRET_KEY dài ngẫu nhiên ổn định; AI_PROVIDER=gemini; GEMINI_API_KEY; GEMINI_MODEL/GEMINI_MEETING_MODEL và timeout/budget. Không in `.env` hoặc khóa trong log/báo cáo.
3. Kiểm tra MySQL đang chạy bằng công cụ quản trị sẵn có; không tự đoán tên Windows service. Chỉ chạy `python database/init_db.py` cho môi trường mới đã kiểm tra đúng database; schema mẫu và seed nằm trong database/. Trên môi trường cũ, app có ensure_* migration khi khởi động; cần sao lưu trước. Lượt hồ sơ này không chạy khởi tạo hoặc migration.
4. Khởi động `python app.py`; `HOST` mặc định 127.0.0.1, `PORT` mặc định 5000. Muốn LAN dùng HOST=0.0.0.0 và địa chỉ IPv4 máy chủ. Máy khách dùng cùng server/MySQL, không tạo DB riêng trên mỗi máy.
5. Kiểm tra `GET /api/health` (200/HEALTHY/mysql_ready=true), đăng nhập theo quyền. DB không sẵn sàng trả 503, không tự chuyển SQLite.

## AI và email

AI_CONFIG_SOURCE=env_file đọc cấu hình khóa mới theo yêu cầu. AI_LOCAL_FALLBACK_ENABLED bật dự phòng; Qwen3/runtime cục bộ được cài qua scripts/setup_local_brain.py, không đưa model/runtime lên Git. Có thể dùng domain rules khi local model chưa có. Gemini vẫn ưu tiên; UI/history ghi engine đã dùng.

Worker email chạy khi app.py khởi động, có cờ DEADLINE_WORKER_ENABLED; WSGI có thể dùng `python -m services.deadline_worker` riêng một tiến trình. `SMTP_ENABLED=false` là mô phỏng, không chứng minh gửi mail. Bật SMTP cần đúng host/port/user/password/from; không tự gửi thư thật để làm báo cáo.

## Triển khai cần nghiệm thu riêng

HTTPS qua hạ tầng vận hành, SESSION_COOKIE_SECURE khi HTTPS; tài khoản DB hạn chế quyền; backup và kiểm tra restore theo lịch, tệp upload dưới instance/uploads cần sao lưu cùng DB. Không tự thay cấu hình máy chủ đang chạy. Phiên bản phụ thuộc cần lock/audit sau khi kiểm tương thích.

## Chẩn đoán

| Dấu hiệu | Kiểm tra không lộ secret | Hướng xử lý | Kết quả quan sát |
| --- | --- | --- | --- |
| Khóa AI bị từ chối | Kiểm tra provider và khóa có được đặt; không in giá trị | Đổi đúng khóa Gemini ở backend; đối chiếu quyền/quota | AI_KEY_REJECTED hoặc fallback có engine |
| Model/quota/network | Xem mã AI_MODEL_UNAVAILABLE/AI_RATE_LIMIT/AI_DNS/AI_TIMEOUT | Kiểm tra cấu hình/quota/mạng máy chủ; thử lại có giới hạn | Lỗi rõ hoặc local fallback |
| MySQL không kết nối | GET /api/health, cấu hình host/port/name; không in password | Kiểm tra service/kết nối, đúng database và quyền | 503 UNAVAILABLE |
| Schema cũ | So cột/tables với schema/migrations ở môi trường sao lưu | Áp dụng migration hiện có sau kiểm tra dữ liệu; không reseed production | Không coi thiếu bảng là lỗi API key |
| 403 dự án | Kiểm session/role/membership; archive_by nếu archived | Admin/PM điều chỉnh quyền hợp lệ | Không giả role trong payload |
| AI thiếu/mâu thuẫn | Đọc warnings/source references | Đối chiếu tài liệu gốc, sửa draft/version theo quyền | needs_verification, chưa xác nhận chính thức |
| Thiết bị không cập nhật | Cùng URL server, có mạng, còn form chưa lưu không | Lưu/hủy biểu mẫu rồi cập nhật; kiểm tra revision/build | Polling khoảng 5s khi trang hoạt động |

Đây là hướng dẫn vận hành theo mã, không phải bằng chứng mọi bước đã được chạy trong lượt này. Kết quả thực thi nằm trong test-report.md.
