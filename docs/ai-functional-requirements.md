# Yêu cầu chức năng AI truy vết

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

| Mã AI phụ | FR | Nội dung | Căn cứ |
| --- | --- | --- | --- |
| AI-FR-01 | FR-12 | Tóm tắt có scope/week, nguồn và warnings | URD FR-12/UC009; retriever/prompt/validator |
| AI-FR-02 | FR-13 | Sinh/sửa draft biên bản từ ghi chú; chỉ PM xác nhận | URD FR-13/UC010; meeting_minutes/draft/confirmation |
| AI-FR-03 | FR-14 | Gợi ý 1–3 ở nhánh cũ; v2 số lượng/recruitment theo C03/C04 | URD FR-14/UC011 và yêu cầu mở rộng |
| AI-FR-04 | FR-15 | Lưu requester/provider/prompt_version/reference/status | history_service; REQ-10 |
| AI-FR-05 | NFR-06/11 | API trước, fallback có engine, lỗi được chuẩn hóa | Yêu cầu chủ hệ thống, provider_service |
| AI-FR-06 | BR-06/07 | Đối chiếu ID/schema/số liệu, giữ draft/cần xác minh | validator; canonical staffing; confirmation |

Mã AI-FR là mã phụ hồ sơ, không thêm FR-18 hay thay 17 mã nguồn.
