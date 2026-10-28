const reportStates = [['backlog','Tồn đọng','#94a3b8'],['todo','Cần làm','#38bdf8'],['in_progress','Đang làm','#a78bfa'],['review','Kiểm tra','#fbbf24'],['done','Hoàn thành','#34d399']];
let reportRequest = 0;
document.addEventListener('DOMContentLoaded', async () => {
    await projectReady;
    if(!currentProjectId){document.getElementById('workload-table-body').innerHTML='<tr><td colspan="7">Bạn chưa tham gia dự án nào.</td></tr>';return;}
    try{
        await loadWorkloadReport();
    }catch(error){showReportError(error.message);}
});
function reportNumber(value){const n=Number(value);return Number.isFinite(n)?Math.max(0,n):0;}
function showReportError(message){const el=document.getElementById('report-error');el.textContent=message;el.hidden=false;}
async function loadWorkloadReport(){
    const request=++reportRequest;
    try{
        const options=await apiRequest(`/api/projects/${currentProjectId}/sprints`);
        if(request!==reportRequest)return;
        const select=document.getElementById('report-sprint'),previous=select.value;
        select.replaceChildren(new Option('Toàn dự án',''));
        for(const sprint of options.sprints)select.add(new Option(sprint.name,sprint.id));
        if(Array.from(select.options).some(option=>option.value===previous))select.value=previous;
        const sprint=select.value;
        const data=await apiRequest(`/api/projects/${currentProjectId}/report?${new URLSearchParams({sprint_id:sprint})}`);
        if(request!==reportRequest)return;
        document.getElementById('report-error').hidden=true;
        const m=data.metrics, members=data.workload;
        for(const [id,value] of Object.entries({total:m.total_tasks,completion:`${m.completion_rate}%`,average:`${m.average_progress}%`,overdue:m.overdue_count,overloaded:members.filter(x=>x.is_overloaded).length}))document.getElementById(`report-${id}`).textContent=value;
        renderStatusChart(m,sprint);
        renderWorkloadChart(members);
        document.getElementById('workload-table-body').innerHTML=members.map(member=>`<tr data-user-id="${member.user_id}">
          <td><a href="/kanban?assignee_id=${member.user_id}">${escapeHtml(member.full_name)}</a></td>
          <td>${escapeHtml(member.skills||'Chưa cập nhật')}</td><td>${member.availability_percent}%</td>
          <td>${member.effective_capacity_hours}h / ${member.capacity_hours}h</td><td>${member.current_workload_hours}h</td><td>${member.active_task_count} việc (${member.overdue_task_count} trễ)</td>
          <td class="${member.is_overloaded?'workspace-warning':'workspace-success'}">${member.is_overloaded?'Quá tải':'Trong năng lực'}${member.missing_estimate_count?` · ${member.missing_estimate_count} việc thiếu ước lượng`:''}${member.configuration_warning?` · ${escapeHtml(member.configuration_warning)}`:''}</td></tr>`).join('')||'<tr><td colspan="7">Chưa có thành viên.</td></tr>';
    }catch(error){if(request===reportRequest)showReportError(error.message);throw error;}
}
function renderStatusChart(metrics,sprint){
    const total=reportNumber(metrics.total_tasks), circumference=2*Math.PI*76;
    let offset=0;
    const circles=reportStates.map(([status,,color])=>{
        const value=reportNumber(metrics[`count_${status}`]),length=total?circumference*value/total:0;
        const svg=`<circle cx="110" cy="110" r="76" fill="none" stroke="${color}" stroke-width="24" stroke-dasharray="${length} ${circumference-length}" stroke-dashoffset="${-offset}" transform="rotate(-90 110 110)"/>`;
        offset+=length;return svg;
    }).join('');
    const chart=document.getElementById('report-status-chart');
    chart.setAttribute('aria-label',`${total} nhiệm vụ: ${reportStates.map(([s,label])=>`${label} ${reportNumber(metrics[`count_${s}`])}`).join(', ')}`);
    chart.innerHTML=`<title>Phân bố trạng thái nhiệm vụ</title><circle cx="110" cy="110" r="76" fill="none" stroke="#283548" stroke-width="24"/>${circles}<text x="110" y="108" text-anchor="middle" fill="#f8fafc" font-size="32" font-weight="700">${total}</text><text x="110" y="133" text-anchor="middle" fill="#94a3b8" font-size="13">${total?'nhiệm vụ':'Chưa có nhiệm vụ'}</text>`;
    document.getElementById('report-status-legend').innerHTML=reportStates.map(([status,label,color])=>`<a href="/kanban?${new URLSearchParams({status,...(sprint?{sprint_id:sprint}:{})})}"><span class="legend-dot" style="background:${color}"></span>${label}: <strong>${reportNumber(metrics[`count_${status}`])}</strong></a>`).join('');
}
function renderWorkloadChart(members){
    const max=Math.max(1,...members.flatMap(m=>[reportNumber(m.current_workload_hours),reportNumber(m.effective_capacity_hours)]));
    document.getElementById('report-workload-chart').innerHTML=members.map(m=>{
        const workload=reportNumber(m.current_workload_hours),capacity=reportNumber(m.effective_capacity_hours);
        return `<div class="workload-chart-row" data-user-id="${m.user_id}" role="img" aria-label="${escapeHtml(m.full_name)}: tải ${workload} giờ, khả dụng ${capacity} giờ${m.is_overloaded?', quá tải':''}">
          <div class="workload-chart-label"><a href="/kanban?assignee_id=${m.user_id}">${escapeHtml(m.full_name)}</a><span>${workload}h / ${capacity}h ${m.is_overloaded?'· Quá tải':''}</span></div>
          <div class="chart-track"><div class="chart-fill" style="width:${100*workload/max}%;background:${m.is_overloaded?'#fb7185':'#22d3ee'}"></div></div>
          <div class="chart-track"><div class="chart-fill" style="width:${100*capacity/max}%;background:#34d399"></div></div></div>`;
    }).join('')||'<p class="form-help">Chưa có thành viên để thống kê.</p>';
}
