# Nhu cầu chủ hệ thống và phạm vi hồ sơ

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

Chủ hệ thống đã hoàn thiện phần mềm và yêu cầu thực hiện các Skill để bổ sung hồ sơ thiếu trong docs, bảo toàn chức năng, luồng nghiệp vụ và giao diện. Đây là hoạt động lập hồ sơ hiện trạng sau triển khai, không viết lại lịch sử phát triển.

Nghiệp vụ gốc: quản lý tài khoản, dự án, thành viên, nhiệm vụ/Kanban, Sprint, cộng tác, tra cứu/báo cáo; AI tóm tắt tuần, biên bản họp và gợi ý phân công. Ngoài phạm vi: chấm công, lương, AI tự phân công hoặc tự sửa dữ liệu.

Các yêu cầu mở rộng đã được chủ hệ thống nêu trong cuộc trao đổi: Gemini ưu tiên và AI cục bộ dự phòng; Member nhập phần trăm/kéo thả; biểu đồ báo cáo; hồ sơ tài khoản/năng lực; đồng bộ qua một máy chủ; quyền khôi phục theo người lưu trữ; gợi ý số người linh hoạt và tuyển thêm backend.

Lượt này chỉ thêm/sửa tài liệu, hướng dẫn Skill và bằng chứng kiểm thử. Không thay source ứng dụng, SQL schema/migration, template, JavaScript, CSS, cấu hình môi trường; không sửa dữ liệu MySQL; không phát hành bản mới. Kiểm thử ghi dữ liệu chỉ trong SQLite tạm. Không tự commit/push hoặc phê duyệt Human Gate.
