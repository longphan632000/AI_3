def build_ai_context(retrieved_data):
    """
    Module xây dựng ngữ cảnh sạch (context-builder skill).
    Đóng gói dữ liệu CSDL thành text context cô đọng, loại bỏ dữ liệu thừa,
    tuyệt đối không thêm bất kỳ dữ liệu nào ngoài CSDL.
    """
    data_type = retrieved_data.get('type')
    
    if data_type == 'weekly_summary_data':
        tasks = retrieved_data.get('tasks', [])
        lines = [
            f"KHOẢNG THỜI GIAN: Từ ngày {retrieved_data.get('week_start')} đến ngày {retrieved_data.get('week_end')}",
            "PHẠM VI: Nhiệm vụ được tạo, cập nhật hoặc đến hạn trong khoảng trên. Trạng thái và cờ trễ là dữ liệu hiện tại, không phải ảnh chụp lịch sử của tuần.",
            f"TỔNG SỐ NHIỆM VỤ ĐÃ TRUY XUẤT: {len(tasks)}"
        ]
        
        if not tasks:
            lines.append("LƯU Ý: Không có nhiệm vụ nào trong khoảng thời gian và phạm vi này.")
            return "\n".join(lines)
            
        lines.append("\nDANH SÁCH NHIỆM VỤ DỰ ÁN:")
        for t in tasks:
            overdue_str = " (ĐANG TRỄ HẠN!)" if t['is_overdue'] else ""
            assignee_ref = f" [User #{t['assignee_id']}]" if t['assignee_id'] else ''
            lines.append(
                f"- [Task #{t['task_id']}] '{t['title']}' | Trạng thái: {t['status'].upper()}{overdue_str} | "
                f"Người phụ trách: {t['assignee']}{assignee_ref} | "
                f"Ưu tiên: {t['priority']} | Hạn chót: {t['due_date']} | "
                f"Ước lượng: {t['estimated_hours']}h | Vướng mắc: {t['blockers']}"
            )
        return "\n".join(lines)
        
    elif data_type == 'meeting_minutes_data':
        note = retrieved_data.get('note')
        raw_notes = retrieved_data.get('raw_notes')
        members = retrieved_data.get('project_members', [])
        
        lines = []
        if note:
            lines.append(f"TIÊU ĐỀ CUỘC HỌP GỐC: {note['title']} [Note #{note['id']}]")
            lines.append(f"THỜI GIAN HỌP: {note['meeting_date']}")
            lines.append(f"THÀNH VIÊN THAM DỰ: {note['attendees']}")
            lines.append(f"NGƯỜI GHI CHÚ: {note['creator_name']}")
            lines.append("\nNỘI DUNG GHI CHÚ GỐC:")
            lines.append(note['content'])
        elif raw_notes:
            lines.append("NỘI DUNG GHI CHÚ CUỘC HỌP:")
            lines.append(raw_notes)
            
        lines.append("\nDANH SÁCH THÀNH VIÊN TRONG DỰ ÁN ĐỂ ĐỐI CHIẾU PHÂN CÔNG:")
        for m in members:
            lines.append(f"- [User #{m['id']}] {m['full_name']} (Vai trò: {m['project_role']}, Kỹ năng: {m['skills'] or 'Chưa rõ'})")
            
        return "\n".join(lines)
        
    elif data_type == 'assignment_suggestion_data':
        if retrieved_data.get('staffing_v2'):
            import json
            data = retrieved_data
            candidates = data['candidates'][:100]
            public_fields = ('user_id','full_name','skills','availability','capacity_hours','current_workload_hours',
                             'overdue_task_count','projected_workload_hours','is_projected_overloaded','in_project','eligible','reason')
            return ('DỮ LIỆU NHU CẦU VÀ ỨNG VIÊN ĐÃ ĐỐI CHIẾU:\n'+json.dumps({
                'purpose':data['purpose'],'candidate_scope':data['candidate_scope'],'task':data.get('task'),
                'requested_count':data['requested_count'],'eligible_count':data['eligible_count'],
                'required_skills':data['required_skills'],'total_candidates':data['total_candidates'],
                'missing_count':data['missing_count'],
                'candidates':[{k:c[k] for k in public_fields} for c in candidates]},ensure_ascii=False,default=str)+
                '\nTrích dẫn người dùng bằng [User #ID], nhiệm vụ bằng [Task #ID] khi có nhiệm vụ. Không tự thêm thành viên/giao việc.')
        task = retrieved_data.get('task')
        candidates = retrieved_data.get('candidates', [])
        
        if not task:
            return "LƯU Ý: Không tìm thấy nhiệm vụ tương ứng để gợi ý phân công."
            
        lines = [
            f"THÔNG TIN NHIỆM VỤ CẦN PHÂN CÔNG: [Task #{task['id']}] '{task['title']}'",
            f"Mô tả: {task['description'] or 'Không có'}",
            f"Mức ưu tiên: {task['priority']} | Hạn chót: {task['due_date'] or 'Không có'}",
            f"Ước lượng: {task['estimated_hours']}h | Nhãn/Kỹ năng yêu cầu: {task['labels'] or 'Không có'}",
            f"Vướng mắc hiện tại: {task['blockers'] or 'Không có'}",
            "\nDANH SÁCH THÀNH VIÊN ỨNG VIÊN TRONG DỰ ÁN (KÈM KỸ NĂNG VÀ TẢI HIỆN TẠI):"
        ]
        
        for c in candidates:
            overload_str = " (CẢNH BÁO: ĐANG QUÁ TẢI!)" if c['is_currently_overloaded'] else ""
            lines.append(
                f"- [User #{c['user_id']}] {c['full_name']} | Kỹ năng: {c['skills']} | "
                f"Mức sẵn sàng: {c['availability']} | Năng lực định mức: {c['capacity_hours']}h | "
                f"Tải công việc hiện tại: {c['current_workload_hours']}h{overload_str}"
            )
            
        return "\n".join(lines)
        
    return "Không có dữ liệu ngữ cảnh hợp lệ."
