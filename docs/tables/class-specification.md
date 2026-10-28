# Đặc tả lớp miền và lớp Python thực tế

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

Lớp miền dưới đây là khái niệm trong URD, không khẳng định có ORM/Python class cùng tên.

| Lớp khái niệm | Bảng hiện trạng | Module thực hiện | Thuộc tính trong URD |
| --- | --- | --- | --- |
| TaiKhoan | users | auth/account_service | HoTen, Email, MatKhau, TrangThai, VaiTro |
| DuAn | projects | project_service | TenDuAn, MoTa, ThoiGian, TrangThai |
| ThanhVienDuAn | project_members | project_member_service | VaiTroDuAn, KyNang, MucSanSang, NangLucLamViec |
| Sprint | sprints | sprint_service | TenSprint, NgayBatDau, NgayKetThuc, TieuChiHoanThanh |
| NhiemVu | tasks/task_assignees | task_service | TieuDe, TrangThai, HanHoanThanh, UocLuong |
| LichSuAI | ai_history/ai_drafts | ai_history_service | LoaiTacVu, PromptYeuCau, KetQuaAI, TrangThaiXacNhan |

## Class thực sự tìm thấy bằng AST

| Class | Tệp:dòng | Phương thức |
| --- | --- | --- |
| ProjectJSONProvider | app.py:24 | default |
| DraftVersionConflict | services/ai_confirmation_service.py:11 |  |
| AIProviderError | services/ai_errors.py:4 | __init__ |
| AIProviderService | services/ai_provider_service.py:15 | __init__, bind_context, record_verified_ranking, _record, _failure, execution_metadata, fallback_status, _validate_primary, generate_response, generate_local_response |
| GeminiService | services/gemini_service.py:95 | __init__, configured, probe_model, _failed_probe, generate_content, _meeting_schema |
| KiraAIService | services/kira_service.py:13 | __init__, configured, _get_client, probe_model, generate_content |
| LocalBrainService | services/local_brain_service.py:74 | __init__, model_prompt, model_schema, generate_response, weekly_summary, task_line, assignment_suggestion, validate_model_response |
| LocalModelService | services/local_model_service.py:41 | __init__, installed, _request, reachable, ensure_running, generate_content |
| OpenAIService | services/openai_service.py:79 | __init__, configured, _get_client, probe_model, _failed_probe, _response_text, generate_content |
| ValidationError | services/validation.py:11 |  |
