# Kiến trúc Trợ lý AI hiện trạng

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

Browser → AI route → ai_assistant_service → analyzer → retrieval → context → prompt → provider → validator → draft/snapshot/history. Confirmation là endpoint riêng vào ai_confirmation_service sau khi người dùng kiểm tra và có quyền PM. AI provider không giữ kết nối DB hay công cụ ghi nghiệp vụ.

GeminiService gọi HTTP generateContent; OpenAIService là adapter tương thích DeepSeek khi cấu hình chủ động; AIProviderService giữ API-first/budget/fallback, LocalModelService gọi runtime đã cài, LocalBrainService xử lý nghiệp vụ xác định khi cần. Không mô tả local rules như mô hình ngôn ngữ tổng quát.

Meeting có pipeline passage/chunk riêng, kiểm bao phủ nguồn và giữ thông tin không đối chiếu như cảnh báo. Staffing v2 nhận thứ tự ID provider rồi kiểm eligibility/count, dựng lý do/capacity/load từ nguồn; sai số lượng/ID thì dùng bảng xếp hạng xác minh. Lưu engine thực tế cùng draft/history; không đọc nguyên văn mọi claim provider như sự thật.

Sơ đồ trong diagrams/ai-assistant-architecture.puml và ai-assistant-data-flow.puml. REQ-10/11 ghi hạn chế phiên bản prompt và chỉnh sửa staffing draft.
