# Hướng dẫn người dùng theo vai trò

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

## Đăng nhập và tài khoản

Đăng ký Member/PM chờ Admin duyệt. Admin quản lý trạng thái/role, xem audit và cập nhật/xóa tài khoản theo điều kiện backend; không tự xóa chính mình. Bấm avatar để xem tài khoản hiện tại. PM/Member có Hồ sơ năng lực chung để khai báo kỹ năng/mức sẵn sàng/giờ năng lực; trang Thành viên & Năng lực quản lý năng lực riêng dự án.

## Dự án và nhiệm vụ

Chọn dự án ở đầu trang. PM tạo dự án, thêm người hoạt động, tạo Sprint rồi tạo/phân công nhiệm vụ (chính và hỗ trợ). Member nhập % thực tế trên thẻ và Lưu %/Hủy, hoặc mở chi tiết. Kéo thẻ bằng chuột; cảm ứng dùng nút ⠿ hoặc danh sách Chuyển trạng thái. Chỉ người được giao/hỗ trợ cập nhật; Done=100, mở lại Done=0; lưu/hủy phần trăm đang nhập trước khi chuyển cột.

Bộ lọc cho người, sprint, hạn, trạng thái, ưu tiên và việc trễ. Báo cáo có biểu đồ trạng thái/tải; tỷ lệ Done và % trung bình khác nhau. Tải gồm full ước lượng công việc đang mở, cảnh báo thiếu ước lượng/quá tải; không phải chấm công.

## AI

PM được dùng tóm tắt tuần và gợi ý nhân sự. PM/Member được cấp quyền tạo biên bản từ ghi chú hoặc tệp. AI hiển thị nguồn, warnings và engine. Member chỉ chỉnh draft biên bản của mình; PM là người xác nhận chính thức. Dùng Lưu bản nháp để lưu sửa, Hủy/đóng để bỏ nhập, Xác nhận ở màn hình kết quả theo trạng thái hợp lệ. Bản còn cảnh báo cần đối chiếu nguồn; không tự tin chỉ vì AI viết trôi chảy.

Gợi ý phân công không cần chọn người trước: chọn task hoặc nhu cầu recruitment, nguồn system/project và số người 1–100. “Tôi cần 5 người backend” được nhận số/kỹ năng; thiếu người thì báo thiếu. Xem toàn bộ bảng ứng viên bằng phân trang/tìm kiếm và vuốt ngang nếu hẹp. Chọn thêm người rồi xác nhận thêm; người trong dự án có thể Chọn phân công để mở task đã điền người, chỉ Save mới giao. Gợi ý không tự ghi nhiệm vụ.

## Lưu trữ, thông báo và đồng bộ

Dự án đã lưu trữ có trang chi tiết chỉ xem. Admin xem/khôi phục tất cả; PM chỉ dự án chính họ lưu trữ; không xác định actor thì Admin xử lý. Khôi phục project không tự khôi phục task đã lưu trữ riêng. Thông báo có đánh dấu đọc; SMTP mô phỏng không là mail gửi thật.

Thiết bị phải cùng URL máy chủ; localhost trên điện thoại là điện thoại đó. Dữ liệu được kiểm tra thay đổi khoảng 5s khi trang hoạt động; form đang nhập được giữ lại và báo dữ liệu mới. Bố cục thích ứng màn hình, quyền khác nhau sẽ có nút khác nhau.

## Giới hạn đã ghi nhận

Xem requirements-issues.md, code-review.md và security-review.md trước demo/nghiệm thu. Đặc biệt REQ-11: sửa bản gợi ý trên 3 người cần kiểm tra riêng; không hiểu “test xanh” là đã loại mọi lỗi.
