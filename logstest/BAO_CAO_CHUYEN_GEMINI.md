# Báo cáo chuyển API chính từ DeepSeek sang Gemini

Ngày: 28/10/2026. Thư mục đã chỉnh: `D:\UNG DUNG AL_NAM3\Code Chuan`.

## Kết quả

Đã chuyển cấu hình và bộ điều phối sang **Gemini API**, dùng **gemini-3.6-flash** cho cả ba chức năng.
Khóa Gemini người dùng vừa lưu đã được Google chấp nhận và tạo phản hồi thử thành công.
Trong lượt chạy thật cuối cùng, cả ba chức năng dùng trực tiếp Gemini, không cần AI cục bộ dự phòng.

Luồng hiện tại: **Gemini API → Qwen3 tại máy nếu Gemini lỗi → bộ xử lý nghiệp vụ cục bộ nếu cần**.
Mỗi yêu cầu mới ưu tiên Gemini. DeepSeek chỉ được dùng khi chủ động chọn lại provider đó;
ứng dụng không tự lấy khóa DeepSeek để gọi Google và không tự gọi DeepSeek trong cấu hình Gemini.

## Các thay đổi đã thực hiện

- Đặt `AI_PROVIDER=gemini`, `GEMINI_MODEL=gemini-3.6-flash`, `GEMINI_MEETING_MODEL=gemini-3.6-flash`.
  Khóa được đọc từ `GEMINI_API_KEY` ở phía máy chủ. Cấu hình cũ ngoài bốn mục này được bảo toàn.
- Bộ điều phối hỗ trợ Gemini làm API chính; giữ cơ chế AI cục bộ dự phòng đã có.
- Trang Quản trị hiển thị đúng Gemini. Nút kiểm tra API thực sự gọi tạo nội dung,
  không chỉ xác nhận có tên model hoặc đọc metadata.
- Cập nhật adapter Google: xác thực qua header, giới hạn kích thước phản hồi,
  kiểm tra tên model, xử lý lỗi khóa/quota/mạng/TLS/timeout, nội dung bị chặn và phản hồi bị cắt.
- Dùng mức suy luận `low` tương thích với model. Biên bản có JSON schema giới hạn số mục,
  kiểu dữ liệu, loại nội dung và các ID được phép từ nguồn.
- Sửa lỗi kiểm định nhầm số thứ tự tiêu đề và mã FR-12 thành số liệu dự án.
  Các số liệu sai, phần trăm sai và ID ngoài nguồn vẫn bị phát hiện.
- Ngữ cảnh nhiệm vụ chưa phân công không còn tạo trích dẫn giả `[User #None]`.
- Cập nhật cấu hình mẫu, README, hướng dẫn vận hành, kiểm thử giao diện và runner chạy thật.
  Runner AI cục bộ cũng sử dụng provider đang được chọn khi yêu cầu thử API chính.

## Những lỗi đã gặp và cách xử lý

1. Tham số `minimal` bị Gemini 3.8 Flash từ chối với HTTP 400: đã sửa thành `low`.
2. Gemini 3.8 Flash tiếp tục trả HTTP 503 hoặc timeout trong kiểm thử thật: đã kiểm tra
   danh sách model Google cấp cho khóa này và chọn Gemini 3.6 Flash sau khi model đó tạo phản hồi thành công.
3. Kết quả tóm tắt có số thứ tự tiêu đề và FR-12 bị bộ kiểm định cũ đánh nhầm là số liệu không có nguồn:
   đã phân biệt phần cấu trúc văn bản với số liệu thực, có kiểm thử giữ nguyên khả năng chặn số liệu bịa.
4. Đầu ra biên bản có thể thiếu ID hoặc sai cấu trúc: đã bổ sung JSON schema và giữ kiểm tra nguồn ở backend.

## Kết quả kiểm thử

Tất cả kiểm thử dùng cơ sở dữ liệu **SQLite tạm**. Không chạy bộ kiểm thử MySQL,
không ghi vào cơ sở dữ liệu người dùng. Cấu hình MySQL vận hành hiện có được giữ nguyên.

| Nhóm kiểm thử | Kết quả |
| --- | --- |
| Hồi quy chức năng và tích hợp trên SQLite | **212/212 đạt** |
| Kiểm tra giao diện Microsoft Edge, provider Gemini | **26/26 đạt**, không có lỗi JavaScript runtime ghi nhận |
| Kiểm tra khóa bằng tạo nội dung Gemini thật | **Đạt** |
| Ba chức năng gọi Gemini thật với dữ liệu giả lập | **3/3 đạt trực tiếp qua Gemini**, không dùng dự phòng |
| Kiểm tra cú pháp, import và tên biến của các tệp liên quan | Đạt |
| Kiểm tra cấu hình cũ được bảo toàn | Đạt |

Chi tiết lượt gọi API thật cuối cùng:

| Chức năng | HTTP | Nguồn kết quả | Trạng thái | Thời gian (giây) |
| --- | --- | --- | --- | --- |
| Tóm tắt tiến độ tuần | 200 | Gemini API | draft | 9.016 |
| Lập biên bản họp | 200 | Gemini API | draft | 1.937 |
| Gợi ý phân công | 200 | Gemini API | draft | 9.141 |

Lịch sử SQLite lưu `model_provider=gemini`; mỗi bản nháp lưu nguồn `gemini` và không có mã lỗi chuyển nguồn.
Nhiệm vụ kiểm thử vẫn chưa được tự phân công. Không có biên bản chính thức hoặc bản nháp nào tự xác nhận.
Thời gian trong bảng là số đo của dữ liệu mẫu nhỏ tại lượt thử này, không phải cam kết độ trễ mọi yêu cầu.

## Tệp chính đã chỉnh

- `services/ai_provider_service.py`: chọn Gemini và ghi đúng nguồn xử lý.
- `services/gemini_service.py`: kết nối Google, probe thật, xử lý lỗi và JSON schema.
- `services/ai_response_validator.py`, `services/context_builder.py`: sửa hai lỗi kiểm định/ngữ cảnh.
- `routes/admin_routes.py`, `templates/admin.html`: trạng thái nhà cung cấp và kiểm tra API.
- `.env`, `.env.example`, `README.md` và tài liệu hướng dẫn.
- `tests/test_gemini_migration.py`: 19 ca bổ sung bên cạnh bộ 193 ca trước đó.
- `tests/run_gemini_live.py`, `tests/run_local_brain_live.py`, `tests/browser_smoke.py` và các test tương thích.

## Sử dụng

Không cần nhập lại khóa Gemini. Nếu phần mềm đang chạy từ trước lúc chỉnh mã,
khởi động lại tiến trình máy chủ một lần để nạp mã mới. Chạy từ thư mục dự án như trước:

```powershell
python app.py
```

Sau đó vào Quản trị → Kiểm tra API để xem trạng thái Gemini. Cấu hình AI trong `.env`
được đọc lại cho yêu cầu mới khi `AI_CONFIG_SOURCE=env_file`.

Chạy lại kiểm thử bằng:

```powershell
python -B tests/run_isolated.py
python -B tests/browser_smoke.py
python -B tests/run_gemini_live.py
```

Lệnh cuối gọi Gemini thật bằng dữ liệu kiểm thử tổng hợp. Chế độ dự phòng cục bộ vẫn được
giữ để trợ lý tiếp tục tạo bản nháp nếu dịch vụ Google lỗi trong những lần dùng sau.

Tài liệu tham khảo: [Google Gemini API key](https://ai.google.dev/gemini-api/docs/generate-content/api-key),
[mức suy luận theo model](https://ai.google.dev/gemini-api/docs/generate-content/thinking),
[đầu ra có cấu trúc](https://ai.google.dev/gemini-api/docs/generate-content/structured-output).
