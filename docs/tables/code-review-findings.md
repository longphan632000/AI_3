# Các phát hiện code review

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh hiện trạng, không thay phê duyệt của nhóm.

| ID | Mức | Phát hiện | Cách xác minh | Vị trí | Bằng chứng | Đề nghị/trạng thái |
| --- | --- | --- | --- | --- | --- | --- |
| CR-01 | HIGH | Sửa draft staffing >3 người bị áp lại giới hạn 3 | REPRODUCED | services/ai_draft_service.py:64 | PROBE-01; validator nhận thiếu v2/count | Khi được cho phép sửa: dùng input_params/snapshot request v2 cho validator, thêm test lưu không đổi 5 người; hiện chưa sửa. |
| CR-02 | MEDIUM | Phiên bản prompt lịch sử cố định | STATIC | services/ai_assistant_service.py:129 | FR-15/REQ-10; prompt thực tế có nhiều nhánh | Cần quản lý version/hash thực sau phê duyệt; hiện chỉ ghi hash tệp trong hồ sơ. |
| CR-03 | MEDIUM | Scanner sắp hạn chưa nối worker định kỳ | STATIC | services/email_service.py:120 | Worker email gọi scan email; không gọi scan_and_create_deadline_notifications | Chốt FR-16 lịch/người nhận rồi thay đổi trong nhiệm vụ riêng. |
| CR-04 | MEDIUM | Ràng buộc ngày/ước lượng/mốc khác URD | OBSERVED | database/schema.sql:104 | PROBE-03; schema/criteria NULL; milestone riêng chưa có | REQ-04/05 cần nhóm chốt, không siết dữ liệu khi chưa duyệt. |
| CR-05 | LOW | Một số route truy vấn SQL trực tiếp | STATIC | routes/project_routes.py:284 | Kiến trúc phân tầng chưa tuyệt đối; query vẫn dùng tham số | Ghi đúng kiến trúc hiện trạng; refactor chỉ khi cần, không thêm layer giả. |
| CR-06 | LOW | Import/biến không dùng | LINT | evidence/lint.json | 8 findings F401/F841 trong kiểm tra đã chạy | Không sửa code để giữ phạm vi; không coi là lỗi cú pháp hoặc test thất bại. |
| CR-07 | MEDIUM | Lượt browser có timeout 5 giây | OBSERVED | tests/browser_workspace.py:274 | Attempt1 fail, attempt2 functional wait 15s pass; không JS runtime error | Cần theo dõi nguyên nhân/timing, chưa kết luận race hoặc chậm DB. |
| CR-08 | MEDIUM | Quyền Admin cộng tác khác giữa các thao tác | OBSERVED | routes/collaboration_routes.py; PROBE-02 | comment/note 201; attachment 403 | REQ-02: thống nhất chính sách và hướng dẫn, không tự đổi quyền. |
