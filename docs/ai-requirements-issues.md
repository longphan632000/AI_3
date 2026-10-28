# Điểm còn thiếu hoặc mâu thuẫn AI

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

| Issue | Nội dung | Trạng thái |
| --- | --- | --- |
| REQ-01 | UN-08/UN-09 và D01–D08 — URD L0128–0137 có UN-08 là lịch sử AI; hướng dẫn thực hành yêu cầu UN-08 báo cáo đã xác nhận và UN-09 lịch sử. URD hiện tại không có bảng quyết định D01–D08. | Giữ ID nguồn, không tự tạo UN-09 hoặc phê duyệt D01–D08; nhóm chốt khi nghiệm thu. |
| REQ-02 | Quyền UC007, UC008, UC012 — Bảng UC ghi “Tất cả” cho lịch sử; đặc tả UC012 ghi Admin/PM. UC007 ghi “Tất cả” nhưng code chỉ cho PM/Member ghi; Admin/Viewer chỉ đọc theo quyền. | Tài liệu hiện trạng ghi đúng backend; phần diễn giải URD cần nhóm xác nhận. |
| REQ-03 | FR-14 và dữ liệu ngoài dự án — URD yêu cầu 1–3 người, dữ liệu thuộc dự án. Yêu cầu mới của chủ hệ thống đã cho phép số người 1–100, tuyển backend và hồ sơ/tải tổng hợp nhân sự toàn hệ thống. | Áp dụng quyết định C03/C04 của cuộc trao đổi; giữ kín nội dung nhiệm vụ dự án khác; đánh dấu mở rộng so với URD. |
| REQ-07 | NFR-01 thời gian AI — Mục tiêu URD khoảng 30 giây; lớp AI có budget tổng mặc định 180 giây và budget primary riêng 30 giây. | Mục tiêu 30 giây cho toàn yêu cầu chưa được nghiệm thu; ghi riêng thời gian API và tổng fallback. |
| REQ-10 | FR-15 phiên bản prompt — ai_assistant_service lưu prompt_version v1.0 cố định dù prompt đã thay đổi theo chế độ. | Lịch sử có trường phiên bản nhưng chưa quản lý phiên bản phản ánh nội dung; chưa đo A/B hai prompt. |
| REQ-11 | Sửa bản nháp gợi ý >3 người — edit_ai_draft gọi validator chỉ với task_type, không truyền staffing_v2/requested_count; validator nhánh mặc định chỉ chấp nhận 1–3 ID. | Cần kiểm tra bổ sung trên SQLite; nếu xác nhận lỗi thì ghi defect, không sửa ứng dụng trong lượt hồ sơ. |
| REQ-12 | Human Gate và đóng góp con người — Hai commit hiện có không chứng minh đã phê duyệt lần lượt các Gate trước triển khai; bảng phân công URD là phân công dự kiến. | Các checklist nghiệm thu để PENDING; nhóm điền người/ngày/minh chứng thực tế, không ký thay. |
