"""Versioned, authorized draft review for FR-12/13/15."""
import json
from database.connection import query_db, execute_db, atomic
from services.validation import text, integer, ValidationError
from services.project_member_service import check_user_project_role
from services.access_service import require_active_project
from services.ai_response_validator import validate_ai_response
from services.audit_service import log_audit


def get_ai_draft(draft_id, user_id, system_role):
    draft = query_db('SELECT * FROM ai_drafts WHERE id=%s', (draft_id,), one=True)
    if not draft:
        return None
    access, role = check_user_project_role(user_id, draft['project_id'], system_role)
    if not access or (role in ('member','viewer') and draft['status'] != 'confirmed'
                      and (role == 'viewer' or draft['task_type'] != 'meeting_minutes'
                           or draft['created_by'] != user_id)):
        return None
    draft['structured_result'] = json.loads(draft.get('structured_result_json') or 'null')
    snapshot = json.loads(draft.get('validation_json') or '{}')
    draft['warnings'] = snapshot.get('warnings', [])
    draft['revisions'] = query_db('SELECT version,edited_by,created_at FROM ai_draft_revisions WHERE draft_id=%s ORDER BY version', (draft_id,))
    return draft


@atomic
def edit_ai_draft(draft_id, user_id, system_role, data):
    draft = get_ai_draft(draft_id, user_id, system_role)
    if not draft:
        return False, 'Bản nháp không tồn tại hoặc bạn không có quyền chỉnh sửa.'
    access, role = check_user_project_role(user_id, draft['project_id'], system_role)
    if system_role == 'admin' or role not in ('leader','member') or draft['status'] not in ('draft','needs_verification'):
        return False, 'Không thể chỉnh sửa bản đã xác nhận hoặc bản ngoài quyền.'
    require_active_project(draft['project_id'])
    version = integer(data.get('version', draft['version']), 'Phiên bản', minimum=1)
    content = text(data.get('draft_content',draft['draft_content']), 'Nội dung bản nháp', 500000, required=True)
    snapshot = json.loads(draft.get('validation_json') or '{}')
    structured = draft['structured_result']
    status = 'draft'
    warnings = []
    if draft['task_type'] == 'meeting_minutes':
        if not structured:
            status = 'needs_verification'
            warnings = ['Biên bản cũ thiếu dữ liệu cấu trúc; hãy tạo lại bản nháp.']
        else:
            structured = dict(structured)
            for key, label in (('title','Tiêu đề'),('decisions','Quyết định'),('action_items','Việc cần làm')):
                if key in data:
                    structured[key] = text(data[key], label, 200 if key == 'title' else 120000)
            warnings = snapshot.get('warnings', [])
            if warnings:
                status = 'needs_verification'
                if data.get('verified') is True and role == 'leader' and system_role == 'leader':
                    reason = text(data.get('review_note'), 'Ghi chú đối chiếu nguồn', 2000, required=True)
                    snapshot['review_note'] = reason
                    snapshot['reviewed_by'] = user_id
                    warnings = []
                    status = 'draft'
    else:
        refs = snapshot.get('source_refs')
        if not refs:
            return False, 'Bản cũ thiếu dữ liệu nguồn kiểm định; hãy tạo lại.'
        validation = validate_ai_response(content, {'task_type':draft['task_type']}, refs, snapshot.get('data'))
        status, warnings = validation['status'], validation['warnings']
    snapshot['warnings'] = warnings
    changed = execute_db('''UPDATE ai_drafts SET draft_content=%s,structured_result_json=%s,
        status=%s,validation_json=%s,version=version+1 WHERE id=%s AND version=%s AND status IN ('draft','needs_verification')''',
        (content,json.dumps(structured,ensure_ascii=False) if structured else None,status,
         json.dumps(snapshot,ensure_ascii=False),draft_id,version))
    if changed != 1:
        raise ValidationError('Bản nháp đã thay đổi; hãy tải lại phiên bản mới trước khi lưu.')
    execute_db('''INSERT INTO ai_draft_revisions(draft_id,version,edited_by,draft_content,structured_result_json)
        VALUES (%s,%s,%s,%s,%s)''', (draft_id,draft['version'],user_id,draft['draft_content'],draft.get('structured_result_json')))
    execute_db('UPDATE ai_history SET confirmation_status=%s,result_summary=%s WHERE draft_id=%s', (status,content[:300],draft_id))
    log_audit(user_id, 'EDIT_AI_DRAFT', 'AI_DRAFT', draft_id, {'from_version':version,'to_version':version+1,'status':status})
    return True, 'Đã lưu bản nháp và lịch sử chỉnh sửa.'
