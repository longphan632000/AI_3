# Hướng dẫn tiến độ, lưu trữ và gợi ý nhân sự

## Member cập nhật thực tế

Vào Bảng Kanban, nhập **% thực tế** ngay trên nhiệm vụ được giao hoặc được phân công hỗ trợ, rồi bấm **Lưu %**. Bấm **Hủy** để bỏ phần đang nhập. Giá trị hợp lệ là số nguyên 0–100.

Kéo thẻ giữa các cột bằng chuột; trên màn hình cảm ứng kéo bằng nút ⠿. Có thể dùng ô **Chuyển trạng thái**. Chuyển sang Hoàn thành đặt 100%; nhập 100% cũng chuyển sang Hoàn thành. Khi mở lại nhiệm vụ đã hoàn thành sang cột khác, phần trăm trở về 0 để nhập lại tiến độ hiện tại. Các chuyển cột còn lại giữ nguyên phần trăm đã lưu. Nếu đang sửa phần trăm, cần lưu hoặc hủy trước khi chuyển cột.

## Dự án lưu trữ

Bấm **Dự án đã lưu trữ → Xem chi tiết**. Trang chi tiết có thông tin dự án, người/thời điểm lưu trữ, thành viên, thống kê và nhiệm vụ. Dữ liệu lưu trữ chỉ xem.

Admin xem và khôi phục mọi dự án. PM chỉ xem/khôi phục dự án chính mình đã trực tiếp chuyển sang lưu trữ, kể cả khi người khác tạo dự án. Người tạo hoặc PM cùng dự án không tự có quyền này. Quyền cũng áp dụng cho lịch sử AI và thông báo liên quan. Dự án cũ được xác định người lưu trữ bằng nhật ký; nếu không có bằng chứng thì chỉ Admin có quyền. Khôi phục giữ trạng thái trước lưu trữ khi có dữ liệu; không tự khôi phục các nhiệm vụ đã lưu trữ riêng.

## Tìm và chọn ứng viên

Vào **Trợ lý AI → Gợi ý Phân công Nhiệm vụ**. Mặc định nguồn ứng viên là toàn bộ nhân sự đang hoạt động trong hệ thống, gồm người ngoài dự án. Không cần chọn thành viên trước. Tài khoản Admin, tài khoản bị khóa/chưa duyệt và người chỉ có vai trò xem trong dự án không nằm trong nguồn phân công. Danh sách phân trang 12 người; dùng **Trang sau** để xem hết và vuốt ngang bảng trên màn hình hẹp. Bộ lọc tên/kỹ năng chỉ lọc phần hiển thị, không thu hẹp dữ liệu AI xếp hạng.

- Phân công nhiệm vụ: chọn nhiệm vụ và số người cần gợi ý (1–100). Nhập **Tôi cần 5 người backend** cũng được; số người trong câu sẽ được ưu tiên hơn ô số lượng.
- Thêm người vào dự án: chọn **Tìm người bổ sung vào dự án**, nhập **tôi cần backend** rồi tạo gợi ý; không cần chọn nhiệm vụ. Nếu không chọn nhiệm vụ mà nhập nhu cầu, giao diện tự chuyển sang tìm người bổ sung.
- Kết quả có lý do dựa trên kỹ năng đã khai báo, giờ khả dụng, tải và việc trễ. Nếu không đủ 5 người đáp ứng điều kiện, hệ thống báo thiếu thay vì bịa thêm ứng viên.
- Người ngoài dự án: bấm **Chọn thêm vào dự án**, sau đó **Thêm người đã chọn** và xác nhận. Hồ sơ mới nhất được sao chép vào thông tin thành viên dự án. Không tự giao nhiệm vụ.
- Người đã trong dự án: bấm **Chọn phân công** để mở biểu mẫu nhiệm vụ đã điền ứng viên; bấm **Lưu thay đổi** mới thực hiện giao việc. Có thể hủy.

## Khai báo năng lực

Member/PM bấm biểu tượng tài khoản → **Hồ sơ năng lực chung**, hoặc dùng nút cập nhật hồ sơ chung trong trang **Thành viên & Năng lực**. Khai báo kỹ năng, mức sẵn sàng và số giờ năng lực. Hồ sơ chung dùng để PM tìm người ngoài dự án. Thông tin năng lực riêng từng dự án vẫn được cập nhật tại trang Thành viên & Năng lực.

Nếu chưa có hồ sơ chung, hệ thống dùng thông tin năng lực đã khai báo trong dự án và hiện cảnh báo; nếu chưa từng khai báo thì kỹ năng để trống, mặc định 100%/40 giờ được ghi rõ là cần xác minh. AI không tự tạo kỹ năng.

Tải được tính từ giờ ước lượng của nhiệm vụ chưa hoàn thành trong mọi dự án đang hoạt động, gồm cả vai trò hỗ trợ, không đếm trùng một người trong một nhiệm vụ. Đây là tải ước lượng công việc đang mở, không phải bảng chấm công hoặc dự báo theo lịch tuần. Các việc chưa ước lượng được cảnh báo. Chỉ chia sẻ tổng giờ/số việc trễ cho nguồn ứng viên, không đưa tiêu đề/nội dung nhiệm vụ dự án khác vào bảng này. Giờ khả dụng = năng lực × mức sẵn sàng; với người trong dự án, lấy giới hạn thấp hơn giữa hồ sơ chung và năng lực riêng dự án.

## Đồng bộ thiết bị

Các thiết bị phải truy cập cùng máy chủ: **http://192.168.1.39:5000** khi cùng mạng và địa chỉ máy chủ không đổi. `127.0.0.1` trên điện thoại là chính điện thoại, không phải máy chủ. Mỗi thiết bị đăng nhập tài khoản được cấp.

Dữ liệu dùng chung MySQL và kiểm tra thay đổi khoảng 5 giây khi trang hoạt động/có kết nối. Trang nhận cùng bản giao diện và chức năng theo quyền; bố cục thích ứng kích thước màn hình. Các biểu mẫu đang nhập được giữ lại, có thông báo dữ liệu mới và cập nhật sau khi lưu/hủy; tạo gợi ý luôn lấy lại dữ liệu mới từ máy chủ. Sau lần cập nhật này, tải lại trang đang mở nếu cần để nhận bản mới.

Đã kiểm tra 5 kích thước màn hình và các phiên trình duyệt độc lập; chưa trực tiếp kiểm tra mọi thiết bị vật lý/hệ điều hành. Thiết bị mất mạng không thể nhận dữ liệu tức thời.
