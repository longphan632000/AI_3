# Báo cáo tích hợp trợ lý AI có dự phòng cục bộ

Ngày: 28/10/2026. Thư mục đã sửa trực tiếp: `D:\UNG DUNG AL_NAM3\Code Chuan`.

## Kết quả

Đã tích hợp dự phòng vào cả ba chức năng trợ lý đang có trong phần mềm: tóm tắt tiến độ tuần,
lập biên bản cuộc họp và gợi ý phân công. DeepSeek API tiếp tục được ưu tiên; khi API lỗi,
ứng dụng tự xử lý tại máy. Mỗi yêu cầu mới thử API lại trước, không bị kẹt vĩnh viễn ở chế độ cục bộ.

Luồng hoạt động: **DeepSeek API → Qwen3-1.7B tại máy → bộ xử lý nghiệp vụ cục bộ → kiểm định → bản nháp và lịch sử**.
Riêng gợi ý phân công khi API lỗi dùng tính toán nghiệp vụ trực tiếp để giữ chính xác tải và thứ tự ứng viên.

## Bộ não nằm ở đâu

| Thành phần | Vị trí trong thư mục phần mềm |
| --- | --- |
| Xử lý nghiệp vụ, nguồn và kiểm định cục bộ | `services/local_brain_service.py` |
| Nạp/chạy mô hình CPU, kết nối nội bộ | `services/local_model_service.py` |
| Điều phối ưu tiên API và tự chuyển nguồn | `services/ai_provider_service.py` |
| Mô hình đã cài, khoảng 1,83 GB | `local_models/Qwen3-1.7B-Q8_0.gguf` |
| Runtime llama.cpp đã cài | `runtime/local_ai/` |
| Phiên bản, giấy phép, nguồn tải và SHA-256 | `runtime/local_ai/installation.json` |
| Cài lại mô hình trên máy Windows x64 khác | `scripts/setup_local_brain.py` |
| Kiểm thử bổ sung và kiểm thử mô hình thật | `tests/test_local_brain.py`, `tests/run_local_brain_live.py` |
| Hướng dẫn vận hành đầy đủ | `logstest/HUONG_DAN_BO_NAO_AI_CUC_BO.md` |

Các đường dẫn trên bắt đầu từ `D:\UNG DUNG AL_NAM3\Code Chuan`.
Các điểm nối đã chỉnh gồm xử lý yêu cầu, thời gian chờ, biên bản, truy xuất tải,
trạng thái quản trị, trang trợ lý, cấu hình mẫu, README và runner kiểm thử.

## Những thay đổi cụ thể

- Ưu tiên API hiện có, tự chuyển nguồn khi thiếu khóa, khóa bị từ chối, hết hạn mức,
  lỗi mạng/DNS/TLS, quá thời gian, dịch vụ lỗi hoặc nội dung không qua kiểm định.
- Dùng mô hình CPU thật đã tải và kiểm tra SHA-256. Mô hình chỉ lắng nghe trên
  `127.0.0.1:18081`, không cần API key khi xử lý tại máy.
- Khi mô hình chưa sẵn sàng, bận hoặc trả kết quả không hợp lệ, bộ xử lý nghiệp vụ
  vẫn hỗ trợ ba chức năng từ đúng dữ liệu được phép truy xuất.
- Tóm tắt có số liệu tính từ cơ sở dữ liệu, nhiệm vụ trễ, vướng mắc, ưu tiên và dữ liệu thiếu.
- Biên bản giữ nguyên văn và ID từng đoạn; đầu ra mô hình bị ràng buộc đủ ID bằng JSON schema.
  Không nhận ID không có trong nguồn. Người phụ trách và hạn không được tự suy đoán.
- Sửa cách tính tải dự kiến để không cộng hai lần nhiệm vụ đã giao cho chính ứng viên.
  Có xử lý ứng viên không sẵn sàng, quá tải, thiếu kỹ năng hoặc thiếu ước lượng.
- Các câu mang tính đề xuất, điều kiện, chưa phê duyệt hoặc chưa chốt được giữ ở dạng
  cần đối chiếu; không tự chuyển thành quyết định/phân công đã chốt, kể cả trong mục quyết định hoặc bảng.
- Hiển thị nguồn xử lý trên trang trợ lý; lưu nguồn và mã chuyển nguồn trong bản nháp,
  đồng thời ghi tên nguồn thực sự dùng trong lịch sử AI.
- Giữ kiểm tra quyền, phạm vi dự án và bước xác nhận của Trưởng nhóm. Gợi ý không tự
  thay đổi người được giao. Bản nháp, dữ liệu kiểm định và lịch sử được lưu trong một giao dịch.

## Kiểm thử đã hoàn tất

| Nhóm kiểm thử | Kết quả |
| --- | --- |
| Bộ kiểm thử ban đầu trước khi sửa | 159/159 đạt |
| Bộ kiểm thử sau tích hợp trên SQLite tạm | **193/193 đạt** |
| Kiểm tra giao diện bằng Microsoft Edge | **26/26 đạt**, không có lỗi JavaScript được ghi nhận |
| Kiểm thử mô hình cục bộ thật và API thật trên dữ liệu mẫu SQLite | **8/8 đạt** |
| Kiểm tra lỗi tên biến/import/cú pháp của các mô-đun liên quan | Đạt |
| Kiểm tra cấu hình hiện có được bảo toàn | Đạt; giá trị khóa API, cấu hình MySQL và các cấu hình cũ không đổi |

Có 34 ca kiểm thử mới bên cạnh 159 ca ban đầu, bao gồm quyền, lịch sử, xác nhận,
không tự phân công, xử lý thiếu dữ liệu, API phục hồi, các mã lỗi, HTTP 401/404/429/503,
mô hình hỏng/quá thời gian và biên bản dài 80 đoạn qua nhiều phần đồng thời.
Các ca kiểm thử thường giả lập lỗi có kiểm soát; các ca trong bảng dưới dùng mô hình/API thật.

### Kết quả chạy thật gần nhất

| Kịch bản | Kết quả | Thời gian (giây) | Nguồn tạo kết quả | Mã chuyển nguồn |
| --- | --- | --- | --- | --- |
| Nạp mô hình CPU thật và tạo phản hồi không cần khóa | Đạt | 8.25 | Qwen3-1.7B CPU thật | Không có |
| Tóm tắt tuần — xử lý cục bộ thật | Đạt | 4.94 | local_llm, local_rules | AI_KEY_MISSING |
| Biên bản họp — xử lý cục bộ thật | Đạt | 6.08 | local_llm | AI_KEY_MISSING |
| Gợi ý phân công — xử lý nghiệp vụ cục bộ | Đạt | 0.2 | local_rules | AI_KEY_MISSING |
| Tắt mô hình — bộ xử lý nghiệp vụ vẫn hoạt động | Đạt | — | local_rules | Không có |
| Tóm tắt tuần — thử API thật trước | Đạt | 42.78 | local_llm, local_rules | AI_TIMEOUT |
| Biên bản họp — thử API thật trước | Đạt | 3.3 | deepseek | Không có |
| Gợi ý phân công — thử API thật trước | Đạt | 34.33 | local_rules | AI_TIMEOUT |

Khóa DeepSeek hiện có đã xác thực và tạo phản hồi thử thành công. Trong lượt chạy thật gần nhất,
biên bản dùng trực tiếp DeepSeek; tóm tắt tuần và gợi ý phân công gặp API quá thời gian,
sau đó hoàn tất bằng đường dự phòng. Các tình huống đó được ghi đúng nguồn trong lịch sử,
không được tính thành API đã tạo nội dung thành công.

Thời gian trên áp dụng cho dữ liệu mẫu nhỏ trên máy này; không suy rộng cho mọi tài liệu.
Các bài kiểm thử dùng SQLite tạm và dữ liệu giả lập, không ghi vào cơ sở dữ liệu người dùng.
Ứng dụng chính tiếp tục dùng MySQL như trước. Chưa chạy bộ kiểm thử MySQL trong lần làm việc này.

## Cách sử dụng

Cấu hình dự phòng đã được thêm vào `.env`, API key cũ được giữ nguyên.
Nếu đang mở phiên bản phần mềm trước lúc sửa, hãy khởi động lại tiến trình phần mềm để nạp mã mới.
Chạy trong thư mục dự án như trước:

```powershell
python app.py
```

Không cần cài lại mô hình trên máy này. Khi API lỗi, nguồn xử lý tại máy được hiển thị
ngay cạnh kết quả. Có thể xem trạng thái cài đặt trong trang Quản trị.

Cấu hình chính: `AI_LOCAL_FALLBACK_ENABLED=true`, `AI_PRIMARY_BUDGET_SECONDS=30`,
`LOCAL_AI_MODEL_ENABLED=true`, `LOCAL_AI_AUTOSTART=true`, `LOCAL_AI_TIMEOUT_SECONDS=45`,
`AI_TOTAL_TIMEOUT_SECONDS=180`. Cấu hình API được đọc lại theo `AI_CONFIG_SOURCE=env_file`.

Để chạy lại kiểm thử:

```powershell
python -B tests/run_isolated.py
python -B tests/browser_smoke.py
python -B tests/run_local_brain_live.py
# Có gọi API thật bằng dữ liệu mẫu:
python -B tests/run_local_brain_live.py --probe-primary
```

## Phạm vi và giới hạn

Trợ lý đã được tích hợp cho ba chức năng hiện có, không phải một trợ lý đa năng tự học mọi nghiệp vụ.
Qwen3-1.7B là mô hình nhỏ chạy CPU, chất lượng diễn đạt có thể thấp hơn API.
Bộ xử lý nghiệp vụ là thuật toán dựa trên quy tắc và dữ liệu nguồn, không phải một mô hình ngôn ngữ khác.
Đầu ra vẫn là bản nháp để người dùng đối chiếu và Trưởng nhóm xác nhận.

Nguồn: [mô hình Qwen chính thức](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF),
[llama.cpp và tài liệu máy chủ](https://github.com/ggml-org/llama.cpp/tree/master/tools/server).
Giấy phép mô hình: Apache-2.0; runtime: MIT. Phiên bản và checksum được lưu trong dự án.
