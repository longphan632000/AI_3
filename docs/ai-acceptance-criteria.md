# Điều kiện chấp nhận AI

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

| ID | Given/When | Then | Truy vết |
| --- | --- | --- | --- |
| AI-AC-01 | Member gửi weekly/staffing hoặc confirm trực tiếp API | 403, không ghi bản chính thức | FR-12/14, BR-06 |
| AI-AC-02 | Task/note ID thuộc project khác | Không dùng làm nguồn; từ chối/không tìm thấy | NFR-03/04, BR-07 |
| AI-AC-03 | Provider nhắc ID ngoài nguồn/schema sai/mâu thuẫn | Lỗi/cần xác minh hoặc fallback có đối chiếu; không tự công nhận | BR-07 |
| AI-AC-04 | Thiếu người/hạn trong ghi chú | Không tự tạo danh tính/hạn; tham chiếu passage | FR-13 |
| AI-AC-05 | API timeout hoặc key/quota/network lỗi | Lỗi rõ hoặc local fallback được ghi đúng nguồn | NFR-01/11, C02 |
| AI-AC-06 | Có 5 người phù hợp; yêu cầu 5 | Gợi ý 5 ID thật, không đổi assignee/membership | FR-14 mở rộng |
| AI-AC-07 | Yêu cầu nhiều hơn đủ điều kiện | Trả số thật và số thiếu, không bịa người | BR-07 |
| AI-AC-08 | Lưu/xác nhận draft với version cũ | 409/không ghi đè; confirmed chỉ theo quyền PM | BR-06 |
| AI-AC-09 | Ghi chú chứa chỉ dẫn chống nguồn/prompt injection | Dữ liệu được kiểm định; không chấp nhận quyền hoặc ID bịa | BR-06/07; không bảo đảm chống mọi dạng prompt injection |
