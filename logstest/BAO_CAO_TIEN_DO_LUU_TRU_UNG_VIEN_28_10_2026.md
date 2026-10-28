# Báo cáo cập nhật tiến độ, lưu trữ và gợi ý phân công — 28/10/2026

Đã tích hợp và cập nhật máy chủ tại **D:\UNG DUNG AL_NAM3\Code Chuan**. Phiên bản: `396983399f12706bcbdf`. Máy chủ khởi động thành công, MySQL sẵn sàng. Đã sao lưu cơ sở dữ liệu riêng trước khi thêm cấu trúc; không đưa bản sao lưu hoặc khóa API vào gói bàn giao.

## Kết quả kiểm thử cuối cùng

| Bộ kiểm thử | Kết quả | Phạm vi |
|---|---:|---|
| Chức năng và phân quyền trên SQLite tạm | 253/253 | Gồm 18 ca mới cho yêu cầu lần này; không thử trên dữ liệu đang dùng |
| Trình duyệt mới | 14/14 nhóm | Toàn bộ ứng viên, yêu cầu 5 người, tuyển backend, chọn/thêm/giao việc, phần trăm, lưu trữ, đồng bộ, 5 kích thước |
| Hồi quy Member/biểu đồ/đồng bộ | 21/21 nhóm | Kéo chuột, kéo cảm ứng, phần trăm, hồ sơ, báo cáo và bảo toàn nội dung đang nhập |
| Hồi quy giao diện chính | 26/26 nhóm | Admin/PM/Member, thao tác thật, bố cục và cảm ứng |
| Hồi quy sửa lỗi tài khoản/bản nháp | 18/18 nhóm | Xóa tài khoản, lưu/hủy/xác nhận, kiểm tra quyền |
| Gemini thật, dữ liệu nhân sự giả lập trên SQLite tạm | 2/2 dùng Gemini thành công | Phân công và tuyển thêm người đều trả đủ 5, HTTP 200, không dùng dự phòng trong lượt cuối |

Tổng 79 nhóm kiểm thử trình duyệt đều đạt, không ghi nhận lỗi JavaScript trong các lượt cuối. Kiểm tra cú pháp JavaScript/HTML nằm trong bộ SQLite; kiểm tra lỗi Python trong các tệp sửa/thêm đạt. Kiểm tra rộng toàn kho còn 8 cảnh báo import/biến không sử dụng ở các tệp cũ ngoài phần sửa lần này; không coi đó là kết quả kiểm tra toàn kho sạch tuyệt đối.

Lần thử Gemini đầu phát hiện thời gian chờ và bước kiểm định cũ chưa phù hợp với kết quả xếp hạng mới. Đã rút gọn đầu ra API thành danh sách ID, đối chiếu lại điều kiện/số lượng và dựng lý do bằng dữ liệu thực. Lượt kiểm tra Gemini cuối thành công cả hai luồng. Vẫn ưu tiên API; bộ dự phòng hoạt động khi API lỗi. Gợi ý không tự thêm thành viên, không tự giao nhiệm vụ.

## Những gì đã thay đổi

1. Thêm nhập/lưu/hủy phần trăm ngay trên thẻ Kanban; tiếp tục hỗ trợ kéo chuột, kéo cảm ứng và chuyển cột bằng danh sách. Không tự đoán 10%/80% khi chỉ thay đổi cột.
2. Thêm người lưu trữ, thời điểm và trạng thái trước lưu trữ. Admin có toàn quyền xem/khôi phục; PM theo đúng người thực hiện lưu trữ. Bổ sung trang chi tiết chỉ xem, siết cả lịch sử AI và thông báo để tránh đọc vòng qua trang khác.
3. Thêm nguồn ứng viên toàn hệ thống, phân trang/tìm kiếm, chọn phạm vi và số lượng 1–100. Câu “cần 5 người” không còn bị chặn ở 3 người. Mặc định vẫn là 3 nếu người dùng không đổi số lượng.
4. Thêm tìm người cho dự án đang có mà không cần chọn nhiệm vụ; hỗ trợ nhận diện các nhóm kỹ năng phổ biến như backend/frontend/kiểm thử/database/devops và một số công nghệ. Điều kiện kỹ năng được đối chiếu theo từ khóa/bằng chứng; mô tả phức tạp ngoài nhóm nhận diện vẫn cần PM kiểm tra.
5. Thêm hồ sơ năng lực chung do chính tài khoản khai báo, làm dữ liệu tìm ứng viên ngoài dự án; tổng hợp tải/việc trễ trên các dự án đang hoạt động, giữ kín nội dung nhiệm vụ của dự án khác.
6. Thêm lựa chọn đưa người vào dự án và mở biểu mẫu giao nhiệm vụ có ứng viên điền sẵn; luôn có bước xác nhận/lưu của PM.
7. Dùng cơ chế đồng bộ và phiên bản chung đã có; bổ sung trang lưu trữ/nguồn ứng viên vào quá trình cập nhật. Cùng chức năng theo quyền, bố cục thích ứng thiết bị, không cam kết mọi màn hình vật lý giống nhau từng điểm ảnh.

Yêu cầu mới về số ứng viên và quyền lưu trữ được áp dụng theo chỉ dẫn mới nhất của bạn, thay cho giới hạn 1–3 người và quy tắc PM cũ trong tài liệu ban đầu.

## Vị trí mã và cơ sở dữ liệu

- `services/staffing_service.py`: nhận nhu cầu/số người, truy xuất/xếp hạng, đối chiếu kết quả và tạo nội dung có bằng chứng.
- `services/member_profile_service.py`: hồ sơ chung và tải tổng hợp, không chia sẻ nội dung nhiệm vụ ngoài dự án.
- `static/js/staffing.js`, `templates/ai_assistant.html`: bảng ứng viên, bộ lọc, lựa chọn và thêm/giao việc.
- `static/js/kanban.js`, `services/task_service.py`: nhập phần trăm, kéo/chuyển cột và bảo vệ nội dung chưa lưu.
- `templates/archived_project.html`, `static/js/archived_project.js`: trang chi tiết lưu trữ.
- `services/project_service.py`, `services/project_member_service.py`, `routes/project_routes.py`: quyền lưu trữ/khôi phục, hồ sơ, nguồn ứng viên và thêm người.
- `services/ai_history_service.py`, `services/notification_service.py`: quyền đọc dữ liệu liên quan dự án lưu trữ.
- Các mô-đun AI (analyzer/retriever/context/prompt/provider/validator/local brain/coordinator) được cập nhật đồng bộ với chế độ gợi ý mới.
- `database/archive_schema.py`, `database/migrations.py`, `database/init_db.py`, `database/operational_schema.py`, `database/schema.sql`: cấu trúc và cập nhật tương thích MySQL/SQLite.
- Bảng mới `member_profiles`; trường dự án mới `archived_by`, `archived_at`, `pre_archive_status`. Dữ liệu lịch sử chỉ được khôi phục người lưu trữ khi có nhật ký chứng minh; không đoán từ người tạo.
- `tests/test_staffing_archive.py`, `tests/browser_staffing_archive.py`, `tests/run_staffing_live.py`: bằng chứng kiểm thử mới; các kịch bản trình duyệt cũ được điều chỉnh để bấm đúng vùng tiêu đề thẻ và chờ lưu xong trước khi kiểm tra.

Tất cả đường dẫn mã trên nằm dưới **D:\UNG DUNG AL_NAM3\Code Chuan**. MySQL đang dùng chỉ được sao lưu, thêm cấu trúc và kiểm tra tình trạng/cấu trúc sau khởi động; kiểm thử ghi dữ liệu đều dùng SQLite tạm. Không chèn các tài khoản QA vào cơ sở dữ liệu đang dùng.

---

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
