# Kết quả sắp xếp tài liệu và kiểm thử

Thực hiện: 2026-10-28T22:45:04.834100+07:00. Theo yêu cầu, giữ nguyên chức năng, luồng nghiệp vụ, quyền người dùng, giao diện và cấu hình ứng dụng.

## Thay đổi đã thực hiện

- Giữ **281 tệp hồ sơ/minh chứng Skill** trong `docs/`, gồm 48 Markdown, 39 bộ sơ đồ PlantUML/PNG/SVG, bản nguồn và các minh chứng.
- Chuyển **81 tệp** từ vị trí báo cáo/QA cũ sang `logstest/`, giữ cấu trúc thư mục. Đã kiểm tra nội dung khớp mã SHA-256 trước khi cập nhật liên kết.
- Giữ riêng **40 ảnh của đợt Skill** trong `docs/evidence/screenshots/`; ảnh/log/JSON trong `logstest/` là vị trí đầu ra của chương trình kiểm thử về sau.
- Cập nhật liên kết README, mục lục Skill và các báo cáo cần thiết. Cập nhật danh mục hồ sơ để trỏ đúng vị trí.
- Chỉ đổi chuỗi đường dẫn xuất báo cáo trong **11 công cụ kiểm thử**. So sánh cấu trúc mã xác nhận điều kiện kiểm tra và dữ liệu thử không bị sửa.

Danh sách từng tệp và mã kiểm tra: [reorganization-plan.json](reorganization-plan.json). Có [bản sao lưu nguyên gốc 81 tệp](reorganization-backup-before.zip) trước khi sửa liên kết/chạy lại kiểm thử. Bằng chứng tự động: [reorganization-verification.json](reorganization-verification.json), [report-path-verification.json](report-path-verification.json).

## Bằng chứng bảo toàn

**104/104 tệp ứng dụng, cấu hình và Skill giữ nguyên nội dung** so với trước lượt sắp xếp: mã backend, template, CSS/JS, schema/migration, cấu hình môi trường và các Skill. Không xuất khóa hoặc mã kiểm tra `.env` vào báo cáo.

Máy chủ đang chạy vẫn trả HTTP 200, trạng thái `HEALTHY`, MySQL sẵn sàng; build trước/sau đều `396983399f12706bcbdf`. Không khởi động lại máy chủ và không ghi dữ liệu thử vào database đang dùng.

Toàn bộ **281 tệp trong docs giữ nguyên qua các lần kiểm thử mới**; các chương trình kiểm thử không tạo lại thư mục QA tại docs. 28 tệp minh chứng thô của đợt Skill và 40 bản chụp ảnh giữ nguyên nội dung. Đường dẫn/thời gian cũ bên trong log và JSON thô phản ánh lúc chúng được tạo.

## Kết quả kiểm thử mới

| Bộ kiểm thử | Kết quả | Minh chứng |
| --- | --- | --- |
| SQLite unit/tích hợp | 253/253 đạt | [JSON](qa-results-sqlite.json), [log](reorganization-runs/sqlite.log) |
| Trình duyệt: chức năng chung | 26/26 nhóm đạt | [JSON](qa-browser-results.json), [log](reorganization-runs/browser-smoke.log) |
| Trình duyệt: member, tiến độ, biểu đồ, tài khoản, đồng bộ | 21/21 nhóm đạt | [JSON](qa-workspace-results.json), [log](reorganization-runs/browser-workspace.log) |
| Trình duyệt: ứng viên, phân công, lưu trữ/khôi phục | 14/14 nhóm đạt | [JSON](qa-staffing-results.json), [log](reorganization-runs/browser-staffing.log) |
| Trình duyệt: xóa tài khoản, sửa/hủy/xác nhận bản nháp | 18/18 nhóm đạt | [JSON](qa-ui-repairs.json), [log](reorganization-runs/browser-repairs.log) |

Tổng trình duyệt: **79/79 nhóm đạt**, gồm các kích thước màn hình đã định nghĩa trong bộ kiểm thử. Tất cả dùng SQLite tạm; AI/email giả lập. Nhóm workspace dùng cùng điều kiện kiểm tra, với thời gian chờ mặc định 15 giây qua harness đã có từ đợt Skill. Kiểm tra cú pháp của 11 công cụ đã thay đổi đạt.

Không chạy lại MySQL regression, benchmark, restore hoặc gọi Gemini/email thật trong lượt này. Các kết quả tương ứng đã có trong thư mục là lịch sử. Việc kiểm thử không chứng minh đã kiểm tra mọi thiết bị vật lý hoặc mọi yêu cầu phi chức năng.

## Phạm vi giữ nguyên

Không sửa các lỗi nghiệp vụ đã được nêu trước đó, gồm CR-01 khi lưu lại bản nháp gợi ý trên 3 người; xem [code review Skill](../docs/code-review.md). Đây là lượt sắp xếp tài liệu, không thay đổi phần mềm. Chưa commit hoặc push các thay đổi của lượt này.

Mở [mục lục hồ sơ Skill](../docs/SKILL_REPORT_INDEX.md) hoặc [danh mục logstest](README.md).
