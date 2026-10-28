# Đặc tả tác nhân

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

| Tác nhân | Vai trò | Quyền/hoạt động | Nguồn | Ghi chú |
| --- | --- | --- | --- | --- |
| Admin | Quản lý hệ thống | Tài khoản/vai trò/audit, xem dự án/báo cáo/lịch sử; archive mọi dự án | URD tác nhân + UC002/012; admin_routes, project_service | Không được tạo/xác nhận bản AI chỉ vì là Admin |
| PM | Người chịu trách nhiệm dự án | Quản lý phạm vi dự án; gọi weekly/staffing; tạo/sửa/xác nhận AI | URD UC003–011; request_analyzer | Archive theo C05 |
| Member | Người thực hiện | Cập nhật việc chính/hỗ trợ, cộng tác, tạo/sửa bản meeting của mình | URD UC005/007/010; task_routes, ai_draft_service | Không xác nhận bản chính thức; viewer là quyền dự án hạn chế |
| Dịch vụ AI | Hệ thống hỗ trợ | Nhận context tối thiểu, trả dữ liệu để kiểm định | URD tác nhân AI; provider_service | Không truy cập DB hay quyết định thay con người |
