# Mục lục hồ sơ Skill và báo cáo hệ thống

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh hiện trạng, không thay phê duyệt của nhóm.

Đã áp dụng 14 Skill để bổ sung hồ sơ hiện trạng; giữ nguyên 89 tệp ứng dụng/cấu hình và build `396983399f12706bcbdf`. Kết quả cuối: 253/253 SQLite, 79/79 nhóm browser; có 1 defect mới tái hiện ngoài bộ test cũ. Hồ sơ không đồng nghĩa đã nghiệm thu toàn bộ quy trình trước triển khai.

## Đọc theo thứ tự

1. [Nguồn URD](source-urd.md), [nhu cầu/phạm vi](customer-requirement.md), [mô hình](system-model.md), [truy vết mô hình](system-model-traceability.md).
2. [Requirements](requirements.md), [stories](user-stories.md), [acceptance criteria](acceptance-criteria.md), [issues](requirements-issues.md), [decisions](requirements-decisions.md).
3. [Kiến trúc](architecture.md), [ADRs](architecture-decisions.md), [thiết kế CSDL](database-design.md), [từ điển](tables/data-dictionary.md), [bảng lớp](tables/class-specification.md).
4. [Actor](tables/actor-specification.md), [13 UC](tables/use-case-summary.md), [đặc tả UC](tables/use-case-specifications.md), [traceability](tables/requirements-traceability.md).
5. [Danh mục sơ đồ](diagrams/README.md), [đối chiếu hình nguồn](diagram-comparison.md). Mỗi sơ đồ có .puml/.png/.svg; 13 ảnh phân rã UC gốc chưa tái sinh include/extend cùng loại.
6. [AI requirements](ai-assistant-requirements.md), [AI functional](ai-functional-requirements.md), [AI stories](ai-user-stories.md), [AI AC](ai-acceptance-criteria.md), [AI issues](ai-requirements-issues.md), [AI architecture](ai-assistant-architecture.md), [dataflow](ai-assistant-data-flow.md), [request analysis](ai-request-analysis.md), [prompts](ai-prompts.md).
7. [Implementation audit](implementation-report.md), [test plan](test-plan.md), [test report](test-report.md), [test cases](tables/test-cases.md), [test results](tables/test-results.md), [code review](code-review.md), [security review](security-review.md).
8. [API](api.md), [deployment](deployment.md), [user guide](user-guide.md), [prompt thực hiện](skill-prompts.md), [nhật ký 14 Skill](skill-run-log.md), [Git thật](git-history.md), [Human verification](human-verification.md).

## Việc nhóm còn cần làm

- Đọc/chốt mâu thuẫn và Human Gate thật; cung cấp minh chứng đóng góp từng người.
- Review defect CR-01: lưu draft 5 người bị kiểm lại theo giới hạn 3; ứng dụng được giữ nguyên theo phạm vi lượt này.
- Chốt milestone/ngày/ước lượng, lịch nhắc FR-16, phiên bản prompt; kiểm HTTPS/CVE/backup/SMTP thật theo môi trường.
- Nếu cần đủ sơ đồ phân rã UC giống loại nguồn, chốt quan hệ include/extend từ văn bản trước, không chép ảnh như sản phẩm sinh độc lập.
- Lưu commit các tài liệu mới sau khi xem xét; lượt này không tự push GitHub.

Minh chứng đọc máy ở evidence/: kết quả test, lần fail/retry, probes, skill-validation, initial/final diagram hash, application-preservation, source-version, source-manifest và document-validation. Báo cáo và kết quả kiểm thử ở vị trí cũ đã chuyển sang [logstest](../logstest/README.md). Minh chứng thuộc đợt Skill được giữ tại evidence/, gồm [ảnh chụp giao diện](evidence/screenshots/). Log/JSON thô giữ nguyên đường dẫn và thời điểm thực thi lịch sử; các lần kiểm thử sau ghi vào logstest.

Bổ sung: [quyền theo từng thao tác](tables/role-permissions.md) và [báo cáo thực hiện](SKILL_EXECUTION_REPORT.md).
