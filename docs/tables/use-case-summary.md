# Danh sách Use Case

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

| ID | Tên | Tác nhân thực tế | FR | Mức | Mô tả | Issue |
| --- | --- | --- | --- | --- | --- | --- |
| UC001 | Đăng nhập, đăng xuất | người có tài khoản | FR-01 | Bắt buộc | Đăng nhập, đăng xuất và quản lý phiên. | — |
| UC002 | Quản lý tài khoản | Admin | FR-02 | Bắt buộc | Quản lý tài khoản, vai trò và xem nhật ký. | — |
| UC003 | Quản lý dự án | Admin/PM theo thao tác | FR-03 | Bắt buộc | Tạo, xem, sửa, lưu trữ dự án. | — |
| UC004 | Quản lý thành viên | Admin/PM quản lý; Member sửa năng lực của mình | FR-04 | Bắt buộc | Thêm/xóa thành viên, lưu vai trò, kỹ năng, mức sẵn sàng. | — |
| UC005 | Quản lý nhiệm vụ | PM/Member; Admin cập nhật trạng thái và phần trăm | FR-05, FR-06 | Bắt buộc | Tạo, sửa, xóa nhiệm vụ và hiển thị Kanban. | — |
| UC006 | Quản lý Sprint/Mốc | PM quản lý; Admin/Member chỉ xem | FR-07 | Bắt buộc | Tạo, xem, sửa sprint, mốc tiến độ. | — |
| UC007 | Cộng tác | PM/Member; Admin bình luận/ghi chú theo API, đọc tệp; Viewer chỉ xem | FR-08 | Bắt buộc | Bình luận, đính kèm, ghi chú họp. | REQ-02 |
| UC008 | Tra cứu & Báo cáo | người có quyền dự án | FR-09, FR-10, FR-11 | Bắt buộc | Tìm kiếm, lọc, thống kê tiến độ, tải công việc. | REQ-02 |
| UC009 | AI Tóm tắt tiến độ | PM | FR-12 | Bắt buộc | Yêu cầu AI tóm tắt tiến độ tuần từ dữ liệu nhiệm vụ. | — |
| UC010 | AI Sinh biên bản họp | PM/Member được cấp quyền | FR-13 | Bắt buộc | Dùng ghi chú họp để AI tạo biên bản, chỉnh sửa và xác nhận. | — |
| UC011 | AI Gợi ý phân công | PM | FR-14 | Bắt buộc | AI gợi ý người phụ trách theo kỹ năng, tải công việc. | REQ-03/11 |
| UC012 | Lịch sử AI | Admin/PM | FR-15 | Nên có | Lưu lịch sử yêu cầu/kết quả AI, trạng thái xác nhận. | REQ-02/10 |
| UC013 | Nhận thông báo | người liên quan | FR-16, FR-17 | Nên có | Thông báo sự kiện, sắp đến hạn trong ứng dụng; gửi email cho người phụ trách khi nhiệm vụ trễ. | REQ-06 |
