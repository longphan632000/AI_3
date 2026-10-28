# Báo cáo kiểm thử thực tế sau khi bổ sung hồ sơ

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh hiện trạng, không thay phê duyệt của nhóm.

Kết quả SQLite mới: **253/253**, timestamp `2026-10-28T21:18:01.886083+07:00`. Các lượt cuối browser **79/79 nhóm**. Đã xác minh 89 tệp ứng dụng/cấu hình giữ nguyên hash và app_version vẫn `396983399f12706bcbdf`.

| Bộ | Lệnh | Đạt | Tổng | Trạng thái | Bằng chứng |
| --- | --- | --- | --- | --- | --- |
| SQLite unit/integration | python -B tests/run_isolated.py | 253 | 253 | PASS | evidence/tests-sqlite.log |
| Browser core | python -B tests/browser_smoke.py | 26 | 26 | PASS | evidence/browser-smoke.log |
| Browser staffing/archive | python -B tests/browser_staffing_archive.py | 14 | 14 | PASS | evidence/browser-staffing.log |
| Browser draft/account | python -B tests/browser_ui_repairs.py | 18 | 18 | PASS | evidence/browser-repairs.log |
| Browser workspace lần 1 | python -B tests/browser_workspace.py | Xem JSON | — | FAIL: chờ report-total quá 5s | evidence/browser-workspace-attempt1.json |
| Browser workspace lần 2 | python -B [workspace]/work/rerun_workspace_acceptance.py | 21 | 21 | PASS; assertion cũ, default functional wait 15s | evidence/browser-workspace-attempt2.log |
| Review probes | python -B [workspace]/work/probe_skill_findings.py | 3 | 3 | Hoàn tất quan sát, 1 defect tái hiện | evidence/review-probes.json |
| Python static | python -m ruff check app.py routes services database --select F,E9 --output-format json | — | 8 | 8 cảnh báo lint, không sửa | evidence/lint.json |
| Skill structure | quick_validate.py từng thư mục | 14 | 14 | PASS sau dùng interpreter có PyYAML | evidence/skill-validation.json |
| Sơ đồ | PlantUML local PNG/SVG | 39 | 39 | RENDERED; kiểm trực quan riêng | evidence/diagram-final-freeze.json |

## Lần lỗi được giữ lại

Workspace lần 1 dừng ở kiểm report-total=5 nhưng màn hình còn 0 sau cửa sổ chờ 5 giây trong lúc các tác vụ render/browser đồng thời hoạt động; chưa đủ dữ kiện kết luận nguyên nhân gốc. Lần 2 giữ nguyên test/expectation, tăng chờ chức năng mặc định lên 15 giây qua harness ngoài source và đạt 21 nhóm. Đây là tín hiệu độ ổn định/thời gian chờ cần theo dõi, không được xóa lần thất bại hoặc dùng lần pass để nghiệm thu mục tiêu 2 giây của NFR-01.

## Defect ngoài bộ kiểm thử cũ

PROBE-01: draft staffing v2 có 5 ứng viên hợp lệ ban đầu status=draft. Lưu lại cùng nội dung bằng PUT draft với version=1 trả 200 nhưng status chuyển needs_verification, warning “Đề xuất phải có từ 1 đến 3 ứng viên”. Đây là defect CR-01/REQ-11 tái hiện thật, giữ nguyên để chủ hệ thống xem xét trong yêu cầu sửa riêng. Bộ 253 tests hiện tại chưa phát hiện nhánh này.

PROBE-02 quan sát chính sách Admin cộng tác: comment/note 201, attachment 403; không gọi đó là bug bảo mật khi yêu cầu còn cần chốt. PROBE-03 xác nhận due_date=NULL và estimated_hours=0 được lưu hiện trạng.

## Phần không được suy rộng

Không gọi API Gemini thật hoặc gửi mail thật; provider trong regression được giả lập. Các JSON qa-staffing-gemini-live.json/qa-system-checks.json cũ chỉ là HISTORICAL. Không chạy MySQL migration, benchmark 10.000 hoặc restore mới, không xác minh mọi thiết bị vật lý. Lượt này không chứng minh đã đạt tất cả NFR hoặc các Human Gate trước khi viết mã.
