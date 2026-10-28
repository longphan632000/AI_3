# Báo cáo cũ và kết quả kiểm thử

`docs/` giữ bộ hồ sơ và minh chứng của đợt chạy 14 Skill. Thư mục `logstest/` lưu các báo cáo/hướng dẫn trước đó và đầu ra kiểm thử ở vị trí cũ; các lần chạy kiểm thử tiếp theo cũng ghi tại đây.

- `BAO_CAO_*.md`, `HUONG_DAN_*.md`, CSV/HTML: báo cáo và hướng dẫn đã có trước đợt Skill.
- `qa-*.json`, `qa-screenshots/`, `qa-workspace/`, `qa-staffing/`, `qa-ui-repairs/`: kết quả và ảnh của các chương trình kiểm thử.
- `TEST_CASES_*`: các bảng xuất từ kết quả kiểm thử.
- [Danh sách di chuyển](reorganization-plan.json): 81 tệp, có mã kiểm tra nội dung trước khi sửa liên kết; không phân loại chỉ theo đuôi tệp.
- [Bản sao lưu 81 tệp gốc](reorganization-backup-before.zip): giữ nội dung trước khi sửa liên kết hoặc chạy lại kiểm thử.
- [Kiểm tra thay đổi đường dẫn](report-path-verification.json): chỉ đổi nơi xuất báo cáo của 11 công cụ kiểm thử, giữ nguyên điều kiện kiểm tra.
- [Báo cáo sắp xếp và kiểm thử](REORGANIZATION_REPORT.md).
- [Quay lại hồ sơ Skill](../docs/SKILL_REPORT_INDEX.md).

40 ảnh được tạo/cập nhật trong đợt Skill có bản chụp giữ riêng tại `docs/evidence/screenshots/`. Các ảnh ở đây là đầu ra của chương trình kiểm thử và có thể được cập nhật khi chạy lại. Bản log/JSON nguyên gốc của đợt Skill trong `docs/evidence/` được giữ nguyên.

Các tệp MySQL/Gemini thật đã có là kết quả lịch sử; chúng không chứng minh đã chạy lại MySQL hoặc gọi API thật trong lượt sắp xếp này. Xem thời điểm và phạm vi trong báo cáo tương ứng.

## Cập nhật giao diện Kanban

[Báo cáo tối ưu bảng nhiều nhiệm vụ](KANBAN_COMPACT_REPORT.md) và thư mục `kanban-compact/` lưu kết quả kiểm thử, ảnh màn hình và hướng dẫn nạp giao diện mới của lượt chỉnh sửa sau đó.

[Sửa task bị cắt và cập nhật %](KANBAN_VISIBILITY_REPAIR.md) ghi nhận lượt sửa tiếp theo: tương thích HTML cũ đang được máy chủ giữ, 254 ca SQLite và 26 nhóm trình duyệt; bản sửa này nhận được bằng Ctrl+F5.

[Member cập nhật % tiến độ — 29/10/2026](MEMBER_PROGRESS_29_10_2026.md): thêm nút Việc của tôi, làm rõ nút cập nhật trên task được giao/hỗ trợ và đưa ô nhập % lên đầu cửa sổ; 14 ca SQLite và 36 nhóm giao diện đạt. Minh chứng của lượt này ở `member-progress/`.
