# Kiểm tra bảo mật trong phạm vi hồ sơ

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh hiện trạng, không thay phê duyệt của nhóm.

Không tấn công server đang dùng, không in khóa, không gửi mail hoặc dữ liệu người thật ra provider. Static review và các phép thử kiểm quyền/validation được chạy trên SQLite cách ly. Kết luận bên dưới có phạm vi cụ thể, không phải pentest/chứng nhận an toàn.

| Checklist | Quan sát/kiểm tra | Trạng thái |
| --- | --- | --- |
| SQL Injection | Query dữ liệu dùng %s/tham số, identifier động là danh sách kiểm soát; test lọc/validation hiện có | REVIEWED; không phải chứng minh toàn bộ query không thể lỗi |
| XSS | escapeHtml và markdown renderer trong UI, test JavaScript/schema/file/link | REVIEWED trong các đường đã đọc; chưa fuzz toàn UI |
| Authentication/session | Hash password, account active, backend role refresh, logout; cookie HttpOnly/Lax | TESTED theo ca có sẵn; xem TLS/CSRF còn lại |
| Authorization | Project/membership/assigned/supporter, Admin vs PM AI, archive owner, draft version | TESTED; chính sách Admin UC007 cần chốt |
| Secrets | Backend .env, gitignore, DTO/context không đưa password/key; báo cáo chỉ lưu hash nguồn công khai | REVIEWED và kiểm tra rò khóa của gói tài liệu trước bàn giao |
| Validation/upload | Số/ngày/ID/version, loại/dung lượng/chữ ký/path, download scope, link scheme | TESTED theo bộ hiện có |
| History/information leakage | Draft refs, history scope/archived_by, lỗi provider chuẩn hóa | TESTED/REVIEWED; staffing scope mở rộng theo C04 |
| CSRF | Không thấy token/Origin validation chuyên biệt | OPEN SEC-01 |
| Dependency vulnerabilities | Inventory phiên bản thực; chưa quét advisory CVE | NOT RUN SEC-03 |
| Transport/ops | HTTP nội bộ; chưa nghiệm thu TLS/backup lịch | OPEN SEC-02/05 |

| ID | Mức | Nội dung | Phương pháp | Nguồn | Minh chứng | Xử lý |
| --- | --- | --- | --- | --- | --- | --- |
| SEC-01 | MEDIUM | CSRF token/Origin check chưa thấy | STATIC | app.py, routes/, yêu cầu POST cookie session | HttpOnly/SameSite=Lax có cấu hình; không thấy token/Origin guard chuyên biệt | Cần threat model/test chuyên biệt; chưa chứng minh exploit. Không sửa trong lượt hồ sơ. |
| SEC-02 | HIGH khi public | Chưa nghiệm thu TLS | OBSERVED | GET http://127.0.0.1:5000/api/health; app.py SESSION_COOKIE_SECURE | HTTP nội bộ hoạt động; không kiểm HTTPS/proxy | NFR-03 còn thiếu minh chứng; triển khai HTTPS và Secure cookie khi có hạ tầng. |
| SEC-03 | MEDIUM | Dependency CVE và lock chưa thực hiện | NOT RUN | requirements.txt dùng >=; inventory trong evidence/dependency-inventory.json | Chưa chạy SCA/pip-audit trong lượt này | Không được kết luận không có CVE; audit/lock sau kiểm tương thích. |
| SEC-04 | Thận trọng | Prompt injection không có bảo đảm tuyệt đối | LIMITATION | prompt_builder.py, meeting_minutes_service.py, validators | Có grounding/schema/source ID; test sai ID/schema có thể hiện | Cần adversarial evaluation riêng cho dữ liệu tự do; không tự xóa prompt warning để đạt báo cáo. |
| SEC-05 | Cần nghiệm thu | Sao lưu upload + DB, quyền vận hành | NOT RUN | instance/uploads và database/schema.sql | Bằng chứng restore MySQL cũ không chứng minh backup theo lịch hiện tại | Kiểm restore cả file và DB/least privilege/retention khi triển khai. |

Severity phân biệt rủi ro vận hành với lỗ hổng đã khai thác; SEC-02 là HIGH khi công khai kết nối không TLS, không khẳng định hệ thống đã bị xâm nhập. Không có finding CRITICAL được xác minh trong phạm vi này; điều đó không chứng minh không tồn tại lỗi nghiêm trọng.
