import json
from database.connection import query_db, execute_db

def save_ai_history(project_id, requester_id, task_type, model_provider, prompt_version, data_references, result_summary, confirmation_status='draft', draft_id=None):
    """
    Lưu vết lịch sử sử dụng AI (FR-15).
    Tuyệt đối không lưu mật khẩu, API key hoặc secret.
    """
    refs_json = json.dumps(data_references, ensure_ascii=False) if data_references else None
    query = """
        INSERT INTO ai_history (draft_id, project_id, requester_id, task_type, model_provider,
                               prompt_version, data_references_json, result_summary, confirmation_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    return execute_db(query, (
        draft_id, project_id, requester_id, task_type, model_provider,
        prompt_version, refs_json, result_summary, confirmation_status
    ))

def get_ai_history(user_id, user_system_role, project_id=None, limit=50):
    """
    Xem lịch sử sử dụng AI (UC012 / D07).
    Chỉ dành cho Quản trị viên và Trưởng nhóm trong phạm vi quyền truy cập.
    """
    if user_system_role == 'admin':
        if project_id:
            query = """
                SELECT ah.id, ah.draft_id, ah.project_id, p.name AS project_name, ah.requester_id,
                       u.full_name AS requester_name, ah.task_type, ah.model_provider,
                       ah.prompt_version, ah.data_references_json, ah.result_summary,
                       ah.confirmation_status, ah.created_at
                FROM ai_history ah
                JOIN projects p ON ah.project_id = p.id
                JOIN users u ON ah.requester_id = u.id
                WHERE ah.project_id = %s
                ORDER BY ah.created_at DESC LIMIT %s;
            """
            return query_db(query, (project_id, limit))
        else:
            query = """
                SELECT ah.id, ah.draft_id, ah.project_id, p.name AS project_name, ah.requester_id,
                       u.full_name AS requester_name, ah.task_type, ah.model_provider,
                       ah.prompt_version, ah.data_references_json, ah.result_summary,
                       ah.confirmation_status, ah.created_at
                FROM ai_history ah
                JOIN projects p ON ah.project_id = p.id
                JOIN users u ON ah.requester_id = u.id
                ORDER BY ah.created_at DESC LIMIT %s;
            """
            return query_db(query, (limit,))
    else:
        # Trưởng nhóm chỉ xem trong các dự án mà mình làm Leader
        query = """
            SELECT ah.id, ah.draft_id, ah.project_id, p.name AS project_name, ah.requester_id,
                   u.full_name AS requester_name, ah.task_type, ah.model_provider,
                   ah.prompt_version, ah.data_references_json, ah.result_summary,
                   ah.confirmation_status, ah.created_at
            FROM ai_history ah
            JOIN projects p ON ah.project_id = p.id
            JOIN users u ON ah.requester_id = u.id
            JOIN project_members pm ON pm.project_id = p.id AND pm.user_id = %s AND pm.project_role = 'leader'
            ORDER BY ah.created_at DESC LIMIT %s;
        """
        params = [user_id]
        if project_id:
            query = query.replace('ORDER BY ah.created_at', 'WHERE ah.project_id = %s ORDER BY ah.created_at')
            params.append(project_id)
        params.append(limit)
        return query_db(query, tuple(params))
