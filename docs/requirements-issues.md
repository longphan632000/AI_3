# Các điểm cần làm rõ và sai lệch hiện trạng

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

| Mã | Chủ đề | Bằng chứng/khác biệt | Xử lý hiện tại |
| --- | --- | --- | --- |
| REQ-01 | UN-08/UN-09 và D01–D08 | URD L0128–0137 có UN-08 là lịch sử AI; hướng dẫn thực hành yêu cầu UN-08 báo cáo đã xác nhận và UN-09 lịch sử. URD hiện tại không có bảng quyết định D01–D08. | Giữ ID nguồn, không tự tạo UN-09 hoặc phê duyệt D01–D08; nhóm chốt khi nghiệm thu. |
| REQ-02 | Quyền UC007, UC008, UC012 | Bảng UC ghi “Tất cả” cho lịch sử; đặc tả UC012 ghi Admin/PM. UC007 có quyền khác theo thao tác: Admin ghi bình luận/ghi chú qua API được, POST attachment bị chặn; Viewer chỉ đọc. | Tài liệu hiện trạng ghi đúng backend; phần diễn giải URD cần nhóm xác nhận. |
| REQ-03 | FR-14 và dữ liệu ngoài dự án | URD yêu cầu 1–3 người, dữ liệu thuộc dự án. Yêu cầu mới của chủ hệ thống đã cho phép số người 1–100, tuyển backend và hồ sơ/tải tổng hợp nhân sự toàn hệ thống. | Áp dụng quyết định C03/C04 của cuộc trao đổi; giữ kín nội dung nhiệm vụ dự án khác; đánh dấu mở rộng so với URD. |
| REQ-04 | Ngày và ước lượng | Từ điển URD yêu cầu ngày dự án/hạn nhiệm vụ NOT NULL, ước lượng >0; schema hiện tại cho NULL ngày, ước lượng >=0. FR-11 lại yêu cầu cảnh báo thiếu ước lượng. | Giữ hiện trạng; cần chốt quy tắc bắt buộc trước thay đổi dữ liệu. |
| REQ-05 | Sprint và mốc độc lập | Mã có sprint ngày bắt đầu/kết thúc/tiêu chí; không có bảng hoặc API milestone độc lập. completion_criteria có thể trống. | Ghi hỗ trợ Sprint và mốc thời gian của Sprint; chưa tuyên bố đủ quản lý milestone độc lập. |
| REQ-06 | FR-16 nhắc sắp hạn/người nhận | Có scan_and_create_deadline_notifications; worker định kỳ hiện chỉ gọi quét email trễ. Scanner gửi chính/hỗ trợ; chưa chứng minh lịch “ngày trước hạn một lần” hoặc mọi PM nhận đúng sự kiện. | PARTIAL; cần nhóm quyết định cách nhắc và người nhận; lượt này không sửa luồng đang dùng. |
| REQ-07 | NFR-01 thời gian AI | Mục tiêu URD khoảng 30 giây; lớp AI có budget tổng mặc định 180 giây và budget primary riêng 30 giây. | Mục tiêu 30 giây cho toàn yêu cầu chưa được nghiệm thu; ghi riêng thời gian API và tổng fallback. |
| REQ-08 | NFR-03 kết nối mã hóa | Máy chủ kiểm tra ở HTTP nội bộ; HTTPS và Secure cookie phụ thuộc môi trường triển khai. | Chưa đạt minh chứng mã hóa toàn tuyến; giữ cấu hình hiện tại theo yêu cầu bảo toàn. |
| REQ-09 | NFR-05/NFR-10 vận hành | Có bằng chứng MySQL cũ về restore/10.000 nhiệm vụ nhưng không chạy lại ở lượt hồ sơ; chưa có bằng chứng lịch backup vận hành thường xuyên. | HISTORICAL hoặc NOT RUN; không đổi thành kết quả mới. |
| REQ-10 | FR-15 phiên bản prompt | ai_assistant_service lưu prompt_version v1.0 cố định dù prompt đã thay đổi theo chế độ. | Lịch sử có trường phiên bản nhưng chưa quản lý phiên bản phản ánh nội dung; chưa đo A/B hai prompt. |
| REQ-11 | Sửa bản nháp gợi ý >3 người | edit_ai_draft gọi validator chỉ với task_type, không truyền staffing_v2/requested_count; validator nhánh mặc định chỉ chấp nhận 1–3 ID. | Đã tái hiện trên SQLite (PROBE-01): lưu draft 5 người không đổi nội dung chuyển từ draft sang needs_verification. Ghi defect, không sửa ứng dụng trong lượt hồ sơ. |
| REQ-12 | Human Gate và đóng góp con người | Hai commit hiện có không chứng minh đã phê duyệt lần lượt các Gate trước triển khai; bảng phân công URD là phân công dự kiến. | Các checklist nghiệm thu để PENDING; nhóm điền người/ngày/minh chứng thực tế, không ký thay. |

## Metadata học phần cần nhóm chốt

URD ghi môn Ứng dụng trí tuệ nhân tạo, trong khi hướng dẫn thực hành/README cũ ghi Phân tích thiết kế hệ thống. Hồ sơ mới dùng tên hệ thống/Đề tài 33; nhóm cần chốt tên học phần, hình thức bìa và người ký trước khi nộp. Không tự đổi nội dung hai nguồn Word.
