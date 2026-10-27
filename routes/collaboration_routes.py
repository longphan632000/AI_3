from services.validation import json_object
from flask import Blueprint, request, session, jsonify
from routes import login_required
from services.collaboration_service import (
    get_task_comments, add_comment,
    get_task_attachments, add_attachment,
    get_project_meeting_notes, get_meeting_note_by_id, create_meeting_note
)
from services.task_service import get_task_by_id
from services.project_member_service import check_user_project_role

collab_bp = Blueprint('collab_bp', __name__)


@collab_bp.route('/api/tasks/<int:task_id>/attachments', methods=['GET','POST'])
@login_required
def task_attachments_api(task_id):
    task = get_task_by_id(task_id)
    if not task:
        return jsonify(success=False,error='Nhiệm vụ không tồn tại.'), 404
    access, role = check_user_project_role(session['user_id'], task['project_id'], session['role'])
    if not access:
        return jsonify(success=False,error='Không có quyền truy cập tài liệu.'), 403
    if request.method == 'GET':
        attachments = get_task_attachments(task_id)
        for attachment in attachments:
            attachment['download_url'] = f"/api/attachments/{attachment['id']}/download"
            attachment.pop('file_path', None)
        return jsonify(success=True,attachments=attachments)
    if role not in ('leader','member') or session['role'] == 'admin':
        return jsonify(success=False,error='Bạn chỉ có quyền xem tài liệu.'), 403
    from services.attachment_service import upload_attachment, add_link
    if 'file' in request.files:
        identifier = upload_attachment(session['user_id'],task,request.files['file'])
    else:
        data = json_object()
        identifier = add_link(session['user_id'],task,data.get('name'),data.get('url'))
    return jsonify(success=True,attachment_id=identifier,message='Đã thêm tài liệu.'), 201


@collab_bp.route('/api/attachments/<int:attachment_id>/download', methods=['GET'])
@login_required
def download_attachment_api(attachment_id):
    from services.attachment_service import attachment_download
    from flask import send_file, redirect
    attachment, target = attachment_download(attachment_id)
    if not attachment:
        return jsonify(success=False,error='Tài liệu không tồn tại.'), 404
    access, _ = check_user_project_role(session['user_id'],attachment['project_id'],session['role'])
    if not access:
        return jsonify(success=False,error='Không có quyền tải tài liệu.'), 403
    if attachment['file_type'] == 'link':
        return redirect(attachment['file_path'])
    response = send_file(target,as_attachment=True,download_name=attachment['file_name'])
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

# Comments
@collab_bp.route('/api/tasks/<int:task_id>/comments', methods=['GET'])
@login_required
def get_comments_api(task_id):
    task = get_task_by_id(task_id)
    if not task:
        return jsonify({'success': False, 'error': 'Nhiệm vụ không tồn tại.'}), 404
        
    has_access, _ = check_user_project_role(session['user_id'], task['project_id'], session['role'])
    if not has_access:
        return jsonify({'success': False, 'error': 'Từ chối quyền truy cập.'}), 403
        
    comments = get_task_comments(task_id)
    return jsonify({'success': True, 'comments': comments}), 200

@collab_bp.route('/api/tasks/<int:task_id>/comments', methods=['POST'])
@login_required
def add_comment_api(task_id):
    task = get_task_by_id(task_id)
    if not task:
        return jsonify({'success': False, 'error': 'Nhiệm vụ không tồn tại.'}), 404
        
    has_access, _ = check_user_project_role(session['user_id'], task['project_id'], session['role'])
    if not has_access:
        return jsonify({'success': False, 'error': 'Từ chối quyền truy cập.'}), 403
        
    data = json_object()
    content = data.get('content')
    success, msg = add_comment(session['user_id'], task_id, content)
    status_code = 201 if success else 400
    return jsonify({'success': success, 'message' if success else 'error': msg}), status_code

# Meeting Notes
@collab_bp.route('/api/projects/<int:project_id>/meeting-notes', methods=['GET'])
@login_required
def get_notes_api(project_id):
    has_access, _ = check_user_project_role(session['user_id'], project_id, session['role'])
    if not has_access:
        return jsonify({'success': False, 'error': 'Từ chối quyền truy cập dự án.'}), 403
        
    notes = get_project_meeting_notes(project_id)
    return jsonify({'success': True, 'meeting_notes': notes}), 200

@collab_bp.route('/api/projects/<int:project_id>/meeting-notes', methods=['POST'])
@login_required
def create_note_api(project_id):
    has_access, _ = check_user_project_role(session['user_id'], project_id, session['role'])
    if not has_access:
        return jsonify({'success': False, 'error': 'Từ chối quyền truy cập dự án.'}), 403
        
    data = json_object()
    success, msg, note_id = create_meeting_note(
        user_id=session['user_id'],
        project_id=project_id,
        title=data.get('title'),
        meeting_date=data.get('meeting_date'),
        attendees=data.get('attendees', ''),
        content=data.get('content')
    )
    status_code = 201 if success else 400
    return jsonify({'success': success, 'message' if success else 'error': msg, 'note_id': note_id}), status_code
