# Sửa task bị cắt và cập nhật % thực tế trên Kanban

Thực hiện: 2026-10-28T23:59:00.906479+07:00. Đây là lượt sửa tiếp theo sau phản hồi kèm ảnh về bản Kanban gọn.

## Nguyên nhân đã tái hiện

Máy chủ đang giữ HTML cũ trong bộ nhớ, nhưng trình duyệt nhận CSS/JavaScript mới. HTML cũ thiếu `kanban-workspace`, nên `height:0` của bảng bị áp dụng ngoài bố cục flex dự kiến; bảng co xuống khoảng 180px. Kiểu popup cũng áp dụng vào bộ lọc cũ, khiến nó rời vị trí. Vì vậy task và phần %/nút cập nhật bị khuất như ảnh phản hồi.

Đã lưu bản template cũ từ commit `8ac8a77` làm fixture, chạy với tài nguyên mới và tái hiện lỗi trước khi sửa. [Kết quả trước sửa](kanban-visibility-repair/before/browser-results.json), [log](kanban-visibility-repair/before.log).

## Thay đổi

- `static/js/kanban.js`: nhận diện HTML cũ và chuyển các thành phần đang có vào bố cục hiện tại. Giữ nguyên ID, bộ lọc, dữ liệu nhập, phân trang và hàm xử lý. Tương thích cả trang cũ đang được máy chủ giữ và template mới.
- `static/css/kanban.css`: có chiều cao dự phòng khi chưa có wrapper; chỉ áp dụng kiểu bộ lọc popup bên trong đúng panel. Tránh bảng bị ép thấp và bộ lọc bị ẩn nếu các thành phần chưa cùng phiên bản.
- Nút ghi rõ **Cập nhật %**. Bấm để nhập số nguyên 0–100, chọn **Lưu tiến độ**. Thẻ chỉ xem giải thích điều kiện phân công/hỗ trợ thay vì chỉ hiện chữ Chỉ xem.
- `app.py`: bật `TEMPLATES_AUTO_RELOAD` cho các lần chạy ứng dụng tiếp theo để template được kiểm tra lại khi đổi nguồn. Không bật debug và không đổi cấu hình kết nối dữ liệu.
- Bổ sung fixture HTML cũ, chế độ kiểm thử template cũ/mới và một unit test kiểm tra template đã cache có thể đổi theo nguồn.

Routes, services, database/schema, Skill và bộ hồ sơ docs giữ nguyên. Không thay đổi phân quyền: người được giao/hỗ trợ và người quản lý có quyền tương ứng mới được lưu %; task của người khác vẫn được bảo vệ tại backend.

## Kiểm thử sau sửa

| Bộ | Kết quả | Minh chứng |
| --- | --- | --- |
| SQLite unit/tích hợp | **254/254 đạt** | [JSON](qa-results-sqlite.json), [log](kanban-visibility-repair/sqlite.log) |
| HTML cũ + CSS/JS mới | **13/13 nhóm đạt** | [JSON](kanban-visibility-repair/legacy-after/browser-results.json), [log](kanban-visibility-repair/legacy-after.log) |
| HTML mới + CSS/JS mới | **13/13 nhóm đạt** | [JSON](kanban-visibility-repair/current-after/browser-results.json), [log](kanban-visibility-repair/current-after.log) |

Hai chế độ dùng bảng 56 nhiệm vụ, kiểm tra máy tính/tablet/điện thoại từ 1920px đến 320px, các thẻ dài, cuộn riêng từng cột, bộ lọc/phân trang, kéo chuột/cảm ứng, cập nhật từ nhiều phiên, giữ bản nhập chưa lưu và hủy không ghi database. Đã kiểm tra % ngoài phạm vi bị từ chối; % được đọc/lưu từ SQLite thật trong môi trường thử; lưu 100% vẫn đưa nhiệm vụ sang Hoàn thành. Member không được giao/hỗ trợ bị từ chối khi cố cập nhật task khác.

Không có lỗi JavaScript trong hai lượt cuối. Kiểm tra cú pháp JavaScript, Ruff F/E9 cho các tệp kiểm thử liên quan và kiểm tra diff đều đạt. Dữ liệu kiểm thử chỉ nằm trong SQLite tạm; không gọi Gemini/email thật và không tạo dữ liệu thử trong MySQL đang vận hành.

## Bản sửa được phục vụ trên máy chủ hiện tại

Đã đọc lại JavaScript và CSS từ `127.0.0.1:5000` và đối chiếu nội dung: cả hai trả HTTP 200, khớp tệp đã lưu. Health trả HTTP 200, HEALTHY, MySQL sẵn sàng. [Minh chứng tài nguyên đang phục vụ](kanban-visibility-repair/live-assets.json).

**Nhấn Ctrl+F5 tại trang Kanban để nhận bản sửa.** Cơ chế tương thích mới sửa được bố cục HTML cũ mà không cần dừng máy chủ đang chạy. Cấu hình tự nạp template trong Python sẽ có hiệu lực ở lần khởi động ứng dụng bình thường tiếp theo; lượt này không dừng/khởi động lại máy chủ.

Công cụ Computer Use dừng kiểm tra trực tiếp cửa sổ Edge của người dùng vì không xác định được URL hiện tại đủ chắc chắn để thực thi chính sách. Không thao tác thêm trên cửa sổ đó; các kết quả phía trên là Edge tách biệt và SQLite tạm, cùng kiểm tra HTTP tài nguyên hiện tại.

## Cách cập nhật tiến độ

1. Tải lại trang bằng Ctrl+F5.
2. Tìm task mình phụ trách hoặc được thêm làm người hỗ trợ; chọn **Cập nhật %**.
3. Nhập số nguyên 0–100 rồi chọn **Lưu tiến độ**. Có **Hủy** và nút đóng khi không muốn lưu.
4. Nếu thẻ báo chỉ xem, tài khoản hiện tại chưa có quyền sửa task đó. PM có thể phân công người phụ trách/người hỗ trợ qua chức năng sửa nhiệm vụ hiện có; bản sửa này không tự mở rộng quyền của tài khoản.

Ảnh đã kiểm tra: [bảng dùng HTML cũ sau sửa](kanban-visibility-repair/legacy-after/board-desktop.png), [điện thoại nhỏ](kanban-visibility-repair/legacy-after/board-small-phone.png), [PM điện thoại nhỏ](kanban-visibility-repair/legacy-after/board-pm-small-phone.png), [lưu 100% trên điện thoại](kanban-visibility-repair/legacy-after/progress-editor-phone.png).

[Kết quả tổng hợp](kanban-visibility-repair/verification.json). Chưa commit/push lượt sửa này.
