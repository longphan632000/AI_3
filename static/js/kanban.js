let editingTaskId = null;
let detailTaskId = null;
let taskPageOffset = 0;
const taskPageSize = 50;
// Kanban Board Controller (BR-01, FR-06)
let currentTasks = [];
let projectMembers = [];
let projectSprints = [];
let kanbanRequest = 0;
let lastTaskDragEndedAt = 0;
window.taskDragActive = false;
const taskStatusLabels = {backlog:'Tồn đọng',todo:'Cần làm',in_progress:'Đang làm',review:'Kiểm tra',done:'Hoàn thành'};

function canUpdateTask(task) {
    if (typeof task.can_update_progress === 'boolean') return task.can_update_progress;
    const uid=Number(currentUser?.id);
    return !task.is_archived && (canManageCurrentProject || (currentProjectRole==='member' &&
        (Number(task.assignee_id)===uid || (task.support_member_ids||[]).some(id=>Number(id)===uid))));
}

document.addEventListener('DOMContentLoaded', () => {
    initKanbanPage();
});

async function initKanbanPage() {
    setupKanbanLayout();
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
    setupMemberProgressControls();
    const params=new URLSearchParams(location.search),suggestedTask=params.get('task_id'),suggestedUser=params.get('suggested_assignee_id');
    if(canManageCurrentProject&&suggestedTask&&suggestedUser){
        await editTask(Number(suggestedTask));
        const input=document.getElementById('new-task-assignee');
        if(Array.from(input.options).some(option=>option.value===suggestedUser))input.value=suggestedUser;
        else showToast('Ứng viên chưa thuộc dự án hoặc không còn đủ quyền; hãy cập nhật danh sách.','error');
    }
}

function setupMemberProgressControls() {
    if(currentProjectRole!=='member')return;
    const bar=document.querySelector('.kanban-filter-bar');
    if(!bar||document.getElementById('kanban-my-tasks'))return;
    const button=document.createElement('button');
    button.id='kanban-my-tasks';button.type='button';button.className='btn btn-secondary kanban-my-tasks';
    button.textContent='Việc của tôi';button.title='Nhiệm vụ tôi phụ trách hoặc hỗ trợ';
    button.setAttribute('aria-label','Chỉ xem nhiệm vụ tôi phụ trách hoặc hỗ trợ');
    button.onclick=()=>{
        const select=document.getElementById('filter-assignee'),ownId=String(currentUser.id);
        select.value=select.value===ownId?'':ownId;
        select.dispatchEvent(new Event('change',{bubbles:true}));
    };
    bar.insertBefore(button,document.getElementById('kanban-filter-panel'));
    const help=document.createElement('p');help.id='kanban-member-progress-help';help.className='form-help kanban-member-progress-help';help.hidden=true;
    help.textContent='Chưa có nhiệm vụ bạn phụ trách hoặc hỗ trợ khớp bộ lọc. Hãy đổi bộ lọc hoặc nhờ PM phân công nhiệm vụ.';
    document.querySelector('.kanban-board').before(help);
    updateMemberProgressControls();
}

function updateMemberProgressControls() {
    const button=document.getElementById('kanban-my-tasks');
    if(!button)return;
    const active=document.getElementById('filter-assignee').value===String(currentUser.id);
    button.setAttribute('aria-pressed',String(active));
    const help=document.getElementById('kanban-member-progress-help');
    if(help)help.hidden=!active||currentTasks.length>0;
}

// A running server or an already-open tab may still carry the previous HTML.
// Move its existing controls into the current layout without replacing task data.
function ensureKanbanWorkspace() {
    const existing=document.querySelector('.kanban-workspace');
    if(existing)return existing;
    const board=document.querySelector('.kanban-board');
    const main=board?.parentElement;
    const heading=main?.querySelector('.kanban-toolbar');
    const filterBody=main?.querySelector('.kanban-filters');
    const search=document.getElementById('filter-keyword');
    const pagination=document.getElementById('tasks-prev')?.parentElement;
    if(!board||!heading||!filterBody||!search||!pagination)return null;
    const filterBar=filterBody.parentElement;
    const workspace=document.createElement('section');
    workspace.className='kanban-workspace';workspace.setAttribute('aria-label','Bảng nhiệm vụ');
    main.insertBefore(workspace,heading);
    heading.classList.add('kanban-heading');
    const caption=heading.querySelector('p');
    if(caption)caption.textContent='Kéo thẻ sang cột khác hoặc chọn Cập nhật để thay đổi tiến độ.';
    const createButton=document.getElementById('create-task-button');
    if(createButton){
        createButton.setAttribute('aria-label','Tạo nhiệm vụ mới');createButton.title='Tạo nhiệm vụ mới';
        createButton.innerHTML='<span aria-hidden="true">+</span><span class="create-task-label">Tạo nhiệm vụ mới</span>';
    }
    filterBar.className='kanban-filter-bar';filterBar.removeAttribute('style');
    search.removeAttribute('style');search.type='search';search.setAttribute('aria-label','Tìm kiếm nhiệm vụ');
    filterBar.prepend(search);
    for(const [id,label] of [['filter-sprint','Sprint'],['filter-assignee','Người phụ trách']]){
        const select=document.getElementById(id);
        if(select&&!select.closest('label')){
            const wrapper=document.createElement('label');wrapper.textContent=label;
            select.before(wrapper);wrapper.append(select);
        }
    }
    for(const label of Array.from(pagination.children).filter(el=>el.tagName==='LABEL'))filterBody.append(label);
    const archivedButton=pagination.querySelector('[data-project-manager]');
    if(archivedButton){archivedButton.classList.add('kanban-archived-tasks');filterBody.append(archivedButton);}
    filterBody.querySelectorAll('input,select').forEach(el=>el.removeAttribute('style'));
    const overdueLabel=document.getElementById('filter-overdue')?.closest('label');
    if(overdueLabel){overdueLabel.removeAttribute('style');overdueLabel.classList.add('kanban-overdue-filter');}
    const panel=document.createElement('details');panel.id='kanban-filter-panel';panel.className='kanban-filter-panel';
    panel.innerHTML='<summary>Bộ lọc <span id="kanban-filter-count" class="column-count" hidden>0</span></summary>';
    panel.append(filterBody);filterBar.append(panel);
    if(document.getElementById('archived-projects-button')){
        const projects=document.createElement('details');projects.id='kanban-project-panel';projects.className='kanban-filter-panel kanban-project-panel';
        projects.innerHTML='<summary>Dự án</summary><div id="kanban-project-actions" class="kanban-filters kanban-project-actions"></div>';
        filterBar.append(projects);
    }
    pagination.className='kanban-pagination';pagination.removeAttribute('style');
    const hint=document.createElement('span');hint.className='kanban-drag-hint';hint.textContent='Kéo bằng tay nắm ⠿ để chuyển cột';pagination.prepend(hint);
    workspace.append(heading,filterBar,board,pagination);
    const modal=document.getElementById('modal-task-detail');
    if(modal){
        modal.setAttribute('role','dialog');modal.setAttribute('aria-modal','true');modal.setAttribute('aria-labelledby','detail-task-title');
        const close=modal.querySelector('.modal-header .btn-icon');
        if(close){close.setAttribute('aria-label','Đóng chi tiết nhiệm vụ');close.onclick=closeTaskDetail;}
    }
    return workspace;
}

function setupKanbanLayout() {
    const workspace=ensureKanbanWorkspace();
    if(!workspace)return;
    workspace.parentElement.classList.add('kanban-content');
    const projectActions=document.getElementById('kanban-project-actions');
    if(projectActions){
        const commands=document.querySelectorAll('.project-select-container > button,[onclick="openEditProjectModal()"],[onclick="deleteCurrentProject()"],#archived-projects-button');
        for(const button of commands){
            const parent=button.parentElement;
            projectActions.append(button);
            if(parent.parentElement?.classList.contains('app-main'))parent.hidden=true;
        }
        projectActions.addEventListener('click',event=>{
            if(event.target.closest('button'))document.getElementById('kanban-project-panel').open=false;
        });
    }
    let layoutFrame=0;
    const fit=()=>{
        cancelAnimationFrame(layoutFrame);
        layoutFrame=requestAnimationFrame(()=>{
            const top=workspace.getBoundingClientRect().top+window.scrollY;
            const bottomPadding=parseFloat(getComputedStyle(workspace.parentElement).paddingBottom)||0;
            workspace.style.height=`${Math.max(420,innerHeight-top-bottomPadding)}px`;
        });
    };
    const observer=new ResizeObserver(fit);
    for(const el of document.querySelectorAll('.app-header,.sync-banner,.kanban-heading,.kanban-pagination'))observer.observe(el);
    window.addEventListener('resize',fit);
    window.visualViewport?.addEventListener('resize',fit);
    fit();
    const panels=Array.from(document.querySelectorAll('.kanban-filter-panel'));
    document.addEventListener('click',event=>{
        panels.forEach(panel=>{if(!panel.contains(event.target))panel.open=false;});
    });
    document.addEventListener('keydown',event=>{
        const panel=panels.find(item=>item.open);
        if(event.key==='Escape'&&panel){
            panel.open=false;panel.querySelector('summary').focus();return;
        }
        const modal=document.getElementById('modal-task-detail');
        if(!modal.classList.contains('active'))return;
        if(event.key==='Escape'){event.preventDefault();closeTaskDetail();}
        if(event.key==='Tab'){
            const controls=Array.from(modal.querySelectorAll('button,input,select,a[href],textarea')).filter(el=>!el.disabled&&el.getClientRects().length);
            const first=controls[0],last=controls[controls.length-1];
            if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
            else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
        }
    });
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
                const fromUrl=new URLSearchParams(location.search).get('assignee_id');
                if(fromUrl&&Array.from(assigneeFilter.options).some(o=>o.value===fromUrl))assigneeFilter.value=fromUrl;
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
    const request=++kanbanRequest;
    const statusFromUrl=new URLSearchParams(location.search).get('status');
    if(!document.getElementById('filter-status').dataset.initialized){
        if(statusFromUrl in taskStatusLabels)document.getElementById('filter-status').value=statusFromUrl;
        document.getElementById('filter-status').dataset.initialized='true';
    }
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
    const filterCount=['filter-sprint','filter-assignee','filter-priority','filter-status','filter-due-from','filter-due-to']
        .filter(id=>document.getElementById(id).value).length+(overdueOnly==='true'?1:0)+(keyword.trim()?1:0);
    const filterBadge=document.getElementById('kanban-filter-count');
    if(filterBadge){filterBadge.textContent=filterCount;filterBadge.hidden=filterCount===0;}

    try {
        const res = await fetch(url);
        const data = await res.json();
        if(request!==kanbanRequest)return;
        if (data.success) {
            document.getElementById('tasks-prev').disabled=taskPageOffset===0;
            document.getElementById('tasks-next').disabled=data.tasks.length<=taskPageSize;
            document.getElementById('tasks-page').textContent=`Trang ${1+taskPageOffset/taskPageSize}`;
            currentTasks = data.tasks.slice(0,taskPageSize);
            renderKanbanBoard(currentTasks);
            updateMemberProgressControls();
        } else { showToast(data.error||'Không tải được nhiệm vụ.','error'); }
    } catch (e) {
        showToast('Lỗi tải danh sách nhiệm vụ.', 'error');
    }
}

function renderKanbanBoard(tasks) {
    const columns = ['backlog', 'todo', 'in_progress', 'review', 'done'];
    const colCounts = { backlog: 0, todo: 0, in_progress: 0, review: 0, done: 0 };
    const scrollPositions=new Map(columns.map(col=>[col,document.getElementById(`col-body-${col}`).scrollTop]));

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
        document.getElementById(`col-body-${col}`).scrollTop=scrollPositions.get(col);
    });

    // Khởi tạo lại hiệu ứng 3D tilt cho các card mới render
    if (typeof init3DTiltEffects === 'function') {
        init3DTiltEffects();
    }
}

function createTaskCardElement(task) {
    const card = document.createElement('div');
    const canUpdate=canUpdateTask(task);
    card.className = `task-card ${canUpdate?'can-update-progress':''} ${task.is_overdue ? 'is-overdue' : ''}`;
    card.draggable = canUpdate;
    card.dataset.taskId = task.id;

    // Badges
    const priorityClass = `badge-${task.priority || 'medium'}`;
    const overdueBadge = task.is_overdue ? `<span class="badge badge-overdue">TRỄ HẠN</span>` : '';

    // Labels
    let labelsHtml = '';
    if (task.labels) {
        const labels=task.labels.split(',').map(label=>label.trim()).filter(Boolean);
        labelsHtml=labels.slice(0,2).map(label=>`<span class="task-label-tag">${escapeHtml(label)}</span>`).join('');
        if(labels.length>2)labelsHtml+=`<span class="task-label-tag">+${labels.length-2}</span>`;
    }

    // Assignee
    const assigneeName = task.assignee_name || 'Chưa phân công';
    const initial = assigneeName.charAt(0).toUpperCase();

    card.innerHTML = `
        <div class="task-header">
            <span class="task-id-badge">${escapeHtml(task.task_code||'#TASK-'+task.id)}</span>
            ${canUpdate?`<button type="button" class="task-drag-handle" aria-label="Kéo di chuyển nhiệm vụ ${task.id}" title="Kéo để chuyển trạng thái">⠿</button>`:''}
            <div class="task-header-badges">
                ${overdueBadge}
                <span class="badge ${priorityClass}">${escapeHtml(task.priority||'medium')}</span>
            </div>
        </div>
        <button type="button" class="task-title" title="${escapeHtml(task.title)}">${escapeHtml(task.title)}</button>
        ${labelsHtml ? `<div class="task-labels" title="${escapeHtml(task.labels)}">${labelsHtml}</div>` : ''}
        <div class="task-footer">
            <div class="task-meta-left">
                <span title="Thời gian dự kiến">⏱️ ${task.estimated_hours}h</span>
            </div>
            <div class="task-assignee" title="Người phụ trách: ${escapeHtml(assigneeName)}">
                <div class="task-avatar-mini">${escapeHtml(initial)}</div>
                <span>${escapeHtml(assigneeName)}</span>
            </div>
        </div>
        <div class="task-progress-line"><span>Tiến độ thực tế</span><strong>${Number(task.progress_percent)||0}%</strong></div>
        <div class="task-progress-track" role="progressbar" aria-label="Tiến độ nhiệm vụ ${task.id}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Number(task.progress_percent)||0}"><span style="width:${Math.max(0,Math.min(100,Number(task.progress_percent)||0))}%"></span></div>
        ${canUpdate?`<div class="task-card-controls"><button type="button" class="btn btn-primary task-progress-edit" aria-label="Cập nhật tiến độ nhiệm vụ ${task.id}" onclick="openTaskProgressEditor(${task.id})">Cập nhật % tiến độ</button></div>`:'<p class="form-help task-readonly-hint">Chỉ xem · Chỉ người phụ trách hoặc hỗ trợ mới được cập nhật.</p>'}
    `;
    card.querySelector('.task-title').addEventListener('click',()=>{
        if(Date.now()-lastTaskDragEndedAt>=250)openTaskDetailDrawer(task.id);
    });
    card.addEventListener('click',event=>{
        if(event.target.closest('button,input,select,a,form')||Date.now()-lastTaskDragEndedAt<250)return;
        openTaskDetailDrawer(task.id);
    });
    return card;
}

// Both native mouse drag and touch drag scroll the board/column under the pointer.
function scrollKanbanAtPointer(clientX,clientY) {
    const board=document.querySelector('.kanban-board'),rect=board.getBoundingClientRect();
    const left=Math.max(0,rect.left),right=Math.min(innerWidth,rect.right);
    const edge=48,speed=18;
    // A finger can reach the screen edge just outside the board's padding.
    if(clientY<rect.top||clientY>rect.bottom||clientX<Math.max(0,left-edge)||clientX>Math.min(innerWidth,right+edge))return;
    if(clientX>right-edge)board.scrollLeft+=speed*(1-(right-clientX)/edge);
    else if(clientX<left+edge)board.scrollLeft-=speed*(1-(clientX-left)/edge);
    const column=document.elementFromPoint(clientX,clientY)?.closest('.kanban-column');
    if(!column)return;
    const body=column.querySelector('.column-body'),bodyRect=body.getBoundingClientRect();
    if(clientY<bodyRect.top||clientY>bodyRect.bottom)return;
    if(clientY>bodyRect.bottom-edge)body.scrollTop+=speed*(1-(bodyRect.bottom-clientY)/edge);
    else if(clientY<bodyRect.top+edge)body.scrollTop-=speed*(1-(clientY-bodyRect.top)/edge);
}

function setupDragAndDrop() {
    const columns = document.querySelectorAll('.kanban-column');
    const board=document.querySelector('.kanban-board');
    let pointer=null,scrollFrame=0;
    const autoScroll=()=>{
        if(!pointer||!window.taskDragActive)return;
        scrollKanbanAtPointer(pointer.x,pointer.y);
        scrollFrame=requestAnimationFrame(autoScroll);
    };
    const clearNativeDrag=()=>{
        cancelAnimationFrame(scrollFrame);scrollFrame=0;pointer=null;
        window.taskDragActive=false;lastTaskDragEndedAt=Date.now();
        board.classList.remove('is-task-dragging');
        columns.forEach(col=>col.classList.remove('drag-over'));
    };

    document.addEventListener('dragstart', (e) => {
        const card = e.target.closest('.task-card');
        if (!card) return;
        if(!card.draggable||e.target.closest('input,select,.task-progress-edit')){e.preventDefault();return;}
        window.taskDragActive=true;
        board.classList.add('is-task-dragging');
        card.classList.add('dragging');
        e.dataTransfer.effectAllowed='move';
        e.dataTransfer.setData('text/plain', card.dataset.taskId);
    });

    document.addEventListener('dragend', (e) => {
        const card = e.target.closest('.task-card');
        if (card) card.classList.remove('dragging');
        clearNativeDrag();
    });
    document.addEventListener('dragover',event=>{
        if(!window.taskDragActive)return;
        pointer={x:event.clientX,y:event.clientY};
        if(!scrollFrame)scrollFrame=requestAnimationFrame(autoScroll);
    });

    columns.forEach(col => {
        col.addEventListener('dragover', (e) => {
            if(!window.taskDragActive)return;
            e.preventDefault();
            e.dataTransfer.dropEffect='move';
            col.classList.add('drag-over');
        });

        col.addEventListener('dragleave', (e) => {
            if(!col.contains(e.relatedTarget))col.classList.remove('drag-over');
        });

        col.addEventListener('drop', async (e) => {
            e.preventDefault();
            col.classList.remove('drag-over');
            const taskId = e.dataTransfer.getData('text/plain');
            const newStatus = col.dataset.status;
            clearNativeDrag();
            if (taskId && newStatus && currentTasks.some(t=>String(t.id)===taskId&&canUpdateTask(t))) {
                await updateTaskStatusApi(taskId, newStatus);
            }
        });
    });
    setupTouchTaskDrag();
}

async function updateTaskStatusApi(taskId, newStatus) {
    const editor=document.getElementById('modal-task-detail'),progress=document.getElementById('detail-progress');
    if(editor.classList.contains('active')&&Number(detailTaskId)===Number(taskId)&&progress&&progress.value!==progress.defaultValue){
        showToast('Hãy lưu hoặc hủy phần trăm đang nhập trước khi chuyển cột.','info');
        return false;
    }
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
            return true;
        } else {
            showToast(data.error || 'Không thể chuyển trạng thái.', 'error');
            await loadKanbanTasks();
        }
    } catch (e) {
        showToast('Lỗi máy chủ khi cập nhật trạng thái.', 'error');
        await loadKanbanTasks();
    }
    return false;
}

function setupFilterEvents() {
    const reload=()=>{taskPageOffset=0;resetKanbanColumnScroll();loadKanbanTasks();};
    for(const id of ['filter-priority','filter-status','filter-due-from','filter-due-to','filter-sort','filter-order']) {
        document.getElementById(id).addEventListener('change',reload);
    }
    document.getElementById('filter-sprint')?.addEventListener('change',reload);
    document.getElementById('filter-assignee')?.addEventListener('change',reload);
    document.getElementById('filter-overdue')?.addEventListener('change',reload);

    let debounceTimer;
    document.getElementById('filter-keyword')?.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(reload, 300);
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
let taskDetailRequest=0;
async function openTaskDetailDrawer(taskId, {refresh=false}={}) {
    const modal=document.getElementById('modal-task-detail');
    const generation=modal.dataset.generation||'0',request=++taskDetailRequest;
    const stillCurrent=()=>request===taskDetailRequest&&(modal.dataset.generation||'0')===generation&&
        (!refresh||(modal.classList.contains('active')&&modal.dataset.dirty!=='true'));
    if(!stillCurrent())return;
    try {
        const res = await fetch(`/api/tasks/${taskId}`);
        const data = await res.json();
        if(!stillCurrent())return;
        if (data.success) {
            const task = data.task;
            detailTaskId=task.id;
            const canUpdate=canUpdateTask(task);
            document.getElementById('modal-task-detail').dataset.dirty='false';
            const actions=document.getElementById('task-detail-actions');
            modal.querySelector('.modal-header').after(actions);
            actions.innerHTML=(canUpdate?'<h4 class="task-progress-editor-heading">Cập nhật tiến độ thực tế</h4>':'')+(canManageCurrentProject?`<button class="btn btn-secondary" onclick="editTask(${task.id})">Sửa nhiệm vụ</button><button class="btn btn-secondary" onclick="archiveTask(${task.id})">Lưu trữ nhiệm vụ</button>`:'')+(canUpdate?`<label>Tiến độ thực tế (%) <input id="detail-progress" class="form-input" type="number" min="0" max="100" step="1" required value="${Number(task.progress_percent)||0}" style="width:100px"></label><button type="button" data-save-progress class="btn btn-primary" onclick="saveTaskProgress(${task.id})">Lưu tiến độ</button>`:`<p>Tiến độ thực tế: ${Number(task.progress_percent)||0}% · Bạn chỉ có quyền xem nhiệm vụ này.</p>`);
            if(canUpdate){
                const label=document.createElement('label');label.textContent='Trạng thái ';
                const select=document.createElement('select');select.id='detail-status';select.className='form-select';
                for(const [value,text] of Object.entries({backlog:'Tồn đọng',todo:'Cần làm',in_progress:'Đang làm',review:'Kiểm tra',done:'Hoàn thành'}))select.add(new Option(text,value,false,task.status===value));
                const button=document.createElement('button');button.className='btn btn-secondary';button.textContent='Lưu trạng thái';button.type='button';
                button.onclick=async()=>{
                    button.disabled=true;
                    const savedGeneration=modal.dataset.generation||'0';
                    try{
                        if(await updateTaskStatusApi(task.id,select.value)){
                            if(modal.classList.contains('active')&&(modal.dataset.generation||'0')===savedGeneration){
                                modal.dataset.dirty='false';
                                await openTaskDetailDrawer(task.id,{refresh:true});
                            }
                        }
                    }finally{button.disabled=false;}
                };
                label.append(select);document.getElementById('task-detail-actions').append(label,button);
                const cancel=document.createElement('button');cancel.className='btn btn-secondary';cancel.type='button';cancel.textContent='Hủy';
                cancel.onclick=closeTaskDetail;document.getElementById('task-detail-actions').append(cancel);
            }
            const canCollaborate=currentProjectRole==='leader'||currentProjectRole==='member';
            for(const id of ['form-add-comment','attachment-upload-form','attachment-link-form']) document.getElementById(id).hidden=!canCollaborate;
            await loadTaskAttachments(task.id);
            if(!stillCurrent())return;
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
            if(!stillCurrent())return;
            openModal('modal-task-detail');
            if(!refresh)modal.querySelector('.modal-header .btn-icon').focus({preventScroll:true});
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



function resetKanbanColumnScroll(){document.querySelectorAll('.column-body').forEach(body=>body.scrollTop=0);}
function changeTaskPage(direction) { taskPageOffset=Math.max(0,taskPageOffset+direction*taskPageSize);resetKanbanColumnScroll();loadKanbanTasks(); }

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
    const input=document.getElementById('detail-progress'),button=document.querySelector('[data-save-progress]');
    if(!input||!input.reportValidity()||button.disabled)return;
    const modal=document.getElementById('modal-task-detail'),generation=modal.dataset.generation||'0';
    button.disabled=true;
    input.disabled=true;
    try{
        const data=await apiRequest(`/api/tasks/${id}/progress`,jsonRequest('PUT',{progress_percent:Number(input.value)}));
        const latest=await apiRequest(`/api/tasks/${id}`);
        if(modal.classList.contains('active')&&(modal.dataset.generation||'0')===generation&&detailTaskId===id){
            input.value=latest.task.progress_percent;
            input.defaultValue=String(latest.task.progress_percent);
            document.getElementById('detail-task-status').textContent=latest.task.status.toUpperCase();
            if(document.getElementById('detail-status'))document.getElementById('detail-status').value=latest.task.status;
            modal.dataset.dirty='false';
        }
        await loadKanbanTasks();showToast(data.message,'success');
    }
    catch(error){showToast(error.message,'error');}
    finally{button.disabled=false;input.disabled=false;}
}

async function openTaskProgressEditor(id){await openTaskDetailDrawer(id);document.getElementById('detail-progress')?.focus();}
function closeTaskDetail(){
    closeModal('modal-task-detail');
    const card=document.querySelector(`.task-card[data-task-id="${detailTaskId}"]`);
    (card?.querySelector('.task-progress-edit')||card?.querySelector('.task-title'))?.focus({preventScroll:true});
}


function setupTouchTaskDrag(){
    let drag=null;
    let dragFrame=0;
    const updateTarget=()=>{
        if(!drag)return;
        drag.target=document.elementFromPoint(drag.clientX,drag.clientY)?.closest('.kanban-column');
        document.querySelectorAll('.kanban-column').forEach(el=>el.classList.toggle('drag-over',el===drag.target));
    };
    const autoScroll=()=>{
        if(!drag?.moved)return;
        scrollKanbanAtPointer(drag.clientX,drag.clientY);
        updateTarget();dragFrame=requestAnimationFrame(autoScroll);
    };
    const clear=()=>{
        if(!drag)return;
        cancelAnimationFrame(dragFrame);dragFrame=0;
        document.querySelector('.kanban-board').classList.remove('is-task-dragging');
        if(drag){drag.card.classList.remove('dragging');if(drag.handle.hasPointerCapture(drag.pointerId))drag.handle.releasePointerCapture(drag.pointerId);}
        document.querySelectorAll('.kanban-column.drag-over').forEach(el=>el.classList.remove('drag-over'));
        window.taskDragActive=false;drag=null;
    };
    document.addEventListener('pointerdown',event=>{
        const handle=event.target.closest('.task-drag-handle');
        if(!handle||event.pointerType==='mouse')return;
        const card=handle.closest('.task-card');if(!card?.draggable)return;
        event.preventDefault();handle.setPointerCapture(event.pointerId);
        drag={handle,card,pointerId:event.pointerId,id:card.dataset.taskId,x:event.clientX,y:event.clientY,clientX:event.clientX,clientY:event.clientY,moved:false,target:null};
        window.taskDragActive=true;
    });
    document.addEventListener('pointermove',event=>{
        if(!drag||event.pointerId!==drag.pointerId)return;
        event.preventDefault();
        if(Math.hypot(event.clientX-drag.x,event.clientY-drag.y)<8&&!drag.moved)return;
        drag.moved=true;drag.card.classList.add('dragging');
        drag.clientX=event.clientX;drag.clientY=event.clientY;
        document.querySelector('.kanban-board').classList.add('is-task-dragging');
        updateTarget();if(!dragFrame)dragFrame=requestAnimationFrame(autoScroll);
    },{passive:false});
    document.addEventListener('pointerup',event=>{
        if(!drag||event.pointerId!==drag.pointerId)return;
        updateTarget();const {id,moved,target}=drag;clear();
        if(moved){
            lastTaskDragEndedAt=Date.now();
            if(target)updateTaskStatusApi(id,target.dataset.status).then(saved=>{
                if(saved&&innerWidth<=992){const board=document.querySelector('.kanban-board');board.scrollTo({left:board.scrollLeft+target.getBoundingClientRect().left-board.getBoundingClientRect().left,behavior:'smooth'});}
            });
        }
    });
    document.addEventListener('pointercancel',()=>clear());
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
