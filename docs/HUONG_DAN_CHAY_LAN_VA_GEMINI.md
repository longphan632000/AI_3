# Chạy trên mạng nội bộ và sử dụng Gemini

## Máy chủ và máy khách

Chỉ máy chủ chạy Flask và kết nối MySQL. Laptop, điện thoại, máy tính bảng mở cùng
địa chỉ của máy chủ bằng trình duyệt. Không dùng `127.0.0.1` trên máy khách: địa chỉ
này trỏ tới chính máy khách.

Trong `.env` của máy chủ:

```env
HOST=0.0.0.0
PORT=5000
FLASK_DEBUG=false
SESSION_COOKIE_SECURE=false
```

Chạy `python -B app.py`. Dùng `ipconfig` để xem địa chỉ IPv4 của adapter Wi-Fi/Ethernet,
rồi truy cập `http://<IPv4>:5000` trên máy khách. Khi Windows Firewall chặn, cấu hình
cho phép TCP cổng 5000 trên mạng riêng của máy chủ. Router cũng cần cho phép các
thiết bị giao tiếp; một số Wi-Fi khách bật chế độ cô lập thiết bị.

HTTP local không cần secure cookie. Khi triển khai HTTPS, bật SESSION_COOKIE_SECURE.
Không dùng Flask development server làm máy chủ triển khai công khai.

## Cấu hình Gemini cho cả ba chức năng

```env
AI_CONFIG_SOURCE=env_file
AI_PROVIDER=gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.8-flash
GEMINI_MEETING_MODEL=gemini-3.8-flash
AI_TIMEOUT_SECONDS=60
AI_MEETING_TIMEOUT_SECONDS=120
AI_TOTAL_TIMEOUT_SECONDS=30
```

Nhập khóa Gemini sau dấu `=` ở GEMINI_API_KEY và lưu tệp trên máy chủ. Không gửi khóa
cho máy khách. Các yêu cầu AI mới đọc cấu hình từ file khi AI_CONFIG_SOURCE=env_file;
giá trị rỗng không khôi phục khóa cũ trong môi trường tiến trình. Sau khi cập nhật mã,
khởi động lại máy chủ một lần. Admin có thể bấm `Kiểm tra API` để xác minh quyền
truy cập model; thao tác đó gọi dịch vụ Google thật.

Máy chủ cần được chạy trong môi trường cho phép kết nối Internet. Nếu Codex chạy
Flask trong sandbox chặn mạng, hãy dừng tiến trình đó rồi chạy `python -B app.py`
trong PowerShell thông thường, hoặc cấp quyền chạy ngoài sandbox cho tiến trình máy chủ.
AI_NETWORK_DENIED/WinError 10013 là lỗi quyền kết nối; việc thay key không giải quyết
được quyền mạng của tiến trình. Không cần chạy bằng Administrator chỉ để gọi Gemini.

`Kiểm tra API` chỉ đọc metadata model: trạng thái thành công chưa chứng minh quota
hoặc tạo nội dung thành công. Các lỗi DNS, TLS, timeout, key/model và dịch vụ 503
được báo riêng; không bỏ xác minh TLS để vượt lỗi chứng chỉ.

Timeout từng lượt là giới hạn trên. Toàn bộ retry và các phần của biên bản vẫn dùng
chung ngân sách 30 giây theo NFR-01. Tệp quá dài hoặc dịch vụ chậm có thể trả lỗi rõ
ràng; nội dung nguồn trong giao diện được giữ để người dùng chia nhỏ và thử lại.

Model được đối chiếu theo [tài liệu Google](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash).
Quyền/hạn mức thực tế phụ thuộc tài khoản và API key; kiểm thử giả lập không xác minh
được hạn mức hoặc kết nối thật.

## Nhân viên, dự án và duyệt đăng ký

1. Member hoặc PM đăng ký và chờ Admin duyệt. Chưa duyệt thì chưa đăng nhập được.
2. Admin thấy cả hai loại tài khoản tại `Tài khoản đăng ký chờ duyệt` và chọn duyệt/từ chối.
3. PM bấm `Tạo dự án`, nhập thông tin và tìm/chọn nhân viên tham gia từ đầu. Chỉ tài khoản
   hoạt động đã được duyệt xuất hiện. Nhân viên được tạo membership cùng transaction với dự án.
4. Sau này dùng `Thêm thành viên` để bổ sung; xem đội ngũ để cập nhật kỹ năng/năng lực
   hoặc loại thành viên theo quyền. Xóa membership giữ lịch sử.
5. Trên điện thoại có nút menu điều hướng. Có thể đổi trạng thái nhiệm vụ bằng biểu mẫu
   trong chi tiết nhiệm vụ, ngoài cách kéo thả.

## Đồng bộ dữ liệu

Mọi vai trò dùng cùng dữ liệu trên máy chủ và được kiểm tra quyền ở backend. Các trang
kiểm tra token thay đổi mỗi 5 giây khi đang hiển thị, đồng thời kiểm tra khi quay lại cửa sổ
hoặc kết nối lại mạng. Nội dung bảng được tải lại sau thay đổi; dữ liệu đang nhập hoặc AI
đang xử lý được giữ nguyên và có thông báo cập nhật. Người bị khóa bị thu hồi phiên ở
yêu cầu kế tiếp. API dùng Cache-Control: no-store; CSS/JS có phiên bản theo tệp.

Đồng bộ này cần kết nối máy chủ; không cung cấp chế độ chỉnh sửa offline. Địa chỉ local
và địa chỉ LAN có bộ cookie/localStorage riêng nên cần đăng nhập riêng trên mỗi địa chỉ.

## Kiểm thử lại

```powershell
python -B tests/run_isolated.py
python -B tests/run_mysql_isolated.py
python -B tests/export_test_cases.py
pip install -r requirements-dev.txt
python -B tests/browser_smoke.py
```

Runner API và trình duyệt dùng dữ liệu cách ly. Runner MySQL tạo rồi xóa đúng database
`qa_repair_...` của nó. Kiểm thử Edge kiểm tra bốn độ rộng 1366, 768, 390, 320px; đây là
trình duyệt desktop với viewport mô phỏng, không thay thế nghiệm thu Safari/iOS/Android
trên thiết bị vật lý.
