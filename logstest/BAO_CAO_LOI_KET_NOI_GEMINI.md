# Sửa lỗi kết nối Gemini và kiểm thử dịch vụ thật

Ngày: 27/10/2026. Phạm vi: kế hoạch chẩn đoán, chạy ngoài sandbox, phân loại lỗi và
kiểm thử ba chức năng AI đã được người dùng duyệt. API key và .env hiện có được giữ nguyên.

## Nguyên nhân và kết quả sau sửa

Tiến trình Flask trước đây được khởi chạy trong sandbox hạn chế kết nối ra ngoài.
Gọi HTTPS trong môi trường đó gặp PermissionError, WinError 10013. Mã cũ thử lại
ba lần rồi hiển thị AI_CONNECTION chung chung. Cùng key và model được Google chấp nhận
ở bước đọc metadata khi chạy ngoài sandbox.

Đã dừng đúng tiến trình cũ và chạy lại máy chủ ngoài sandbox. Kiểm tra qua API của
chính ứng dụng trả configured=true, api_reachable=true, error_code=null, cả hai model
là gemini-3.8-flash. Máy chủ đang lắng nghe tại 0.0.0.0:5000; địa chỉ LAN lúc kiểm tra
là http://192.168.1.39:5000. SMTP thật và worker nền vẫn tắt trong tiến trình local kiểm thử.

Đọc được metadata không chứng minh generateContent hoặc quota đang hoạt động.
Kiểm thử sinh nội dung thật gặp vấn đề dịch vụ được ghi riêng bên dưới.

## Thay đổi mã nguồn

| Phạm vi | Thay đổi |
| --- | --- |
| services/gemini_service.py | Phân biệt AI_NETWORK_DENIED, AI_DNS, AI_TLS_CERTIFICATE, AI_TLS_ERROR, AI_TIMEOUT và AI_CONNECTION; xử lý lỗi HTTP key/model/quota/dịch vụ riêng. |
| Chính sách retry | Không retry lỗi quyền kết nối, chứng chỉ/TLS hoặc DNS không tồn tại. DNS tạm thời, kết nối gián đoạn, timeout, HTTP 429/5xx vẫn có retry giới hạn trong ngân sách hiện có. |
| Bảo vệ thông tin | Log chỉ ghi mã lỗi, loại exception và mã OS/HTTP; không ghi exception text, API key hoặc nội dung prompt. Giữ xác minh TLS. |
| Chẩn đoán Admin | Trả error_code và diagnostics an toàn theo model; hai chức năng dùng cùng model chỉ probe một lần. Nêu rõ probe chỉ đọc metadata. |
| Giao diện Admin | Hiển thị nguyên nhân cụ thể; không suy rộng metadata thành tạo nội dung hoặc quota thành công. |
| Kiểm thử | Bổ sung lỗi WinError 10013 trực tiếp/bọc trong URLError, TLS, DNS, HTTP 400/401/403/404/429/503, no-retry và không tạo draft dở dang. |

## Kết quả kiểm thử

| Nhóm | Thực tế | Kết quả |
| --- | --- | --- |
| Hồi quy SQLite cách ly | 145/145 ca | Thành công |
| Hồi quy MySQL cách ly | 145/145 ca | Thành công |
| Bảng nghiệm thu API/service | 67/67 kịch bản chi tiết, AI giả lập | Thành công |
| Microsoft Edge headless | 23/23 nhóm, gồm hiển thị AI_NETWORK_DENIED rồi phục hồi trạng thái metadata | Thành công |
| Kết nối từ máy chủ Flask mới | api_reachable=true; metadata Gemini truy cập được | Thành công |
| Tóm tắt tuần bằng Gemini thật | HTTP 503 từ ứng dụng, AI_TIMEOUT sau 30,203 giây; không lưu draft | Thất bại |
| Biên bản bằng Gemini thật | HTTP 503 từ ứng dụng, AI_TIMEOUT sau 30,109 giây; không lưu draft | Thất bại |
| Gợi ý phân công bằng Gemini thật | HTTP 503 từ ứng dụng, AI_TIMEOUT sau 30,157 giây; không lưu draft | Thất bại |

Các ca thật dùng database SQLite tạm, tên QA và dữ liệu tổng hợp; không đọc dự án MySQL
đang dùng để gửi tới Google. Nhiệm vụ kiểm thử vẫn chưa được phân công; không có biên bản
chính thức hoặc draft được xác nhận tự động. Ngân sách 30 giây theo NFR-01 được giữ nguyên.

## Phân tích lỗi dịch vụ còn lại

Ngoài ba ca pipeline, yêu cầu rất ngắn `Reply only OK.` gọi trực tiếp endpoint
generateContent cũng gặp timeout hoặc HTTP 503. Một phản hồi Google trả status UNAVAILABLE
với thông báo model đang có nhu cầu cao và yêu cầu thử lại sau. Phép đối chiếu bằng curl
của Windows timeout sau 20 giây, không nhận byte phản hồi.

Đây là bằng chứng lỗi tạo nội dung hiện còn phụ thuộc endpoint/dịch vụ, sau khi đã xử lý
quyền truy cập mạng của tiến trình. Không có bằng chứng hiện tại cho thấy cần đổi API key
hoặc sửa dữ liệu dự án. Không chuyển sang model khác và không tạo kết quả giả khi dịch vụ lỗi.
Theo [hướng dẫn Google](https://ai.google.dev/gemini-api/docs/troubleshooting), lỗi 503 là
trường hợp retry với backoff; ứng dụng đã có retry giới hạn. Nếu dịch vụ không hồi phục
trong ngân sách yêu cầu, hệ thống trả lỗi rõ và giữ nguyên dữ liệu.

## Tệp bằng chứng và chạy lại

- qa-results-sqlite.json, qa-results-mysql.json: toàn bộ 145 ca trên từng engine.
- qa-browser-results.json: 23 nhóm kiểm tra giao diện/luồng.
- qa-gemini-live-results.json: ba ca thật với thời gian, mã lỗi và kiểm tra không tự xác nhận.
- TEST_CASES_SAU_CHINH_SUA.md/.csv/.html: bảng 67 kịch bản API/service; phần Markdown có phụ lục trình duyệt và Gemini thật.

```powershell
python -B tests/run_isolated.py
python -B tests/run_mysql_isolated.py
python -B tests/browser_smoke.py
python -B tests/export_test_cases.py
```

Chạy riêng ca thật khi dịch vụ ổn định và đã được phép dùng API key (có thể tính token):

```powershell
python -B tests/run_gemini_live.py
```

Lệnh thật phải chạy từ PowerShell thông thường hoặc môi trường được cấp kết nối Internet,
ngoài sandbox chặn mạng. Không chạy script này như một phần mặc định của hồi quy tự động.
Để khởi chạy ứng dụng local, dùng `python -B app.py` trong môi trường tương tự.
