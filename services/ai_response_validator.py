import re

def validate_ai_response(raw_response, structured_request, source_references, source_data=None):
    """
    Bộ kiểm định phản hồi AI (Response Validator).
    Kiểm tra:
    1. Cấu trúc phản hồi theo từng task_type.
    2. Đối chiếu các ID nhiệm vụ [Task #ID] và ID thành viên [User #ID] xuất hiện trong phản hồi
       với tập dữ liệu nguồn đã được phép truy xuất (source_references).
    3. Ngăn chặn ảo giác (hallucination) về người hoặc nhiệm vụ không có thật.
    """
    task_type = structured_request['task_type']
    if not isinstance(raw_response, str):
        raw_response = ''
    allowed_tasks = set(source_references.get('tasks', []))
    allowed_members = set(source_references.get('members', []))
    
    # Tìm kiếm các mẫu [Task #123] hoặc [User #123]
    task_pattern = r'\[Task\s*#(\d+)\]'
    member_pattern = r'\[User\s*#(\d+)\]'
    
    found_tasks = [int(m) for m in re.findall(task_pattern, raw_response, re.IGNORECASE)]
    found_members = [int(m) for m in re.findall(member_pattern, raw_response, re.IGNORECASE)]
    
    unauthorized_tasks = [tid for tid in found_tasks if tid not in allowed_tasks]
    unauthorized_members = [uid for uid in found_members if uid not in allowed_members]
    
    warnings = []
    status = 'draft'
    modern = bool(structured_request.get('staffing_v2'))
    expected = min(structured_request.get('requested_count',3), (source_data or {}).get('eligible_count',3)) if modern else None
    valid_count = len(set(found_members)) == expected if modern else 1 <= len(set(found_members)) <= 3
    if task_type == 'assignment_suggestion' and not valid_count:
        warnings.append(f'Đề xuất phải có đúng {expected} ứng viên đủ điều kiện.' if modern else 'Đề xuất phải có từ 1 đến 3 ứng viên, không trùng nhau.')
        status = 'needs_verification'
    if task_type == 'assignment_suggestion' and not (modern and expected==0) and not re.search(r'lý do|vì|phù hợp|kỹ năng|mức sẵn sàng', raw_response, re.I):
        warnings.append('Đề xuất chưa nêu lý do dựa trên kỹ năng hoặc mức sẵn sàng.')
        status = 'needs_verification'
    if task_type == 'weekly_summary' and source_data is not None:
        import json
        tasks = source_data.get('tasks', [])
        total = len(tasks)
        done = sum(task['status'] == 'done' for task in tasks)
        rate = round(done / total * 100, 1) if total else 0.0
        # ID citations aren't statistics. Validate all other numeric claims against
        # the snapshot and computed counts; percentages must match completion.
        narrative = re.sub(r'\[(?:Task|User)\s*#\d+\]', '', raw_response, flags=re.I)
        # Outline numbers and the known requirement label are document structure,
        # not claims about project statistics. Keep all numbers in the actual text.
        narrative = re.sub(r'^[ \t]*(?:#{1,6}[ \t]*)?(?:\*\*|__)?\d{1,3}[.)][ \t]+',
                           '', narrative, flags=re.M)
        narrative = re.sub(r'\bFR-12\b', '', narrative, flags=re.I)
        numbers = set(re.findall(r'\d+(?:[.,]\d+)?', narrative))
        allowed = set(re.findall(r'\d+(?:[.,]\d+)?', json.dumps(source_data, ensure_ascii=False)))
        allowed.update({str(total), str(done), str(total-done), str(rate), str(int(rate))})
        allowed.update(str(sum(task['status'] == state for task in tasks)) for state in ('backlog','todo','in_progress','review','done'))
        unsupported = {n for n in numbers if n.replace(',', '.') not in allowed}
        percentages = [float(n.replace(',', '.')) for n in re.findall(r'(\d+(?:[.,]\d+)?)\s*%', narrative)]
        if unsupported or any(abs(percent-rate) > 0.11 for percent in percentages):
            warnings.append('Số liệu AI không khớp dữ liệu nguồn; cần sửa trước khi xác nhận.')
            status = 'needs_verification'
    
    if unauthorized_tasks:
        warnings.append(f"Cảnh báo ảo giác: AI nhắc tới các mã nhiệm vụ không thuộc tập dữ liệu đã truy xuất: {unauthorized_tasks}")
        status = 'needs_verification'
        
    if unauthorized_members:
        warnings.append(f"Cảnh báo ảo giác: AI nhắc tới các mã thành viên không thuộc dự án: {unauthorized_members}")
        status = 'needs_verification'

    if not raw_response or not raw_response.strip():
        warnings.append('AI không trả về nội dung.')
        status = 'needs_verification'
    if task_type in ('weekly_summary', 'assignment_suggestion') and allowed_tasks and not found_tasks:
        warnings.append('Kết quả không trích dẫn nhiệm vụ nào trong dữ liệu nguồn.')
        status = 'needs_verification'
    if task_type == 'assignment_suggestion' and allowed_members and not found_members and not (modern and expected==0):
        warnings.append('Đề xuất không nêu thành viên dự án có thể đối chiếu.')
        status = 'needs_verification'
        
    # Xử lý nội dung hiển thị
    final_content = raw_response
    if warnings:
        warning_block = "\n\n> ⚠️ **LƯU Ý TỪ HỆ THỐNG KIỂM ĐỊNH (RESPONSE VALIDATOR):**\n" + "\n".join([f"> - {w}" for w in warnings])
        final_content += warning_block
        
    valid_task_refs = [f"Task #{tid}" for tid in set(found_tasks) if tid in allowed_tasks]
    valid_member_refs = [f"User #{uid}" for uid in set(found_members) if uid in allowed_members]
    
    return {
        'is_valid': not warnings,
        'status': status,
        'validated_draft': final_content,
        'source_references': valid_task_refs + valid_member_refs,
        'warnings': warnings
    }
