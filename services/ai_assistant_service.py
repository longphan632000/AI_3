from services.ai_deadline import with_ai_budget, remaining_timeout
import json
from services.ai_request_analyzer import analyze_ai_request
from services.project_data_retriever import retrieve_ai_data
from services.context_builder import build_ai_context
from services.prompt_builder import build_ai_prompt
from services.ai_provider_service import AIProviderService
from services.ai_response_validator import validate_ai_response
from services.ai_history_service import save_ai_history
from services.meeting_minutes_service import create_meeting_minutes
from services.ai_errors import AIProviderError
from database.connection import execute_db, transaction

@with_ai_budget
def process_ai_request(client_data, session_user_id, session_system_role):
    """
    Module trung tâm điều phối Trợ lý AI (ai_assistant_service.py).
    Tuân thủ quy trình 5 bước AI-Augmented SDLC:
    Request -> Analyze -> Retrieve -> Context -> Prompt -> Provider -> Validate -> Draft Save -> Return
    """
    # 1. Phân tích yêu cầu và kiểm tra quyền RBAC (ai-request-analysis)
    valid, msg, structured_req = analyze_ai_request(client_data, session_user_id, session_system_role)
    if not valid:
        return {'success': False, 'error': msg}, 403
        
    from services.access_service import require_active_project
    require_active_project(structured_req['project_id'])
    # 2. Truy xuất dữ liệu an toàn bằng Parameterized SQL (project-data-retrieval)
    retrieved_data, source_refs = retrieve_ai_data(structured_req)
    
    structured_result = None
    try:
        ai_provider = AIProviderService()
        if getattr(type(ai_provider), 'bind_context', None):
            ai_provider.bind_context(structured_req, retrieved_data)
        if structured_req['task_type'] == 'meeting_minutes':
            content, structured_result, references, warnings = create_meeting_minutes(
                retrieved_data['note'], retrieved_data['raw_notes'], ai_provider
            )
            validation = {
                'validated_draft': content,
                'source_references': references,
                'status': 'needs_verification' if warnings else 'draft',
                'warnings': warnings,
            }
            extraction_warnings = client_data.get('extraction_warnings')
            if isinstance(extraction_warnings, list) and extraction_warnings:
                validation['warnings'].append('Tệp có trang không trích xuất được; hãy kiểm tra nội dung gốc hoặc dùng OCR.')
                validation['status'] = 'needs_verification'
        else:
            if structured_req['task_type'] == 'assignment_suggestion' and not retrieved_data.get('task') and not structured_req.get('staffing_v2'):
                return {'success': False, 'error': 'Không tìm thấy nhiệm vụ thuộc dự án.'}, 404
            context_text = build_ai_context(retrieved_data)
            user_note = client_data.get('user_note', '')
            if structured_req.get('staffing_v2'):
                prompt_text = build_ai_prompt(structured_req['task_type'],context_text,user_note,staffing_options=structured_req)
            else:
                prompt_text = build_ai_prompt(structured_req['task_type'], context_text, user_note)
            if structured_req.get('staffing_v2'):
                raw_response = ai_provider.generate_response(prompt_text,max_output_tokens=2048) if retrieved_data['eligible_count'] else ''
            else:
                raw_response = ai_provider.generate_response(prompt_text)
            if structured_req.get('staffing_v2'):
                from services.staffing_service import verified_staffing_result, render_staffing_result
                structured_result = verified_staffing_result(retrieved_data,raw_response)
                raw_response = render_staffing_result(retrieved_data,structured_result)
                if structured_result['count_normalized'] or not structured_result['recommendations']:
                    if getattr(type(ai_provider),'record_verified_ranking',None):
                        ai_provider.record_verified_ranking()
            validation = validate_ai_response(raw_response, structured_req, source_refs, retrieved_data)
            if structured_req['task_type'] == 'weekly_summary':
                tasks = retrieved_data.get('tasks', [])
                total = len(tasks)
                done = sum(task['status'] == 'done' for task in tasks)
                rate = round(done / total * 100, 1) if total else 0.0
                validation['validated_draft'] = f'**Số liệu từ hệ thống:** {done}/{total} nhiệm vụ hoàn thành ({rate}%).\n\n' + validation['validated_draft']
    except ValueError as error:
        return {'success': False, 'error': str(error)}, 422
    except AIProviderError as error:
        return {'success': False, 'error': str(error), 'error_code': error.code}, 503
    
    remaining_timeout(1)
    # 7. Lưu bản nháp vào bảng ai_drafts để Trưởng nhóm xem xét và xác nhận (UC010)
    # Do not duplicate the entire uploaded document in input_params_json.
    input_params = {key: value for key, value in structured_req.items() if key != 'raw_notes'}
    if structured_req['task_type'] == 'meeting_minutes':
        input_params['source_chars'] = len(structured_req.get('raw_notes') or '')
    input_params_str = json.dumps(input_params, ensure_ascii=False)
    source_refs_str = json.dumps(validation['source_references'], ensure_ascii=False)
    
    query = """
        INSERT INTO ai_drafts (project_id, task_type, input_params_json, draft_content,
                               source_references_json, structured_result_json, status, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """
    # Draft, validation snapshot and history are one atomic write.
    with transaction():
        return _persist_result(query, structured_req, input_params_str, source_refs_str,
                               structured_result, validation, session_user_id, ai_provider,
                               source_refs, retrieved_data)


def _persist_result(query, structured_req, input_params_str, source_refs_str,
                    structured_result, validation, session_user_id, ai_provider,
                    source_refs, retrieved_data):
    draft_id = execute_db(query, (
        structured_req['project_id'],
        structured_req['task_type'],
        input_params_str,
        validation['validated_draft'],
        source_refs_str,
        json.dumps(structured_result, ensure_ascii=False, default=str) if structured_result else None,
        validation['status'],
        session_user_id
    ))
    engine = ai_provider.execution_metadata() if getattr(type(ai_provider), 'execution_metadata', None) else {}
    snapshot = {'source_refs': source_refs, 'data': retrieved_data if structured_req['task_type'] != 'meeting_minutes' else {},
                'warnings': validation['warnings'], 'original_status': validation['status']}
    snapshot['engine'] = engine
    execute_db('UPDATE ai_drafts SET validation_json=%s WHERE id=%s',
               (json.dumps(snapshot, ensure_ascii=False, default=str), draft_id))
    
    # 8. Ghi lịch sử sử dụng AI theo FR-15 (không chứa API key / secret)
    save_ai_history(
        project_id=structured_req['project_id'],
        requester_id=session_user_id,
        task_type=structured_req['task_type'],
        model_provider=ai_provider.provider_name,
        prompt_version='v1.0',
        data_references=validation['source_references'],
        result_summary=validation['validated_draft'][:300] + "...",
        confirmation_status=validation['status'],
        draft_id=draft_id
    )
    
    # 9. Trả kết quả bản nháp cho client
    return {
        'success': True,
        'draft_id': draft_id,
        'version': 1,
        'result': validation['validated_draft'],
        'source_references': validation['source_references'],
        'status': validation['status'], # 'draft' hoặc 'needs_verification'
        'warnings': validation['warnings'],
        'engine': engine,
        'structured_result': structured_result,
    }, 200

