# Phát hiện và giới hạn kiểm tra bảo mật

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh hiện trạng, không thay phê duyệt của nhóm.

| ID | Mức | Nội dung | Phương pháp | Nguồn | Minh chứng | Xử lý |
| --- | --- | --- | --- | --- | --- | --- |
| SEC-01 | MEDIUM | CSRF token/Origin check chưa thấy | STATIC | app.py, routes/, yêu cầu POST cookie session | HttpOnly/SameSite=Lax có cấu hình; không thấy token/Origin guard chuyên biệt | Cần threat model/test chuyên biệt; chưa chứng minh exploit. Không sửa trong lượt hồ sơ. |
| SEC-02 | HIGH khi public | Chưa nghiệm thu TLS | OBSERVED | GET http://127.0.0.1:5000/api/health; app.py SESSION_COOKIE_SECURE | HTTP nội bộ hoạt động; không kiểm HTTPS/proxy | NFR-03 còn thiếu minh chứng; triển khai HTTPS và Secure cookie khi có hạ tầng. |
| SEC-03 | MEDIUM | Dependency CVE và lock chưa thực hiện | NOT RUN | requirements.txt dùng >=; inventory trong evidence/dependency-inventory.json | Chưa chạy SCA/pip-audit trong lượt này | Không được kết luận không có CVE; audit/lock sau kiểm tương thích. |
| SEC-04 | Thận trọng | Prompt injection không có bảo đảm tuyệt đối | LIMITATION | prompt_builder.py, meeting_minutes_service.py, validators | Có grounding/schema/source ID; test sai ID/schema có thể hiện | Cần adversarial evaluation riêng cho dữ liệu tự do; không tự xóa prompt warning để đạt báo cáo. |
| SEC-05 | Cần nghiệm thu | Sao lưu upload + DB, quyền vận hành | NOT RUN | instance/uploads và database/schema.sql | Bằng chứng restore MySQL cũ không chứng minh backup theo lịch hiện tại | Kiểm restore cả file và DB/least privilege/retention khi triển khai. |
