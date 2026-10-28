# Báo cáo bổ sung 5 nhóm chức năng — 28/10/2026

Đã sửa và bổ sung tại **D:\UNG DUNG AL_NAM3\Code Chuan**. Đã nạp bản mới vào đúng tiến trình phần mềm đang phục vụ cổng **5000**, kiểm tra máy chủ trả **HEALTHY** và MySQL sẵn sàng. Phiên bản hiện tại: `8db3f99a94378eeba500`; thời điểm nạp: `2026-10-28T18:03:06`.

Mở phần mềm trên các thiết bị cùng mạng tại [http://192.168.1.39:5000](http://192.168.1.39:5000). Địa chỉ Wi-Fi đã được xác minh từ máy chủ trong lượt này. Thiết bị đang mở giao diện cũ cần **tải lại trang một lần** để nhận mã đồng bộ mới. Những lần phát hành tiếp theo có cơ chế phát hiện phiên bản và chờ người dùng hoàn tất biểu mẫu trước khi tải lại.

## 1. Member kéo thả và cập nhật tiến độ thực tế

- Thẻ Kanban hiển thị phần trăm và thanh tiến độ; có nút **Cập nhật tiến độ**, lựa chọn **Chuyển trạng thái** và tay nắm kéo **⠿** khi được quyền sửa.
- Thành viên được cập nhật nhiệm vụ mình phụ trách chính hoặc tham gia hỗ trợ. Nhiệm vụ ngoài quyền hiển thị chỉ xem; backend kiểm tra lại khi nhận thao tác lưu.
- Trên máy tính hỗ trợ kéo thả thẻ; màn hình cảm ứng kéo bằng tay nắm, tự cuộn ngang khi giữ gần cạnh bảng và đưa cột đích vào vùng xem. Lựa chọn trạng thái dùng được ở cả hai cách nhập liệu.
- Tiến độ nhận số nguyên 0–100. 100% đưa nhiệm vụ về Hoàn thành; giảm từ 100% đưa về Đang làm. Giá trị ngoài giới hạn bị chặn.
- Đã sửa bố cục thẻ bị co khi có nhiều nút, xử lý sự kiện hủy cảm ứng ảnh hưởng kéo thả chuột, xung đột với hiệu ứng nghiêng và việc cửa sổ chi tiết có thể tự mở lại sau khi đã đóng trong lúc nhận cập nhật.

## 2. Báo cáo và tải công việc dạng biểu đồ

- **Biểu đồ vòng:** số nhiệm vụ theo năm trạng thái; chú giải mở danh sách nhiệm vụ theo trạng thái đã chọn.
- **Biểu đồ thanh:** tải hiện tại và giờ khả dụng của từng thành viên; tải vượt khả dụng có màu/cảnh báo quá tải.
- Có các số tổng hợp: tổng nhiệm vụ, tỷ lệ việc hoàn thành, tiến độ thực tế trung bình, số nhiệm vụ trễ và số người quá tải.
- Bộ lọc sprint áp dụng lên số liệu, hai biểu đồ và bảng chi tiết cùng phạm vi. Sprint mới từ phiên khác tự xuất hiện trong bộ lọc. Bảng chi tiết có vùng cuộn ngang riêng trên điện thoại.
- Tỷ lệ việc hoàn thành = Done/tổng việc. Tiến độ thực tế trung bình là trung bình phần trăm của các nhiệm vụ trong phạm vi, không phải trung bình theo số giờ. Khi chưa có nhiệm vụ hiển thị 0.
- Biểu đồ dùng tài nguyên của phần mềm, không cần tải thư viện biểu đồ bên ngoài.

## 3. Click tài khoản để xem thông tin đăng nhập

Ảnh đại diện ở góc phải đã là nút mở cửa sổ thông tin: họ tên, mã tài khoản, tên đăng nhập, email, vai trò, trạng thái, ngày tạo và dự án/vai trò hiện tại. Dữ liệu lấy từ phiên đăng nhập của máy chủ. Có Đóng, X, Escape và bấm ngoài cửa sổ; có đường dẫn đến trang năng lực. Không trả mật khẩu/hash mật khẩu/API key vào phần thông tin này.

## 4. Đồng bộ nhiều thiết bị

- Cùng máy chủ, cùng MySQL, cùng bộ giao diện và phân quyền. Bố cục điều chỉnh theo màn hình, các thao tác cần thiết vẫn có theo quyền tài khoản.
- Kiểm tra thay đổi khoảng **5 giây** khi đang xem, và khi quay lại cửa sổ/kết nối lại. Nhận cập nhật nhiệm vụ, tiến độ, thành viên/năng lực, báo cáo, danh sách chọn và thông báo.
- Nếu đang nhập/chỉnh sửa, hiện thông báo chờ và giữ nguyên nội dung. Khi lưu/hủy/đóng, tự nhận dữ liệu đang chờ kể cả máy chủ không phát sinh thay đổi thêm.
- Cửa sổ chi tiết đang xem nhận số mới khi chưa có chỉnh sửa; thao tác đóng không bị một phản hồi đang chờ làm mở lại.
- Trang và API được yêu cầu lấy dữ liệu mới, tài nguyên có phiên bản, Service Worker không giữ bản nội dung cũ. Có kiểm tra phiên bản máy chủ để cập nhật giao diện khi phát hành.
- Thanh trạng thái phân biệt đã đồng bộ và mất kết nối. Khi mất mạng, nội dung chưa được máy chủ xác nhận vẫn là nội dung chưa lưu.

Đã kiểm tra phiên trình duyệt độc lập và các kích thước **1366×900, 1024×768, 768×1024, 390×844, 320×740**. Sự kiện chạm được kiểm tra riêng ở màn hình 768 và 390. Đây là kiểm thử trình duyệt/màn hình mô phỏng; không phải tuyên bố đã trực tiếp kiểm mọi mẫu thiết bị vật lý hoặc mọi trình duyệt. Để nhận cùng dữ liệu, thiết bị phải dùng cùng địa chỉ máy chủ và kết nối được tới máy chủ; dự án/bộ lọc đang xem có thể được chọn riêng trên từng thiết bị.

## 5. Kỹ năng, mức sẵn sàng, năng lực, tải và dữ liệu AI

- Thêm trang **Thành viên & Năng lực** trong menu cho cả member và PM. Có tìm thành viên/kỹ năng, thông tin khả dụng/tải/cảnh báo và liên kết tới nhiệm vụ.
- Member có **Cập nhật năng lực của tôi** và chỉ sửa thông tin của mình. PM có nút cập nhật ở thành viên khác trong dự án. Năng lực được lưu riêng theo từng dự án, thao tác được ghi nhật ký.
- Kỹ năng nhập theo danh sách; mức sẵn sàng 0–100%; năng lực là số giờ/sprint. Ví dụ 10h × 50% = 5h khả dụng. Tải tự tính từ tổng ước lượng nhiệm vụ chưa Hoàn thành, gồm việc phụ trách/hỗ trợ; mỗi người được tính đủ ước lượng nhiệm vụ tham gia.
- Form nhiệm vụ làm rõ trường **Nhãn / Kỹ năng cần cho nhiệm vụ**. PM bổ sung mô tả, nhãn/kỹ năng, ước lượng, hạn và sprint để AI có dữ liệu đối chiếu.
- Trong **Trợ lý AI → Gợi ý phân công**, có liên kết cập nhật năng lực và vùng xem trước thông tin nhiệm vụ/các ứng viên. Khi tạo gợi ý, backend lấy lại dữ liệu mới nhất của nhiệm vụ/sprint/dự án; không dùng dữ liệu xem trước đã cũ làm nguồn quyết định.
- Đã kiểm tra kỹ năng cập nhật, giờ khả dụng và tải đi vào đường tạo prompt của adapter Gemini. Kết quả đề xuất có ứng viên/lý do/cảnh báo và không tự sửa người được phân công; PM quyết định cuối cùng.

## Kiểm thử và kết quả

| Bộ kiểm tra | Kết quả cuối | Nội dung |
|---|---:|---|
| Backend SQLite tạm | **235/235 đạt** | Có 14 ca mới về quyền member/supporter, tiến độ, tự cập nhật năng lực, PM, phạm vi dự án, báo cáo/sprint, tài khoản, phiên bản và cache. |
| Giao diện chức năng mới | **21/21 nhóm đạt** | Kéo thả chuột/cảm ứng, tiến độ, profile, năng lực, biểu đồ, AI nhận dữ liệu, hai phiên, offline/reconnect, 5 kích thước, nâng phiên bản giữ nội dung. |
| Hồi quy giao diện tổng thể | **26/26 nhóm đạt** | Đăng nhập/vai trò, dự án, cộng tác, AI/Gemini mô phỏng và dự phòng, nhiều màn hình/cảm ứng. |
| Hồi quy các lỗi bản nháp/admin vừa sửa | **18/18 nhóm đạt** | Xóa/hủy xóa tài khoản, nút xác nhận, hủy/X/Escape/nền ngoài, modal trên màn hình nhỏ. |
| Rà mã F/E9, cú pháp JS và diff | **Đạt** | Các tệp Python thay đổi; toàn bộ mã JavaScript theo bộ kiểm tra cú pháp, không có lỗi JS trong kịch bản trình duyệt. |
| Nạp máy chủ | **Đạt** | Tiến trình đúng thư mục, cổng 5000; health MySQL; HTTP qua IP Wi-Fi cùng mã phiên bản. |

Các ca chức năng dùng **SQLite tạm, dữ liệu kiểm thử và phản hồi Gemini mô phỏng**; không gửi email thật hoặc gọi Gemini thật trong lượt này. Kiểm tra máy chủ đang vận hành chỉ là kiểm tra sẵn sàng qua health; không gộp thành 235 ca đã chạy trên MySQL. Dữ liệu dùng vẽ trong ảnh là dữ liệu QA.

Các lỗi phát hiện khi chạy lần đầu đã được sửa và chạy lại: sự kiện kéo thả/chạm, giữ bố cục thẻ, phản hồi đồng bộ mở lại modal đã đóng, và cập nhật đang chờ sau khi hủy form. Một số điều chỉnh chỉ thuộc bộ kiểm thử: tọa độ kéo phải nằm trong vùng hiển thị, định dạng số 29 và 29.0, cập nhật hợp đồng `/api/sync` thêm mã phiên bản. Kết quả ở bảng trên là lượt cuối sau sửa, không lấy kết quả thất bại ban đầu làm kết quả hoàn thành.

## Vị trí mã và cách dùng nhanh

| Nhóm | Tệp chính trong thư mục Code Chuan |
|---|---|
| Kanban/tiến độ | `routes/task_routes.py`, `static/js/kanban.js`, `static/css/kanban.css`, `templates/kanban.html`, `static/js/effects_3d.js` |
| Biểu đồ | `routes/report_routes.py`, `services/report_service.py`, `templates/reports.html`, `static/js/reports.js` |
| Thành viên/năng lực | `routes/project_routes.py`, `services/project_member_service.py`, `templates/team.html`, `static/js/team.js` |
| Tài khoản/đồng bộ | `templates/base.html`, `static/js/main.js`, `routes/sync_routes.py`, `services/app_version_service.py`, `app.py`, `static/sw.js` |
| Dữ liệu xem trước AI | `templates/ai_assistant.html`, `static/js/ai.js` |
| Bố cục chung | `static/css/workspace.css` |
| Kiểm thử | `tests/test_workspace_enhancements.py`, `tests/browser_workspace.py`, cập nhật kiểm tra hợp đồng trong `tests/test_requirement_repairs.py` |

Các chức năng này dùng những trường dữ liệu hiện có; không thêm bảng hay đổi cấu trúc DB trong lượt này. Ứng dụng tiếp tục dùng MySQL khi vận hành. Các thay đổi có sẵn từ trước được giữ lại.

1. Tải lại trang đang mở một lần; trên thiết bị khác cùng mạng mở [http://192.168.1.39:5000](http://192.168.1.39:5000).
2. Member vào **Thành viên & Năng lực → Cập nhật năng lực của tôi**; PM rà/cập nhật nhóm.
3. PM bổ sung thông tin nhiệm vụ và mở **AI → Gợi ý phân công** để xem dữ liệu và tạo đề xuất.
4. Member cập nhật nhiệm vụ được giao/hỗ trợ trên Kanban; mở **Báo cáo & Tải việc** để xem số liệu/biểu đồ.

## Minh chứng kèm theo

- [Hướng dẫn sử dụng](Huong_dan_Member_bieu_do_dong_bo.md)
- [Bảng 21 nhóm kiểm tra giao diện](Ket_qua_21_nhom_kiem_thu_Member_va_dong_bo.csv)
- [Biểu đồ trên máy tính](qa-workspace/reports-desktop.png)
- [Biểu đồ trên điện thoại](qa-workspace/reports-phone.png)
- [Năng lực thành viên trên điện thoại](qa-workspace/team-phone.png)
- [Thông tin tài khoản trên màn hình nhỏ](qa-workspace/profile-small-phone.png)
- [Kanban/thao tác member từ bộ hồi quy](qa-screenshots/kanban-phone.png)

Gói `Minh_chung_Member_Bieu_do_Dong_bo_28-10-2026.zip` chứa báo cáo, hướng dẫn, bảng kiểm tra, JSON kết quả, kiểm tra máy chủ và ảnh minh chứng.
