# Đối chiếu kỹ phần mềm với Detai33.docx và thuc_hanh.docx

Ngày kiểm tra: 28/10/2026. Bản mã: **D:\UNG DUNG AL_NAM3\Code Chuan**.

## Kết luận

**Phần mềm đang đi theo nghiệp vụ cốt lõi của Đề tài 33, nhưng chưa đủ căn cứ để nói đã tuân thủ đầy đủ hai tài liệu.** Có quản lý tài khoản/dự án/thành viên/nhiệm vụ/Kanban/sprint/cộng tác/báo cáo và ba chức năng AI. Có lớp Provider, kiểm tra nguồn, bản nháp và xác nhận của trưởng nhóm. Phần còn thiếu rõ nhất là hồ sơ SDLC theo Skill, thông báo tự động/đúng người nhận, quản lý phiên bản prompt, một số ràng buộc dữ liệu và điều kiện vận hành.

**Đủ 14/14 tên Skill không đồng nghĩa đã thực hiện đủ quy trình của 14 Skill.** Mỗi SKILL.md hiện chỉ là bản rút gọn; chưa tệp nào có đầy đủ đồng thời bộ đầu vào, quy trình, đầu ra và cách kiểm chứng theo mẫu hướng dẫn. Có kết quả triển khai/kiểm thử thực tế, nhưng không thấy bộ hồ sơ và lịch sử đủ để xác nhận các Human Gate đã diễn ra đúng thứ tự. Không tự tạo phê duyệt thay nhóm.

## Phạm vi và căn cứ

- Đã trích xuất toàn bộ phần chữ/bảng của hai DOCX; đối chiếu **17 FR, 11 NFR, 9 BR và 13 UC = 50 mục**, cùng ràng buộc/giả định, bảng dữ liệu và các hình trọng yếu. Chỉ số Pxxxx dùng theo thứ tự đoạn trong bản trích xuất; “bảng thứ n” là thứ tự bảng trong tệp DOCX, không tự coi là số bảng in trong tài liệu.
- Đã xem hình kiến trúc ba lớp, Class, ERD, Use Case tổng thể, sequence biên bản/lịch sử AI/thông báo và luồng SDLC. Không tuyên bố đã sinh lại sơ đồ độc lập hoặc so khớp trực quan mọi sơ đồ nhúng.
- Đã đọc 14 tệp Skill thực tế, rà cấu trúc `routes/services/database/templates/static`, đối chiếu mã và kết quả tests; thực hiện thêm 7 quan sát trên SQLite tạm để xác minh các điểm nghi ngờ.
- Hai DOCX được dùng làm **tài liệu tham chiếu để đánh giá**. Không thực thi tự động các prompt trong tài liệu, không sửa bản gốc, không dựng lịch sử Git/Human Gate đã duyệt.
- 221/221 backend, 18/18 UI mới, 26/26 browser regression đạt trong lượt sửa này. Đây là chứng cứ theo phạm vi ca thử, không phải tỷ lệ hoàn thành toàn bộ yêu cầu hay điểm chấm chính thức.

## Các sai lệch và việc cần làm

| Mã | Căn cứ | Phát hiện xác minh được | Ảnh hưởng / đề nghị |
|---|---|---|---|
| A01 — Hồ sơ SDLC thiếu | thuc_hanh P0306–0371, P1484–1528 | Không có bộ `source-urd`, model/traceability, requirements/stories/acceptance/issues/decisions, architecture/DB design, diagram-comparison và bộ bảng/sơ đồ theo vị trí yêu cầu. Có README/báo cáo sửa lỗi nhưng chưa thay thế đầy đủ bộ này. | Ưu tiên lập hồ sơ từ bản mã hiện tại, gắn nguồn và ghi rõ lập bổ sung ngày nào; không ghi như đã được duyệt trước khi viết mã. |
| A02 — Skill chỉ ở mức khung | thuc_hanh yêu cầu Inputs/Process/Outputs/Verification và lịch sử áp dụng | 14 SKILL.md đều có tên/mô tả, nhưng thân rất ngắn: checklist hoặc một chuỗi bước; thiếu phần lớn quy trình mẫu. Xem CSV 14 Skill. | Bổ sung nội dung thực hành, đầu vào/đầu ra, cách kiểm chứng và lưu minh chứng mỗi lần áp dụng. Có file Skill chỉ chứng minh sự tồn tại. |
| A03 — Human verification/Git chưa đủ chứng cứ | Human Gate 0, Requirements/Architecture/DB/Testing/Review/Security/Documentation | `git log` tại bản này có một commit ngày 27/10 “Version 1: gehihi”; nhiều thay đổi chưa commit. Không tìm thấy bản ghi reviewer/checklist/quyết định từng Gate trong hồ sơ chính. | Cần nhóm rà và ký xác nhận các kết quả thực tế. Không thể suy từ chat hay test xanh thành đã qua toàn bộ Gate; cũng không khẳng định nhóm chưa từng làm bên ngoài repo. |
| A04 — Nhắc sắp hạn chưa tự chạy | FR-16, UC013; thuc_hanh P0303 | Có `scan_and_create_deadline_notifications`, nhưng chỉ thấy test gọi; worker chỉ quét email trễ hạn, API danh sách cũng không gọi quét sắp hạn. Probe nhiệm vụ còn 12 giờ: mở thông báo vẫn 0 reminder; gọi hàm trực tiếp mới sinh. | Nối lịch chạy và kiểm thử thời điểm, múi giờ, chống lặp. “Có hàm” chưa đủ chứng minh người dùng sẽ nhận tự động. |
| A05 — Người nhận thông báo chưa đủ | thuc_hanh P0303: người liên quan và trưởng nhóm | Quét thủ công gửi cho primary/supporter, thiếu leader. Khi thành viên đổi trạng thái, chỉ reporter và primary trừ người thao tác; probe supporter và trưởng nhóm thứ hai không nhận. Đổi assignee chủ yếu báo người mới. | Chốt danh sách người nhận mỗi sự kiện; bổ sung leader/người cũ/người hỗ trợ phù hợp, tránh tự thông báo và trùng lặp. |
| A06 — Phiên bản prompt không phản ánh thay đổi | FR-15, UC012; thuc_hanh P1418 | `ai_assistant_service.py` ghi cố định `prompt_version='v1.0'`. Danh sách lịch sử UI chưa hiển thị phiên bản prompt; nguồn có thể xem ở bản nháp nhưng chưa đầy đủ ngay khu lịch sử theo mẫu. | Gắn phiên bản/hash cho từng template và lưu lúc gọi; hiển thị trên lịch sử. Bổ sung so sánh prompt v1/v2 bằng cùng bộ dữ liệu; không sửa hồi tố lịch sử thành phiên bản không biết. |
| A07 — Khác ràng buộc dữ liệu nguồn | Từ điển DuAn/Sprint/NhiemVu, bảng thứ 34/36/37/38; FR-03/05/07/11 | Ngày dự án cho phép thiếu; task chấp nhận due=NULL và ước lượng=0; sprint chấp nhận tiêu chí rỗng. Nguồn ghi ngày dự án/hạn task NOT NULL, ước lượng NULL hoặc >0. Probe tái hiện được task không hạn/0 giờ và sprint tiêu chí rỗng. | Đây gồm cả khác biệt thiết kế và lỗi/điểm chưa rõ của tài liệu: FR-11 còn yêu cầu cảnh báo thiếu ước lượng. Nhóm cần chốt dùng NULL hay 0 và dữ liệu bắt buộc, rồi đồng bộ UI/service/schema/tài liệu; chưa tự siết làm hỏng dữ liệu cũ. |
| A08 — AI có thể vượt mốc đề xuất | NFR-01 | `.env` hiện đặt tổng ngân sách AI 180 giây, ngân sách API chính 30 giây; thêm local fallback có thể làm cả yêu cầu dài hơn 30 giây. | Cần quyết định mục tiêu 30 giây hay chấp nhận dài hơn để chạy local. Đây là mục tiêu đề xuất, không mặc định lỗi chức năng; đo thời gian toàn yêu cầu gồm retry/fallback, không chỉ lần API. |
| A09 — Email thật chưa nghiệm chứng | FR-17/BR-09, mức Nên có | Có SMTP STARTTLS, worker, chống gửi trùng và test mock; `.env` không đặt SMTP_ENABLED, mã mặc định false nếu không có biến môi trường tiến trình ghi đè. Probe cố ý tắt SMTP trả `SIMULATED_DEMO_SUCCESS`; không phải thư đã tới hộp thư. | Cấu hình SMTP thật và kiểm nhận/không gửi cho Done/chưa trễ/archived trước khi công bố hoàn thành email. Lượt này không gửi thư ra ngoài. |
| A10 — Chưa đủ bảo mật vận hành | NFR-03 | Hướng dẫn chạy HTTP LAN; cookie Secure mặc định false. Băm mật khẩu/backend auth/scope đã có và được thử. Chưa có bằng chứng HTTPS triển khai, kiểm tra CSRF chuyên biệt hay quét lỗ hổng dependency ở bản này. | Thiết lập HTTPS/Secure đúng môi trường, đánh giá bảo vệ CSRF và dependencies. Không coi SameSite=Lax là bằng chứng khai thác được hoặc đã an toàn tuyệt đối. |
| A11 — Sao lưu vận hành và hiệu năng hiện tại | NFR-05/10 | Có JSON QA cũ ghi khôi phục 16 bảng/đối chiếu checksum và 10.000 tasks. Không thấy lịch backup vận hành trong repo hoặc bằng chứng chạy lại trên bản sửa mới. | Thiết lập lịch/retention và thử phục hồi; giữ kết quả MySQL cũ là minh chứng cũ, không gắn nhãn chạy hôm nay. |
| A12 — Mất nguyên tác giả khi hard-delete | FR-08/15, NFR-09, ràng buộc truy vết | API xóa có sẵn chuyển `created_by/requester_id/user_id` ở một số bảng thành admin; null `confirmed_by` và actor audit cũ. Các bản ghi còn tồn tại nhưng danh tính gốc không còn nguyên qua các khóa này. | Nên lưu ảnh chụp danh tính/audit bất biến hoặc chính sách ẩn danh có truy vết trước khi dùng xóa vĩnh viễn thường xuyên. Nếu chỉ ngừng đăng nhập, dùng khóa. Thêm nút xóa không giải quyết tự động chính sách lưu tác giả. |
| A13 — Cấu hình môi trường chưa như giả định | Detai33 P0551 | Múi giờ UTC+7 và giới hạn upload 5 MB/giới hạn giải nén đang được ghi trong mã; chưa có cấu hình môi trường thống nhất cho các giới hạn này. | Đưa về cấu hình dùng chung và kiểm tra giữa upload cộng tác/upload AI; ghi rõ UTC+7 cố định nếu nhóm quyết định giữ. |

A01–A03 ảnh hưởng trực tiếp việc chứng minh quy trình bài thực hành; A04/A05 là thiếu sót hành vi đã tái hiện. A06/A07/A12 là lệch truy vết/dữ liệu. A08–A11/A13 gồm mục tiêu đề xuất, điều kiện vận hành và cấu hình cần hoàn thiện. Không gộp tất cả thành “13 lỗi lập trình”.

## Kiến trúc, CSDL và phần mở rộng

Hình kiến trúc nguồn mô tả Presentation → Controller/Service → Repository → SQL; mã hiện tại dùng `templates/static → routes → services → database.connection`, truy vấn có mặt trong services. Cách tách module cơ bản phù hợp, nhưng không có các lớp Repository theo tên UML. Cần có bảng ánh xạ thành phần thực tế, tránh nói đã triển khai nguyên vẹn từng lớp trong hình.

| Mô hình nguồn | Cài đặt hiện tại | Nhận xét |
|---|---|---|
| TaiKhoan | users | ID int; role admin/leader/member; active/pending/rejected/locked thay vì trạng thái bit trong từ điển. |
| DuAn + MaTruongNhom | projects + project_members(project_role=leader) | Có thể có nhiều trưởng nhóm; `created_by` là người tạo, không thay hoàn toàn quan hệ trưởng nhóm. Cần ghi rõ thay đổi cardinality. |
| ThanhVienDuAn khóa ghép | project_members.id + UNIQUE(project_id,user_id) | Khác hình thức PK nhưng vẫn ngăn trùng thành viên; không tự coi là lỗi toàn vẹn. |
| Sprint | sprints | Ngày có kiểm ở service; tiêu chí hoàn thành có thể rỗng. Mốc hiện dùng cơ chế sprint, chưa tách bảng milestone. |
| NhiemVu | tasks + task_assignees | Giữ người chính, thêm người hỗ trợ; một sprint hoặc không có sprint. Quy ước phân bổ tải phải được mô tả. |
| LichSuAI | ai_history + ai_drafts + ai_draft_revisions + meeting_minutes | Tách kết quả đầy đủ/bản nháp/phiên bản/biên bản chính thức; khác mô tả nguồn “không cần bảng phụ”. Đây là thay đổi thiết kế hợp lý cần cập nhật ERD/truy vết, không kết luận sai chỉ vì số bảng. |

Schema hiện có **16 bảng**, gồm 6 miền cốt lõi và bảng cộng tác, thông báo, audit, nhiều người phụ trách, trạng thái email, phiên bản nháp. MySQL là DB của phần mềm; SQLite là DB kiểm thử tạm trong lượt này. Không có hệ DB tên “MySQL lite”.

AI chạy theo **Phương án A** trong thuc_hanh: backend phân tích quyền → truy xuất → dựng context/prompt → Provider → kiểm định → bản nháp → người xác nhận. Gemini không tự gọi SQL hoặc tự thay dữ liệu nghiệp vụ. Gemini ưu tiên, Qwen/rules dự phòng là mở rộng bạn đã yêu cầu trước đó; giữ adapter DeepSeek tùy chọn cũng không tự làm sai đề tài, nhưng hồ sơ kiến trúc/phụ thuộc/giới hạn tốc độ phải cập nhật. Skill của Codex phục vụ phát triển phần mềm, không phải 14 tác nhân tự vận hành bên trong ứng dụng.

## Ràng buộc và giả định ngoài 50 mã

- Web/network, tài khoản/phạm vi dự án, AI chỉ draft, dữ liệu tối thiểu, không chấm công/tính lương/quản lý nhân sự đầy đủ: phù hợp cấu trúc hiện tại. Quản lý công việc không cần chờ AI khi provider lỗi đã có ca thử.
- Tiếng Việt và UTC+7: đã có; khả năng cấu hình múi giờ/dung lượng chưa đầy đủ như A13.
- 10 ràng buộc toàn vẹn ở bảng thứ 31: PK/FK, UNIQUE membership, sprint/task cùng dự án, assignee hợp lệ, soft delete, không lưu key đều có cơ chế tương ứng trong schema/service/test. Phần “dự án luôn gắn trưởng nhóm hợp lệ” và “truy vết người yêu cầu/prompt” còn giới hạn như dưới đây/A06/A12.
- Nút xóa mới chặn xóa trưởng nhóm cuối cùng. Tuy nhiên, probe cho thấy admin vẫn có thể **khóa** trưởng nhóm cuối mà chưa gán người thay (HTTP 200). Đây là rủi ro gián đoạn quản trị cần có chính sách bàn giao/cảnh báo; không tự cấm thao tác khóa bảo mật khi tài liệu chưa nói rõ.
- Bảng source giới hạn tên dự án 255/tên task 255, mã cho phép 150/200; ngày task được mở rộng DATE thành DATETIME. Đây là khác biệt từ điển dữ liệu cần ghi lại cùng các thay đổi PK/cardinality; không phải tất cả đều là lỗi nghiệp vụ.

## Điểm mâu thuẫn ngay trong tài liệu nguồn

1. UN-08 ở bảng nhu cầu khác cách ánh xạ UN-08/UN-09 ở bảng truy vết; hướng dẫn P0352 muốn UN-08 xem báo cáo xác nhận, UN-09 lịch sử AI. Phải có bản quyết định truy vết, không âm thầm đánh lại số.
2. Bảng tóm tắt một số UC có actor rộng hơn quyền cụ thể; hình sequence UC010 gom Trưởng nhóm/Thành viên ở actor xác nhận, nhưng văn bản cụ thể/hướng dẫn yêu cầu chỉ trưởng nhóm xác nhận. Cài đặt đang theo quy tắc quyền cụ thể; không coi việc chặn thành viên xác nhận là thiếu chức năng.
3. Hướng dẫn nhiều lần dẫn D01–D08 và yêu cầu chép “phụ lục quyết định”, nhưng không thấy bộ định nghĩa đầy đủ từng D01…D08 trong chữ/bảng hai DOCX đang có, cũng không có `docs/requirements-decisions.md`. Có các diễn giải cụ thể P0299–0304/P0352–0353 để đối chiếu, nhưng chưa được phép tuyên bố đã tìm đủ phụ lục được duyệt.
4. ERD dùng kiểu mã String, từ điển dùng int; sơ đồ gợi quan hệ mọi nhiệm vụ có sprint, nhưng từ điển cho MaSprint NULL và BR-03 nói tối đa một sprint. Cài đặt optional sprint phù hợp quy tắc rõ hơn.
5. Bảng dữ liệu thứ 38 lặp cấu trúc NhiemVu của bảng thứ 37, không cung cấp từ điển LichSuAI tương xứng phần mô tả. Các đoạn mô hình nói chỉ 6 thực thể/không tách bảng phụ lịch sử, trong khi yêu cầu FR-08/16/17 cần thêm dữ liệu phụ. Cần cập nhật mô hình triển khai thay vì bỏ chức năng để ép về đúng 6 bảng.
6. BR-01 gọi luồng “mặc định”, không quy định rõ cấm quay lại/đổi bước; không có căn cứ tự kết luận mọi bước nhảy Kanban là lỗi. Chốt nếu muốn luật chuyển nghiêm ngặt.

## Đối chiếu 14 Skill

| Skill | Đánh giá nội dung tệp | Thực tế/đầu ra |
|---|---|---|
| `requirements-analysis` | Có Objective/Outputs; thiếu Inputs, quy trình đầy đủ, kiểm chứng và xử lý issue | Thiếu requirements, user stories, acceptance, system model/traceability và Human Gate |
| `diagram-design` | Có loại sơ đồ/quy tắc hình thức; thiếu đủ quy trình độc lập rồi đối chiếu nguồn | Chưa có .puml/PNG mới, comparison và bằng chứng chốt mô hình trước khi vẽ |
| `table-design` | Chỉ Objective/loại bảng; chưa có mẫu cột, nguồn, thao tác và verification | Chưa có bộ bảng actor/UC/class/data dictionary/traceability theo mẫu |
| `architecture-design` | Có Objective/Outputs; thiếu đầu vào được duyệt, process, quy tắc/verification | Mã có phân lớp nhưng thiếu architecture, decisions và bộ sequence/activity 13 UC |
| `database-design` | Có Objective/Outputs; chưa đủ quy trình thiết kế và kiểm tra toàn vẹn | Có schema.sql, migrations và SQLite/MySQL tests; thiếu thiết kế DB/ERD/data dictionary truy vết |
| `implementation` | Process chỉ một dòng; chưa đủ quy tắc chi tiết, inputs/outputs/verification | Có triển khai rộng; lượt này sửa 8 tệp nguồn, lint/test/diff; không chứng minh được thứ tự SDLC trước đây |
| `testing` | Process chỉ một dòng; thiếu kịch bản chi tiết/đầu ra mẫu/quy tắc kết luận | Có 221 tests, 44 nhóm browser và JSON/CSV; thiếu bộ test-plan/test-report/traceability theo hướng dẫn |
| `code-review` | Checklist một dòng; thiếu cách kiểm tra, severity, đầu ra và điều kiện kết thúc | Lượt này có review/diff và báo cáo thực tế; chưa có code-review.md hoặc minh chứng review các pha cũ |
| `security-review` | Checklist một dòng; thiếu thủ tục, minh chứng, xử lý lỗi và verification | Có test auth/scope/XSS/upload/key; chưa đủ hồ sơ HTTPS, CSRF/dependency audit và security-review.md |
| `ai-request-analysis` | Chỉ danh sách task và quyền; thiếu schema/inputs/process/outputs/verification | Module thật kiểm task/session/role/tham số; thiếu tài liệu request-analysis và traceability |
| `project-data-retrieval` | Hai quy tắc; thiếu whitelist dữ liệu/filter/source-ref/đầu ra kiểm chứng | Module thật có SQL tham số hóa và scope; Skill chưa mô tả đủ để lặp lại quy trình |
| `context-builder` | Hai quy tắc; thiếu cấu trúc context, nguồn, giới hạn và kiểm tra thiếu/mâu thuẫn | Có context_builder/source_refs nhưng thiếu tài liệu ngữ cảnh theo hướng dẫn |
| `project-ai-prompt` | Một chuỗi bước + draft-only; thiếu template/phiên bản/đánh giá/verification | Có prompt_builder, grounding và test lỗi; v1.0 cố định, chưa có so sánh các phiên bản prompt |
| `documentation` | Chỉ danh sách outputs; thiếu quy trình đối chiếu implementation và verification | Có README và nhiều hướng dẫn/báo cáo sửa lỗi; thiếu api/deployment/user-guide theo bộ yêu cầu |

## Minh chứng và giới hạn

221 ca SQLite và 44 nhóm kiểm tra trình duyệt đều đạt sau sửa; 7 quan sát audit là các lệch còn tồn tại, được ghi riêng, không đổi nhãn thành test thành công của yêu cầu còn thiếu. Các ca mới dùng dữ liệu giả lập, DB tạm được dọn sau chạy. Không viết vào dữ liệu MySQL đang dùng, không gọi API/email thật trong lượt này.

Minh chứng MySQL cũ trong `docs/qa-system-checks.json`: 10.000 nhiệm vụ, tìm kiếm 0.0823s, dashboard 0.1049s, workload 0.1971s; sao lưu/khôi phục 16 bảng cùng checksum. Đây là quan sát trước đó, không thay kiểm thử bản hiện tại. Minh chứng gọi Gemini thật đã có trong báo cáo chuyển Gemini trước, cũng không được tính là chạy lại hôm nay.

Rà bảo mật ở lượt này: quyền backend/ngoài dự án/phiên khóa, SQL tham số hóa, XSS qua escape, tệp upload theo loại/dung lượng/chữ ký/đường dẫn, secrets backend, thao tác hủy không ghi dữ liệu và xung đột phiên bản. Chưa làm pentest đầy đủ, kiểm dependency/CVE, thử tấn công CSRF chuyên biệt hoặc nghiệm thu HTTPS. Không suy diễn có lỗ hổng khai thác được chỉ từ việc thiếu hồ sơ.

## Thứ tự hoàn thiện đề nghị

1. Sửa nối lịch nhắc sắp hạn và thống nhất người nhận FR-16; bổ sung phiên bản prompt thật/hiển thị lịch sử. Chốt quy ước hạn/ước lượng/tiêu chí sprint và chính sách danh tính khi xóa tài khoản.
2. Bổ sung hồ sơ yêu cầu → mô hình/traceability → kiến trúc/ERD/bảng dữ liệu → ca thử/kết quả → review/security, dựa trên mã đang chạy. Rà 14 Skill đầy đủ đầu vào/quy trình/đầu ra/kiểm chứng; lưu prompt/kết quả/diff/commit của việc làm mới.
3. Nhóm thực hiện Human Gate thật, cập nhật mâu thuẫn và phê duyệt có người/ngày/phạm vi. Không viết lại lịch sử như đã duyệt từ trước.
4. Hoàn tất SMTP thật, HTTPS, backup định kỳ, phục hồi và đo lại hiệu năng/AI timeout trước demo/triển khai chính thức.

Lượt này đã sửa các lỗi giao diện bạn nêu và lỗi khởi tạo nút AI, sau đó kiểm thử lại. Các sai lệch nghiệp vụ/quy trình rộng hơn được báo cáo để nhóm biết chính xác việc còn thiếu; chưa tự thay chính sách dữ liệu, gửi thư thật hoặc tạo phê duyệt lịch sử.

## Tệp kèm theo

- [Ma_tran_50_yeu_cau_28-10-2026.csv](Ma_tran_50_yeu_cau_28-10-2026.csv): từng FR/NFR/BR/UC, trạng thái và giới hạn.
- [Doi_chieu_14_Skill_28-10-2026.csv](Doi_chieu_14_Skill_28-10-2026.csv): 14 Skill, thiếu trong tệp và đầu ra hiện có.
- `Du_lieu_doi_chieu_28-10-2026.json`: nguồn/SHA256 và danh sách kiểm tra các artifact yêu cầu.
- `Minh_chung_kiem_tra_28-10-2026.zip`: báo cáo, JSON kết quả, 7 quan sát và ảnh QA.

Dấu vết nguồn (SHA256, để nhận đúng phiên bản đã kiểm):

- `Detai33.docx` — 1467 đoạn, 45 bảng; SHA256 `fb7160c3b84f2c9c22a20a17e427d324bda0218d2de9f8536fd14f66103bc506`.
- `thuc_hanh.docx` — 1605 đoạn, 2 bảng; SHA256 `54676f47b0b0d25454dbbbe3bd7ac8657c27c6bc6ec1f800e29a6e2a68cc087f`.
