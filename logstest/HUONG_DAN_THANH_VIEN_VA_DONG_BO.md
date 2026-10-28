# Thành viên, năng lực, biểu đồ và đồng bộ

Các thay đổi ngày 28/10/2026 được bổ sung theo yêu cầu người dùng. Thành viên được cập nhật năng lực của chính mình; PM/Trưởng nhóm được cập nhật năng lực thành viên trong dự án. Đây là bổ sung quyền có chủ đích so với giao diện cũ chỉ dành cho PM.

## Cập nhật công việc

- Vào **Bảng Kanban**. Nhiệm vụ do mình phụ trách hoặc hỗ trợ có tay nắm kéo, lựa chọn trạng thái và nút **Cập nhật tiến độ**.
- Trên máy tính, kéo thẻ sang cột mong muốn. Trên màn hình cảm ứng, kéo bằng tay nắm ⠿; cũng có thể chọn **Chuyển trạng thái** trực tiếp trên thẻ ở mọi thiết bị.
- Chọn **Cập nhật tiến độ**, nhập số nguyên 0–100 rồi **Lưu tiến độ**. Thanh tiến độ và các báo cáo lấy số đã lưu từ máy chủ.
- Tiến độ 100% chuyển nhiệm vụ sang Hoàn thành; giảm từ 100% về dưới 100% đưa nhiệm vụ trở lại Đang làm. Tỷ lệ việc Hoàn thành và tiến độ trung bình là hai chỉ số riêng.
- Nhiệm vụ không được giao/hỗ trợ chỉ hiển thị để xem; máy chủ cũng kiểm tra quyền khi lưu. Người chỉ xem và dữ liệu đã lưu trữ không được thay đổi.

## Dữ liệu để AI phân công

1. Mở **Thành viên & Năng lực** từ menu bên trái.
2. Thành viên chọn **Cập nhật năng lực của tôi**. Nhập kỹ năng, mức sẵn sàng (%) và năng lực (giờ/sprint). PM có thêm nút cập nhật ở các thẻ thành viên khác.
3. Giờ khả dụng = năng lực × mức sẵn sàng / 100. Ví dụ 10 giờ × 50% = 5 giờ khả dụng. Có thể đặt sẵn sàng 0% khi không thể nhận việc.
4. **Tải hiện tại** được tính tự động bằng tổng ước lượng của nhiệm vụ chưa Hoàn thành. Người chính và người hỗ trợ đều được tính đủ giờ của nhiệm vụ tham gia. Tiến độ phần trăm không tự giảm số giờ ước lượng của việc chưa hoàn thành.
5. PM nhập tên/mô tả, nhãn (có thể dùng cho kỹ năng cần thiết như Python, Flask), ước lượng, hạn và sprint khi tạo/sửa nhiệm vụ.
6. Vào **Trợ lý AI → Gợi ý phân công**, chọn nhiệm vụ. Phần dữ liệu bên dưới cho xem thông tin nhiệm vụ và kỹ năng/giờ khả dụng/tải của ứng viên. Khi bấm tạo, backend truy xuất lại dữ liệu mới nhất; AI trả tối đa 3 ứng viên, lý do và cảnh báo quá tải. PM chọn người và phân công qua luồng sửa nhiệm vụ.

Năng lực được lưu theo từng dự án. Đổi năng lực của mình ở dự án A không làm thay đổi năng lực ở dự án B.

## Báo cáo bằng biểu đồ

- Biểu đồ vòng thể hiện số nhiệm vụ theo năm trạng thái. Bấm chú giải để mở danh sách nhiệm vụ tương ứng.
- Biểu đồ thanh so sánh tải hiện tại và giờ khả dụng của từng thành viên; màu cảnh báo thể hiện quá tải. Tên thành viên dẫn tới danh sách nhiệm vụ được phân công.
- Bộ lọc sprint áp dụng đồng thời lên số liệu, biểu đồ và bảng chi tiết. Khi không có nhiệm vụ, hiển thị 0 và trạng thái trống.
- **Tỷ lệ việc hoàn thành** = số nhiệm vụ Done / tổng nhiệm vụ. **Tiến độ thực tế trung bình** = trung bình phần trăm tiến độ của các nhiệm vụ trong phạm vi lọc; đây là trung bình theo số nhiệm vụ, không phải theo số giờ.
- Biểu đồ được vẽ bằng các tài nguyên sẵn có của ứng dụng, không phải tải thư viện biểu đồ từ bên ngoài.

## Tài khoản đang đăng nhập

Bấm biểu tượng/ảnh đại diện ở góc phải để xem họ tên, mã tài khoản, tên đăng nhập, email, vai trò, trạng thái, ngày tạo và vai trò trong dự án hiện tại. Dữ liệu lấy từ phiên đăng nhập ở máy chủ. Có nút Đóng, phím Escape và đường dẫn đến trang năng lực.

## Dùng nhiều thiết bị

- Các thiết bị phải truy cập **cùng máy chủ và cùng cơ sở dữ liệu MySQL**. Ví dụ trên mạng nội bộ: `http://<IP_máy_chủ>:5000`; thay phần trong ngoặc bằng địa chỉ thực của máy chủ. `127.0.0.1` trên điện thoại là chính điện thoại, không phải máy tính chạy phần mềm.
- Phiên đang xem kiểm tra thay đổi khoảng mỗi 5 giây, và kiểm tra lại khi quay lại cửa sổ hoặc có mạng trở lại. Thanh trạng thái cho biết đã đồng bộ hoặc mất kết nối.
- Dữ liệu mới tự cập nhật khi không có nội dung đang sửa. Nếu đang nhập, có thông báo chờ; dữ liệu nhập được giữ lại, rồi cập nhật khi lưu/hủy/đóng. Các thao tác vẫn được kiểm tra quyền tại backend ngay lúc gửi.
- Mỗi thiết bị có thể chọn dự án và bộ lọc đang xem riêng. Dữ liệu nghiệp vụ và phiên bản chức năng dùng chung trên máy chủ; bố cục thích ứng với kích thước màn hình.
- Khi áp dụng bản này, khởi động lại tiến trình phần mềm và tải lại các trang đang mở một lần để nhận mã đồng bộ mới. Những lần triển khai sau: khởi động lại máy chủ bằng bản mã mới; trình duyệt có cơ chế phát hiện phiên bản và tải lại khi người dùng hoàn tất biểu mẫu.
- Khi mất kết nối, nội dung đang nhập còn ở trang hiện tại; thao tác chưa được máy chủ xác nhận chưa được tính là đã lưu. Không có cơ chế âm thầm ghi vào cơ sở dữ liệu riêng của điện thoại.

SQLite chỉ được dùng trong các lượt kiểm thử tạm của thay đổi này. Không chuyển cơ sở dữ liệu vận hành MySQL sang SQLite.
