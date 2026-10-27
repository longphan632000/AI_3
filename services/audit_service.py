import json
from database.connection import execute_db, query_db

def log_audit(user_id, action, target_type, target_id=None, details=None, ip_address='127.0.0.1'):
    """
    Ghi nhật ký kiểm toán hệ thống (FR-02, NFR-09).
    Tuyệt đối không lưu mật khẩu hoặc khóa bí mật.
    """
    details_str = json.dumps(details, ensure_ascii=False) if details else None
    query = """
        INSERT INTO audit_logs (user_id, action, target_type, target_id, details_json, ip_address)
        VALUES (%s, %s, %s, %s, %s, %s);
    """
    return execute_db(query, (user_id, action, target_type, target_id, details_str, ip_address))

def get_recent_audit_logs(limit=50):
    query = """
        SELECT al.id, al.user_id, u.username, u.full_name, al.action, 
               al.target_type, al.target_id, al.details_json, al.ip_address, al.created_at
        FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.id
        ORDER BY al.created_at DESC
        LIMIT %s;
    """
    return query_db(query, (limit,))
