from services.validation import json_object, integer
from flask import Blueprint, render_template, request, session, jsonify
from io import BytesIO
from routes import login_required
from services.ai_assistant_service import process_ai_request
from services.ai_confirmation_service import confirm_ai_draft, DraftVersionConflict
from services.ai_history_service import get_ai_history

ai_bp = Blueprint('ai_bp', __name__)

@ai_bp.route('/ai-assistant')
def ai_assistant_page():
    if 'user_id' not in session:
        return render_template('login.html')
    return render_template('ai_assistant.html', user=session)

@ai_bp.route('/api/ai', methods=['POST'])
@login_required
def process_ai_api():
    """
    API Trợ lý AI trung tâm (FR-12, FR-13, FR-14).
    Yêu cầu đi qua toàn bộ pipeline 5 bước kiểm định.
    Không nhận requester_id do client tự gửi!
    """
    client_data = json_object()
    res, status_code = process_ai_request(
        client_data=client_data,
        session_user_id=session['user_id'],
        session_system_role=session['role']
    )
    return jsonify(res), status_code

@ai_bp.route('/api/ai/drafts/<int:draft_id>/confirm', methods=['POST'])
@login_required
def confirm_draft_api(draft_id):
    """
    API Xác nhận bản nháp AI thành bản chính thức (UC010, D05).
    Chỉ Trưởng nhóm dự án mới có quyền xác nhận!
    """
    data = json_object() if request.is_json else {}
    version = integer(data['version'], 'Phiên bản', minimum=1) if 'version' in data else None
    try:
        success, msg = confirm_ai_draft(
            draft_id=draft_id,
            user_id=session['user_id'],
            user_system_role=session['role'],
            expected_version=version,
        )
    except DraftVersionConflict as error:
        return jsonify(success=False, error=str(error)), 409
    status_code = 200 if success else 403
    return jsonify({'success': success, 'message' if success else 'error': msg}), status_code

@ai_bp.route('/api/ai/history', methods=['GET'])
@login_required
def get_ai_history_api():
    """
    Xem lịch sử sử dụng AI (FR-15, UC012, D07).
    Chỉ dành cho Quản trị viên và Trưởng nhóm trong phạm vi quyền.
    """
    if session['role'] not in ['admin', 'leader']:
        return jsonify({'success': False, 'error': 'Từ chối quyền: Chỉ Quản trị viên hoặc Trưởng nhóm mới có thể xem lịch sử AI.'}), 403
        
    project_id = request.args.get('project_id', type=int)
    limit = request.args.get('limit', 50, type=int)
    
    history = get_ai_history(session['user_id'], session['role'], project_id, limit)
    return jsonify({'success': True, 'history': history}), 200

@ai_bp.route('/api/ai/upload-meeting-file', methods=['POST'])
@login_required
def upload_meeting_file_api():
    """
    Tải lên tệp ghi chú cuộc họp (.docx, .pdf, .txt, .md) để trích xuất nội dung
    phục vụ tóm tắt biên bản cuộc họp thông minh (FR-13).
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Không tìm thấy tệp đính kèm.'}), 400
        
    file = request.files['file']
    if not file or not file.filename:
        return jsonify({'success': False, 'error': 'Tệp không hợp lệ.'}), 400
        
    filename = file.filename.lower()
    extracted_text = ""
    warnings = []
    max_bytes = 5 * 1024 * 1024
    raw_bytes = file.read(max_bytes + 1)
    if len(raw_bytes) > max_bytes:
        return jsonify({'success': False, 'error': 'Tệp vượt quá 5 MB. Vui lòng chia nhỏ trước khi tải lên.'}), 413
    
    try:
        if filename.endswith('.docx'):
            from zipfile import ZipFile
            with ZipFile(BytesIO(raw_bytes)) as archive:
                if len(archive.infolist()) > 10000 or sum(item.file_size for item in archive.infolist()) > 30 * 1024 * 1024:
                    return jsonify(success=False,error='Tệp Word vượt quá giới hạn giải nén cho phép.'), 413
            import docx
            doc = docx.Document(BytesIO(raw_bytes))
            paragraphs = []
            for block in doc.iter_inner_content():
                if isinstance(block, docx.table.Table):
                    for row in block.rows:
                        row_text = ' | '.join(' / '.join(cell.text.splitlines()).strip()
                                              for cell in row.cells if cell.text.strip())
                        if row_text:
                            paragraphs.append(row_text)
                elif block.text.strip():
                    paragraphs.append(block.text.strip())
            extracted_text = '\n'.join(paragraphs)
            
        elif filename.endswith('.pdf'):
            import pypdf
            reader = pypdf.PdfReader(BytesIO(raw_bytes))
            pages = []
            empty_pages = []
            for number, page in enumerate(reader.pages, 1):
                page_text = (page.extract_text() or '').strip()
                if page_text:
                    pages.append(f'[Trang {number}]\n{page_text}')
                else:
                    empty_pages.append(number)
            if empty_pages:
                warnings.append(f"Không đọc được chữ ở trang {', '.join(map(str, empty_pages))}; nếu là bản quét, hãy dùng OCR trước.")
            extracted_text = '\n'.join(pages)
            
        elif filename.endswith('.txt') or filename.endswith('.md'):
            try:
                extracted_text = raw_bytes.decode('utf-8-sig')
            except UnicodeDecodeError:
                return jsonify({'success': False, 'error': 'Tệp văn bản cần dùng mã hóa UTF-8. Vui lòng chuyển mã rồi tải lại.'}), 400
                
        else:
            return jsonify({
                'success': False,
                'error': 'Định dạng tệp không được hỗ trợ. Vui lòng tải lên tệp .docx, .pdf, .txt hoặc .md.'
            }), 400
            
        extracted_text = extracted_text.strip()
        if not extracted_text:
            return jsonify({
                'success': False,
                'error': 'Tệp tải lên không chứa nội dung văn bản đọc được.'
            }), 400
        if len(extracted_text) > 120_000:
            return jsonify({'success': False, 'error': 'Nội dung sau trích xuất quá dài. Hãy chia tệp thành các phần nhỏ hơn.'}), 413
            
        word_count = len(extracted_text.split())
        return jsonify({
            'success': True,
            'filename': file.filename,
            'word_count': word_count,
            'extracted_text': extracted_text,
            'warnings': warnings,
            'message': f"Đã trích xuất thành công {word_count} từ từ tệp '{file.filename}'."
        }), 200
        
    except Exception:
        return jsonify({
            'success': False,
            'error': 'Không thể đọc tệp. Vui lòng kiểm tra định dạng, nội dung và thử lại.'
        }), 500

@ai_bp.route('/api/projects/<int:project_id>/meeting-minutes', methods=['GET'])
@login_required
def get_project_meeting_minutes_api(project_id):
    """
    Lấy danh sách các biên bản cuộc họp chính thức của dự án (UC010 / FR-13).
    """
    from database.connection import query_db
    from services.project_member_service import check_user_project_role
    
    has_access, _ = check_user_project_role(session['user_id'], project_id, session['role'])
    if not has_access:
        return jsonify({'success': False, 'error': 'Từ chối quyền truy cập dự án.'}), 403
        
    query = """
        SELECT m.id, m.project_id, m.title, m.summary, m.decisions, m.action_items,
               m.status, m.created_at, m.confirmed_at,
               u_cr.full_name AS creator_name,
               u_cf.full_name AS confirmer_name
        FROM meeting_minutes m
        LEFT JOIN users u_cr ON m.created_by = u_cr.id
        LEFT JOIN users u_cf ON m.confirmed_by = u_cf.id
        WHERE m.project_id = %s
        ORDER BY m.created_at DESC;
    """
    minutes = query_db(query, (project_id,))
    return jsonify({'success': True, 'minutes': minutes}), 200




@ai_bp.route('/api/ai/drafts/<int:draft_id>', methods=['GET','PUT'])
@login_required
def read_edit_draft_api(draft_id):
    from services.ai_draft_service import get_ai_draft, edit_ai_draft
    draft = get_ai_draft(draft_id, session['user_id'], session['role'])
    if not draft:
        return jsonify(success=False,error='Bản nháp không tồn tại hoặc bạn không có quyền truy cập.'), 404
    if request.method == 'GET':
        return jsonify(success=True,draft=draft)
    data = json_object()
    success,message = edit_ai_draft(draft_id,session['user_id'],session['role'],data)
    if not success:
        return jsonify(success=False,error=message), 403
    saved_version = integer(data.get('version',draft['version']), 'Phiên bản', minimum=1) + 1
    saved = get_ai_draft(draft_id,session['user_id'],session['role'])
    return jsonify(success=True,message=message,version=saved_version,status=saved['status'])
