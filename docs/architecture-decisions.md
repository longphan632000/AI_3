# Quyết định kiến trúc quan sát từ mã

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

| ADR | Lựa chọn thực tế | Lý do/đánh đổi | Bằng chứng |
| --- | --- | --- | --- |
| ADR-01 | Flask + HTML/JS và services/SQL | Giữ hệ thống hiện hữu; service functions tách route/DB; không gán nhãn ORM/MVC có model khi chưa có | app.py; routes/; services/; database/connection.py |
| ADR-02 | MySQL runtime, SQLite test | Một nguồn dữ liệu thật; test cách ly, không ghi song song hai DB khi lỗi | database/connection.py; tests/run_isolated.py |
| ADR-03 | Provider Gemini-first, local fallback | Đáp ứng yêu cầu tiếp tục trợ lý khi API lỗi; phải ghi nguồn xử lý | ai_provider_service.py; local_*_service.py |
| ADR-04 | Human confirmation + version lock | Draft được lưu để đối chiếu; chính thức chỉ khi PM xác nhận; chống ghi đè bản cũ | ai_draft_service.py; ai_confirmation_service.py |
| ADR-05 | Staffing canonical bằng dữ liệu đã kiểm | Provider xếp hạng ID; thiếu/sai ID thì bộ xếp hạng xác minh; không tự phân công | staffing_service.py; ai_assistant_service.py |
| ADR-06 | Polling 5 giây + version assets | Đồng bộ dùng chung HTTP; giữ form chưa lưu; không phải WebSocket | sync_routes.py; main.js; app_version_service.py |
| ADR-07 | Archive provenance + audit backfill có bằng chứng | Khôi phục theo người lưu trữ; không đoán người tạo khi lịch sử thiếu | archive_schema.py; project_service.py |

Các ADR mô tả quyết định hiện trạng và căn cứ từ mã/yêu cầu, không xác nhận lịch sử cuộc họp thiết kế hoặc tự đặt trạng thái APPROVED.
