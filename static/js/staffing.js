// Full candidate pool; suggestions never change membership or assignments automatically.
let staffingOffset=0,staffingTotal=0,staffingRequest=0,staffingTimer=null;
const staffingPageSize=12,staffingSelected=new Map();
let staffingLastResult=null;

document.addEventListener('DOMContentLoaded',()=>{
    document.getElementById('ai-user-prompt')?.addEventListener('input',()=>{
        if(currentAIMode==='assignment_suggestion'){
            if(!document.getElementById('ai-task-select').value&&document.getElementById('ai-user-prompt').value.trim())document.getElementById('ai-staffing-purpose').value='recruitment';
            scheduleStaffingPreview();
        }
    });
});
function buildStaffingPayload(autoPurpose=false){
    const task=document.getElementById('ai-task-select').value;
    const note=document.getElementById('ai-user-prompt').value.trim();
    const purpose=document.getElementById('ai-staffing-purpose');
    if(autoPurpose&&!task&&note)purpose.value='recruitment';
    document.getElementById('staffing-task-picker').hidden=purpose.value==='recruitment';
    return {staffing_version:2,purpose:purpose.value,candidate_scope:document.getElementById('ai-candidate-scope').value,
        requested_count:document.getElementById('ai-requested-count').value,user_note:note,
        task_id:purpose.value==='assignment'&&task?Number(task):null};
}
function clearStaffingRecommendations(){
    staffingLastResult=null;
    document.getElementById('staffing-recommendations').replaceChildren();
}
function staffingControlsChanged(){
    staffingSelected.clear();updateStaffingSelection();clearStaffingRecommendations();
    staffingOffset=0;loadStaffingPreview();
}
function scheduleStaffingPreview(){
    clearTimeout(staffingTimer);++staffingRequest;staffingOffset=0;clearStaffingRecommendations();
    staffingTimer=setTimeout(loadStaffingPreview,350);
}
async function loadStaffingPreview(){
    if(!currentProjectId||!canManageCurrentProject)return;
    const request=++staffingRequest;
    const summary=document.getElementById('staffing-pool-summary');
    try{
        const payload=buildStaffingPayload();
        const data=await apiRequest(`/api/projects/${currentProjectId}/staffing-preview`,jsonRequest('POST',{
            ...payload,search:document.getElementById('staffing-search').value,offset:staffingOffset,limit:staffingPageSize}));
        if(request!==staffingRequest)return;
        document.getElementById('ai-requested-count').value=data.requested_count;
        staffingTotal=data.total_visible;
        summary.textContent=`Toàn bộ nguồn: ${data.total_candidates} người · Đủ điều kiện: ${data.eligible_count} · Cần: ${data.requested_count}${data.missing_count?' · Thiếu '+data.missing_count+' người phù hợp':''}. Đang hiển thị ${data.candidates.length}/${data.total_visible} sau lọc.`;
        const context=document.getElementById('ai-assignment-context');
        context.textContent=data.task?`${data.task.title} · ${data.task.estimated_hours} giờ · Hạn: ${data.task.due_date||'Chưa có'} · ${data.task.labels||'Chưa khai báo kỹ năng'}. Tải tính trên mọi dự án đang hoạt động.`:
            data.purpose==='recruitment'?'Tìm người chưa thuộc dự án. Nhập nhu cầu, tạo gợi ý rồi chọn người để thêm.':'Chọn nhiệm vụ để đánh giá tải sau khi nhận việc. Danh sách không yêu cầu chọn thành viên trước.';
        const body=document.getElementById('staffing-candidates-body');
        body.innerHTML=data.candidates.map(c=>`<tr data-candidate-id="${c.user_id}">
            <td>${!c.in_project&&currentUser?.role==='leader'?`<input type="checkbox" aria-label="Chọn ${escapeHtml(c.full_name)}" data-staffing-select="${c.user_id}" ${staffingSelected.has(c.user_id)?'checked':''}>`:'—'}</td>
            <td><strong>${escapeHtml(c.full_name)}</strong><br>${escapeHtml(c.user_code||c.username)}<br>${c.in_project?'Trong dự án':'Ngoài dự án'}</td>
            <td>${escapeHtml(c.skills||'Chưa cập nhật')}<small>${escapeHtml(c.profile_warnings.join(' '))}</small></td>
            <td>${c.availability_percent}% / ${c.capacity_hours}h</td><td>${c.current_workload_hours}h / ${c.projected_workload_hours}h${c.is_projected_overloaded?'<br><strong class="workspace-warning">Quá tải</strong>':''}</td>
            <td>${c.overdue_task_count}</td><td>${escapeHtml(c.eligible?c.reason:c.not_recommended_reason)}${c.missing_estimate_count?'<br>Có việc chưa ước lượng; tải chưa đầy đủ.':''}
            ${c.in_project&&data.task&&currentUser?.role==='leader'?`<button class="btn btn-secondary" data-staffing-assign="${c.user_id}">Chọn phân công</button>`:''}</td></tr>`).join('')||'<tr><td colspan="7">Không có ứng viên trong bộ lọc.</td></tr>';
        body.querySelectorAll('[data-staffing-select]').forEach(input=>input.addEventListener('change',()=>{
            const c=data.candidates.find(c=>c.user_id===Number(input.dataset.staffingSelect));
            if(input.checked)staffingSelected.set(c.user_id,c);else staffingSelected.delete(c.user_id);
            updateStaffingSelection();
        }));
        body.querySelectorAll('[data-staffing-assign]').forEach(button=>button.addEventListener('click',()=>chooseStaffingAssignee(data.task.id,Number(button.dataset.staffingAssign))));
        document.getElementById('staffing-prev').disabled=staffingOffset===0;
        document.getElementById('staffing-next').disabled=staffingOffset+staffingPageSize>=staffingTotal;
        document.getElementById('staffing-page').textContent=`Trang ${Math.floor(staffingOffset/staffingPageSize)+1}/${Math.max(1,Math.ceil(staffingTotal/staffingPageSize))}`;
        updateStaffingSelection();
    }catch(error){if(request===staffingRequest){summary.textContent=error.message;document.getElementById('staffing-candidates-body').replaceChildren();}}
}
function updateStaffingSelection(){
    const button=document.getElementById('staffing-add-selected');
    button.disabled=!staffingSelected.size||currentUser?.role!=='leader';
    button.textContent=`Thêm người đã chọn (${staffingSelected.size})`;
}
function changeStaffingPage(delta){staffingOffset=Math.max(0,staffingOffset+delta*staffingPageSize);loadStaffingPreview();}
async function addSelectedStaffingCandidates(){
    if(!staffingSelected.size)return;
    if(!confirm(`Thêm ${staffingSelected.size} người vào dự án hiện tại? Hồ sơ năng lực mới nhất sẽ được dùng; nhiệm vụ chưa được giao.`))return;
    const button=document.getElementById('staffing-add-selected');button.disabled=true;
    try{
        const result=await apiRequest(`/api/projects/${currentProjectId}/members`,jsonRequest('POST',{
            user_ids:Array.from(staffingSelected.keys()),project_role:'member',use_professional_profile:true}));
        staffingSelected.clear();clearStaffingRecommendations();await loadStaffingPreview();showToast(result.message,'success');
    }catch(error){showToast(error.message,'error');}finally{updateStaffingSelection();}
}
function chooseStaffingAssignee(taskId,userId){
    window.location.href=`/kanban?${new URLSearchParams({task_id:taskId,suggested_assignee_id:userId})}`;
}
function renderStaffingRecommendations(result){
    const el=document.getElementById('staffing-recommendations');
    if(!result?.recommendations||currentAIMode!=='assignment_suggestion'){el.replaceChildren();return;}
    staffingLastResult=result;
    el.innerHTML=`<h3>Gợi ý ${result.recommendations.length}/${result.requested_count} người</h3><p>${result.missing_count?'Thiếu '+result.missing_count+' người đáp ứng điều kiện.':'Đã có đủ ứng viên theo yêu cầu.'} Thông tin bên dưới là dữ liệu lúc tạo bản nháp; thao tác thêm/giao việc luôn kiểm tra lại quyền và dữ liệu hiện tại.</p>`+
        result.recommendations.map(c=>`<article class="staffing-recommendation" data-recommended-id="${c.user_id}"><strong>${escapeHtml(c.full_name)}</strong><p>${escapeHtml(c.reason)}</p><p>${escapeHtml(c.skills||'Chưa khai báo kỹ năng')} · ${c.current_workload_hours}/${c.capacity_hours}h · ${c.overdue_task_count} việc trễ${c.is_projected_overloaded?' · Cảnh báo quá tải':''}</p>${currentUser?.role==='leader'?
            c.in_project&&result.task_id?`<button class="btn btn-secondary" data-recommend-assign="${c.user_id}">Chọn phân công</button>`:
            !c.in_project?`<button class="btn btn-secondary" data-recommend-add="${c.user_id}">Chọn thêm vào dự án</button>`:'':''}</article>`).join('');
    el.querySelectorAll('[data-recommend-assign]').forEach(button=>button.addEventListener('click',()=>chooseStaffingAssignee(result.task_id,Number(button.dataset.recommendAssign))));
    el.querySelectorAll('[data-recommend-add]').forEach(button=>button.addEventListener('click',()=>{
        const c=result.recommendations.find(c=>c.user_id===Number(button.dataset.recommendAdd));staffingSelected.set(c.user_id,c);
        const input=document.querySelector(`[data-staffing-select="${c.user_id}"]`);if(input)input.checked=true;updateStaffingSelection();
        showToast('Đã chọn. Bấm Thêm người đã chọn để xác nhận.','info');
    }));
}
