# Member cập nhật phần trăm tiến độ — 29/10/2026

## Phạm vi được xác nhận

Member cập nhật task mình phụ trách hoặc hỗ trợ; làm nút cập nhật rõ hơn. Giữ nguyên phân quyền, các trạng thái và quy tắc nghiệp vụ hiện có.

## Những gì đã thay đổi

- Thêm **Việc của tôi** trên thanh tìm kiếm Kanban, lọc cả nhiệm vụ phụ trách và nhiệm vụ hỗ trợ. Bấm lại để bỏ bộ lọc cá nhân.
- Task được phép cập nhật có nút xanh **Cập nhật % tiến độ** chiếm toàn chiều rộng thẻ và viền dễ nhận biết.
- Đưa phần nhập **Tiến độ thực tế (%)** và nút **Lưu tiến độ** lên ngay dưới tiêu đề cửa sổ chi tiết, trước mô tả và tài liệu.
- Thông báo rõ khi không có nhiệm vụ cá nhân khớp bộ lọc.
- Task không được giao/hỗ trợ vẫn chỉ xem. Giữ nguyên kéo thả, lưu trạng thái, đóng/hủy và cơ chế giữ nội dung chưa lưu khi đồng bộ.

Mã giao diện của lượt này: `static/js/kanban.js`, `static/css/kanban.css`. Cập nhật bài kiểm tra trong `tests/browser_workspace.py`. Không sửa backend, cấu trúc dữ liệu, cấu hình riêng hoặc hồ sơ Skill trong `docs/` ở lượt này. Các sửa Kanban và tự nạp mẫu HTML của lượt trước vẫn được giữ.

## Cách sử dụng

1. Đăng nhập member, mở **Bảng Kanban** và chọn dự án.
2. Bấm **Việc của tôi** để tìm nhiệm vụ được giao/hỗ trợ.
3. Bấm **Cập nhật % tiến độ**, nhập số nguyên từ 0 đến 100 rồi bấm **Lưu tiến độ**.
4. Dữ liệu được lưu và đồng bộ qua máy chủ. Quy tắc hiện có: 100% chuyển sang Hoàn thành; giảm dưới 100% ở task đã hoàn thành sẽ mở lại trạng thái Đang làm.

Nếu task không có nút cập nhật, kiểm tra người phụ trách/danh sách hỗ trợ và quyền của dự án. Mở ứng dụng theo cách thông thường và nhấn Ctrl+F5 để tải lại các tệp giao diện.

## Kết quả kiểm thử

Các phép ghi dữ liệu dùng SQLite tạm, tách khỏi dữ liệu sử dụng thật. Tắt email thật, tác vụ gửi email và mô hình cục bộ; kết nối Gemini trong bài kiểm tra giao diện được giả lập.

| Bộ kiểm tra | Kết quả | Minh chứng |
| --- | --- | --- |
| Chức năng workspace và quyền cập nhật | 14/14 đạt | [Log SQLite](member-progress/workspace-unit.log) |
| Workspace trên Edge, gồm 2 nhóm kiểm tra mới cho bộ lọc cá nhân | 23/23 nhóm đạt | [Kết quả](member-progress/workspace-browser-results.json), [log](member-progress/browser-workspace.log) |
| Bảng 56 task với mẫu HTML cũ và giao diện mới, kiểm tra 5 kích thước màn hình | 13/13 nhóm đạt | [Kết quả](member-progress/crowded-legacy/browser-results.json), [log](member-progress/crowded-legacy.log) |
| Cú pháp JavaScript, Ruff F/E9 cho bài kiểm tra và kiểm tra khoảng trắng của bản sửa | Đạt | [Kết quả kiểm tra tĩnh](member-progress/static-checks.json) |

Đã xác nhận: lọc đúng task phụ trách và hỗ trợ; có giải thích khi bộ lọc rỗng; lưu 45% trên task phụ trách và giữ sau tải lại; lưu 60% trên task hỗ trợ; báo cáo PM tự cập nhật; task khác bị từ chối quyền sửa; chặn giá trị không hợp lệ; 100% chuyển Done; kéo thả chuột/cảm ứng; giữ biểu mẫu chưa lưu khi có dữ liệu mới; giao diện không tràn trang ở 320, 390, 768, 1024/1366 và 1920 px trong các bộ tương ứng. Hai bộ giao diện hoàn tất không có lỗi JavaScript runtime được ghi nhận.

Lần chạy workspace đầu tiên dừng vì bài kiểm tra đọc vị trí khối điều khiển trước khi cửa sổ tải xong. Đã bổ sung chờ cửa sổ và tiêu đề hiển thị, giữ nguyên kiểm tra vị trí ngay dưới tiêu đề. Lần chạy lại đạt 23/23. Giữ nguyên [log lần đầu](member-progress/browser-workspace-attempt1.log) và [kết quả lần đầu](member-progress/browser-workspace-attempt1-results.json).

Lệnh đã chạy từ thư mục dự án:

```powershell
# Với AI_CONFIG_SOURCE=process, AI_LOCAL_FALLBACK_ENABLED=false,
# LOCAL_AI_MODEL_ENABLED=false, SMTP_ENABLED=false,
# DEADLINE_WORKER_ENABLED=false, QA_TEST_ENGINE=sqlite:
python -B -m unittest tests.test_workspace_enhancements -v
python -B tests/browser_kanban_compact.py --legacy-template --output logstest/member-progress/crowded-legacy
node --check static/js/kanban.js
python -m ruff check tests/browser_workspace.py --select F,E9
git diff --check
```

Bộ workspace được chạy qua `work/rerun_workspace_acceptance.py` trong workspace Codex để đặt thời gian chờ xác nhận giao diện 15 giây; chương trình đó thực thi trực tiếp `tests/browser_workspace.py`. Không bỏ qua assertion hay thay dữ liệu kỳ vọng.

## Ảnh và giới hạn xác nhận

- [Member: Việc của tôi và nút cập nhật](member-progress/member-progress-desktop.png).
- [Ô nhập phần trăm ngay đầu cửa sổ](member-progress/member-progress-form.png).
- [Bảng nhiều task trên màn hình 320 px](member-progress/crowded-legacy/board-small-phone.png).
- [Cửa sổ cập nhật trên điện thoại](member-progress/crowded-legacy/progress-editor-phone.png).

Kiểm tra đọc tệp giao diện qua `http://127.0.0.1:5000` trong lượt tiếp tục nhận lỗi kết nối bị từ chối (WinError 10061). Do đó chưa xác nhận phiên ứng dụng thực tế đang phục vụ tệp mới. Không khởi động lại máy chủ hay thay dữ liệu thật trong lượt này; các kết quả phía trên thuộc máy chủ kiểm thử riêng dùng SQLite tạm. Kích thước màn hình và thao tác cảm ứng được mô phỏng trong Edge; chưa kiểm tra trực tiếp trên mọi thiết bị vật lý. Không chạy lại MySQL hoặc Gemini thật trong lượt này.

Chưa commit hoặc push các sửa đổi của lượt này.
