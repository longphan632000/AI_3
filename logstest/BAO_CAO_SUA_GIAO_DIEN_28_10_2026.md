# Kết quả sửa giao diện và kiểm thử — 28/10/2026

Đã sửa trực tiếp tại **D:\UNG DUNG AL_NAM3\Code Chuan**. Ba vấn đề trong ảnh đã có cách xử lý và được kiểm thử bằng thao tác trình duyệt trên SQLite tạm. Không xóa tài khoản hoặc sửa bản nháp trong cơ sở dữ liệu vận hành của bạn.

## Những thay đổi đã hoàn thành

| Vấn đề | Nguyên nhân xác minh được | Cách xử lý hiện tại |
|---|---|---|
| Admin không có nút xóa tài khoản | Đã có API xóa, bảng người dùng chưa có nút gọi | Thêm **Xóa tài khoản**, hỏi xác nhận, làm mới danh sách; hủy thì giữ nguyên tài khoản. Không tự xóa mình; chặn xóa trưởng nhóm cuối cùng của dự án nếu chưa có người thay thế. |
| Không thấy xác nhận bản nháp AI | Giao diện ẩn nút khi bản nháp có cảnh báo `needs_verification` | Trưởng nhóm luôn thấy trạng thái nút và lý do bị khóa. Bản sạch có thể xác nhận; bản có cảnh báo phải mở chỉnh sửa, đối chiếu nguồn, đánh dấu đã kiểm tra và ghi chú trước khi **Lưu và xác nhận**. Thành viên không có quyền xác nhận. |
| Không thể thoát khi không muốn chỉnh sửa | Nút X chỉ ở đầu cửa sổ, có thể bị cuộn khỏi màn hình; không có nút hủy cuối form | Giữ đầu/cuối cửa sổ trong màn hình, chỉ nội dung ở giữa cuộn. Có **Hủy thay đổi**, X, Escape và bấm nền ngoài. Đóng không lưu không gọi API sửa/xác nhận. |

Thêm riêng **Lưu bản nháp** và **Lưu và xác nhận** để tránh nhầm lẫn giữa lưu để tiếp tục sửa với duyệt chính thức. Cơ chế phiên bản từ chối xác nhận bản cũ bằng HTTP 409 nếu người khác đã sửa. Khi đang lưu, chặn thao tác lặp. Cửa sổ hỗ trợ bàn phím và trả tiêu điểm về nút đã mở.

Trong kiểm thử tổng thể còn phát hiện nút tạo AI có thể nhận click trước khi trang tải xong dữ liệu và gắn xử lý sự kiện. Đã khóa nút lúc khởi tạo, chỉ mở khi sẵn sàng. Đã dọn một câu lệnh không thể chạy tới và một import thừa do kiểm tra mã phát hiện.

## Kết quả kiểm thử thực tế

| Bộ kiểm tra | Kết quả | Phạm vi |
|---|---:|---|
| Backend trên SQLite tạm | **221/221 đạt** | Gồm 212 ca hiện có và 9 ca mới: quyền xóa/xác nhận, giữ liên kết dữ liệu, cảnh báo, phiên bản cũ, lưu riêng, bản đã duyệt không sửa được. |
| Kiểm tra giao diện cho các lỗi mới | **18/18 đạt** | Admin xóa/hủy; bảo vệ trưởng nhóm cuối; lưu/xác nhận; hủy/X/Escape/nền ngoài không làm đổi DB; kiểm tra cửa sổ ở 1366×600, 768×700, 390×640, 320×560. |
| Kiểm tra hồi quy trên Edge | **26/26 đạt** | Admin/leader/member; dự án, Kanban, cộng tác, AI mô phỏng, fallback, giao diện nhiều kích thước và thao tác cảm ứng mô phỏng. |
| Kiểm tra mã Python F/E9, cú pháp JS và diff | **Đạt** | Kiểm tra các tệp thay đổi; không có lỗi JavaScript lúc chạy trong các kịch bản trình duyệt. |
| Đối chiếu bổ sung | **7 quan sát được tái hiện** | Đây là bằng chứng về các điểm còn lệch tài liệu, không cộng vào số ca hồi quy đạt. Xem báo cáo đối chiếu riêng. |

Lần chạy hồi quy đầu có lỗi chờ phản hồi do nút tạo AI chưa sẵn sàng; đã sửa nguyên nhân và chạy lại đạt 26/26. Không dùng kết quả thất bại ban đầu làm kết quả cuối.

Các lượt này không gửi email thật, không gọi Gemini thật và không thử MySQL. HTTP Gemini được mô phỏng để kiểm đúng luồng/định dạng và tình huống lỗi. Kết quả Gemini thật/MySQL từ các lần trước được phân biệt rõ trong báo cáo đối chiếu; không tính là chạy lại hôm nay.

## Tệp đã sửa trong lượt này

| Tệp nguồn | Nội dung |
|---|---|
| `templates/admin.html` | Nút xóa, xác nhận và tự bảo vệ tài khoản admin đang dùng. |
| `services/account_service.py` | Chặn xóa trưởng nhóm cuối khi chưa có người thay; dọn import thừa. |
| `templates/ai_assistant.html` | Trạng thái xác nhận và cửa sổ có nút hủy/lưu/lưu xác nhận; khóa nút tạo AI trước khởi tạo. |
| `static/css/ai.css` | Đầu/cuối cửa sổ cố định, vùng cuộn và bố cục điện thoại. |
| `static/js/ai.js` | Hiển thị quyền/trạng thái, lưu/xác nhận theo phiên bản, hủy không ghi dữ liệu, bàn phím, khởi tạo an toàn. |
| `services/ai_confirmation_service.py` | Kiểm tra phiên bản người dùng vừa xem trước khi xác nhận. |
| `routes/ai_routes.py` | Nhận/kiểm tra phiên bản; trả 409 khi xung đột; trả phiên bản sau lưu; bỏ câu lệnh dư. |
| `services/ai_assistant_service.py` | Trả phiên bản ban đầu của bản nháp cho giao diện. |

Thêm `tests/test_ui_actions.py`, `tests/browser_ui_repairs.py`, `tests/run_alignment_audit.py`; báo cáo và ảnh minh chứng nằm trong `logstest/qa-ui-repairs/` và các tệp `logstest/qa-*.json` tương ứng. Các thay đổi có sẵn từ trước trong dự án được giữ lại.

## Cách sử dụng sau sửa

1. Mở Admin → danh sách tài khoản → **Xóa tài khoản** → đọc và xác nhận hoặc hủy.
2. Trưởng nhóm mở bản nháp AI → **Chỉnh sửa bản nháp**. Chọn **Lưu bản nháp** để sửa tiếp; chọn **Lưu và xác nhận** khi đã đối chiếu. Nếu có cảnh báo, phải đánh dấu đã xử lý và ghi chú nguồn.
3. Nếu không muốn đổi nội dung: **Hủy thay đổi**, X hoặc Escape. Nội dung đã lưu trước đó được giữ nguyên.

Nếu ứng dụng đang chạy ở chế độ không tự nạp mã, khởi động lại phần mềm rồi tải lại trang để nhận thay đổi. Các ảnh trong gói minh chứng được chụp trên dữ liệu QA tạm.

Xóa tài khoản là xóa vĩnh viễn. API có sẵn chuyển một số tác giả sang admin để giữ liên kết dữ liệu; báo cáo đối chiếu đã ghi rõ hạn chế truy vết này. Nếu mục đích chỉ là ngừng truy cập, nút Khóa hiện có vẫn phù hợp.
