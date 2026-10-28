let archiveOffset=0,archiveRequest=0;
document.addEventListener('DOMContentLoaded',async()=>{await projectReady;await loadArchivedProjectView();});
async function loadArchivedProjectView(){
    const request=++archiveRequest;
    try{
        const data=await apiRequest(`/api/projects/${archiveProjectId}/archive-details?offset=${archiveOffset}&limit=50`);
        if(request!==archiveRequest)return;
        document.getElementById('archive-error').hidden=true;document.getElementById('archive-content').hidden=false;
        const p=data.project,m=data.metrics;
        document.getElementById('archive-name').textContent=p.name;
        document.getElementById('archive-state').textContent=p.is_archived?'Dự án đang lưu trữ, dữ liệu ở chế độ chỉ xem.':'Dự án đã được khôi phục; dữ liệu dưới đây là bản hiện tại.';
        document.getElementById('restore-archived-project').hidden=!data.can_restore;
        const fields=[['Mã dự án',p.project_code],['Người tạo',p.creator_name],['Người lưu trữ',p.archiver_name||'Không xác định từ nhật ký'],['Thời điểm lưu trữ',p.archived_at],['Bắt đầu',p.start_date],['Kết thúc',p.end_date],['Trạng thái trước lưu trữ',p.pre_archive_status||'Chưa ghi nhận']];
        document.getElementById('archive-metadata').innerHTML=fields.map(([k,v])=>`<dt>${k}</dt><dd>${escapeHtml(v||'Chưa có')}</dd>`).join('');
        document.getElementById('archive-description').textContent=p.description||'Chưa có mô tả.';
        document.getElementById('archive-metrics').innerHTML=[['Nhiệm vụ chưa xóa mềm',m.total_tasks],['Đã hoàn thành',m.count_done],['Tỷ lệ hoàn thành',m.completion_rate+'%'],['Tiến độ trung bình',m.average_progress+'%']].map(([k,v])=>`<article><strong>${v}</strong><span>${k}</span></article>`).join('');
        document.getElementById('archive-members').innerHTML=data.members.map(member=>`<article class="member-card"><strong>${escapeHtml(member.full_name)}</strong><p>${escapeHtml(roleLabel(member.project_role))}</p><p class="form-help">${escapeHtml(member.skills||'Chưa cập nhật kỹ năng')} · ${escapeHtml(member.availability)} · ${member.capacity_hours}h</p></article>`).join('')||'<p>Không có thành viên.</p>';
        document.getElementById('archive-tasks').innerHTML=data.tasks.map(t=>`<details class="archive-task"><summary>${escapeHtml(t.task_code||'#'+t.id)} · ${escapeHtml(t.title)} · ${escapeHtml(t.status)} · ${t.progress_percent}%${t.is_archived?' · Đã lưu trữ riêng':''}</summary><p style="white-space:pre-wrap">${escapeHtml(t.description||'Chưa có mô tả')}</p><p class="form-help">Người phụ trách: ${escapeHtml(t.assignee_name||'Chưa phân công')} · ${t.estimated_hours}h · Hạn: ${escapeHtml(t.due_date||'Chưa có')}</p></details>`).join('')||'<p>Chưa có nhiệm vụ.</p>';
        document.getElementById('archive-page').textContent=`Trang ${1+archiveOffset/50} · ${data.total_tasks} nhiệm vụ`;
        document.getElementById('archive-prev').disabled=archiveOffset===0;
        document.getElementById('archive-next').disabled=archiveOffset+50>=data.total_tasks;
    }catch(error){document.getElementById('archive-error').hidden=false;document.getElementById('archive-error').textContent=error.message;document.getElementById('archive-content').hidden=true;document.getElementById('restore-archived-project').hidden=true;}
}
async function changeArchivePage(direction){archiveOffset=Math.max(0,archiveOffset+direction*50);await loadArchivedProjectView();}
