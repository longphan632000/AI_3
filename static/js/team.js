let teamMembers = [];
document.addEventListener('DOMContentLoaded', async () => {
    await projectReady;
    await loadTeamData();
});

async function loadTeamData() {
    const grid = document.getElementById('team-members-grid');
    if (!currentProjectId) { grid.textContent='Bạn chưa tham gia dự án nào.'; return; }
    try {
        const data = await apiRequest(`/api/projects/${currentProjectId}/workload-stats`);
        teamMembers = data.workload;
        const self = teamMembers.find(m=>Number(m.user_id)===Number(currentUser?.id));
        document.getElementById('edit-my-capacity').hidden = !self || !canEditMemberCapacity(self.user_id);
        document.getElementById('team-permission-help').textContent = canManageCurrentProject
            ? 'Bạn có thể cập nhật năng lực của các thành viên trong dự án.'
            : 'Bạn được cập nhật năng lực của mình. Chỉ Trưởng nhóm được chỉnh thông tin năng lực của người khác.';
        renderTeamMembers();
    } catch(error) { grid.textContent=error.message; }
}

function renderTeamMembers() {
    const term = (document.getElementById('team-search').value||'').trim().toLocaleLowerCase('vi');
    const members = teamMembers.filter(m=>[m.full_name,m.username,m.user_code,m.skills].join(' ').toLocaleLowerCase('vi').includes(term));
    document.getElementById('team-count').textContent=`${members.length}/${teamMembers.length} thành viên`;
    document.getElementById('team-members-grid').innerHTML = members.map(m=>`<article class="member-card" data-user-id="${m.user_id}">
        <div class="workspace-heading"><h3>${escapeHtml(m.full_name)}${Number(m.user_id)===Number(currentUser?.id)?' · Bạn':''}</h3><span class="badge">${escapeHtml(roleLabel(m.project_role))}</span></div>
        <p class="form-help">${escapeHtml(m.user_code||m.username)} · ${escapeHtml(m.email)}</p>
        <dl class="profile-details"><dt>Kỹ năng</dt><dd class="member-skills">${escapeHtml(m.skills||'Chưa cập nhật')}</dd>
        <dt>Mức sẵn sàng</dt><dd class="member-availability">${m.availability_percent}%</dd>
        <dt>Năng lực</dt><dd>${m.capacity_hours} giờ / sprint</dd><dt>Giờ khả dụng</dt><dd class="member-effective">${m.effective_capacity_hours} giờ</dd>
        <dt>Tải hiện tại</dt><dd class="member-workload">${m.current_workload_hours} giờ · ${m.active_task_count} việc (${m.overdue_task_count} trễ)</dd></dl>
        <p class="${m.is_overloaded?'workspace-warning':'workspace-success'}">${m.is_overloaded?'Quá tải':'Trong năng lực'}${m.missing_estimate_count?` · ${m.missing_estimate_count} việc chưa có ước lượng`:''}</p>
        ${m.configuration_warning?`<p class="workspace-warning">${escapeHtml(m.configuration_warning)}</p>`:''}
        <div class="workspace-actions"><a class="btn btn-secondary" href="/kanban?assignee_id=${m.user_id}">Xem nhiệm vụ</a>
        ${canEditMemberCapacity(m.user_id)?`<button class="btn btn-primary capacity-edit-button" data-user-id="${m.user_id}" onclick="editMemberCapacity(${m.user_id})">${Number(m.user_id)===Number(currentUser?.id)?'Cập nhật của tôi':'Cập nhật năng lực'}</button>`:''}</div>
    </article>`).join('') || '<p>Không tìm thấy thành viên phù hợp.</p>';
}
