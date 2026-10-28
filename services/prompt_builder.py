def build_ai_prompt(task_type, context_text, user_extra_prompt="", staffing_options=None):
    """
    Module xây dựng Prompt an toàn (project-ai-prompt skill).
    Đính kèm Grounding Rules nghiêm ngặt chống ảo giác (hallucination).
    """
    base_instructions = """Bạn là Trợ lý AI Quản lý Dự án Nhóm thông minh, hỗ trợ quy trình AI-Augmented SDLC (Đề tài 33).

CÁC NGUYÊN TẮC BẮT BUỘC (GROUNDING RULES):
1. CHỈ SỬ DỤNG thông tin được cung cấp trong phần [NGỮ CẢNH DỰ ÁN] bên dưới.
2. TUYỆT ĐỐI KHÔNG tự bịa đặt nhiệm vụ, thành viên, hạn chót hoặc số liệu không có trong nguồn.
3. TUYỆT ĐỐI KHÔNG tự động phân công hoặc tự ý cập nhật dữ liệu. Kết quả của bạn CHỈ LÀ BẢN NHÁP HOẶC ĐỀ XUẤT (Draft/Suggestion) để con người (Trưởng nhóm) xem xét và xác nhận.
4. Nếu dữ liệu nguồn thiếu, mơ hồ hoặc mâu thuẫn, bạn PHẢI NÊU RÕ PHẦN CẦN XÁC MINH thay vì tự suy đoán.
5. Luôn trả lời bằng TIẾNG VIỆT, cấu trúc Markdown chuyên nghiệp, rõ ràng.
6. Mỗi khi nhắc đến một nhiệm vụ hoặc thành viên, HÃY TRÍCH DẪN RÕ RÀNG ID tương ứng dạng [Task #ID] hoặc [User #ID].
"""

    if task_type == 'weekly_summary':
        specific_task = """
MỤC TIÊU: Tạo bản tóm tắt tiến độ tuần của dự án (FR-12).
Chỉ mô tả nhiệm vụ được truy xuất theo ngày tạo, ngày cập nhật hoặc hạn trong khoảng đã chọn. Không khẳng định nhiệm vụ được hoàn thành trong tuần nếu nguồn không có lịch sử chuyển trạng thái.
YÊU CẦU CẤU TRÚC KẾT QUẢ:
1. TỔNG QUAN TIẾN ĐỘ: Tóm lược số lượng việc đã hoàn thành, đang làm, tồn đọng và tỷ lệ tiến độ.
2. CÁC NHIỆM VỤ TRỄ HẠN & RỦI RO: Nêu rõ các [Task #ID] trễ hạn, có vướng mắc (blockers) và người phụ trách [User #ID].
3. DANH SÁCH VIỆC CẦN ƯU TIÊN TRONG TUẦN TỚI: Đề xuất các nhiệm vụ quan trọng cần tập trung xử lý.
4. DỮ LIỆU THIẾU HOẶC CẦN XÁC MINH: Nêu rõ nếu có nhiệm vụ thiếu hạn, thiếu ước lượng hoặc thông tin chưa đầy đủ.
"""

    elif task_type == 'meeting_minutes':
        specific_task = """
MỤC TIÊU: Tạo bản nháp Biên bản họp (Meeting Minutes Draft) từ ghi chú cuộc họp (FR-13).
YÊU CẦU CẤU TRÚC KẾT QUẢ:
1. THÔNG TIN CHUNG: Tiêu đề cuộc họp, thời gian, thành viên tham dự.
2. NỘI DUNG THẢO LUẬN CHÍNH: Các vấn đề trọng tâm đã trao đổi.
3. CÁC QUYẾT ĐỊNH ĐÃ THỐNG NHẤT: Quyết định chốt trong cuộc họp.
4. DANH SÁCH HÀNH ĐỘNG CẦN LÀM (ACTION ITEMS): 
   - Việc cần làm cụ thể
   - Người phụ trách đề xuất (chỉ chọn từ danh sách thành viên dự án [User #ID] nếu có ghi trong ghi chú, nếu không ghi rõ hãy để trống hoặc ghi "Cần phân công")
   - Hạn hoàn thành đề xuất (nếu không có thì ghi "Chưa xác định")
5. ĐIỂM CẦN TRƯỞNG NHÓM XÁC MINH TRƯỚC KHI LƯU CHÍNH THỨC.
"""

    elif task_type == 'assignment_suggestion':
        specific_task = """
MỤC TIÊU: Gợi ý 1 đến 3 thành viên phù hợp nhất để phân công nhiệm vụ (FR-14).
YÊU CẦU CẤU TRÚC KẾT QUẢ:
1. PHÂN TÍCH NHIỆM VỤ: Nêu yêu cầu kỹ năng, độ khó và độ ưu tiên của [Task #ID].
2. TOP 1-3 ỨNG VIÊN ĐỀ XUẤT:
   - Ứng viên 1: Tên [User #ID] | Lý do phù hợp (dựa vào kỹ năng, mức sẵn sàng) | Cảnh báo tải (nêu rõ số giờ tải hiện tại và có đang bị quá tải hay không).
   - Ứng viên 2 (nếu có): ...
   - Ứng viên 3 (nếu có): ...
3. CẢNH BÁO QUÁ TẢI & KHUYẾN NGHỊ: Cảnh báo nếu ứng viên tiềm năng đang quá tải hoặc thiếu thời gian.
4. LƯU Ý CHO TRƯỞNG NHÓM: Nhắc nhở Trưởng nhóm là người đưa ra quyết định phân công cuối cùng, AI không tự gán người phụ trách.
"""
        if staffing_options:
            count = staffing_options['requested_count']
            specific_task = f'''MỤC TIÊU: Gợi ý đúng {count} người đáp ứng nhu cầu từ dữ liệu nguồn.
Nếu số người eligible=true ít hơn {count}, trả toàn bộ người đủ điều kiện và nêu rõ số còn thiếu.
Không giới hạn cố định ba người. Chỉ chọn ứng viên eligible=true. Không bịa người/kỹ năng/số giờ.
Ưu tiên kỹ năng phù hợp, mức sẵn sàng, tải hiện tại/sau nhận việc và số việc trễ hạn.
Chỉ trả về danh sách ID theo thứ tự ưu tiên, mỗi dòng một [User #ID]. Không lặp ID, không cần viết diễn giải dài.
Máy chủ sẽ đối chiếu ID và tự gắn lý do bằng chứng, tải/giờ khả dụng, việc trễ và cảnh báo từ dữ liệu nguồn.
Nếu purpose=recruitment thì đây là tìm người bổ sung, không yêu cầu nhiệm vụ và không tạo nhiệm vụ giả.
PM phải chủ động chọn thêm người và phân công; không tự ghi dữ liệu.'''
    else:
        specific_task = "Hãy xử lý yêu cầu quản lý dự án sau dựa trên ngữ cảnh được cấp."

    user_note = f"\nYÊU CẦU BỔ SUNG TỪ NGƯỜI DÙNG: {user_extra_prompt}" if user_extra_prompt else ""

    full_prompt = f"""{base_instructions}
{specific_task}

[NGỮ CẢNH DỰ ÁN]
{context_text}
{user_note}

HÃY BẮT ĐẦU TẠO BẢN NHÁP / ĐỀ XUẤT NGAY BÂY GIỜ:"""

    return full_prompt
