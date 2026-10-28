# Kết quả thực thi và giới hạn

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh hiện trạng, không thay phê duyệt của nhóm.

| Bộ | Lệnh/thao tác | Đạt/hoàn tất | Tổng | Trạng thái | Minh chứng |
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

Các số 79 nhóm browser là tổng các lượt cuối 26+14+18+21; lần timeout đầu được giữ nguyên trong bằng chứng. Probe tái hiện lỗi không được cộng vào số test nghiệp vụ pass. Không chạy lại Gemini thật/SMTP thật/MySQL ghi dữ liệu trong lượt này.
