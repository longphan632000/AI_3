# Kế hoạch kiểm thử bổ sung hồ sơ

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh hiện trạng, không thay phê duyệt của nhóm.

Mục tiêu: kiểm chứng lại ứng dụng hiện có, bảo toàn source/giao diện/cấu hình và tạo bằng chứng trung thực cho Skill. DB nghiệp vụ không được sửa; dữ liệu ghi chỉ trong SQLite tạm. Không tạo test giả để lấp yêu cầu.

## Phạm vi

FR-01..FR-11: account/session/role/project/member/task/Kanban/Sprint/cộng tác/lọc/thống kê. FR-12..FR-14: ba task AI, sai quyền, source ID, schema, timeout/fallback, nội dung họp dài/tiếng Việt, xác nhận riêng và đề xuất không tự phân công. FR-15..FR-17: lịch sử, thông báo, email mô phỏng/dedup/retry theo phần đã triển khai.

Kịch bản tích hợp: tạo project → thêm người → tạo Sprint/task → phân công chính/hỗ trợ → %/Kanban → dashboard/workload → yêu cầu AI → xem draft/nguồn → PM xác nhận; kịch bản từ chối sai role/project/archiver và version cũ. Browser smoke có cả xác nhận qua giao diện; SQLite có gọi trực tiếp API để kiểm quyền.

## Dữ liệu và ca biên

Fixtures account active/pending/locked/rejected, Admin/PM/Member/Viewer và outsider; ngày đảo/hai cận, project/sprint khác scope, nhiệm vụ chưa ước lượng, tải 0/vượt capacity, % -1/0/100/101, file sai loại/dung lượng/path, người chưa trong dự án, yêu cầu 5 người hoặc không đủ người. Prompt injection/ID bịa phải được đối chiếu bằng các assertion thực tế hiện có; không tuyên bố chống mọi prompt injection.

## Cách chạy và kết luận

Runner SQLite và bốn bộ browser đã có được dùng lại. Expect thời gian UI là điều kiện chờ chức năng, không phải benchmark. Lần workspace timeout được giữ, chạy lại trong harness tăng default wait 15s, không sửa assertions hoặc source test. Lỗi review mới được probe riêng; không đổi expectation thành đúng để làm pass.

Code review/security sau regression, liên kết result/defect. NFR hiệu năng 10.000, backup/restore mới, CVE/pentest, HTTPS và SMTP/Gemini thật: NOT RUN tại lượt này hoặc HISTORICAL nếu có kết quả cũ. Gate cuối do nhóm kiểm tra.
