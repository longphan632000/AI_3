from services.project_member_service import check_user_project_role
from datetime import date

def analyze_ai_request(client_data, session_user_id, session_system_role):
    """
    Module phân tích yêu cầu AI (ai-request-analysis skill).
    Chuẩn hóa yêu cầu người dùng thành Structured Request JSON.
    Kiểm tra quyền hạn riêng cho từng chức năng theo D06:
    - weekly_summary: Chỉ Trưởng nhóm (FR-12)
    - meeting_minutes: Trưởng nhóm hoặc Thành viên được phân quyền (FR-13)
    - assignment_suggestion: Chỉ Trưởng nhóm (FR-14)
    requester_id lấy nghiêm ngặt từ session ở backend, không tin client!
    """
    task_type = client_data.get('task_type')
    project_id = client_data.get('project_id')
    
    if not task_type or task_type not in ['weekly_summary', 'meeting_minutes', 'assignment_suggestion']:
        return False, "Loại tác vụ AI không hợp lệ. Phải là weekly_summary, meeting_minutes hoặc assignment_suggestion.", None
        
    if not project_id:
        return False, "Thiếu project_id bắt buộc.", None
        
    try:
        project_id = int(project_id)
    except (ValueError, TypeError):
        return False, "project_id phải là số nguyên.", None
        
    # Kiểm tra quyền trong dự án
    has_access, project_role = check_user_project_role(session_user_id, project_id, session_system_role)
    if not has_access:
        return False, "Bạn không có quyền truy cập vào dự án này.", None
        
    # Kiểm tra phân quyền từng chức năng AI (D06)
    if task_type in ['weekly_summary', 'assignment_suggestion']:
        if project_role != 'leader' or session_system_role != 'leader':
            return False, f"Chỉ Trưởng nhóm dự án mới có quyền thực hiện tác vụ '{task_type}'.", None
            
    if task_type == 'meeting_minutes':
        # Cả Trưởng nhóm và Thành viên đều có thể tạo bản nháp (D05, D06)
        if project_role not in ['leader', 'member'] or session_system_role == 'admin':
            return False, "Bạn không có quyền tạo biên bản họp cho dự án này.", None

    structured_request = {
        "task_type": task_type,
        "project_id": project_id,
        "requester_id": session_user_id, # Lấy từ auth context
        "requester_role": project_role
    }
    
    # Kiểm tra các trường bắt buộc riêng của từng task_type
    if task_type == 'weekly_summary':
        week_start = client_data.get('week_start')
        week_end = client_data.get('week_end')
        if not week_start or not week_end:
            return False, "Tác vụ tóm tắt tiến độ tuần yêu cầu cung cấp week_start và week_end (YYYY-MM-DD).", None
        try:
            start_date = date.fromisoformat(str(week_start))
            end_date = date.fromisoformat(str(week_end))
        except ValueError:
            return False, 'Ngày phải theo định dạng YYYY-MM-DD.', None
        if start_date > end_date:
            return False, "week_start không được lớn hơn week_end.", None
            
        structured_request["week_start"] = start_date.isoformat()
        structured_request["week_end"] = end_date.isoformat()
        structured_request["sprint_id"] = client_data.get("sprint_id")
        
    elif task_type == 'meeting_minutes':
        meeting_note_id = client_data.get('meeting_note_id')
        raw_notes = client_data.get('raw_notes')
        if not meeting_note_id and not raw_notes:
            return False, "Tác vụ biên bản họp yêu cầu meeting_note_id hoặc nội dung raw_notes.", None
        if raw_notes is not None and not isinstance(raw_notes, str):
            return False, 'Nội dung biên bản phải là văn bản.', None
        if raw_notes and len(raw_notes) > 120_000:
            return False, 'Nội dung biên bản quá dài; hãy chia thành các phần nhỏ hơn.', None
        try:
            structured_request["meeting_note_id"] = int(meeting_note_id) if meeting_note_id else None
        except (ValueError, TypeError):
            return False, 'meeting_note_id không hợp lệ.', None
        structured_request["raw_notes"] = raw_notes
        
    elif task_type == 'assignment_suggestion':
        task_id = client_data.get('task_id')
        if not task_id:
            return False, "Tác vụ gợi ý phân công yêu cầu task_id nhiệm vụ cần phân công.", None
            
        try:
            structured_request["task_id"] = int(task_id)
        except (ValueError, TypeError):
            return False, 'task_id không hợp lệ.', None
        
    return True, "Yêu cầu hợp lệ.", structured_request
