# Những quyền thao tác cần phân biệt

Ghi nhận từ route/service hiện tại, không tạo thêm chính sách hoặc đồng nhất vai trò Admin với mọi quyền nghiệp vụ.

| Thao tác | Admin | PM | Member / Viewer | Nguồn |
| --- | --- | --- | --- | --- |
| Tạo/cập nhật/lưu trữ dự án | Có theo route | Có theo scope | Không | project_routes.py |
| Xem/khôi phục dự án lưu trữ | Mọi dự án | Chỉ archived_by của mình | Không | project_service.py, archive-details/restore |
| Quản lý thành viên/năng lực dự án | Có theo route | Có theo scope | Member sửa năng lực của mình; Viewer không ghi | project_routes.py |
| Hồ sơ năng lực chung | Không nằm trong nguồn ứng viên | Chính mình | Member chính mình; user_id payload không cấp quyền | professional-profile API |
| Tạo task, sửa đầy đủ/phân công | Không tạo task | PM của dự án | Không | task_routes.py; quyền theo từng endpoint |
| Cập nhật trạng thái/% task | Có theo route/capability | Có theo scope | Member chỉ việc chính/hỗ trợ; Viewer không | task_routes.py task_capabilities/status/progress |
| Tạo/sửa Sprint | Bị từ chối | PM của dự án | Chỉ xem theo scope | sprint_routes.py |
| Bình luận/ghi chú | PROBE-02: được ghi qua API | Được theo scope | Member theo scope; Viewer không ghi | collaboration_routes.py |
| Thêm attachment | Bị từ chối | Được theo scope | Member được theo scope; Viewer không ghi | collaboration_routes.py |
| Đọc attachment/báo cáo | Theo scope quản trị | Theo scope dự án | Theo scope và project role | collaboration/report routes |
| Gọi weekly/staffing AI | Bị từ chối | PM của dự án | Bị từ chối | ai_request_analyzer.py |
| Tạo meeting draft | Bị từ chối | Theo scope | Member được cấp quyền | ai_request_analyzer.py |
| Chỉnh draft chưa confirmed | Không | Theo scope | Member chỉ meeting draft do mình tạo; Viewer không | ai_draft_service.py |
| Xác nhận AI chính thức | Bị từ chối | PM, status/version hợp lệ | Bị từ chối | ai_confirmation_service.py |
| Xem lịch sử AI | Có | Scope đang hoạt động / archive do mình lưu | Không | ai_history_service.py |
| Staffing preview | Có theo scope | Theo scope | Không | project_routes.py staffing-preview |

Đây là bảng các khác biệt đáng chú ý, không là ACL hình thức bao phủ mọi endpoint. Middleware vẫn chặn dữ liệu archived/Viewer khi ghi; Admin không được suy ra quyền một thao tác chỉ từ quyền thao tác khác. Các điểm khác URD phải qua REQ-02/Human Gate, không tự thay quyền trong đợt hồ sơ.
