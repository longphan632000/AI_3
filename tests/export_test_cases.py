"""Export verified acceptance scenarios to Markdown, CSV and copyable HTML."""
import csv
from html import escape
import json
from pathlib import Path
import re
import sys

from case_catalog import CASES

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'logstest'


def cell(value):
    return str(value).replace('|','\\|').replace('\n',' ')


def main():
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    sqlite=json.loads((OUT/'qa-results-sqlite.json').read_text(encoding='utf-8'))
    mysql=json.loads((OUT/'qa-results-mysql.json').read_text(encoding='utf-8'))
    engines={engine:{record['method']:record for record in data['records'] if 'TestRequirementRepairs' in record['test']}
             for engine,data in [('SQLite',sqlite),('MySQL',mysql)]}
    headers=['Mã TC','Yêu cầu','Kịch bản/chức năng','Tiền điều kiện và dữ liệu','Các bước kiểm thử','Kết quả mong đợi','Kết quả thực tế','Kết quả']
    rows=[]
    for number,(scenario,preconditions,steps,expected) in CASES.items():
        matches=[name for name in engines['MySQL'] if re.match(f'test_{number:02d}_',name)]
        if len(matches)!=1:
            raise RuntimeError(f'Missing executed evidence for TC-{number:02d}')
        method=matches[0]
        records=[engines[engine][method] for engine in ('SQLite','MySQL')]
        success=all(record['result']=='Thành công' for record in records)
        evidence=records[1].get('evidence',{})
        actual=json.dumps(evidence.get('actual'),ensure_ascii=False,separators=(',',':'))
        actual=f"SQLite: {records[0]['result']}; MySQL: {records[1]['result']}. Thực tế: {actual}"
        rows.append([f'TC-{number:02d}',', '.join(evidence.get('requirements',[])),scenario,preconditions,steps,expected,actual,'Thành công' if success else 'Thất bại'])
    note=('Kết quả lấy từ các ca đã thực thi trên SQLite tạm và MySQL cách ly. '
          'Bảng hồi quy dùng AI/email giả lập; kết quả Gemini thật được trình bày riêng khi có. '
          'TC-33/34/48 kiểm tra mã/HTML/tài nguyên; xem qa-browser-results.json để đối chiếu kiểm thử Edge bổ sung. '
          'Thành công nghĩa là hệ thống cho kết quả mong đợi, kể cả ca từ chối đầu vào hoặc quyền sai.')
    summary=f"Bộ hồi quy: SQLite {sqlite['passed']}/{sqlite['tests_run']} đạt; MySQL {mysql['passed']}/{mysql['tests_run']} đạt. Bảng dưới có {len(rows)} kịch bản nghiệm thu/hồi quy chi tiết."
    browser_result_path=OUT/'qa-browser-results.json'
    if browser_result_path.exists():
        browser_result=json.loads(browser_result_path.read_text(encoding='utf-8'))
        passed=sum(record['passed'] for record in browser_result['records'])
        summary+=f" Kiểm thử Edge bổ sung: {passed}/{len(browser_result['records'])} nhóm đạt."
    live_rows=[]
    live_path=OUT/'qa-gemini-live-results.json'
    if live_path.exists():
        live=json.loads(live_path.read_text(encoding='utf-8'))
        labels={'weekly_summary':('FR-12','Tóm tắt tiến độ tuần bằng Gemini thật'),
                'meeting_minutes':('FR-13','Tạo biên bản bằng Gemini thật'),
                'assignment_suggestion':('FR-14','Gợi ý phân công bằng Gemini thật')}
        for number,record in enumerate(live['records'],1):
            requirement,scenario=labels[record['task_type']]
            actual=json.dumps({key:record.get(key) for key in ('http','error_code','status','seconds','draft_saved')},ensure_ascii=False)
            live_rows.append([f'LIVE-AI-{number:02d}',requirement,scenario,
                              'API key đã cấu hình; ngoài sandbox; dữ liệu QA tổng hợp trong SQLite tạm.',
                              f"POST /api/ai với task_type={record['task_type']}; kiểm tra draft; không xác nhận.",
                              'HTTP 200; có nội dung và draft đọc được; không tự phân công/xác nhận.',
                              actual,'Thành công' if record['passed'] else 'Thất bại'])
        summary+=f" Gemini thật: {sum(row[-1]=='Thành công' for row in live_rows)}/{len(live_rows)} đạt (dữ liệu QA riêng)."
    markdown='# Bảng kịch bản kiểm thử sau chỉnh sửa\n\n'+summary+'\n\n'+note+'\n\n'
    markdown+='| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'
    markdown+='\n'.join('| '+' | '.join(cell(value) for value in row)+' |' for row in rows)+'\n'
    system_path=OUT/'qa-system-checks.json'
    if system_path.exists():
        system=json.loads(system_path.read_text(encoding='utf-8'))
        markdown+='\n## Kiểm tra bổ sung trên MySQL cách ly\n\n| Kiểm tra | Thực tế | Kết quả |\n| --- | --- | --- |\n'
        for check in system['checks']:
            details={key:value for key,value in check.items() if key not in ('name','passed')}
            markdown+=f"| {cell(check['name'])} | {cell(json.dumps(details,ensure_ascii=False))} | {'Thành công' if check['passed'] else 'Thất bại'} |\n"
    browser_path=OUT/'qa-browser-results.json'
    if browser_path.exists():
        browser=json.loads(browser_path.read_text(encoding='utf-8'))
        markdown+='\n## Kiểm tra giao diện và đồng bộ trên Microsoft Edge headless\n\nViewport mô phỏng; database cách ly; Gemini HTTP giả lập. Chưa thay thế kiểm tra thiết bị vật lý.\n\n| Mã | Kịch bản | Thực tế | Kết quả |\n| --- | --- | --- | --- |\n'
        for number,record in enumerate(browser['records'],1):
            details=record.get('details',record.get('error',''))
            markdown+=f"| UI-{number:02d} | {cell(record['name'])} | {cell(json.dumps(details,ensure_ascii=False))} | {'Thành công' if record['passed'] else 'Thất bại'} |\n"
    if live_rows:
        markdown+='\n## Gemini thật — dữ liệu QA cách ly\n\nCác ca này gọi Google thật; không dùng phản hồi giả lập. Đọc metadata thành công chưa chứng minh tạo nội dung hoặc quota thành công.\n\n'
        markdown+='| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'
        markdown+='\n'.join('| '+' | '.join(cell(value) for value in row)+' |' for row in live_rows)+'\n'
        with (OUT/'TEST_CASES_GEMINI_THAT.csv').open('w',encoding='utf-8-sig',newline='') as file:
            writer=csv.writer(file);writer.writerow(headers);writer.writerows(live_rows)
    (OUT/'TEST_CASES_SAU_CHINH_SUA.md').write_text(markdown,encoding='utf-8')
    with (OUT/'TEST_CASES_SAU_CHINH_SUA.csv').open('w',encoding='utf-8-sig',newline='') as file:
        writer=csv.writer(file);writer.writerow(headers);writer.writerows(rows)
    html='''<!doctype html><html lang="vi"><meta charset="utf-8"><title>Kịch bản kiểm thử sau chỉnh sửa</title>
<style>body{font:12pt Arial,sans-serif;margin:24px;color:#111}table{border-collapse:collapse;width:100%}th,td{border:1px solid #bbb;padding:8px;vertical-align:top}th{background:#16324f;color:white}tr:nth-child(even){background:#f2f5f8}thead{display:table-header-group}@media print{@page{size:A4 landscape;margin:12mm}body{font-size:9pt}tr{break-inside:avoid}}</style><h1>Kịch bản kiểm thử sau chỉnh sửa</h1>'''
    html+='<p>'+escape(summary)+'</p><p>'+escape(note)+'</p><table><thead><tr>'+''.join('<th>'+escape(h)+'</th>' for h in headers)+'</tr></thead><tbody>'
    html+=''.join('<tr>'+''.join('<td>'+escape(str(value))+'</td>' for value in row)+'</tr>' for row in rows)+'</tbody></table></html>'
    if live_rows:
        extra='<h2>Gemini thật — dữ liệu QA cách ly</h2><p>Các ca gọi Google thật; kết quả tách khỏi hồi quy giả lập.</p><table><thead><tr>'+''.join('<th>'+escape(h)+'</th>' for h in headers)+'</tr></thead><tbody>'
        extra+=''.join('<tr>'+''.join('<td>'+escape(str(value))+'</td>' for value in row)+'</tr>' for row in live_rows)+'</tbody></table>'
        html=html.replace('</html>',extra+'</html>')
    (OUT/'TEST_CASES_SAU_CHINH_SUA.html').write_text(html,encoding='utf-8')
    print(summary)
    print('Acceptance results:',sum(row[-1]=='Thành công' for row in rows),'success;',sum(row[-1]=='Thất bại' for row in rows),'failure')


if __name__=='__main__':
    main()
