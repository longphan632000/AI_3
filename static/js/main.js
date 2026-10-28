// Global State & Helper Functions
let currentProjectId = localStorage.getItem('active_project_id') || null;
let currentUser = null;
let canManageCurrentProject = false;
let currentProjectRole = null;
let resolveProjectReady;
const projectReady = new Promise(resolve => { resolveProjectReady = resolve; });

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    await fetchCurrentUser();
    await loadProjectSelector();
    const addMemberButton = document.getElementById('add-project-member-button');
    if (addMemberButton) addMemberButton.style.display = canManageCurrentProject ? '' : 'none';
    document.querySelectorAll('[data-project-manager]').forEach(el => el.hidden = !canManageCurrentProject);
    resolveProjectReady();
    updateUnreadNotificationsCount();

    // Polling nhẹ thông báo mỗi 30s
    setInterval(updateUnreadNotificationsCount, 30000);
    startSharedDataSync();
}

async function fetchCurrentUser() {
    try {
        const res = await fetch('/api/auth/me');
        const data = await res.json();
        if (data.logged_in) {
            currentUser = data.user;
            const nameEl = document.getElementById('header-user-name');
            const roleEl = document.getElementById('header-user-role');
            if (nameEl) nameEl.textContent = currentUser.full_name;
            if (roleEl) roleEl.textContent = currentUser.role.toUpperCase();
            const avatar = document.getElementById('header-user-avatar');
            if (avatar) avatar.textContent = (currentUser.full_name || 'U').charAt(0).toUpperCase();
            return currentUser;
        }
        currentUser=null;
    } catch (e) {
        console.error('Lỗi lấy thông tin user:', e);
    }
    return null;
}

async function loadProjectSelector() {
    const selector = document.getElementById('project-select-input');
    if (!selector) return;

    try {
        const res = await fetch('/api/projects');
        const data = await res.json();
        if (data.success && data.projects.length > 0) {
            const selectedProject = data.projects.find(p => String(p.id) === String(currentProjectId)) || data.projects[0];
            currentProjectId = selectedProject.id;
            localStorage.setItem('active_project_id', currentProjectId);
            currentProjectRole = selectedProject.current_user_project_role;
            canManageCurrentProject = currentUser?.role === 'leader' && selectedProject.current_user_project_role === 'leader';
            selector.innerHTML = '';
            data.projects.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.id;
                opt.textContent = p.name;
                if (p.id == currentProjectId) opt.selected = true;
                selector.appendChild(opt);
            });
            selector.disabled = false;

            selector.onchange = (e) => {
                currentProjectId = e.target.value;
                localStorage.setItem('active_project_id', currentProjectId);
                window.location.reload();
            };
        } else {
            currentProjectId = null;
            canManageCurrentProject = false;
            localStorage.removeItem('active_project_id');
            selector.innerHTML = '<option value="">Chưa tham gia dự án nào</option>';
            selector.disabled = true;
        }
    } catch (e) {
        console.error('Lỗi tải danh sách dự án:', e);
        currentProjectId = null;
        canManageCurrentProject = false;
        selector.innerHTML = '<option value="">Không tải được dự án</option>';
        selector.disabled = true;
    }
}

async function updateUnreadNotificationsCount() {
    const badge = document.getElementById('unread-noti-badge');
    if (!badge) return;

    try {
        const res = await fetch('/api/notifications/unread-count');
        const data = await res.json();
        if (data.success && data.unread_count > 0) {
            badge.textContent = data.unread_count;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    } catch (e) {
        // im lặng nếu không có mạng
    }
}

// Toast Notifications
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const messageElement = document.createElement('span');
    messageElement.textContent = message;
    toast.appendChild(messageElement);

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function escapeHtml(value) {
    if (value == null) return '';
    return String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// Modal Helpers
function openModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.add('active');
}

function closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.remove('active');
    if (modalId === 'modal-task-detail' && el) {
        el.dataset.dirty = 'false';
        el.dataset.generation=String(Number(el.dataset.generation||0)+1);
    }
    setTimeout(() => { if (syncHasChanges && !hasUnsavedWork()) refreshSharedData(); }, 0);
}

async function submitCreateProject(event) {
    event.preventDefault();
    const submitButton = event.submitter || event.target.querySelector('[type="submit"]');
    if (submitButton?.disabled) return;
    if (submitButton) submitButton.disabled = true;
    const name = document.getElementById('new-project-name').value.trim();
    const description = document.getElementById('new-project-description').value.trim();
    try {
        const response = await fetch('/api/projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description, member_ids:Array.from(initialProjectMembers), project_code:document.getElementById('new-project-code')?.value, start_date:document.getElementById('new-project-start-date')?.value, end_date:document.getElementById('new-project-end-date')?.value })
        });
        const data = await response.json();
        if (!data.success) {
            showToast(data.error || 'Không thể tạo dự án.', 'error');
            return;
        }
        localStorage.setItem('active_project_id', data.project_id);
        window.location.href = '/dashboard';
    } catch (error) {
        showToast('Lỗi kết nối khi tạo dự án.', 'error');
    } finally {
        if (submitButton) submitButton.disabled = false;
    }
}

let initialMemberOptions = [];
const initialProjectMembers = new Set();

async function openCreateProjectModal() {
    openModal('modal-create-project');
    const list = document.getElementById('initial-members-list');
    const submit = document.querySelector('#modal-create-project [type="submit"]');
    list.textContent = 'Đang tải nhân viên...';
    if (submit) submit.disabled = true;
    try {
        const data = await apiRequest('/api/users/assignable');
        initialMemberOptions = data.users.filter(user => user.id !== currentUser?.id);
        const available = new Set(initialMemberOptions.map(user => user.id));
        for (const id of initialProjectMembers) if (!available.has(id)) initialProjectMembers.delete(id);
        filterInitialMembers();
        if (submit) submit.disabled = false;
    } catch(error) {
        list.textContent = 'Không tải được danh sách. Hãy đóng và mở lại để thử lại.';
        showToast(error.message,'error');
    }
}

function filterInitialMembers() {
    const keyword = document.getElementById('initial-members-search').value.trim().toLocaleLowerCase('vi');
    const list = document.getElementById('initial-members-list');
    const users = initialMemberOptions.filter(user => [user.full_name,user.username,user.user_code||''].join(' ').toLocaleLowerCase('vi').includes(keyword));
    list.replaceChildren();
    for (const user of users) {
        const label = document.createElement('label');
        label.className = 'initial-member-option';
        const input = document.createElement('input');
        input.type = 'checkbox'; input.value = user.id; input.checked = initialProjectMembers.has(user.id);
        input.addEventListener('change', () => {
            if (input.checked) initialProjectMembers.add(user.id); else initialProjectMembers.delete(user.id);
            document.getElementById('initial-members-count').textContent = `Đã chọn ${initialProjectMembers.size} nhân viên`;
        });
        const text = document.createElement('span');
        text.textContent = `${user.full_name} (${user.username})${user.user_code?' · '+user.user_code:''}`;
        label.append(input,text); list.append(label);
    }
    if (!users.length) list.textContent = initialMemberOptions.length ? 'Không có nhân viên phù hợp.' : 'Chưa có nhân viên được duyệt để chọn.';
    document.getElementById('initial-members-count').textContent = `Đã chọn ${initialProjectMembers.size} nhân viên`;
}

async function openAddProjectMemberModal() {
    if (!canManageCurrentProject || !currentProjectId) return;
    try {
        const response = await fetch(`/api/projects/${currentProjectId}/eligible-users`);
        const data = await response.json();
        if (!data.success) {
            showToast(data.error || 'Không tải được tài khoản.', 'error');
            return;
        }
        const select = document.getElementById('new-project-member-user');
        select.innerHTML = '';
        data.users.forEach(user => select.add(new Option(`${user.full_name} (${user.username})`, user.id)));
        if (!data.users.length) {
            showToast('Không có tài khoản nào để thêm vào dự án.', 'info');
            return;
        }
        openModal('modal-add-project-member');
    } catch (error) {
        showToast('Lỗi tải tài khoản.', 'error');
    }
}

async function submitAddProjectMember(event) {
    event.preventDefault();
    if (!canManageCurrentProject || !currentProjectId) return;
    const userId = Number(document.getElementById('new-project-member-user').value);
    try {
        const response = await fetch(`/api/projects/${currentProjectId}/members`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({user_id:userId,project_role:document.getElementById('new-member-role').value,skills:document.getElementById('new-member-skills').value,availability:document.getElementById('new-member-availability').value+'%',capacity_hours:Number(document.getElementById('new-member-capacity').value)})
        });
        const data = await response.json();
        if (!data.success) {
            showToast(data.error || 'Không thể thêm thành viên.', 'error');
            return;
        }
        closeModal('modal-add-project-member');
        window.location.reload();
    } catch (error) {
        showToast('Lỗi kết nối khi thêm thành viên.', 'error');
    }
}
// ==========================================================================
// Responsive navigation for narrow screens and touch controls.
// ==========================================================================

function toggleMobileSidebar() {
    const sidebar = document.getElementById('app-sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (!sidebar) return;

    const isOpen = sidebar.classList.contains('mobile-open');
    if (isOpen) {
        closeMobileSidebar();
    } else {
        sidebar.classList.add('mobile-open');
        document.querySelector('.mobile-toggle-btn')?.setAttribute('aria-expanded','true');
        if (backdrop) backdrop.classList.add('active');
        document.body.style.overflow = 'hidden'; // Ngăn cuộn nền khi mở menu
    }
}

function closeMobileSidebar() {
    const sidebar = document.getElementById('app-sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (sidebar) sidebar.classList.remove('mobile-open');
    document.querySelector('.mobile-toggle-btn')?.setAttribute('aria-expanded','false');
    if (backdrop) backdrop.classList.remove('active');
    document.body.style.overflow = '';
}

// Tự động đóng menu trên điện thoại khi click link hoặc nhấn ESC
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('app-sidebar');
    if (sidebar) {
        sidebar.querySelectorAll('.nav-item').forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth <= 992) {
                    closeMobileSidebar();
                }
            });
        });
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeMobileSidebar();
        }
    });

    window.addEventListener('resize', () => {
        if (window.innerWidth > 992) {
            closeMobileSidebar();
        }
    });
});
async function deleteCurrentProject() {
    if (!canManageCurrentProject || !currentProjectId) return;

    const selector = document.getElementById('project-select-input');
    const currentProjectName = selector?.options[selector.selectedIndex]?.text?.replace(/\s*\([^)]*\)\s*$/, '') || 'dự án này';

    const confirmMsg = `⚠️ CẢNH BÁO QUAN TRỌNG:\n\nBạn có chắc chắn muốn LƯU TRỮ dự án "${currentProjectName}" không?\n\nDự án sẽ chuyển sang chỉ đọc. Lịch sử và dữ liệu được giữ nguyên.`;

    if (!confirm(confirmMsg)) return;

    try {
        const res = await fetch(`/api/projects/${currentProjectId}?permanent=false`, {
            method: 'DELETE'
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message || 'Đã lưu trữ dự án thành công!', 'success');
            localStorage.removeItem('active_project_id');
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 500);
        } else {
            showToast(data.error || 'Không thể xóa dự án.', 'error');
        }
    } catch (e) {
        showToast('Lỗi kết nối khi xóa dự án.', 'error');
    }
}

// Global Password Visibility Toggle
function togglePasswordVisibility(inputId, btnEl) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const isPassword = input.type === 'password';
    input.type = isPassword ? 'text' : 'password';
    if (btnEl) {
        if (isPassword) {
            btnEl.classList.add('visible');
            btnEl.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`;
            btnEl.setAttribute('aria-label', 'Ẩn mật khẩu');
            btnEl.setAttribute('title', 'Ẩn mật khẩu');
        } else {
            btnEl.classList.remove('visible');
            btnEl.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
            btnEl.setAttribute('aria-label', 'Hiện mật khẩu');
            btnEl.setAttribute('title', 'Hiện mật khẩu');
        }
    }
}
window.togglePasswordVisibility = togglePasswordVisibility;



async function apiRequest(url, options = {}) {
    const response = await fetch(url, options);
    let data;
    try { data = await response.json(); } catch (_) { throw new Error('Máy chủ không trả về kết quả hợp lệ.'); }
    if (!response.ok || data.success === false) throw new Error(data.error || 'Không thể thực hiện thao tác.');
    return data;
}

function jsonRequest(method, data) {
    return { method, headers:{'Content-Type':'application/json'}, body:JSON.stringify(data) };
}

async function openEditProjectModal() {
    if (!canManageCurrentProject) return;
    try {
        const {project:p} = await apiRequest(`/api/projects/${currentProjectId}`);
        for (const [id,value] of Object.entries({'name':p.name,'code':p.project_code,'description':p.description,'status':p.status,'start-date':dateInput(p.start_date),'end-date':dateInput(p.end_date)})) {
            document.getElementById(`edit-project-${id}`).value = value || '';
        }
        openModal('modal-edit-project');
    } catch(error) { showToast(error.message,'error'); }
}

function dateInput(value) {
    if (!value) return '';
    if (/^\d{4}-\d{2}-\d{2}/.test(value)) return value.slice(0,10);
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '';
    return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
}

function dateTimeInput(value) {
    if (!value) return '';
    if (/^\d{4}-\d{2}-\d{2}/.test(value) && !/(?:Z|[+-]\d{2}:?\d{2})$/i.test(value)) return value.replace(' ','T').slice(0,16);
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? '' : `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}T${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;
}

async function submitEditProject(event) {
    event.preventDefault();
    try {
        const get = id => document.getElementById(`edit-project-${id}`).value;
        await apiRequest(`/api/projects/${currentProjectId}`,jsonRequest('PUT',{name:get('name'),project_code:get('code'),description:get('description'),status:get('status'),start_date:get('start-date'),end_date:get('end-date')}));
        window.location.reload();
    } catch(error) { showToast(error.message,'error'); }
}

async function openArchivedProjects() {
    try {
        const data=await apiRequest('/api/projects?archived=true');
        document.getElementById('modal-archived-projects').querySelector('h3').textContent='Dự án đã lưu trữ';
        const list=document.getElementById('archived-project-list');
        list.innerHTML=data.projects.map(p=>`<div class="archive-list-row"><div><strong>${escapeHtml(p.name)}</strong><p class="form-help">Người lưu trữ: ${escapeHtml(p.archiver_name||'Chưa xác định')} · ${escapeHtml(p.archived_at||'Chưa rõ thời gian')}</p></div><div class="workspace-actions"><a class="btn btn-secondary" href="/projects/${p.id}/archived">Xem chi tiết</a><button class="btn btn-primary" onclick="restoreProject(${p.id})">Khôi phục</button></div></div>`).join('')||'Không có dự án lưu trữ trong quyền xem của bạn.';
        openModal('modal-archived-projects');
    } catch(error) { showToast(error.message,'error'); }
}
async function restoreProject(id) {
    if(!confirm('Khôi phục dự án này và cho phép làm việc trở lại?'))return;
    try {await apiRequest(`/api/projects/${id}/restore`,{method:'POST'});localStorage.setItem('active_project_id',id);window.location.href='/dashboard';}
    catch(error){showToast(error.message,'error');}
}

async function editMemberCapacity(id){
    try{
        if (!canEditMemberCapacity(id)) throw new Error('Bạn không có quyền cập nhật năng lực của thành viên này.');
        const data=await apiRequest(`/api/projects/${currentProjectId}/members`),m=data.members.find(m=>Number(m.user_id)===Number(id));
        if (!m) throw new Error('Thành viên không còn thuộc dự án.');
        document.getElementById('member-edit-id').value=id;
        document.getElementById('member-edit-name').textContent=m.full_name;
        document.getElementById('member-edit-skills').value=m.skills||'';
        document.getElementById('member-edit-availability').value=m.availability_percent??'';
        document.getElementById('member-edit-capacity').value=m.capacity_hours??40;
        openModal('modal-member-capacity');
    }catch(error){showToast(error.message,'error');}
}

async function saveMemberCapacity(event){
    event.preventDefault();
    const button=event.submitter||event.target.querySelector('[type=submit]');
    if(button.disabled)return;
    button.disabled=true;
    const capacityButtons=document.querySelectorAll('#modal-member-capacity button');
    capacityButtons.forEach(control=>control.disabled=true);
    try{
        const id=Number(document.getElementById('member-edit-id').value);
        await apiRequest(`/api/projects/${currentProjectId}/members/${id}/capacity`,jsonRequest('PUT',{skills:document.getElementById('member-edit-skills').value,availability:document.getElementById('member-edit-availability').value+'%',capacity_hours:Number(document.getElementById('member-edit-capacity').value)}));
        closeModal('modal-member-capacity');
        if(typeof openProjectTeamModal==='function'&&document.getElementById('modal-project-team')?.classList.contains('active'))await openProjectTeamModal();
        if(typeof loadTeamData==='function')await loadTeamData();
        if(typeof loadWorkloadReport==='function')await loadWorkloadReport();
        showToast('Đã cập nhật năng lực. AI phân công sẽ dùng dữ liệu mới.','success');
    }catch(error){showToast(error.message,'error');}
    finally{capacityButtons.forEach(control=>control.disabled=false);}
}

async function removeProjectMember(id){
    if(!confirm('Xóa thành viên khỏi dự án? Lịch sử công việc được giữ nguyên; nhiệm vụ chưa hoàn thành sẽ bỏ phân công cho người này.'))return;
    try{await apiRequest(`/api/projects/${currentProjectId}/members/${id}`,{method:'DELETE'});if(typeof openProjectTeamModal==='function')await openProjectTeamModal();showToast('Đã xóa thành viên khỏi dự án.','success');}
    catch(error){showToast(error.message,'error');}
}

let syncRevision = null;
let syncBusy = false;
let syncHasChanges = false;
let formHasChanges = false;
let syncRefreshBusy = false;
let syncWasOffline = false;
let syncBuildChanged = false;
const pageAppVersion = document.querySelector('meta[name="app-version"]')?.content;

document.addEventListener('input', event => {
    if (event.target.closest('form') && !['search','checkbox'].includes(event.target.type)) formHasChanges = true;
    if (event.target.closest('.project-team-picker')) formHasChanges = true;
    if (event.target.matches('#ai-raw-notes, #ai-user-prompt')) formHasChanges = true;
    const drawer=event.target.closest('#modal-task-detail');
    if(drawer)drawer.dataset.dirty='true';
});
document.addEventListener('change',event=>{
    const drawer=event.target.closest('#modal-task-detail');
    if(drawer)drawer.dataset.dirty='true';
});

function hasUnsavedWork() {
    const editingModal=Array.from(document.querySelectorAll('.modal-overlay.active')).some(el=>
        !['modal-account-profile','modal-project-team'].includes(el.id) &&
        (el.id!=='modal-task-detail'||el.dataset.dirty==='true'||
            Array.from(el.querySelectorAll('textarea,input[type="text"],input[type="url"],input[type="file"]')).some(input=>input.type==='file'?input.files.length:input.value.trim())));
    return editingModal || Boolean(window.taskDragActive) || Boolean(window.kanbanProgressDrafts?.size) ||
        Boolean(document.getElementById('ai-loading-state')?.classList.contains('active')) ||
        Boolean(formHasChanges && (document.getElementById('ai-raw-notes')?.value || document.getElementById('ai-user-prompt')?.value));
}

async function startSharedDataSync() {
    await pollSharedData();
    setInterval(() => { if (!document.hidden) pollSharedData(); },5000);
    window.addEventListener('focus',pollSharedData);
    document.addEventListener('visibilitychange',() => {if(!document.hidden)pollSharedData();});
    window.addEventListener('online',pollSharedData);
}

async function pollSharedData() {
    if (syncBusy) return;
    syncBusy = true;
    try {
        const response = await fetch('/api/sync',{cache:'no-store'});
        if (response.status===401) {
            setSyncState('offline','Cần đăng nhập lại');
            showSyncBanner('Phiên đăng nhập đã hết hiệu lực. Hãy sao chép nội dung đang nhập và đăng nhập lại.');
            return;
        }
        if (!response.ok) throw new Error('Máy chủ chưa sẵn sàng.');
        const data=await response.json();
        if (syncWasOffline || (syncRevision && syncRevision!==data.revision)) syncHasChanges=true;
        syncWasOffline=false;
        syncBuildChanged=Boolean(pageAppVersion&&data.app_version&&pageAppVersion!==data.app_version);
        syncRevision=data.revision;
        if(syncBuildChanged){
            if(hasUnsavedWork())showSyncBanner('Máy chủ có phiên bản mới. Hãy lưu hoặc hủy nội dung đang sửa; trang sẽ cập nhật khi bạn hoàn tất.');
            else { window.location.reload();return; }
        } else if(syncHasChanges){
            if(hasUnsavedWork())showSyncBanner('Có dữ liệu mới từ máy chủ. Nội dung bạn đang nhập được giữ nguyên; dữ liệu sẽ cập nhật khi bạn hoàn tất.');
            else await refreshSharedData();
        }
        setSyncState('online',syncBuildChanged?'Chờ cập nhật phiên bản':syncHasChanges?'Có dữ liệu mới':'Đã đồng bộ');
    }catch(_){syncWasOffline=true;setSyncState('offline','Mất kết nối máy chủ');}
    finally{syncBusy=false;}
}

async function refreshSharedData(manual=false) {
    if(syncRefreshBusy||(!syncHasChanges&&!syncBuildChanged))return;
    if(hasUnsavedWork()){
        if(!manual)return;
        showToast('Hãy lưu hoặc đóng biểu mẫu trước khi cập nhật để giữ nội dung đang nhập.','info');
        return;
    }
    if(syncBuildChanged){window.location.reload();return;}
    syncRefreshBusy=true;
    try {
    const previousProject=String(currentProjectId), previousRole=currentProjectRole, previousSystemRole=currentUser?.role;
    await fetchCurrentUser(); await loadProjectSelector();
    if(previousProject!==String(currentProjectId)||previousRole!==currentProjectRole||previousSystemRole!==currentUser?.role){
        window.location.reload(); return;
    }
    if(typeof loadDashboardData==='function'&&currentProjectId)await loadDashboardData();
    if(typeof loadKanbanTasks==='function'&&currentProjectId){
        const filters=['filter-assignee','filter-sprint'].map(id=>[id,document.getElementById(id)?.value]);
        await loadFilterOptions();
        filters.forEach(([id,value])=>{const el=document.getElementById(id);if(el&&Array.from(el.options).some(o=>o.value===value))el.value=value;});
        await loadKanbanTasks();
    }
    if(typeof loadSprintsList==='function'&&currentProjectId)await loadSprintsList();
    if(typeof loadWorkloadReport==='function'&&currentProjectId)await loadWorkloadReport();
    if(typeof loadTeamData==='function'&&currentProjectId)await loadTeamData();
    if(typeof loadArchivedProjectView==='function')await loadArchivedProjectView();
    if(document.getElementById('modal-archived-projects')?.classList.contains('active'))await openArchivedProjects();
    if(document.getElementById('modal-account-profile')?.classList.contains('active'))await renderAccountProfile();
    if(document.getElementById('modal-project-team')?.classList.contains('active')&&typeof openProjectTeamModal==='function')await openProjectTeamModal();
    if(document.getElementById('modal-task-detail')?.classList.contains('active')&&typeof openTaskDetailDrawer==='function'&&detailTaskId)await openTaskDetailDrawer(detailTaskId,{refresh:true});
    if(typeof loadUsersList==='function'){await loadUsersList();await loadAuditLogs();await loadProjectAssignmentOptions();}
    if(typeof loadNotifications==='function')await loadNotifications();
    if(typeof loadAIDataSources==='function'&&currentProjectId)await loadAIDataSources();
    await updateUnreadNotificationsCount();
    syncHasChanges=false; document.getElementById('sync-banner').hidden=true;
    setSyncState('online','Đã đồng bộ');
    }catch(_){syncHasChanges=true;setSyncState('offline','Chưa cập nhật đủ dữ liệu');}
    finally{syncRefreshBusy=false;}
}

function setSyncState(state,message){
    const el=document.getElementById('sync-connection-status');
    if(el){el.dataset.state=state;el.textContent=message;}
}
function showSyncBanner(message){
    const el=document.getElementById('sync-banner');
    if(el){el.hidden=false;el.querySelector('span').textContent=message;}
}
function roleLabel(role){return {admin:'Quản trị viên',leader:'Trưởng nhóm',member:'Thành viên',viewer:'Chỉ xem'}[role]||role;}
function canEditMemberCapacity(id){
    return Boolean(currentProjectId)&&(canManageCurrentProject||currentUser?.role==='admin'||
        (currentProjectRole==='member'&&Number(id)===Number(currentUser?.id)));
}
async function openAccountProfile(){
    try{await projectReady;if(!await fetchCurrentUser())throw new Error('Vui lòng đăng nhập lại hoặc kiểm tra kết nối.');
        await renderAccountProfile();openModal('modal-account-profile');
        document.querySelector('#modal-account-profile .btn-icon').focus();
    }catch(error){showToast(error.message,'error');}
}
async function renderAccountProfile(){
    const fields=[['Họ tên',currentUser.full_name],['Mã tài khoản',currentUser.user_code||'Chưa cấp'],
        ['Tên đăng nhập',currentUser.username],['Email',currentUser.email],['Vai trò hệ thống',roleLabel(currentUser.role)],
        ['Trạng thái',currentUser.status==='active'?'Đang hoạt động':currentUser.status],['Ngày tạo',dateInput(currentUser.created_at)]];
    document.getElementById('account-profile-info').innerHTML=fields.map(([label,value])=>`<dt>${label}</dt><dd>${escapeHtml(value)}</dd>`).join('');
    document.getElementById('account-profile-project').innerHTML=currentProjectId
        ? `<p class="form-help">Dự án hiện tại: ${escapeHtml(document.getElementById('project-select-input').selectedOptions[0]?.textContent)} · ${escapeHtml(roleLabel(currentProjectRole))}</p><a class="btn btn-secondary" href="/team">Xem năng lực và tải công việc</a>`
        : '<p class="form-help">Bạn chưa chọn dự án.</p>';
    if(currentUser.role!=='admin')document.getElementById('account-profile-project').innerHTML+='<button class="btn btn-primary" type="button" onclick="closeAccountProfile();openProfessionalProfile()">Hồ sơ năng lực chung</button>';
}
function closeAccountProfile(){closeModal('modal-account-profile');document.getElementById('account-profile-button')?.focus();}
document.addEventListener('keydown',event=>{
    if(!document.getElementById('modal-account-profile')?.classList.contains('active'))return;
    if(event.key==='Escape'){event.preventDefault();closeAccountProfile();}
    if(event.key==='Tab'){
        const controls=Array.from(document.querySelectorAll('#modal-account-profile button,#modal-account-profile a')).filter(el=>el.getClientRects().length);
        const first=controls[0],last=controls[controls.length-1];
        if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
        else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
    }
});

async function openProfessionalProfile(){
    try{
        const data=await apiRequest('/api/me/professional-profile'),p=data.profile;
        document.getElementById('professional-skills').value=p.skills;
        document.getElementById('professional-availability').value=p.availability_percent;
        document.getElementById('professional-capacity').value=p.nominal_capacity_hours;
        document.getElementById('professional-profile-hint').textContent=p.profile_declared?'Hồ sơ chung đã khai báo.':p.profile_warnings.join(' ');
        openModal('modal-professional-profile');
    }catch(error){showToast(error.message,'error');}
}
async function saveProfessionalProfile(event){
    event.preventDefault();
    const buttons=event.target.closest('.modal-box').querySelectorAll('button');buttons.forEach(el=>el.disabled=true);
    try{
        await apiRequest('/api/me/professional-profile',jsonRequest('PUT',{skills:document.getElementById('professional-skills').value,
            availability:document.getElementById('professional-availability').value+'%',capacity_hours:Number(document.getElementById('professional-capacity').value)}));
        closeModal('modal-professional-profile');
        if(typeof loadAssignmentPreview==='function')await loadAssignmentPreview();
        showToast('Đã cập nhật hồ sơ chung để PM tìm ứng viên.','success');
    }catch(error){showToast(error.message,'error');}
    finally{buttons.forEach(el=>el.disabled=false);}
}
