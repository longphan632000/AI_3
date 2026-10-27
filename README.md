# Hệ thống Quản lý Dự án Nhóm Tích hợp AI (Đề tài 33)
> **Quy trình AI-Augmented SDLC với Codex**  
> **Nhóm 33** | **Môn học:** Phân tích Thiết kế Hệ thống | **Giảng viên hướng dẫn:** ThS. Nguyễn Đình Dũng  
> **Thành viên:** Phan Chân Long (Trưởng nhóm), Lưu Trà My, Lê Nam Khánh

---

## 1. Giới thiệu Dự án
Hệ thống Quản lý Dự án Nhóm Tích hợp AI là nền tảng quản trị công việc nhóm linh hoạt, hỗ trợ Kanban 5 trạng thái, quản lý Sprint, phân bổ tải công việc thành viên và tích hợp 3 chức năng Trợ lý AI.

Yêu cầu nghiệp vụ được đối chiếu với `Detai33.docx`: 9 quy tắc **BR-01 đến BR-09**, 17 yêu cầu chức năng **FR-01 đến FR-17** và 11 yêu cầu phi chức năng **NFR-01 đến NFR-11**. FR-01–14 là bắt buộc; FR-15–17 là phần nên có. Kết quả và giới hạn kiểm thử được ghi tại [báo cáo sửa lỗi](docs/BAO_CAO_SUA_LOI_VA_KET_QUA.md), không suy rộng tỷ lệ test đạt thành việc đã nghiệm thu mọi yêu cầu.

---

## 2. Thông số Cơ sở Dữ liệu MySQL
- **Tên Database đề xuất:** `ai_project_management`
- **Bộ mã ký tự (Charset / Collation):** `utf8mb4` / `utf8mb4_unicode_ci`
- **File Schema:** `database/schema.sql` gồm 16 bảng; có các bảng phân công nhiều người, lịch sử chỉnh draft và trạng thái gửi email. Migration trong `database/migrations.py` dùng để nâng cấp cấu trúc cũ và bảo toàn dữ liệu.
- **Dữ liệu mẫu:** `database/seed_data.sql` (Có sẵn tài khoản kiểm thử, dự án mẫu, sprint mẫu, nhiệm vụ trễ hạn, ghi chú cuộc họp).

### Cấu hình biến môi trường (`.env`):
```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=mật_khẩu_mysql_của_bạn
DB_NAME=ai_project_management

SECRET_KEY=

# Cấu hình Gemini AI
GEMINI_API_KEY=khoa_api_gemini_cua_ban
AI_PROVIDER=gemini
AI_CONFIG_SOURCE=env_file
GEMINI_MODEL=gemini-3.8-flash
GEMINI_MEETING_MODEL=gemini-3.8-flash
AI_TIMEOUT_SECONDS=30
AI_MEETING_TIMEOUT_SECONDS=90
AI_TOTAL_TIMEOUT_SECONDS=30
```

Với `AI_CONFIG_SOURCE=env_file`, cấu hình AI được đọc từ `.env` cho mỗi yêu cầu mới;
khóa để trống không dùng lại khóa cũ trong tiến trình. Tất cả ba chức năng AI dùng
`gemini-3.8-flash` theo cấu hình trên. Không bật tùy chọn này thì biến môi trường
tiến trình khác rỗng được ưu tiên. Quản trị viên có thể
xem trạng thái AI tại `/admin` và bấm **Kiểm tra API** để xác nhận khóa và mô hình
có truy cập được Gemini hay không; giao diện không hiển thị khóa.
`AI_MEETING_TIMEOUT_SECONDS` là giới hạn cho mỗi lượt xử lý biên bản Word;
`GEMINI_MEETING_MODEL` chọn mô hình riêng cho biên bản Word (mặc định là
`GEMINI_MODEL`); các tác vụ AI còn lại dùng `GEMINI_MODEL`.
Ứng dụng thử lại tối đa ba lần với lỗi mạng, hết thời gian hoặc Gemini tạm thời quá tải.
Toàn bộ retry và các phần của một yêu cầu dùng chung ngân sách
`AI_TOTAL_TIMEOUT_SECONDS` (mặc định 30 giây); thời gian mỗi lượt không vượt ngân sách còn lại.
Nếu một phần thất bại, API báo rõ loại lỗi và số thứ tự phần, đồng thời không lưu bản
nháp chưa hoàn chỉnh. Log chỉ ghi mã lỗi và kích thước phần, không ghi nội dung họp
hoặc khóa API.

> **Lưu trữ:** Ứng dụng sử dụng MySQL cho mọi thao tác đọc và ghi. Nếu MySQL không khả dụng, thao tác trả lỗi thay vì chuyển sang SQLite. Bộ kiểm thử riêng dùng SQLite tạm để không ảnh hưởng dữ liệu thật.

---

## 3. Danh sách Tài khoản Kiểm thử Mặc định
Tất cả tài khoản mẫu có mật khẩu mặc định là: **`Password123!`**

| Tên đăng nhập | Vai trò hệ thống | Quyền hạn & Mục đích kiểm thử |
| :--- | :--- | :--- |
| `admin` | **Quản trị viên** | Quản lý tài khoản (khóa/mở khóa FR-02), xem Audit Logs, xem Lịch sử AI toàn hệ thống (UC012). |
| `leader_long` | **Trưởng nhóm** | Tạo & quản lý dự án, Sprint, phân công nhiệm vụ, **độc quyền** gọi AI tóm tắt tuần (FR-12), gọi AI gợi ý phân công (FR-14), **độc quyền** xác nhận bản chính thức (UC010). |
| `member_my` | **Thành viên** | Xem nhiệm vụ, kéo thả Kanban nhiệm vụ phụ trách, bình luận, đính kèm, tạo/sửa bản nháp biên bản họp (FR-13), *bị từ chối khi cố xác nhận bản chính thức*. |
| `member_khanh` | **Thành viên** | Cập nhật tiến độ, tham gia trao đổi công việc trong dự án. |
| `locked_user` | **Bị khóa** | Kiểm thử **FR-01**: Hệ thống từ chối đăng nhập với thông báo tài khoản bị khóa an toàn. |

---

## 4. Hướng dẫn Cài đặt & Khởi chạy

### Bước 1: Kích hoạt môi trường và cài đặt thư viện
```bash
pip install -r requirements.txt
```

### Bước 2: Khởi tạo Cơ sở Dữ liệu
Điền cấu hình MySQL vào `.env`. Chỉ khi cơ sở dữ liệu chưa được tạo, chạy:
```bash
python database/init_db.py
```
Lệnh này giữ nguyên dữ liệu mẫu và dữ liệu người dùng nếu MySQL đã có tài khoản. Ứng dụng sẽ báo lỗi khi MySQL không kết nối được và không ghi sang SQLite.

### Bước 3: Khởi chạy Ứng dụng Flask
```bash
python app.py
```
Mở trình duyệt tại địa chỉ: **`http://127.0.0.1:5000`**

### Bước 4: Chạy Bộ Kiểm thử Tự động (Unit & Integration Tests)
```bash
python -B tests/run_isolated.py
python -B tests/run_mysql_isolated.py
python -B tests/export_test_cases.py
```
Hai runner thực thi cùng bộ 145 ca trên SQLite tạm và MySQL cách ly. Runner MySQL
tạo database `qa_repair_...`, kiểm tra migration, hiệu năng và khôi phục rồi xóa đúng
database kiểm thử đã tạo. Bảng 67 kịch bản chi tiết nằm tại
[TEST_CASES_SAU_CHINH_SUA.md](docs/TEST_CASES_SAU_CHINH_SUA.md), cùng bản CSV và HTML để sao chép sang Word.

### Duyệt tài khoản Trưởng nhóm

Tài khoản tự đăng ký chọn `leader` hoặc `member` đều được tạo ở trạng thái `pending` và chưa thể đăng nhập. Quản trị viên vào `/admin` để duyệt, từ chối hoặc mở lại yêu cầu; trang này cũng quản lý tài khoản và Trưởng nhóm trong từng dự án. Sau khi được duyệt, Trưởng nhóm có thể tự tạo dự án bằng nút `+ Tạo dự án`, hoặc Quản trị viên gán họ vào dự án hiện có. Trưởng nhóm dùng nút `+ Thêm thành viên` để đưa tài khoản đang hoạt động vào dự án trước khi phân công. Chỉ Trưởng nhóm của dự án đang chọn mới được tạo sprint hoặc nhiệm vụ.

Khi khởi động, ứng dụng tự mở rộng cột `users.status` và các cột AI của MySQL cũ để hỗ trợ xét duyệt, biên bản dài và trạng thái cần kiểm tra. Bộ kiểm thử `tests/run_isolated.py` dùng SQLite tạm và không ghi vào cơ sở dữ liệu ứng dụng.

### Cảnh báo hạn và cấu hình vận hành

`python app.py` chạy worker cảnh báo khi `DEADLINE_WORKER_ENABLED=true`.
Nếu chạy bằng WSGI, dùng một tiến trình riêng `python -m services.deadline_worker`.
Mặc định quét mỗi 60 giây, nhắc lại sau 24 giờ và retry lỗi sau 300 giây.
`SMTP_ENABLED=false` chỉ mô phỏng; cần cấu hình SMTP và bật cờ này để gửi thật.
Khi triển khai, thay SECRET_KEY mẫu bằng khóa ngẫu nhiên riêng, giữ ổn định giữa
các tiến trình; chỉ bật SESSION_COOKIE_SECURE khi phục vụ qua HTTPS.

### Chạy trong mạng nội bộ và kiểm thử giao diện

Đặt `HOST=0.0.0.0` trong `.env`, chạy một máy chủ rồi dùng
`http://<IPv4-máy-chủ>:5000` trên các máy cùng mạng. Mọi máy khách dùng chung
MySQL qua API của máy chủ; không chạy một database riêng trên từng máy khách.
Các trang kiểm tra thay đổi mỗi 5 giây và khi quay lại cửa sổ. Biểu mẫu đang nhập
hoặc AI đang xử lý được giữ nguyên; có thông báo yêu cầu cập nhật sau khi lưu/đóng.

Form tạo dự án cho chọn nhân viên đã được Admin duyệt ngay từ đầu. Nút
`Thêm thành viên` dùng cho bổ sung sau này. Mọi tài khoản tự đăng ký, gồm member
và leader, đều chờ Admin duyệt; tài khoản Admin tạo trực tiếp đã được Admin cho phép.

```powershell
pip install -r requirements-dev.txt
python -B tests/browser_smoke.py
```

Bộ kiểm thử giao diện dùng Microsoft Edge headless đã cài trên máy, database tạm,
Gemini HTTP giả lập; không cần API key thật. Xem hướng dẫn chi tiết tại
[HUONG_DAN_CHAY_LAN_VA_GEMINI.md](docs/HUONG_DAN_CHAY_LAN_VA_GEMINI.md).

---

## 5. Quy trình 5 Bước Trợ lý AI An Toàn (Safe AI Pipeline)
Hệ thống tuân thủ nghiêm ngặt nguyên tắc **AI chỉ là công cụ hỗ trợ - Con người quyết định cuối cùng**:
1. **Kiểm tra quyền RBAC & Intermediate Representation:** Phân tách quyền riêng cho từng chức năng (D06). `requester_id` lấy từ session ở backend.
2. **Truy xuất dữ liệu có tham số (Parameterized SQL):** Chỉ truy vấn đúng phạm vi dự án, không rò rỉ dữ liệu hoặc secret.
3. **Đóng gói Context sạch (Context Builder):** Không bịa đặt số liệu ngoài CSDL.
4. **Prompt Builder (Grounding Rules tiếng Việt):** Ép buộc AI chỉ tạo bản nháp (`Draft / Suggestion`), trích dẫn rõ ID `[Task #ID]`, `[User #ID]`.
5. **Response Validator & Confirmation Service:** Kiểm định ID tham chiếu chống ảo giác (hallucination). Bản nháp chỉ trở thành chính thức khi Trưởng nhóm chủ động click xác nhận.

### Biên bản họp từ tệp

Tệp `.docx`, `.pdf`, `.txt`, `.md` được trích xuất tối đa 5 MB và 120.000 ký tự văn bản. PDF cần có lớp chữ; bản quét cần OCR trước khi tải lên. Với Word, hệ thống giữ thứ tự đoạn văn và bảng. Các quyết định trong mục ghi rõ và các dòng công việc có người phụ trách, hạn hoàn thành trong bảng được giữ trực tiếp từ nguồn. AI phân loại các đoạn còn lại; đoạn bị bỏ sót được thử lại riêng. Mỗi đoạn nguồn đều có vị trí tham chiếu trong bản nháp. Nếu vẫn còn đoạn chưa phân loại hoặc thông tin không đối chiếu được, bản nháp cần kiểm tra trước khi xác nhận. Quyết định và việc cần làm khi xác nhận được lưu từ nội dung nguồn vào MySQL.

Nếu thiếu khóa Gemini, mô hình không khả dụng hoặc dịch vụ quá tải, API trả lỗi rõ ràng và không tạo biên bản mẫu. `GEMINI_MODEL` có thể đổi sang mô hình được tài khoản cho phép; mặc định là `gemini-3.8-flash`.
