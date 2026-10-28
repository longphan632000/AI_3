# Các điểm kiểm tra của con người

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh hiện trạng, không thay phê duyệt của nhóm.

Chủ hệ thống đã cho phép lập hồ sơ và giữ nguyên phần mềm. Đây không đồng nghĩa nhóm/giảng viên đã duyệt URD, bản thiết kế, test hoặc security. Những trạng thái bên dưới để PENDING và cần người thực hiện điền minh chứng/ngày/quyết định thật.

| Gate hồ sơ | Nội dung cần người kiểm | Minh chứng gợi ý | Reviewer/ngày/quyết định |
| --- | --- | --- | --- |
| HG-MODEL (tham chiếu Gate 0) | Nguồn/version, đủ 50 ID, mâu thuẫn và quyền | source-urd, system-model, traceability, issues | PENDING — chưa ghi nhận |
| HG-REQ (tham chiếu Gate 1) | Stories/AC, source vs current changes, UN-08/09 và D01–08 | requirements*, actor/UC tables | PENDING — chưa ghi nhận |
| HG-ARCH (tham chiếu Gate 2) | 39 sơ đồ, flow, cardinality và khác biệt nguồn | architecture*, diagrams, diagram-comparison | PENDING — chưa ghi nhận |
| HG-DB | 17 bảng/cột/FK, nullable và invariant service | database-design, schema, dictionary | PENDING — chưa ghi nhận |
| HG-TEST | 253 test, 79 nhóm cuối, lần timeout và CR-01 | test-report, raw logs, review-probes | PENDING — chưa ghi nhận |
| HG-REVIEW/SECURITY | Defect và rủi ro còn lại; TLS/CVE/ops NOT RUN | code-review, security-review | PENDING — chưa ghi nhận |
| HG-AI | Nguồn/role/confirm, staffing extension và prompt version | AI docs, C02–C06, REQ-10/11 | PENDING — chưa ghi nhận |
| HG-DOC/FINAL | Đọc bản báo cáo, chọn phần nộp, demo và đóng góp cá nhân | SKILL_REPORT_INDEX, README, git-history | PENDING — chưa ghi nhận |

Các mã HG-... là nhãn tổ chức hồ sơ lần này, không khẳng định là số Gate nguyên văn của mọi phần hướng dẫn.

## Đóng góp thành viên

| Thành viên | Phân công ghi trong URD | Minh chứng đóng góp/kiểm tra thực tế |
| --- | --- | --- |
| Phan Chân Long | Phân tích yêu cầu, implementation, request/prompt/provider/API/UI | CHƯA CUNG CẤP xác nhận cá nhân trong lượt hồ sơ |
| Lưu Trà My | Kiến trúc/CSDL/dataflow/retrieval/context/tài liệu | CHƯA CUNG CẤP xác nhận cá nhân trong lượt hồ sơ |
| Lê Nam Khánh | Testing/code review/security | CHƯA CUNG CẤP xác nhận cá nhân trong lượt hồ sơ |

Nhóm cần bổ sung commit/ảnh ghi chú/nhận xét sửa AI có thật cho từng người và thực hiện vấn đáp/demo. Không dùng bảng phân công dự kiến để suy thành công việc đã hoàn thành; Codex không ký thay thành viên.
