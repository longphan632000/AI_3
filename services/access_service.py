"""Project scope and archive guards shared by writes (FR-02, BR-08)."""
from database.connection import query_db
from services.validation import ValidationError


def require_active_project(project_id):
    project = query_db('SELECT id, is_archived FROM projects WHERE id=%s', (project_id,), one=True)
    if not project or project['is_archived']:
        raise ValidationError('Dự án không tồn tại hoặc đã lưu trữ; không thể thay đổi dữ liệu.')
    return project


def require_active_task(task):
    if not task or task['is_archived']:
        raise ValidationError('Nhiệm vụ không tồn tại hoặc đã lưu trữ.')
    require_active_project(task['project_id'])
    if task.get('sprint_id'):
        sprint = query_db('SELECT is_archived FROM sprints WHERE id=%s', (task['sprint_id'],), one=True)
        if sprint and sprint['is_archived']:
            raise ValidationError('Sprint đã lưu trữ; hãy khôi phục sprint trước khi sửa nhiệm vụ.')
