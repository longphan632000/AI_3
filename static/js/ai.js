// AI Assistant Studio Controller (FR-12, FR-13, FR-14, FR-15, UC010)
let currentAIMode = 'weekly_summary';
let lastDraftId = null;
let lastDraftVersion = null;
let lastDraftStatus = null;
let uploadWarnings = [];

document.addEventListener('DOMContentLoaded', () => {
    initAIStudio();
});

async function initAIStudio() {
    setupAIModeTabs();
    await projectReady;
    if (!currentProjectId) {
        showToast('Bạn chưa tham gia dự án nào.', 'info');
        return;
    }
    if (!canManageCurrentProject) {
        document.querySelectorAll('.ai-tab-btn').forEach(button => button.hidden=button.dataset.mode!=='meeting_minutes');
        currentAIMode='meeting_minutes';
        switchAIModeForm(currentAIMode);
    }
    if (currentProjectRole === 'viewer' || currentUser?.role === 'admin') {
        document.getElementById('btn-generate-ai').disabled=true;
        document.getElementById('add-meeting-note-button')?.setAttribute('hidden','');
    }
    await loadAIDataSources();
    setDefaultDateRange();
    setupGenerateButton();
    initFileDropzone();
    document.getElementById('btn-generate-ai').disabled =
        currentProjectRole === 'viewer' || currentUser?.role === 'admin';
}

function setupAIModeTabs() {
    const tabs = document.querySelectorAll('.ai-tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentAIMode = tab.dataset.mode;
            switchAIModeForm(currentAIMode);
        });
    });
}

function switchAIModeForm(mode) {
    document.getElementById('staffing-candidate-panel').hidden=mode!=='assignment_suggestion';
    document.getElementById('form-section-weekly').style.display = (mode === 'weekly_summary') ? 'block' : 'none';
    document.getElementById('form-section-minutes').style.display = (mode === 'meeting_minutes') ? 'block' : 'none';
    document.getElementById('form-section-assignment').style.display = (mode === 'assignment_suggestion') ? 'block' : 'none';

    const titleEl = document.getElementById('ai-target-title');
    if (mode === 'weekly_summary') {
        titleEl.textContent = 'Tóm tắt Tiến độ Tuần (FR-12)';
    } else if (mode === 'meeting_minutes') {
        titleEl.textContent = 'Biên bản Cuộc họp Thông minh (FR-13)';
    } else {
        titleEl.textContent = 'Gợi ý Phân công Nhiệm vụ (FR-14)';
        loadAssignmentPreview();
    }
}

function setDefaultDateRange() {
    const startInput = document.getElementById('ai-week-start');
    const endInput = document.getElementById('ai-week-end');
    if (!startInput || !endInput) return;

    const now = new Date();
    const start = new Date();
    start.setDate(now.getDate() - 7);

    startInput.value = start.toISOString().split('T')[0];
    endInput.value = now.toISOString().split('T')[0];
}

async function loadAIDataSources() {
    try {
        // Tải danh sách nhiệm vụ cho gợi ý phân công
        const taskRes = await fetch(`/api/projects/${currentProjectId}/tasks`);
        const taskData = await taskRes.json();
        if (taskData.success) {
            const taskSelect = document.getElementById('ai-task-select');
            if (taskSelect) {
                const previousValue = taskSelect.value;
                taskSelect.innerHTML = '<option value="">-- Chọn nhiệm vụ cần phân công --</option>';
                taskData.tasks.forEach(t => {
                    taskSelect.innerHTML += `<option value="${t.id}">[#TASK-${t.id}] ${escapeHtml(t.title)} (${t.status})</option>`;
                });
                if(Array.from(taskSelect.options).some(option=>option.value===previousValue))taskSelect.value=previousValue;
                if(currentAIMode==='assignment_suggestion')await loadAssignmentPreview();
            }
        }

        // Tải ghi chú cuộc họp
        const noteRes = await fetch(`/api/projects/${currentProjectId}/meeting-notes`);
        const noteData = await noteRes.json();
        if (noteData.success) {
            const noteSelect = document.getElementById('ai-note-select');
            if (noteSelect) {
                const previousValue = noteSelect.value;
                noteSelect.innerHTML = '<option value="">-- Chọn từ ghi chú có sẵn (hoặc nhập bên dưới) --</option>';
                noteData.meeting_notes.forEach(n => {
                    noteSelect.innerHTML += `<option value="${n.id}">${escapeHtml(n.title)} (${n.meeting_date})</option>`;
                });
                if(Array.from(noteSelect.options).some(option=>option.value===previousValue))noteSelect.value=previousValue;
            }
        }
    } catch (e) {
        console.error('Lỗi tải dữ liệu nguồn cho AI:', e);
    }
}

async function loadAssignmentPreview(){
    if(typeof loadStaffingPreview==='function')await loadStaffingPreview();
}

function setupGenerateButton() {
    const btn = document.getElementById('btn-generate-ai');
    if (btn) {
        btn.addEventListener('click', handleGenerateAI);
    }

    const confirmBtn = document.getElementById('btn-confirm-draft');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', handleConfirmDraft);
    }
}

async function handleGenerateAI() {
    const generateButton = document.getElementById('btn-generate-ai');
    if (generateButton.disabled) return;
    const payload = {
        task_type: currentAIMode,
        project_id: currentProjectId,
        user_note: document.getElementById('ai-user-prompt')?.value || ''
    };

    if (currentAIMode === 'weekly_summary') {
        payload.week_start = document.getElementById('ai-week-start').value;
        payload.week_end = document.getElementById('ai-week-end').value;
        if (!payload.week_start || !payload.week_end) {
            showToast('Vui lòng chọn đầy đủ ngày bắt đầu và kết thúc tuần.', 'error');
            return;
        }
    } else if (currentAIMode === 'meeting_minutes') {
        const noteSelect = document.getElementById('ai-note-select');
        const noteId = noteSelect ? noteSelect.value : null;
        const rawNotes = document.getElementById('ai-raw-notes')?.value || '';
        if (!noteId && !rawNotes.trim()) {
            showToast('Vui lòng tải lên tệp biên bản hoặc nhập nội dung ghi chú cuộc họp.', 'error');
            return;
        }
        if (noteId) payload.meeting_note_id = noteId;
        if (rawNotes.trim()) payload.raw_notes = rawNotes.trim();
        if (uploadWarnings.length) payload.extraction_warnings = uploadWarnings;
    } else if (currentAIMode === 'assignment_suggestion') {
        Object.assign(payload,buildStaffingPayload(true));
        if(!document.getElementById('ai-requested-count').reportValidity())return;
        if(payload.purpose==='assignment'&&!payload.task_id){
            showToast('Vui lòng chọn nhiệm vụ cần gợi ý phân công.', 'error');
            return;
        }
        if(payload.purpose==='recruitment'&&!payload.user_note){showToast('Hãy nhập nhu cầu tìm người vào ô chỉ dẫn bổ sung.','error');return;}
        clearStaffingRecommendations();
    }

    // Hiển thị trạng thái đang xử lý (Pulse Animation)
    generateButton.disabled=true;
    document.querySelectorAll('.ai-tab-btn').forEach(button=>button.disabled=true);
    const contentEl = document.getElementById('ai-output-content');
    const loadingEl = document.getElementById('ai-loading-state');
    const actionsBar = document.getElementById('ai-actions-bar');
    const sourceChipsEl = document.getElementById('ai-source-chips');
    const statusTextEl = document.getElementById('ai-status-text');
    const warningsEl = document.getElementById('ai-warnings');

    contentEl.style.display = 'none';
    loadingEl.classList.add('active');
    actionsBar.style.display = 'none';
    warningsEl.style.display = 'none';
    const previousEngine = document.getElementById('ai-engine-source');
    if (previousEngine) previousEngine.textContent = '';

    try {
        const res = await fetch('/api/ai', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        loadingEl.classList.remove('active');
        contentEl.style.display = 'block';

        if (res.ok && data.success) {
            lastDraftId = data.draft_id;
            lastDraftVersion = data.version || 1;

            // Format markdown to HTML đơn giản
            contentEl.innerHTML = formatMarkdownToHtml(data.result);
            renderStaffingRecommendations(data.structured_result);
            statusTextEl.textContent = (data.status === 'draft') ? 'BẢN NHÁP (DRAFT)' : 'CẦN XÁC MINH';
            let engineLabel = document.getElementById('ai-engine-source');
            if (!engineLabel) {
                engineLabel = document.createElement('p');
                engineLabel.id = 'ai-engine-source';
                engineLabel.style.cssText = 'font-size:0.82rem;color:var(--text-secondary);margin:8px 0;';
                contentEl.before(engineLabel);
            }
            engineLabel.textContent = data.engine?.notice || '';
            statusTextEl.style.color = (data.status === 'draft') ? 'var(--neon-cyan)' : 'var(--neon-amber)';
            if (data.warnings && data.warnings.length) {
                warningsEl.innerHTML = `<strong>Cần kiểm tra:</strong><ul>${data.warnings.map(w => `<li>${escapeHtml(w)}</li>`).join('')}</ul>`;
                warningsEl.style.display = 'block';
            }

            // Render source reference chips
            if (data.source_references && data.source_references.length > 0) {
                const refs = data.source_references;
                sourceChipsEl.innerHTML = refs.slice(0, 12).map(r => `<span class="source-chip">${escapeHtml(r)}</span>`).join('') +
                    (refs.length > 12 ? `<span class="source-chip">+${refs.length - 12} nguồn trong bản nháp</span>` : '');
                document.getElementById('ai-source-box').style.display = 'block';
            } else {
                document.getElementById('ai-source-box').style.display = 'none';
            }

            // Hiển thị nút xác nhận nếu là Trưởng nhóm (Leader)
            actionsBar.style.display = 'flex';
            updateDraftActions(data.status);

            showToast('Trợ lý AI đã xử lý và kiểm định xong!', 'success');
        } else {
            const errorCode = data.error_code
                ? `<small style="display:block; margin-top:8px; opacity:0.75;">Mã lỗi: ${escapeHtml(data.error_code)}</small>`
                : '';
            const retryHint = currentAIMode === 'meeting_minutes' && document.getElementById('ai-raw-notes')?.value
                ? '<p style="margin-top:8px;">Nội dung đã trích xuất vẫn được giữ ở ô ghi chú. Bạn có thể thử tạo lại.</p>'
                : '';
            contentEl.innerHTML = `<div style="color:var(--neon-rose); padding:20px; text-align:center;">
                <h4>⚠️ Yêu cầu không thể hoàn tất</h4>
                <p style="margin-top:8px;">${escapeHtml(data.error || 'Lỗi khi gọi Trợ lý AI.')}</p>
                ${errorCode}
                ${retryHint}
            </div>`;
            showToast(data.error || 'Lỗi gọi AI', 'error');
        }
    } catch (e) {
        loadingEl.classList.remove('active');
        contentEl.style.display = 'block';
        contentEl.innerHTML = `<p style="color:var(--neon-rose);">Lỗi kết nối máy chủ.</p>`;
        showToast('Lỗi kết nối máy chủ.', 'error');
    } finally {
        generateButton.disabled=currentProjectRole==='viewer'||currentUser?.role==='admin';
        document.querySelectorAll('.ai-tab-btn').forEach(button=>button.disabled=false);
    }
}

async function handleConfirmDraft() {
    if (!lastDraftId || !canManageCurrentProject || lastDraftStatus !== 'draft') return;
    const confirmBtn = document.getElementById('btn-confirm-draft');
    confirmBtn.disabled = true;
    confirmBtn.textContent = 'Đang xác nhận...';

    try {
        const data = await apiRequest(`/api/ai/drafts/${lastDraftId}/confirm`, jsonRequest('POST', {version:lastDraftVersion}));
        await displayDraft(lastDraftId);
        showToast(data.message, 'success');
    } catch (e) {
        showToast(e.message || 'Lỗi khi xác nhận.', 'error');
        await displayDraft(lastDraftId);
    }
}

function updateDraftActions(status) {
    lastDraftStatus = status;
    const confirmButton = document.getElementById('btn-confirm-draft');
    confirmButton.style.display = canManageCurrentProject ? 'inline-flex' : 'none';
    confirmButton.disabled = status !== 'draft';
    confirmButton.textContent = status === 'confirmed' ? 'Đã xác nhận chính thức'
        : status === 'needs_verification' ? 'Xác nhận (cần đối chiếu)' : 'Xác nhận bản chính thức';
    document.getElementById('btn-edit-draft').hidden = status === 'confirmed' || currentUser?.role === 'admin' || currentProjectRole === 'viewer';
    document.getElementById('ai-confirmation-hint').textContent = status === 'needs_verification'
        ? 'Bản nháp còn cảnh báo. Chọn Chỉnh sửa bản nháp để đối chiếu, xử lý cảnh báo rồi lưu và xác nhận.'
        : status === 'confirmed' ? 'Bản chính thức đã được Trưởng nhóm xác nhận.' : 'Quyết định cuối cùng thuộc Trưởng nhóm.';
}

async function loadAIHistoryModal() {
    try {
        const res = await fetch(`/api/ai/history?project_id=${currentProjectId}`);
        const data = await res.json();
        const listEl = document.getElementById('ai-history-list');
        if (data.success && listEl) {
            if (data.history.length === 0) {
                listEl.innerHTML = '<p style="color:var(--text-muted); padding:20px;">Chưa có lịch sử gọi AI trong dự án này.</p>';
            } else {
                listEl.innerHTML = data.history.map(h => `
                    <div style="padding:14px; margin-bottom:12px; background:rgba(255,255,255,0.03); border-radius:8px; border-left:3px solid var(--neon-purple);">
                        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                            <strong style="color:#fff;">[${h.task_type.toUpperCase()}]</strong>
                            <span style="font-size:0.75rem; color:var(--text-muted);">${h.created_at}</span>
                        </div>
                        <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:8px;">${escapeHtml(h.result_summary)}</p>
                        <div style="font-size:0.75rem; display:flex; gap:12px; color:var(--text-muted);">
                            <span>Người yêu cầu: <strong>${escapeHtml(h.requester_name)}</strong></span>
                            <span>Trạng thái: <strong style="color:var(--neon-cyan);">${h.confirmation_status.toUpperCase()}</strong></span>
                            <span>Mô hình: ${escapeHtml(h.model_provider)}</span>
                            ${h.draft_id?`<button class="btn btn-secondary" onclick="displayDraft(${h.draft_id})">Xem kết quả đầy đủ</button>`:''}
                        </div>
                    </div>
                `).join('');
            }
            openModal('modal-ai-history');
        } else {
            showToast(data.error || 'Chỉ Quản trị viên và Trưởng nhóm mới có quyền xem lịch sử AI.', 'error');
        }
    } catch (e) {
        showToast('Lỗi tải lịch sử AI.', 'error');
    }
}

function formatMarkdownToHtml(md) {
    if (!md) return '';
    let html = escapeHtml(md);

    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^#### (.*$)/gim, '<h4>$1</h4>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');

    // Bold
    html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');

    // Bullet lists
    html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/gim, '<ul>$1</ul>');

    // Blockquotes
    html = html.replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>');

    // Line breaks
    html = html.replace(/\n\n/gim, '<br><br>');
    return html;
}

// Xử lý Kéo thả Tệp Biên bản Cuộc họp (FR-13)
function initFileDropzone() {
    const dropzone = document.getElementById('ai-file-dropzone');
    if (!dropzone) return;

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            uploadMeetingFile(files[0]);
        }
    });
}

function handleMeetingFileSelect(input) {
    if (input.files && input.files.length > 0) {
        uploadMeetingFile(input.files[0]);
    }
}

async function uploadMeetingFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    showToast(`Đang trích xuất nội dung từ tệp '${file.name}'...`, 'info');

    try {
        const res = await fetch('/api/ai/upload-meeting-file', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');

            // Cập nhật textarea ghi chú thô
            const notesArea = document.getElementById('ai-raw-notes');
            if (notesArea) {
                notesArea.value = data.extracted_text;
            }

            // Hiển thị badge trạng thái
            const statusBox = document.getElementById('file-upload-status');
            const nameEl = document.getElementById('uploaded-filename');
            const wordEl = document.getElementById('uploaded-wordcount');
            if (statusBox && nameEl && wordEl) {
                nameEl.textContent = data.filename;
                wordEl.textContent = `(${data.word_count.toLocaleString()} từ)`;
                statusBox.style.display = 'flex';
            }
            const warningEl = document.getElementById('file-extraction-warning');
            warningEl.textContent = uploadWarnings.join(' ');
            warningEl.style.display = uploadWarnings.length ? 'block' : 'none';
        } else {
            showToast(data.error || 'Không thể trích xuất nội dung tệp.', 'error');
        }
    } catch (e) {
        showToast('Lỗi khi tải lên tệp văn bản.', 'error');
    }
}

function clearUploadedFile() {
    uploadWarnings = [];
    const fileInput = document.getElementById('ai-minute-file-input');
    if (fileInput) fileInput.value = '';

    const statusBox = document.getElementById('file-upload-status');
    if (statusBox) statusBox.style.display = 'none';
    document.getElementById('file-extraction-warning').style.display = 'none';

    const notesArea = document.getElementById('ai-raw-notes');
    if (notesArea) notesArea.value = '';

    showToast('Đã xóa tệp và nội dung đính kèm.', 'info');
}

// Xem Danh sách Biên bản Cuộc họp Chính thức (FR-13 / UC010)
async function openOfficialMinutesModal() {
    const listEl = document.getElementById('official-minutes-list');
    if (!listEl) return;

    openModal('modal-official-minutes');
    listEl.innerHTML = '<p style="color:var(--text-muted); text-align:center; padding:20px;">Đang tải danh sách biên bản họp...</p>';

    try {
        const res = await fetch(`/api/projects/${currentProjectId}/meeting-minutes`);
        const data = await res.json();
        if (data.success) {
            if (data.minutes.length === 0) {
                listEl.innerHTML = `
                    <div style="text-align:center; padding:30px; color:var(--text-muted);">
                        <div style="font-size:2rem; margin-bottom:8px;">📝</div>
                        <p>Chưa có biên bản họp chính thức nào được xác nhận trong dự án này.</p>
                        <p style="font-size:0.8rem; margin-top:4px;">Bạn có thể tải lên tệp và dùng AI tóm tắt, sau đó Trưởng nhóm sẽ bấm "Xác nhận Bản chính thức".</p>
                    </div>
                `;
                return;
            }

            listEl.innerHTML = data.minutes.map(m => `
                <div class="glass-panel" style="padding:16px; border-left:3px solid var(--neon-cyan);">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <h4 style="color:#fff; font-size:1rem;">${escapeHtml(m.title)}</h4>
                        <span class="badge" style="background:rgba(16,185,129,0.15); color:var(--neon-emerald); font-size:0.75rem;">
                            ✓ ${m.status.toUpperCase()}
                        </span>
                    </div>

                    <div style="font-size:0.8rem; color:var(--text-muted); margin-bottom:10px;">
                        Người lập: <strong style="color:#fff;">${escapeHtml(m.creator_name || 'Hệ thống')}</strong> • 
                        Người duyệt: <strong style="color:var(--neon-cyan);">${escapeHtml(m.confirmer_name || 'Trưởng nhóm')}</strong> • 
                        Thời gian: ${m.confirmed_at || m.created_at}
                    </div>

                    <div style="background:rgba(255,255,255,0.02); padding:12px; border-radius:6px; font-size:0.85rem; color:var(--text-secondary); line-height:1.6; white-space:pre-wrap; margin-bottom:10px;">
                        ${escapeHtml(m.summary)}
                    </div>

                    ${m.action_items ? `
                        <div style="font-size:0.8rem; color:var(--text-highlight);">
                            📌 <strong>Hành động kế tiếp:</strong> ${escapeHtml(m.action_items)}
                        </div>
                    ` : ''}
                </div>
            `).join('');
        } else {
            listEl.innerHTML = `<p style="color:var(--neon-rose); text-align:center; padding:20px;">${data.error || 'Lỗi tải biên bản họp.'}</p>`;
        }
    } catch (e) {
        listEl.innerHTML = '<p style="color:var(--neon-rose); text-align:center; padding:20px;">Lỗi kết nối máy chủ.</p>';
    }
}



let editingDraftVersion=null;
let draftEditSaving=false;
let draftEditorSource=null;
let draftEditorReturnFocus=null;

async function displayDraft(id) {
    try {
        const {draft:d}=await apiRequest(`/api/ai/drafts/${id}`);
        lastDraftId=id;
        lastDraftVersion=d.version;
        currentAIMode=d.task_type;
        switchAIModeForm(currentAIMode);
        document.querySelectorAll('.ai-tab-btn').forEach(button=>button.classList.toggle('active',button.dataset.mode===d.task_type));
        const content=document.getElementById('ai-output-content');
        content.style.display='block';content.innerHTML=formatMarkdownToHtml(d.draft_content);
        renderStaffingRecommendations(d.structured_result);
        document.getElementById('ai-status-text').textContent=d.status==='confirmed'?'ĐÃ XÁC NHẬN':d.status==='draft'?'BẢN NHÁP':'CẦN XÁC MINH';
        document.getElementById('ai-actions-bar').style.display='flex';
        updateDraftActions(d.status);
        const warnings=document.getElementById('ai-warnings');warnings.textContent=d.warnings.join(' · ');warnings.style.display=d.warnings.length?'block':'none';
        const refs=JSON.parse(d.source_references_json||'[]');
        document.getElementById('ai-source-chips').innerHTML=refs.slice(0,12).map(ref=>`<span class="source-chip">${escapeHtml(ref)}</span>`).join('');
        document.getElementById('ai-source-box').style.display=refs.length?'block':'none';
        closeModal('modal-ai-history');
    }catch(error){showToast(error.message,'error');}
}

async function openDraftEditor() {
    if(!lastDraftId)return;
    try {
        const {draft:d}=await apiRequest(`/api/ai/drafts/${lastDraftId}`);
        if(d.status==='confirmed'){await displayDraft(lastDraftId);showToast('Bản này đã được xác nhận.','info');return;}
        draftEditorSource=d;
        draftEditorReturnFocus=document.activeElement;
        editingDraftVersion=d.version;
        document.getElementById('draft-edit-content').value=d.draft_content;
        document.getElementById('draft-meeting-fields').hidden=d.task_type!=='meeting_minutes';
        const result=d.structured_result||{};
        document.getElementById('draft-edit-title').value=result.title||'';
        document.getElementById('draft-edit-decisions').value=result.decisions||'';
        document.getElementById('draft-edit-actions').value=result.action_items||'';
        document.getElementById('draft-review-fields').hidden=!canManageCurrentProject||d.status!=='needs_verification';
        document.getElementById('draft-edit-verified').checked=false;
        document.getElementById('draft-edit-review-note').value='';
        document.getElementById('draft-version-info').textContent=`Phiên bản ${d.version}. Các bản chỉnh sửa được lưu để đối chiếu.`;
        document.getElementById('btn-save-confirm-draft').hidden=!canManageCurrentProject;
        openModal('modal-draft-editor');
        document.getElementById('modal-draft-editor').querySelector('.draft-editor-body').scrollTop=0;
        document.getElementById('modal-draft-editor').querySelector('.modal-header button').focus();
    }catch(error){showToast(error.message,'error');}
}

async function saveDraftEdit(event) {
    event.preventDefault();
    if(draftEditSaving)return;
    const confirmAfterSave=event.submitter?.dataset.action==='confirm';
    if(confirmAfterSave&&!canManageCurrentProject)return;
    const payload={version:editingDraftVersion,draft_content:document.getElementById('draft-edit-content').value};
    if(!document.getElementById('draft-meeting-fields').hidden)Object.assign(payload,{title:document.getElementById('draft-edit-title').value,decisions:document.getElementById('draft-edit-decisions').value,action_items:document.getElementById('draft-edit-actions').value,verified:document.getElementById('draft-edit-verified').checked,review_note:document.getElementById('draft-edit-review-note').value});
    if(confirmAfterSave&&draftEditorSource?.status==='needs_verification'&&draftEditorSource.task_type==='meeting_minutes'
            &&(!payload.verified||!payload.review_note.trim())){
        showToast('Hãy đối chiếu nguồn, đánh dấu xác minh và nhập ghi chú trước khi xác nhận.','error');
        document.getElementById(payload.verified?'draft-edit-review-note':'draft-edit-verified').focus();return;
    }
    draftEditSaving=true;
    const buttons=document.querySelectorAll('#modal-draft-editor button');buttons.forEach(button=>button.disabled=true);
    try{
        const saved=await apiRequest(`/api/ai/drafts/${lastDraftId}`,jsonRequest('PUT',payload));
        editingDraftVersion=saved.version;
        lastDraftVersion=saved.version;
        draftEditorSource.status=saved.status;
        document.getElementById('draft-version-info').textContent=`Phiên bản ${saved.version}. Các bản chỉnh sửa được lưu để đối chiếu.`;
        if(confirmAfterSave){
            if(saved.status!=='draft'){showToast('Bản nháp vẫn còn cảnh báo. Hãy xử lý nội dung trước khi xác nhận.','error');return;}
            await apiRequest(`/api/ai/drafts/${lastDraftId}/confirm`,jsonRequest('POST',{version:saved.version}));
        }
        closeModal('modal-draft-editor');
        await displayDraft(lastDraftId);
        showToast(confirmAfterSave?'Đã lưu và xác nhận bản chính thức.':'Đã lưu bản chỉnh sửa.','success');
    }catch(error){showToast(error.message,'error');}
    finally{draftEditSaving=false;buttons.forEach(button=>button.disabled=false);}
}

function closeDraftEditor(){
    if(draftEditSaving)return;
    closeModal('modal-draft-editor');
    draftEditorSource=null;
    draftEditorReturnFocus?.focus();
}

document.addEventListener('keydown',event=>{
    const modal=document.getElementById('modal-draft-editor');
    if(!modal?.classList.contains('active'))return;
    if(event.key==='Escape'){event.preventDefault();closeDraftEditor();}
    if(event.key==='Tab'){
        const controls=Array.from(modal.querySelectorAll('button,input,textarea,select,[tabindex]'))
            .filter(el=>!el.disabled&&el.tabIndex>=0&&el.getClientRects().length);
        const first=controls[0],last=controls[controls.length-1];
        if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}
        else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}
    }
});

function openMeetingNoteForm(){document.getElementById('meeting-note-date').value=dateTimeInput(new Date().toISOString());openModal('modal-meeting-note');}

async function saveMeetingNote(event){
    event.preventDefault();
    try{
        const data=await apiRequest(`/api/projects/${currentProjectId}/meeting-notes`,jsonRequest('POST',{title:document.getElementById('meeting-note-title').value,meeting_date:document.getElementById('meeting-note-date').value,attendees:document.getElementById('meeting-note-attendees').value,content:document.getElementById('meeting-note-content').value}));
        closeModal('modal-meeting-note');event.target.reset();await loadAIDataSources();document.getElementById('ai-note-select').value=data.note_id;showToast('Đã lưu ghi chú cuộc họp.','success');
    }catch(error){showToast(error.message,'error');}
}
