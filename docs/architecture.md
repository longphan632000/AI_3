# Kiến trúc hệ thống hiện trạng

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

Ứng dụng phân tầng bằng module, không có ORM/model class cho từng bảng. Route nhận yêu cầu và kiểm tra quyền; service thực hiện phần lớn nghiệp vụ; một số route vẫn đọc SQL trực tiếp. database/connection quản lý SQL và transaction. Giao diện server-rendered kết hợp fetch JavaScript. Không đưa framework, queue hay cơ sở dữ liệu mới vào sơ đồ.

| Lớp | Tệp | Trách nhiệm | Ranh giới |
| --- | --- | --- | --- |
| Presentation | templates/, static/js/, static/css/ | Form, Kanban chuột/cảm ứng, biểu đồ, xem draft và xác nhận | Không giữ API key; quyền phải kiểm ở backend |
| HTTP/API | app.py, routes/ | Session, request validation, scope, status JSON, no-store/version | Client role/uid không được coi là đáng tin |
| Business | services/*_service.py | Auth, project/task/sprint/collaboration/report/archive | atomic/transaction; archived read-only |
| AI coordination | ai_request_analyzer → project_data_retriever → context_builder → prompt_builder → ai_provider_service → ai_response_validator | Ba task, nguồn tham chiếu, canonical staffing, draft/history | Chỉ PM xác nhận qua endpoint riêng |
| Persistence | database/connection.py, migrations.py, schema.sql | MySQL runtime; SQLite khi test chủ động | Không tự chuyển DB khi MySQL lỗi |
| Integration | gemini_service, openai_service, local_model_service, email_service | Gemini ưu tiên; local fallback; SMTP tùy cờ | Không có tool để AI tự ghi MySQL |
| Sync | sync_routes.py, app_version_service.py, static/js/main.js | Revision/bản build mỗi khoảng 5s, giữ biểu mẫu | Một máy chủ chung; offline không đồng bộ tức thời |

## Phân quyền và transaction

before_request xác minh account còn active và cập nhật role từ DB; write scope chặn viewer/archived. Dịch vụ kiểm tra assignee/supporter cho %/status, role/project cho thao tác PM. `atomic` lồng nhau dùng một transaction, rollback khi lỗi; callback email chạy sau commit. Confirmation dùng version/status optimistic locking. Khôi phục archive theo archived_by, không dựa created_by.

## Triển khai và giới hạn

Entry point `python app.py`; bind/port theo HOST/PORT; SECRET_KEY ổn định và MySQL cấu hình backend. Worker email riêng khi WSGI. HTTPS/proxy/backup theo lịch chưa được nghiệm thu từ mã và cần người vận hành xác nhận. Sequence/activity cho 13 UC nằm trong diagrams/. Hình class là miền khái niệm theo URD; Python thực dùng service/function, một số AI adapter class.
