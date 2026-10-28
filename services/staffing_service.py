"""Grounded, variable-size staffing recommendations and a complete candidate pool."""
import re
import unicodedata
from database.connection import query_db
from services.validation import text, integer, ValidationError
from services.member_profile_service import list_professional_profiles

SKILLS = {
    'backend':('backend','back-end','python','flask','django','fastapi','node.js','nodejs','java','spring','php','laravel','.net','c#','api','nestjs'),
    'frontend':('frontend','front-end','react','vue','angular','javascript','html','css','giao dien'),
    'kiem thu':('kiem thu','testing','tester','test','qa','automation','selenium','playwright'),
    'database':('database','co so du lieu','mysql','sql','sqlite','postgresql','mongodb'),
    'devops':('devops','docker','kubernetes','ci/cd','linux','aws','azure'),
    'python':('python','flask','django','fastapi'), 'java':('java','spring'),
    'javascript':('javascript','js','nodejs','node.js','react','vue','angular'),
    'react':('react',), 'flask':('flask',), 'mysql':('mysql',),
    'thiet ke':('thiet ke','ui/ux','figma','designer','design'),
}


def fold(value):
    value = unicodedata.normalize('NFD',str(value or '').lower().replace('đ','d'))
    return ''.join(c for c in value if unicodedata.category(c)!='Mn')


def contains(value, term):
    return bool(re.search(r'(?<!\w)'+re.escape(term)+r'(?!\w)',value))


def parse_staffing_requirements(note='', requested_count=3):
    note = text(note,'Chỉ dẫn bổ sung',4000)
    normalized = fold(note)
    count = integer(requested_count,'Số ứng viên',minimum=1,maximum=100)
    explicit = re.search(r'(?<!\d)(\d+)\s*(?:nguoi|thanh vien|ung vien|nhan su)\b',normalized)
    words = {'mot':1,'hai':2,'ba':3,'bon':4,'nam':5,'sau':6,'bay':7,'tam':8,'chin':9,'muoi':10}
    word_match = re.search(r'\b('+'|'.join(words)+r')\s+(?:nguoi|thanh vien|ung vien|nhan su)\b',normalized)
    if explicit:
        count = integer(explicit.group(1),'Số người trong chỉ dẫn',minimum=1,maximum=100)
    elif word_match:
        count = words[word_match.group(1)]
    required = [name for name in SKILLS if contains(normalized,name)]
    # Technical names outside the role groups are still matched literally.
    for token in ('c++','c#','typescript','golang','rust','swift','kotlin','php','laravel','nodejs','node.js','django','fastapi','sql','postgresql','mongodb','docker'):
        if contains(normalized,token) and token not in required:
            required.append(token)
    return {'user_note':note,'requested_count':count,'required_skills':required,'explicit_count':bool(explicit or word_match)}


def skill_evidence(skills, requirements):
    normalized = fold(skills)
    matched = []
    for requested in requirements:
        evidence = [alias for alias in SKILLS.get(requested,(requested,)) if contains(normalized,alias)]
        if evidence:
            matched.append({'requirement':requested,'evidence':evidence})
    return matched


def normalize_staffing_options(data, preview=False):
    criteria = parse_staffing_requirements(data.get('user_note',''), data.get('requested_count',3))
    task_id = integer(data.get('task_id'),'Nhiệm vụ',minimum=1,optional=True)
    purpose = data.get('purpose') or ('recruitment' if not task_id and criteria['user_note'] else 'assignment')
    if purpose not in ('assignment','recruitment'):
        raise ValidationError('Mục đích gợi ý không hợp lệ.')
    modern = bool(data.get('staffing_version')==2 or 'purpose' in data or 'candidate_scope' in data or
                  'requested_count' in data or criteria['explicit_count'] or criteria['required_skills'] or purpose=='recruitment')
    scope = data.get('candidate_scope') or ('system' if modern else 'project')
    if scope not in ('project','system'):
        raise ValidationError('Phạm vi ứng viên không hợp lệ.')
    if not preview and purpose=='assignment' and not task_id:
        raise ValidationError('Chọn nhiệm vụ hoặc nhập nhu cầu để tìm thêm thành viên.')
    if not preview and purpose=='recruitment' and not criteria['user_note']:
        raise ValidationError('Hãy nhập nhu cầu, ví dụ: Tôi cần 5 người backend.')
    return {**criteria,'purpose':purpose,'candidate_scope':scope,'task_id':task_id,'staffing_v2':modern}


def staffing_candidates(request, task=None):
    pid = request['project_id']
    purpose = request.get('purpose','assignment')
    scope = request.get('candidate_scope','system')
    profiles = list_professional_profiles()
    memberships = {m['user_id']:m for m in query_db('SELECT * FROM project_members WHERE project_id=%s',(pid,))}
    assigned = set()
    if task:
        assigned = {r['user_id'] for r in query_db('SELECT user_id FROM task_assignees WHERE task_id=%s',(task['id'],))}
        if task.get('assignee_id'):
            assigned.add(task['assignee_id'])
    requirements = request.get('required_skills',[])
    task_skills = fold(' '.join(str((task or {}).get(k) or '') for k in ('labels','title','description')))
    task_requirements = [name for name in SKILLS if contains(task_skills,name)]
    result = []
    for profile in profiles:
        uid = profile['user_id']
        membership = memberships.get(uid)
        if membership and membership['project_role']=='viewer':
            continue
        if scope=='project' and not membership:
            continue
        c = dict(profile)
        c['in_project'] = bool(membership)
        c['project_role'] = membership['project_role'] if membership else None
        if membership:
            from services.validation import availability_percent
            try:
                local_percent = availability_percent(membership['availability'])
            except ValidationError:
                local_percent = profile['availability_percent']
            local_cap = float(membership['capacity_hours'] if membership['capacity_hours'] is not None else 40)*local_percent/100
            c['capacity_hours'] = c['effective_capacity_hours'] = round(min(profile['capacity_hours'],local_cap),2)
            c['skills'] = ', '.join(dict.fromkeys(filter(None,(profile['skills'],membership['skills']))))
        evidence = skill_evidence(c['skills'],requirements)
        task_evidence = skill_evidence(c['skills'],task_requirements)
        c['skill_evidence'] = evidence
        c['task_skill_evidence'] = task_evidence
        c['already_assigned'] = uid in assigned
        extra = 0 if uid in assigned or (task or {}).get('status')=='done' else float((task or {}).get('estimated_hours') or 0)
        c['projected_workload_hours'] = round(c['current_workload_hours']+extra,2)
        c['is_projected_overloaded'] = c['projected_workload_hours']>c['capacity_hours']
        c['is_currently_overloaded'] = c['current_workload_hours']>c['capacity_hours']
        c['eligible'] = bool(c['capacity_hours']>0 and (not requirements or len(evidence)==len(requirements)) and
                             (purpose!='recruitment' or not membership))
        reason_evidence = evidence or task_evidence
        c['reason'] = ('Khớp '+', '.join(e['requirement']+' ('+', '.join(e['evidence'])+')' for e in reason_evidence)
                       if reason_evidence else 'Xếp theo mức sẵn sàng, tải và việc trễ; kỹ năng chưa có bằng chứng phù hợp nhu cầu.')
        if not c['eligible']:
            c['not_recommended_reason'] = ('Đã thuộc dự án' if purpose=='recruitment' and membership else
                'Không còn giờ khả dụng' if c['capacity_hours']<=0 else 'Chưa đủ bằng chứng đáp ứng các kỹ năng yêu cầu')
        result.append(c)
    result.sort(key=lambda c:(not c['eligible'],c['is_projected_overloaded'],c['overdue_task_count'],
        -len(c['skill_evidence']),-len(c['task_skill_evidence']),
        c['current_workload_hours']/c['capacity_hours'] if c['capacity_hours'] else float('inf'),c['user_id']))
    return result


def build_staffing_data(request, preview=False):
    task = None
    if request.get('purpose','assignment')=='assignment' and (request.get('task_id') or not preview):
        task = query_db('''SELECT id,sprint_id,title,description,priority,due_date,estimated_hours,labels,blockers,status,assignee_id
            FROM tasks WHERE id=%s AND project_id=%s AND is_archived=FALSE''', (request.get('task_id'),request['project_id']),one=True)
        if not task:
            raise ValidationError('Không tìm thấy nhiệm vụ hợp lệ của dự án.')
    candidates = staffing_candidates(request,task)
    eligible = [c for c in candidates if c['eligible']]
    selected = eligible[:request['requested_count']]
    return {'type':'assignment_suggestion_data','staffing_v2':True,'purpose':request.get('purpose','assignment'),
            'candidate_scope':request.get('candidate_scope','system'),'task':task,'candidates':candidates,
            'requested_count':request['requested_count'],'required_skills':request.get('required_skills',[]),
            'total_candidates':len(candidates),'eligible_count':len(eligible),'recommendations':selected,
            'missing_count':max(0,request['requested_count']-len(selected))}


def verified_staffing_result(data, raw_response=None):
    eligible = {c['user_id']:c for c in data['candidates'] if c['eligible']}
    ids = list(dict.fromkeys(int(v) for v in re.findall(r'\[User\s*#(\d+)\]',raw_response or '',re.I)))
    expected = min(data['requested_count'],len(eligible))
    valid = len(ids)==expected and all(uid in eligible for uid in ids)
    selected = [eligible[uid] for uid in ids] if valid else data['recommendations']
    return {**{k:data[k] for k in ('purpose','candidate_scope','requested_count','required_skills','total_candidates','eligible_count','missing_count')},
            'task_id':(data.get('task') or {}).get('id'),'recommendations':selected,
            'ranking_source':'provider_validated' if valid and expected else 'verified_skill_workload_ranking',
            'count_normalized':not valid}


def render_staffing_result(data, result=None):
    result = result or verified_staffing_result(data)
    task = data.get('task')
    lines = ['### '+(f"Gợi ý phân công [Task #{task['id']}] {task['title']}" if task else 'Gợi ý thành viên bổ sung vào dự án'),
             f"Yêu cầu: {result['requested_count']} người. Nguồn có {result['total_candidates']} ứng viên đang hoạt động; {result['eligible_count']} phù hợp điều kiện."]
    if result['required_skills']:
        lines.append('Kỹ năng cần: '+', '.join(result['required_skills'])+'.')
    for index,c in enumerate(result['recommendations'],1):
        lines += [f"\n#### {index}. [User #{c['user_id']}] {c['full_name']}",
            f"- Lý do: {c['reason']}", f"- Kỹ năng đã khai báo: {c['skills'] or 'Chưa cập nhật'}.",
            f"- Sẵn sàng: {c['availability']}; tải hiện tại {c['current_workload_hours']:g}h / {c['capacity_hours']:g}h khả dụng; {c['overdue_task_count']} việc trễ.",
            f"- Sau khi nhận việc: {c['projected_workload_hours']:g}h. "+('CẢNH BÁO QUÁ TẢI.' if c['is_projected_overloaded'] else 'Trong năng lực.'),
            '- '+('Đã thuộc dự án.' if c['in_project'] else 'Chưa thuộc dự án: cần PM chọn thêm trước khi giao nhiệm vụ.')]
    if result['missing_count']:
        lines.append(f"\nThiếu {result['missing_count']} người đáp ứng điều kiện so với yêu cầu. Hãy cập nhật hồ sơ/kỹ năng hoặc mở rộng phạm vi; không tạo thêm người không có trong dữ liệu.")
    lines.append('\nPM lựa chọn và xác nhận thao tác. Gợi ý không tự thêm thành viên hoặc phân công nhiệm vụ.')
    return '\n'.join(lines)
