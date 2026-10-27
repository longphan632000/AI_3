let editingTaskId = null;
let detailTaskId = null;
let taskPageOffset = 0;
const taskPageSize = 50;
// Kanban Board Controller (BR-01, FR-06)
let currentTasks = [];
let projectMembers = [];
let projectSprints = [];

document.addEventListener('DOMContentLoaded', () => {
    initKanbanPage();
});

async function initKanbanPage() {
    await projectReady;
    const createButton = document.getElementById('create-task-button');
    if (createButton) createButton.style.display = canManageCurrentProject ? '' : 'none';
    if (!currentProjectId) {
        showToast('Bạn chưa tham gia dự án nào.', 'info');
        return;
    }
    await loadFilterOptions();
    await loadKanbanTasks();
    setupDragAndDrop();
    setupFilterEvents();
}

async function loadFilterOptions() {
    try {
        // Tải danh sách thành viên dự án
        const memRes = await fetch(`/api/projects/${currentProjectId}/members`);
        const memData = await memRes.json();
        if (memData.success) {
            projectMembers = memData.members;
            const assigneeFilter = document.getElementById('filter-assignee');
            const taskAssigneeInput = document.getElementById('new-task-assignee');

            if (assigneeFilter) {
                assigneeFilter.innerHTML = '<option value="">Tất cả người phụ trách</option>';
                projectMembers.forEach(m => {
                    assigneeFilter.add(new Option(m.full_name, m.user_id));
                });
            }
            const supporters=document.getElementById('new-task-supporters');
            supporters.innerHTML='';
            projectMembers.filter(m=>m.account_status==='active'&&m.project_role!=='viewer').forEach(m=>supporters.add(new Option(m.full_name,m.user_id)));
            if (taskAssigneeInput) {
                taskAssigneeInput.innerHTML = '<option value="">Chưa phân công</option>';
                projectMembers.filter(m => m.account_status === 'active' && m.project_role !== 'viewer').forEach(m => {
                    taskAssigneeInput.add(new Option(`${m.full_name} (${m.project_role})`, m.user_id));
                });
            }
        }

        // Tải danh sách Sprint
        const spRes = await fetch(`/api/projects/${currentProjectId}/sprints`);
        const spData = await spRes.json();
        if (spData.success) {
            projectSprints = spData.sprints;
            const sprintFilter = document.getElementById('filter-sprint');
            const taskSprintInput = document.getElementById('new-task-sprint');

            if (sprintFilter) {
                sprintFilter.innerHTML = '<option value="">Tất cả Sprint</option>';
                projectSprints.forEach(s => {
                    sprintFilter.add(new Option(s.name, s.id));
                });

                // Đồng bộ từ URL param ?sprint_id=... nếu có
                const urlParams = new URLSearchParams(window.location.search);
                const sprintParam = urlParams.get('sprint_id');
                if (sprintParam) {
                    sprintFilter.value = sprintParam;
                }
            }
            if (taskSprintInput) {
                taskSprintInput.innerHTML = '<option value="">Không thuộc sprint</option>';
                projectSprints.forEach(s => {
                    taskSprintInput.add(new Option(s.name, s.id));
                });
            }
        }
    } catch (e) {
        console.error('Lỗi tải tùy chọn lọc:', e);
    }
}

async function loadKanbanTasks() {
    const sprintId = document.getElementById('filter-sprint')?.value || '';
    const assigneeId = document.getElementById('filter-assignee')?.value || '';
    const overdueOnly = document.getElementById('filter-overdue')?.checked ? 'true' : 'false';
    const keyword = document.getElementById('filter-keyword')?.value || '';

    const params=new URLSearchParams({sprint_id:sprintId,assignee_id:assigneeId,overdue_only:overdueOnly,keyword,
        priority:document.getElementById('filter-priority').value,status:document.getElementById('filter-status').value,
        due_from:document.getElementById('filter-due-from').value,due_to:document.getElementById('filter-due-to').value,
        sort_by:document.getElementById('filter-sort').value,sort_order:document.getElementById('filter-order').value,
        offset:taskPageOffset,limit:taskPageSize+1});
    const url = `/api/projects/${currentProjectId}/tasks?${params}`;

    try {
        const res = await fetch(url);
        const data = await res.json();
        if (data.success) {
            document.getElementById('tasks-prev').disabled=taskPageOffset===0;
            document.getElementById('tasks-next').disabled=data.tasks.length<=taskPageSize;
            document.getElementById('tasks-page').textContent=`Trang ${1+taskPageOffset/taskPageSize}`;
            currentTasks = data.tasks.slice(0,taskPageSize);
            renderKanbanBoard(currentTasks);
        } else { showToast(data.error||'Không tải được nhiệm vụ.','error'); }
    } catch (e) {
        showToast('Lỗi tải danh sách nhiệm vụ.', 'error');
    }
}

function renderKanbanBoard(tasks) {
    const columns = ['backlog', 'todo', 'in_progress', 'review', 'done'];
    const colCounts = { backlog: 0, todo: 0, in_progress: 0, review: 0, done: 0 };

    columns.forEach(col => {
        const bodyEl = document.getElementById(`col-body-${col}`);
        if (bodyEl) bodyEl.innerHTML = '';
    });

    tasks.forEach(t => {
        const col = t.status || 'backlog';
        if (colCounts.hasOwnProperty(col)) {
            colCounts[col]++;
            const bodyEl = document.getElementById(`col-body-${col}`);
            if (bodyEl) {
                bodyEl.appendChild(createTaskCardElement(t));
            }
        }
    });

    // Cập nhật số đếm trên header cột
    columns.forEach(col => {
        const countEl = document.getElementById(`col-count-${col}`);
        if (countEl) countEl.textContent = colCounts[col];
    });

    // Khởi tạo lại hiệu ứng 3D tilt cho các card mới render
    if (typeof init3DTiltEffects === 'function') {
        init3DTiltEffects();
    }
}

function createTaskCardElement(task) {
    const card = document.createElement('div');
    card.className = `task-card tilt-card ${task.is_overdue ? 'is-overdue' : ''}`;
    card.draggable = canManageCurrentProject || (currentProjectRole==='member' && (Number(task.assignee_id)===currentUser?.id || task.support_member_ids?.includes(currentUser?.id)));
    card.dataset.taskId = task.id;

    // Badges
    const priorityClass = `badge-${task.priority || 'medium'}`;
    const overdueBadge = task.is_overdue ? `<span class="badge badge-overdue">TRỄ HẠN</span>` : '';

    // Labels
    let labelsHtml = '';
    if (task.labels) {
        labelsHtml = task.labels.split(',').map(l => `<span class="task-label-tag">${escapeHtml(l.trim())}</span>`).join('');
    }

    // Assignee
    const assigneeName = task.assignee_name || 'Chưa phân công';
    const initial = assigneeName.charAt(0).toUpperCase();

    card.innerHTML = `
        <div class="task-header">
            <span class="task-id-badge">#TASK-${task.id}</span>
            <div style="display:flex; gap:4px; align-items:center;">
                ${overdueBadge}
                <span class="badge ${priorityClass}">${task.priority}</span>
            </div>
        </div>
        <div class="task-title" onclick="openTaskDetailDrawer(${task.id})">${escapeHtml(task.title)}</div>
        ${labelsHtml ? `<div class="task-labels">${labelsHtml}</div>` : ''}
        <div class="task-footer">
            <div class="task-meta-left">
                <span title="Thời gian dự kiến">⏱️ ${task.estimated_hours}h</span>
            </div>
            <div class="task-assignee" title="Người phụ trách: ${escapeHtml(assigneeName)}">
                <div class="task-avatar-mini">${escapeHtml(initial)}</div>
                <span>${escapeHtml(assigneeName.split(' ').pop())}</span>
            </div>
        </div>
    `;

    return card;
}

function setupDragAndDrop() {
    const columns = document.querySelectorAll('.kanban-column');

    document.addEventListener('dragstart', (e) => {
        const card = e.target.closest('.task-card');
        if (!card) return;
        card.classList.add('dragging');
        e.dataTransfer.setData('text/plain', card.dataset.taskId);
    });

    document.addEventListener('dragend', (e) => {
        const card = e.target.closest('.task-card');
        if (card) card.classList.remove('dragging');
        columns.forEach(c => c.classList.remove('drag-over'));
    });

    columns.forEach(col => {
        col.addEventListener('dragover', (e) => {
            e.preventDefault();
            col.classList.add('drag-over');
        });

        col.addEventListener('dragleave', (e) => {
            col.classList.remove('drag-over');
        });

        col.addEventListener('drop', async (e) => {
            e.preventDefault();
            col.classList.remove('drag-over');
            const taskId = e.dataTransfer.getData('text/plain');
            const newStatus = col.dataset.status;

            if (taskId && newStatus) {
                await updateTaskStatusApi(taskId, newStatus);
            }
        });
    });
}

async function updateTaskStatusApi(taskId, newStatus) {
    try {
        const res = await fetch(`/api/tasks/${taskId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            await loadKanbanTasks();
        } else {
            showToast(data.error || 'Không thể chuyển trạng thái.', 'error');
            await loadKanbanTasks();
        }
    } catch (e) {
        showToast('Lỗi máy chủ khi cập nhật trạng thái.', 'error');
        await loadKanbanTasks();
    }
}

function setupFilterEvents() {
    for(const id of ['filter-priority','filter-status','filter-due-from','filter-due-to','filter-sort','filter-order']) {
        document.getElementById(id).addEventListener('change',()=>{taskPageOffset=0;loadKanbanTasks();});
    }
    document.getElementById('filter-sprint')?.addEventListener('change', ()=>{taskPageOffset=0;loadKanbanTasks();});
    document.getElementById('filter-assignee')?.addEventListener('change', ()=>{taskPageOffset=0;loadKanbanTasks();});
    document.getElementById('filter-overdue')?.addEventListener('change', ()=>{taskPageOffset=0;loadKanbanTasks();});

    let debounceTimer;
    document.getElementById('filter-keyword')?.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(()=>{taskPageOffset=0;loadKanbanTasks();}, 300);
    });
}

// Modal Tạo Nhiệm Vụ
async function submitCreateTask(e) {
    e.preventDefault();
    const title = document.getElementById('new-task-title').value;
    const description = document.getElementById('new-task-desc').value;
    const sprintId = document.getElementById('new-task-sprint').value;
    const assigneeId = document.getElementById('new-task-assignee').value;
    const priority = document.getElementById('new-task-priority').value;
    const dueDate = document.getElementById('new-task-due').value;
    const estimatedHours = document.getElementById('new-task-hours').value;
    const labels = document.getElementById('new-task-labels').value;

    try {
        const res = await fetch(editingTaskId ? `/api/tasks/${editingTaskId}` : `/api/projects/${currentProjectId}/tasks`, {
            method: editingTaskId ? 'PUT' : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title, description,
                sprint_id: sprintId || null,
                assignee_id: assigneeId || null,
                priority,
                due_date: dueDate || null,
                estimated_hours: estimatedHours || 0,
                labels, blockers:document.getElementById('new-task-blockers').value,
                task_code:document.getElementById('new-task-code').value,
                support_member_ids:Array.from(document.getElementById('new-task-supporters').selectedOptions).map(o=>Number(o.value)),
                ...(editingTaskId ? {progress_percent:Number(document.getElementById('new-task-progress').value)} : {})
            })
        });
        const data = await res.json();
        if (data.success) {
            showToast(editingTaskId ? 'Đã cập nhật nhiệm vụ.' : 'Tạo nhiệm vụ thành công!', 'success');
            editingTaskId=null;
            taskPageOffset=0;
            closeModal('modal-create-task');
            document.getElementById('form-create-task').reset();

            // Đồng bộ bộ lọc để người dùng thấy ngay nhiệm vụ mới tạo
            const sprintFilter = document.getElementById('filter-sprint');
            const assigneeFilter = document.getElementById('filter-assignee');
            const overdueFilter = document.getElementById('filter-overdue');
            const keywordFilter = document.getElementById('filter-keyword');
            if (sprintFilter && sprintId) sprintFilter.value = sprintId;
            else if (sprintFilter) sprintFilter.value = '';
            if (assigneeFilter) assigneeFilter.value = '';
            if (overdueFilter) overdueFilter.checked = false;
            if (keywordFilter) keywordFilter.value = '';

            await loadKanbanTasks();
        } else {
            showToast(data.error || 'Lỗi khi tạo nhiệm vụ.', 'error');
        }
    } catch (e) {
        showToast('Lỗi kết nối máy chủ.', 'error');
    }
}

// Task Detail Drawer & Comments
async function openTaskDetailDrawer(taskId) {
    try {
        const res = await fetch(`/api/tasks/${taskId}`);
        const data = await res.json();
        if (data.success) {
            const task = data.task;
            detailTaskId=task.id;
            const canUpdate=canManageCurrentProject||(currentProjectRole==='member'&&(Number(task.assignee_id)===currentUser?.id||task.support_member_ids?.includes(currentUser?.id)));
            document.getElementById('task-detail-actions').innerHTML=(canManageCurrentProject?`<button class="btn btn-secondary" onclick="editTask(${task.id})">Sửa nhiệm vụ</button><button class="btn btn-secondary" onclick="archiveTask(${task.id})">Lưu trữ nhiệm vụ</button>`:'')+(canUpdate?`<label>Tiến độ (%) <input id="detail-progress" type="number" min="0" max="100" step="1" value="${task.progress_percent}" style="width:75px"></label><button class="btn btn-secondary" onclick="saveTaskProgress(${task.id})">Lưu tiến độ</button>`:'');
            if(canUpdate){
                const label=document.createElement('label');label.textContent='Trạng thái ';
                const select=document.createElement('select');select.id='detail-status';select.className='form-select';
                for(const [value,text] of Object.entries({backlog:'Tồn đọng',todo:'Cần làm',in_progress:'Đang làm',review:'Kiểm tra',done:'Hoàn thành'}))select.add(new Option(text,value,false,task.status===value));
                const button=document.createElement('button');button.className='btn btn-secondary';button.textContent='Lưu trạng thái';button.type='button';
                button.onclick=async()=>{await updateTaskStatusApi(task.id,select.value);await openTaskDetailDrawer(task.id);};
                label.append(select);document.getElementById('task-detail-actions').append(label,button);
            }
            const canCollaborate=currentProjectRole==='leader'||currentProjectRole==='member';
            for(const id of ['form-add-comment','attachment-upload-form','attachment-link-form']) document.getElementById(id).hidden=!canCollaborate;
            await loadTaskAttachments(task.id);
            document.getElementById('detail-task-title').textContent = task.title;
            document.getElementById('detail-task-id').textContent = `#TASK-${task.id}`;
            document.getElementById('detail-task-desc').textContent = task.description || 'Không có mô tả chi tiết.';
            document.getElementById('detail-task-assignee').textContent = task.assignee_name || 'Chưa phân công';
            document.getElementById('detail-task-due').textContent = task.due_date || 'Không có';
            document.getElementById('detail-task-hours').textContent = `${task.estimated_hours}h`;
            document.getElementById('detail-task-status').textContent = task.status.toUpperCase();

            const overdueEl = document.getElementById('detail-task-overdue-alert');
            if (overdueEl) {
                overdueEl.style.display = task.is_overdue ? 'block' : 'none';
            }

            document.getElementById('comment-task-id').value = task.id;
            await loadTaskComments(taskId);
            openModal('modal-task-detail');
        }
    } catch (e) {
        showToast('Lỗi lấy chi tiết nhiệm vụ.', 'error');
    }
}

async function loadTaskComments(taskId) {
    const listEl = document.getElementById('comments-list');
    if (!listEl) return;

    try {
        const res = await fetch(`/api/tasks/${taskId}/comments`);
        const data = await res.json();
        if (data.success) {
            if (data.comments.length === 0) {
                listEl.innerHTML = '<p style="color:var(--text-muted); font-size:0.85rem;">Chưa có bình luận nào.</p>';
            } else {
                listEl.innerHTML = data.comments.map(c => `
                    <div style="margin-bottom:12px; padding:10px; background:rgba(255,255,255,0.03); border-radius:8px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:4px; font-size:0.78rem;">
                            <strong style="color:var(--neon-cyan);">${escapeHtml(c.user_name)}</strong>
                            <span style="color:var(--text-muted);">${c.created_at}</span>
                        </div>
                        <div style="font-size:0.88rem; color:#e2e8f0;">${escapeHtml(c.content)}</div>
                    </div>
                `).join('');
            }
        }
    } catch (e) {
        listEl.innerHTML = '<p style="color:var(--neon-rose);">Lỗi tải bình luận.</p>';
    }
}

async function submitComment(e) {
    e.preventDefault();
    const taskId = document.getElementById('comment-task-id').value;
    const content = document.getElementById('new-comment-content').value;
    if (!content.trim()) return;

    try {
        const res = await fetch(`/api/tasks/${taskId}/comments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        const data = await res.json();
        if (data.success) {
            document.getElementById('new-comment-content').value = '';
            await loadTaskComments(taskId);
        } else {
            showToast(data.error, 'error');
        }
    } catch (e) {
        showToast('Lỗi gửi bình luận.', 'error');
    }
}



function changeTaskPage(direction) { taskPageOffset=Math.max(0,taskPageOffset+direction*taskPageSize);loadKanbanTasks(); }

function openTaskForm() {
    editingTaskId=null;
    document.getElementById('form-create-task').reset();
    document.getElementById('task-edit-progress').hidden=true;
    document.getElementById('task-submit-button').textContent='Tạo nhiệm vụ';
    openModal('modal-create-task');
}

async function editTask(id) {
    try {
        const {task:t}=await apiRequest(`/api/tasks/${id}`);
        editingTaskId=id;
        for(const [field,value] of Object.entries({title:t.title,desc:t.description,sprint:t.sprint_id,assignee:t.assignee_id,priority:t.priority,due:dateTimeInput(t.due_date),hours:t.estimated_hours,labels:t.labels,code:t.task_code,blockers:t.blockers,progress:t.progress_percent})) document.getElementById(`new-task-${field}`).value=value??'';
        for(const option of document.getElementById('new-task-supporters').options) option.selected=t.support_member_ids.includes(Number(option.value));
        document.getElementById('task-edit-progress').hidden=false;
        document.getElementById('task-submit-button').textContent='Lưu thay đổi';
        closeModal('modal-task-detail');openModal('modal-create-task');
    } catch(error){showToast(error.message,'error');}
}

async function archiveTask(id) {
    if(!confirm('Lưu trữ nhiệm vụ và giữ nguyên lịch sử?')) return;
    try{await apiRequest(`/api/tasks/${id}`,{method:'DELETE'});closeModal('modal-task-detail');await loadKanbanTasks();}
    catch(error){showToast(error.message,'error');}
}

async function saveTaskProgress(id) {
    try{await apiRequest(`/api/tasks/${id}/progress`,jsonRequest('PUT',{progress_percent:Number(document.getElementById('detail-progress').value)}));await openTaskDetailDrawer(id);await loadKanbanTasks();}
    catch(error){showToast(error.message,'error');}
}

async function loadTaskAttachments(id) {
    const data=await apiRequest(`/api/tasks/${id}/attachments`);
    document.getElementById('task-attachments').innerHTML=data.attachments.map(a=>`<p><a href="${a.download_url}" target="_blank" rel="noopener">${escapeHtml(a.file_name)}</a> · ${escapeHtml(a.uploader_name)}</p>`).join('')||'<p>Chưa có tài liệu.</p>';
}

async function submitAttachment(event) {
    event.preventDefault();
    const body=new FormData();body.append('file',document.getElementById('task-attachment-file').files[0]);
    try{await apiRequest(`/api/tasks/${detailTaskId}/attachments`,{method:'POST',body});event.target.reset();await loadTaskAttachments(detailTaskId);}
    catch(error){showToast(error.message,'error');}
}

async function submitTaskLink(event) {
    event.preventDefault();
    try{await apiRequest(`/api/tasks/${detailTaskId}/attachments`,jsonRequest('POST',{name:document.getElementById('task-link-name').value,url:document.getElementById('task-link-url').value}));event.target.reset();await loadTaskAttachments(detailTaskId);}
    catch(error){showToast(error.message,'error');}
}

async function showArchivedTasks() {
    try{
        const data=await apiRequest(`/api/projects/${currentProjectId}/tasks?archived=true&limit=500`);
        const modal=document.getElementById('modal-archived-projects');
        modal.querySelector('h3').textContent='Nhiệm vụ đã lưu trữ';
        document.getElementById('archived-project-list').innerHTML=data.tasks.map(t=>`<p>${escapeHtml(t.title)} <button class="btn btn-secondary" onclick="restoreTask(${t.id})">Khôi phục</button></p>`).join('')||'Chưa có nhiệm vụ lưu trữ.';
        openModal('modal-archived-projects');
    }catch(error){showToast(error.message,'error');}
}

async function restoreTask(id){try{await apiRequest(`/api/tasks/${id}/restore`,{method:'POST'});closeModal('modal-archived-projects');await loadKanbanTasks();}catch(error){showToast(error.message,'error');}}
