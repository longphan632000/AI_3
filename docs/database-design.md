# Thiết kế dữ liệu hiện trạng

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

| Bảng | Số cột | Vai trò | DDL nguồn |
| --- | --- | --- | --- |
| users | 10 | Tài khoản/role/status; hash mật khẩu không gửi ra AI | database/schema.sql:14 |
| projects | 14 | Dự án, trạng thái, người lưu trữ | database/schema.sql:30 |
| project_members | 8 | Quan hệ người–dự án và năng lực riêng | database/schema.sql:51 |
| sprints | 12 | Sprint, ngày, mục tiêu/tiêu chí | database/schema.sql:68 |
| tasks | 18 | Nhiệm vụ, trạng thái, phần trăm | database/schema.sql:87 |
| comments | 5 | Trao đổi nhiệm vụ | database/schema.sql:121 |
| attachments | 9 | Thông tin tệp/link, lưu file ngoài static | database/schema.sql:133 |
| meeting_notes | 9 | Nguồn cuộc họp | database/schema.sql:150 |
| meeting_minutes | 13 | Biên bản chính thức | database/schema.sql:166 |
| ai_drafts | 14 | Bản nháp/validation snapshot/version | database/schema.sql:189 |
| ai_history | 11 | Người yêu cầu, provider/prompt version/tham chiếu | database/schema.sql:212 |
| notifications | 9 | Thông báo theo người/sự kiện/trạng thái đọc | database/schema.sql:231 |
| audit_logs | 8 | Hành động, đối tượng, người/thời gian | database/schema.sql:248 |
| task_assignees | 5 | Người chính/hỗ trợ, chống đếm trùng | database/schema.sql:263 |
| ai_draft_revisions | 7 | Lịch sử chỉnh sửa draft | database/schema.sql:271 |
| email_deliveries | 9 | Lease/dedup/retry gửi email | database/schema.sql:280 |
| member_profiles | 5 | Hồ sơ năng lực chung | database/schema.sql:290 |

## Toàn vẹn và chuẩn hóa

17 bảng tách tài khoản, thành viên, công việc, trao đổi và lưu vết. Quan hệ nhiều–nhiều dùng project_members và task_assignees với unique ghép; bản nháp và revisions/history có nhiệm vụ riêng. Không có đủ căn cứ để chứng minh hình thức mọi phụ thuộc hàm đều 3NF; việc tách bảng là nhận xét thiết kế, không là chứng nhận chuẩn hóa.

FK vật lý, index và CHECK được chép đúng từ DDL ở data-dictionary.md. Một số ràng buộc liên dự án (sprint/assignee cùng project), quyền và trạng thái được kiểm tại service, không phải FK ghép. archived_by không có FK DDL; xóa account phải xử lý dịch vụ. Các cột polymorphic audit target_type/target_id không là FK tới mọi bảng. source_refs/draft input là JSON văn bản, không tự có FK.

Archive là xóa mềm; Admin có luồng xóa vĩnh viễn kèm dọn quan hệ. Migration bổ sung có kiểm tra tồn tại và backfill chỉ khi có chứng cứ. Lượt lập hồ sơ không chạy migration hay sửa schema; database/schema.sql được giữ nguyên.

Hạn/task ước lượng cho phép thiếu theo hiện trạng (REQ-04). Tải hỗ trợ cộng toàn bộ ước lượng cho mỗi người liên quan, không chia nhỏ; cần đọc đúng khi giải thích quá tải. Schema nguồn URD dùng tên Việt/SQL Server nvarchar(max), còn implementation MySQL dùng utf8mb4/LONGTEXT; bảng ánh xạ ở system-model-traceability.md.
