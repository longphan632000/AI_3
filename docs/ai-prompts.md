# Prompt thực thi và truy vết

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

## Nguồn hiện trạng

Prompt thực thi ở services/prompt_builder.py; meeting pipeline còn có prompt có cấu trúc trong meeting_minutes_service.py; local_brain_service.py có prompt/bộ luật dự phòng. Vai trò → grounding → dữ liệu nguồn → yêu cầu bổ sung → ràng buộc đầu ra. Hệ thống dùng tiếng Việt và Task/User citation; provider không được tự ghi dữ liệu.

## Ba cấu trúc

- Weekly: tiến độ, trễ/rủi ro, ưu tiên, thiếu/mâu thuẫn; không suy thời gian hoàn thành từ trạng thái snapshot.
- Meeting: chia nguồn theo passage/chunk, phân loại discussion/decision/action; đầu ra cấu trúc và đối chiếu từng đoạn, không tự tạo người/hạn.
- Assignment legacy: 1–3 ứng viên. Staffing v2: số lượng thực yêu cầu, eligible=true, ưu tiên kỹ năng/tải/việc trễ; chỉ trả [User #ID] xếp hạng, máy chủ dựng nội dung từ số liệu đã đối chiếu. Thiếu người phải nêu số thật.

## Phiên bản và đánh giá

Lịch sử runtime hiện ghi prompt_version='v1.0' cố định. Hồ sơ này ghi hash tệp prompt trong evidence/source-manifest.json để đối chiếu bản hiện tại, không đổi trường runtime thành một cơ chế quản lý version chưa có. Chưa có phép thử A/B prompt hai phiên bản được nhóm nghiệm thu; trạng thái NOT RUN, không tự ghi điểm chất lượng. Xem REQ-10.

Prompt áp dụng Skill lần này được ghi ở skill-prompts.md. Đó là yêu cầu thực thi phiên hiện tại, không được ghi lùi ngày như prompt đã dùng trước khi lập trình.
