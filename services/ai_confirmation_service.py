"""Confirm reviewed AI drafts and persist actual structured meeting data."""

import json
from datetime import datetime

from database.connection import query_db, execute_db, atomic
from services.audit_service import log_audit
from services.project_member_service import check_user_project_role


@atomic
def confirm_ai_draft(draft_id, user_id, user_system_role):
    draft = query_db('SELECT * FROM ai_drafts WHERE id = %s', (draft_id,), one=True)
    if not draft:
        return False, 'Bản nháp không tồn tại.'
    has_access, project_role = check_user_project_role(user_id, draft['project_id'], user_system_role)
    if not has_access or project_role != 'leader' or user_system_role != 'leader':
        return False, 'Từ chối quyền: Chỉ Trưởng nhóm dự án mới có thẩm quyền xác nhận bản chính thức.'
    from services.access_service import require_active_project
    require_active_project(draft['project_id'])
    if draft['status'] != 'draft':
        return False, 'Bản nháp không ở trạng thái có thể xác nhận; hãy kiểm tra hoặc tạo lại.'

    structured = None
    if draft['task_type'] == 'meeting_minutes':
        try:
            structured = json.loads(draft.get('structured_result_json') or 'null')
        except json.JSONDecodeError:
            structured = None
        if not isinstance(structured, dict):
            return False, 'Biên bản cũ thiếu dữ liệu quyết định và việc cần làm có cấu trúc; hãy tạo lại bản nháp.'

    now = datetime.now()
    changed = execute_db("""UPDATE ai_drafts SET status='confirmed',confirmed_by=%s,confirmed_at=%s
        WHERE id=%s AND status='draft' AND version=%s""", (user_id,now,draft_id,draft['version']))
    if changed != 1:
        return False, 'Bản nháp đã được xử lý hoặc chỉnh sửa bởi yêu cầu khác.'
    if structured is not None:
        execute_db("""INSERT INTO meeting_minutes
            (project_id,meeting_note_id,title,summary,decisions,action_items,status,created_by,confirmed_by,confirmed_at)
            VALUES (%s,%s,%s,%s,%s,%s,'confirmed',%s,%s,%s)""",
            (draft['project_id'],structured.get('meeting_note_id'),structured.get('title') or 'Biên bản cuộc họp',
             draft['draft_content'],structured.get('decisions') or '',structured.get('action_items') or '',
             draft['created_by'],user_id,now))
    execute_db("UPDATE ai_history SET confirmation_status='confirmed' WHERE draft_id=%s", (draft_id,))
    log_audit(user_id, 'CONFIRM_AI_DRAFT', 'AI_DRAFT', draft_id, {
        'project_id': draft['project_id'], 'task_type': draft['task_type'],
    })
    return True, 'Đã xác nhận bản nháp thành văn bản chính thức thành công.'
