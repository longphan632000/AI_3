# Nhật ký thực hiện 14 Skill

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh hiện trạng, không thay phê duyệt của nhóm.

| Prompt tham chiếu | Skill áp dụng | Việc đã làm | Artifact/evidence | Kết luận |
| --- | --- | --- | --- | --- |
| PROMPT 00 | 14 Skill | Đọc bản cũ, bổ sung scope/input/procedure/artifact verification, giữ tên/mô tả | 14 SKILL.md; evidence/skill-validation.json | DONE cấu trúc; không chứng minh hành vi mọi tình huống |
| PROMPT 00A | requirements-analysis | Đọc trọn chữ/bảng hai Word, giữ SHA/ID, tách hiện trạng/nguồn | source-urd, customer-requirement, system-model, system-model-traceability | DONE bản hiện trạng; Human Gate 0 PENDING |
| PROMPT 01 / 01T | requirements-analysis + diagram/table-design | Tạo FR/NFR/BR, stories/AC/issues, actor/13 UC/trace | requirements.md và tables/; use-case-diagram | DONE tài liệu, còn issue chờ nhóm |
| PROMPT 02 / 02A / 02B / 02C / 02D / 02E | architecture + diagram/table | Từ mô hình chữ/mã, dựng component, 13 sequence/activity, class, phân cấp/quy trình | architecture*, diagrams/, class-specification | DONE ghi nhận hiện trạng, không gọi thiết kế đã duyệt |
| PROMPT 03 | database + diagram/table | Trích 17 bảng DDL, FK/nullability, đối chiếu nguồn, ERD | database-design, data-dictionary, ERD; schema.sql giữ nguyên | DONE hồ sơ; không chạy migration |
| PROMPT 03V | diagram-design | Khóa hash sơ đồ trước xem ảnh; so 42 ảnh sau generation | diagram-comparison, source/figures, initial/final hashes | DONE đối chiếu; 13 phân rã cùng loại + commit-before-compare PENDING |
| PROMPT 04 | implementation | Đọc core và giữ nguyên source trong chế độ hồ sơ | implementation-report, source-manifest | AUDITED, không viết lại core |
| PROMPT 05 / 18 | testing + table | Chạy 253 test và bốn bộ browser; lưu lần fail/retry, probe defect | test-plan/report, evidence/, tables/test-* | DONE; 1 defect mới và giới hạn vận hành còn mở |
| PROMPT 06 | code-review | Rà code, lint, transaction, permissions và bản nháp; không sửa code | code-review, finding table, probes | DONE review của Codex; peer review PENDING |
| PROMPT 07 | security-review | Rà kiểm soát bảo mật, secret, scope/upload và giới hạn | security-review, dependency inventory, finding table | DONE phạm vi đã nêu; CVE/pentest/TLS NOT RUN |
| PROMPT 08 | requirements-analysis | Phân tích ba chức năng AI và mở rộng đã được user yêu cầu | ai-*requirements/stories/criteria/issues | DONE tài liệu, không tự thêm FR mới |
| PROMPT 09 | architecture + diagram | Dựng AI pipeline/dataflow với validator/confirmation/provider | ai-assistant-architecture/data-flow + puml/PNG/SVG | DONE hiện trạng |
| PROMPT 10 | ai-request-analysis | Đối chiếu session/project/task quyền và schema input | ai-request-analysis.md; api.md | DONE đối chiếu |
| PROMPT 11 | project-data-retrieval | Rà binding SQL/source refs và staffing aggregate ngoài dự án | ai-assistant-data-flow; source module giữ nguyên | DONE đối chiếu theo C04 |
| PROMPT 12 | context-builder | Rà compact context và thiếu/mâu thuẫn, không sửa số liệu | ai-assistant-data-flow; ai-prompts | DONE đối chiếu |
| PROMPT 13 | project-ai-prompt | Đọc template thật và ràng buộc/phiên bản prompt | ai-prompts; source hash | DONE mô tả; A/B NOT RUN, runtime version còn cố định |
| PROMPT 14 / 15 / 16 / 17 | implementation | Rà provider/coordinator/API/UI đã có; test qua adapter giả lập | implementation-report, API và AI docs; code giữ nguyên | AUDITED, không tái triển khai |
| PROMPT 19 | documentation | Tổng hợp index/api/deployment/user-guide, kiểm liên kết và bảo toàn app | README, SKILL_REPORT_INDEX, api/deployment/user-guide | DONE hồ sơ; nghiệm thu học thuật vẫn PENDING |

## Công cụ thực sự sử dụng

- Đọc/ghi file, AST/XML/ZIP/hash và Git log/status bằng công cụ terminal; không tạo lịch sử giả.
- MCP công cụ desktop `load_workspace_dependencies`: trả runtime Python/Node và thư viện tài liệu thực; không coi đây là kết nối GitHub issue.
- Word được đọc bằng OOXML; dùng runtime tài liệu đóng gói cho trích xuất/tạo artifact. Skill validator cần PyYAML, interpreter đóng gói thiếu module; đã chạy validator bằng Python của dự án có PyYAML và đạt 14/14, không cài/sửa dependency ứng dụng.
- PlantUML release chính thức được tải về thư mục làm việc riêng, render PNG/SVG cục bộ. Tài liệu công cụ: https://plantuml.com/starting và https://plantuml.com/graphviz-dot . Không gửi nội dung sơ đồ qua dịch vụ render ngoài.
- SQLite runner và Playwright/Edge headless chạy trên fixture tạm; có raw output. HTTP health dùng đọc trạng thái, không ghi dữ liệu.

Không có workflow issue→MCP GitHub→fix được thực hiện trong lượt này. Không gửi email, không gọi Gemini thật, không sửa môi trường hoặc khởi động lại máy chủ. Tệp SKILL.md là hướng dẫn cho Agent; không phải chương trình thực thi tự sinh file khi bấm Run.
