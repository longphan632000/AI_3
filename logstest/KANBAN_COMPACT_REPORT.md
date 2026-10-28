# Tối ưu bảng Kanban khi có nhiều nhiệm vụ

> Cập nhật sau phản hồi: [bản sửa task bị cắt và cập nhật %](KANBAN_VISIBILITY_REPAIR.md) bổ sung tương thích HTML cũ. Bản sửa tiếp theo nhận được bằng Ctrl+F5, không còn phụ thuộc vào bước khởi động lại được nêu trong báo cáo lịch sử bên dưới.

Thời điểm: 2026-10-28T23:40:48.650060+07:00. Bản nền: `8ac8a77`.

## Kết quả

- Thẻ chỉ hiện mã/tên nhiệm vụ, tối đa hai nhãn kèm số nhãn còn lại, ưu tiên/trễ hạn, giờ ước lượng, người phụ trách, % thực tế và nút **Cập nhật**. Tên dài được thu gọn hai dòng; tên đầy đủ vẫn đọc được trong chi tiết.
- Bấm **Cập nhật** để mở bảng chi tiết có ô nhập %, **Lưu tiến độ**, chọn trạng thái, **Lưu trạng thái**, **Hủy** và nút đóng. Escape đóng bảng; nội dung chưa lưu không ghi vào database.
- Năm cột có chiều cao bằng nhau, mỗi cột cuộn riêng. Tiêu đề/số lượng cột luôn ở trên; danh sách nhiều task không kéo trang dài theo số lượng task.
- Khi kéo chuột hoặc cảm ứng sát mép, bảng tự cuộn ngang và cột tự cuộn dọc. Cuộn vẫn hoạt động khi ngón tay sát mép màn hình ngoài phần đệm của bảng.
- Giữ vị trí cuộn khi dữ liệu tự làm mới. Tìm kiếm, bộ lọc, sắp xếp và phân trang vẫn dùng API và giới hạn 50 task/trang hiện có.
- Bộ lọc được gom vào **Bộ lọc**. PM/Admin có menu **Dự án** trên trang Kanban, chứa các nút quản lý mà vai trò hiện có được phép dùng. PM truy cập **Nhiệm vụ đã lưu trữ** trong **Bộ lọc**. Các trang khác giữ bố cục hiện có.
- Trên điện thoại nhỏ, nút tạo nhiệm vụ hiển thị **+**, có nhãn truy cập và tiêu đề giải thích. Kiểm tra cả member và PM ở màn hình rộng 320px.

## Phạm vi mã và dữ liệu

Chỉ sửa ba tệp ứng dụng:

1. `templates/kanban.html`: bố cục bảng, bộ lọc/menu dự án, phân trang và nút đóng chi tiết.
2. `static/css/kanban.css`: thẻ gọn, chiều cao bảng/cột, cuộn riêng, bố cục thích ứng.
3. `static/js/kanban.js`: mở bảng chỉnh sửa khi cần, giữ vị trí cuộn, tự cuộn khi kéo và nhóm nút quản lý dự án.

**99 tệp ứng dụng/cấu hình/Skill khác giữ nguyên nội dung** so với đầu lượt sửa. Không sửa routes, services, schema/migration, cấu hình MySQL/Gemini, cơ chế đồng bộ hoặc phân quyền backend. Không sửa bộ hồ sơ Skill lịch sử trong docs. Các nút được chuyển vị trí giữ ID, hàm xử lý và quyền cũ.

Quy tắc nghiệp vụ giữ nguyên: 100% chuyển sang Hoàn thành; chuyển khỏi Hoàn thành đưa % từ 100 về 0; chuyển giữa các trạng thái chưa hoàn thành giữ % thực tế hiện có. Member chỉ cập nhật nhiệm vụ được giao/hỗ trợ. Nếu đang nhập % chưa lưu, thao tác lưu trạng thái được chặn để tránh mất bản nhập.

## Kiểm thử thực thi

| Bộ | Kết quả | Minh chứng |
| --- | --- | --- |
| SQLite unit/tích hợp | **253/253 đạt** | [JSON](qa-results-sqlite.json), [log](kanban-compact/sqlite.log) |
| Edge: luồng chung, nhiều vai trò và kích thước màn hình | **26/26 nhóm đạt** | [JSON](qa-browser-results.json), [log cuối](kanban-compact/browser-smoke-final.log) |
| Edge: member, tiến độ, báo cáo, tài khoản và đồng bộ | **21/21 nhóm đạt** | [JSON](qa-workspace-results.json), [log](kanban-compact/browser-workspace.log) |
| Edge: phân công, lưu trữ và sửa/hủy % qua giao diện mới | **14/14 nhóm đạt** | [JSON](qa-staffing-results.json), [log](kanban-compact/browser-staffing.log) |
| Edge: bảng 56 task, cuộn/kéo chuột và cảm ứng | **13/13 nhóm đạt** | [JSON](kanban-compact/browser-results.json), [log cuối](kanban-compact/browser-compact-attempt7.log) |

Tổng **74/74 nhóm trình duyệt đạt**, không có lỗi JavaScript được ghi nhận trong các lượt cuối. Bộ mới kiểm tra 1920×1080, 1366×900, 768×1024, 390×844 và 320×740; card có tên dài sát giới hạn 200 ký tự và nhiều nhãn, tìm kiếm/phân trang 56 task, quyền member/PM, giữ vị trí cuộn sau đồng bộ, nhập chưa lưu khi thiết bị khác cập nhật, % không hợp lệ, Done 100%, kéo thả bằng sự kiện chuột/cảm ứng thật của trình duyệt.

Các lượt kiểm thử dùng SQLite tạm, AI/email giả lập; không tạo dữ liệu kiểm thử trong MySQL đang sử dụng, không gọi Gemini/email thật. Nhóm workspace giữ ngân sách chờ mặc định 15 giây của harness đã dùng trước đó. Đây là giả lập viewport/cảm ứng bằng Microsoft Edge, không khẳng định đã thử mọi thiết bị vật lý.

`node --check` đạt; Ruff F,E9 cho ba tệp kiểm thử có thay đổi đạt; kiểm tra khoảng trắng diff nguồn đạt. Hai bộ giao diện cũ chỉ điều chỉnh thao tác chọn đúng bảng chỉnh sửa mới, giữ kiểm tra kết quả và phân quyền.

## Các lần phát hiện và sửa

- Lần 1: dữ liệu thử có tiêu đề vượt giới hạn; sửa dữ liệu về 200 ký tự, giữ nguyên giới hạn của ứng dụng.
- Lần 2: tablet cuộn trang thừa do padding; sửa cách tính chiều cao theo padding thực tế.
- Lần 3: ngón tay ra ngoài mép bảng vài pixel làm tự cuộn không chạy; mở vùng nhận diện tới vùng đệm sát mép màn hình.
- Lần 4: kỳ vọng của test về % sau chuyển giữa trạng thái chưa hoàn thành chưa đúng; sửa test để xác minh ứng dụng giữ 55% theo quy tắc hiện có.
- Lần 5: 12 nhóm đạt; xem ảnh để tiếp tục tối ưu phần trống ở điện thoại nhỏ.
- Lần 6: các nút dự án của PM chiếm chiều cao trên điện thoại nhỏ; gom vào menu Dự án trên Kanban.
- Lần 7: **13/13 nhóm đạt** sau chỉnh bố cục cho PM và kiểm tra đường dẫn đến nhiệm vụ đã lưu trữ.

Log các lần thử và JSON của các lượt 2–6 được giữ tại `kanban-compact/`; không đổi các lượt lỗi thành lượt đạt.

## Ảnh đã xem để kiểm tra bố cục

- [Máy tính](kanban-compact/board-desktop.png), [laptop](kanban-compact/board-laptop.png), [tablet](kanban-compact/board-tablet.png).
- [Điện thoại](kanban-compact/board-phone.png), [member 320px](kanban-compact/board-small-phone.png), [PM 320px](kanban-compact/board-pm-small-phone.png).
- [Bảng chỉnh tiến độ](kanban-compact/progress-editor.png), [chỉnh tiến độ trên điện thoại](kanban-compact/progress-editor-phone.png).

## Áp dụng vào phần mềm đang chạy

Các tệp đã được lưu trong `D:\UNG DUNG AL_NAM3\Code Chuan`. Máy chủ hiện tại trả HTTP 200, `HEALTHY`, MySQL sẵn sàng; mã phiên bản đọc từ nguồn hiện tại là `77d78f19e1b29cb7bf9a`.

**Cần khởi động lại phần mềm/máy chủ**, sau đó nhấn **Ctrl+F5** trên trang Kanban để nạp đầy đủ template và tài nguyên mới. Chỉ tải lại trang có thể vẫn gặp template cũ đang được tiến trình Flask giữ trong bộ nhớ.

Thao tác tự dừng/khởi động lại máy chủ đã bị cơ chế xét duyệt tự động từ chối, với thông báo **“blocked by policy”**. Lệnh bị chặn trước khi thực thi; lượt này không tự khởi động lại máy chủ. Chưa commit/push thay đổi giao diện này.

Bằng chứng bảo toàn/kết quả tổng hợp: [verification.json](kanban-compact/verification.json).
