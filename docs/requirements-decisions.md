# Quyết định có căn cứ và mục chờ nghiệm thu

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

| Mã | Quyết định/phạm vi | Căn cứ | Trạng thái |
| --- | --- | --- | --- |
| C01 | Giữ nguyên ứng dụng trong lượt hồ sơ | Yêu cầu hiện tại được chủ hệ thống xác nhận “hãy thực hiện nó” | ÁP DỤNG cho phạm vi thao tác |
| C02 | Gemini được ưu tiên, local fallback khi lỗi | Các yêu cầu và triển khai trước trong cuộc trao đổi | ĐÃ CÓ trong mã, không cấu hình lại |
| C03 | Gợi ý số người linh hoạt và tuyển thêm người | Chủ hệ thống yêu cầu cần 5 người, tìm backend chưa cần chọn nhiệm vụ | ĐÃ CÓ; mở rộng FR-14 so với URD |
| C04 | Nguồn ứng viên toàn hệ thống và tải tổng hợp | Chủ hệ thống yêu cầu hiển thị mọi Member; code chỉ trả số liệu tổng hợp công việc ngoài dự án | ĐÃ CÓ; không công bố nội dung nhiệm vụ ngoài quyền |
| C05 | PM xem/khôi phục chỉ dự án mình lưu trữ; Admin tất cả | Yêu cầu trực tiếp trong cuộc trao đổi | ĐÃ CÓ; khác quyền người tạo dự án |
| C06 | Member cập nhật % và đổi giữa các cột | Yêu cầu trực tiếp; backend giữ phần trăm, Done=100, mở lại=0 | ĐÃ CÓ; trạng thái không tự suy 10%/80% |
| C07 | Sinh hồ sơ trung thực, không ký thay nhóm | Thỏa thuận bổ sung sau triển khai đã được chấp thuận | ÁP DỤNG; Human Gate học thuật vẫn PENDING |

Không dùng tên D01–D08 trong hướng dẫn làm bằng chứng rằng nhóm đã ký tám quyết định đó. Không tìm thấy bảng D01–D08 đã duyệt trong URD hiện có. Các quyền quan sát từ mã được ghi là AS IMPLEMENTED, không đồng nhất với phê duyệt tài liệu gốc. Xem REQ-01/02/12 và [human-verification.md](human-verification.md).
