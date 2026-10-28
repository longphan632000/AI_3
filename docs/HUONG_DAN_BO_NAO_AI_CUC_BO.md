# Trợ lý AI có dự phòng cục bộ

Ngày tích hợp: 28/10/2026. Thư mục phần mềm: `D:\UNG DUNG AL_NAM3\Code Chuan`.

## Cơ chế hoạt động

Ứng dụng ưu tiên Gemini với khóa `GEMINI_API_KEY` trong cấu hình hiện tại. Khi thiếu khóa,
khóa bị từ chối, hết hạn mức, lỗi mạng, lỗi TLS, model không khả dụng, quá thời gian hoặc
kết quả không qua kiểm định, yêu cầu tự chuyển sang xử lý tại máy.

Luồng xử lý:

1. Kiểm tra tài khoản, quyền và dự án; truy xuất dữ liệu nguồn.
2. Thử Gemini API trong ngân sách `AI_PRIMARY_BUDGET_SECONDS`.
3. Nếu API lỗi, dùng Qwen3-1.7B qua llama.cpp tại `127.0.0.1:18081`.
4. Nếu mô hình chưa cài, bị tắt, đang bận, hết giờ hoặc trả kết quả sai nguồn, dùng bộ xử lý nghiệp vụ cục bộ.
5. Kiểm định, lưu bản nháp và lịch sử trong một giao dịch. Trưởng nhóm quyết định xác nhận.

Mỗi yêu cầu mới thử lại API trước, nên hệ thống tự trở về API khi dịch vụ phục hồi.
Trong cùng một yêu cầu bị lỗi, các phần còn lại có thể dùng cục bộ để tránh lặp lại lỗi.
Biên bản dài có thể có nhiều nguồn xử lý; lịch sử ghi đủ các nguồn thực sự được dùng.

## Chức năng được hỗ trợ

| Chức năng | Xử lý cục bộ |
| --- | --- |
| Tóm tắt tiến độ tuần | Mô hình viết đoạn tóm tắt ngắn; bộ xử lý nghiệp vụ bổ sung số liệu chính xác, nhiệm vụ trễ, vướng mắc, ưu tiên và dữ liệu thiếu. |
| Biên bản cuộc họp | Mô hình phân loại từng đoạn bằng JSON bị ràng buộc đủ ID nguồn. Ứng dụng giữ nguyên văn, nguồn, quyết định, công việc, người và hạn có trong nguồn. Các câu chưa chốt hoặc có điều kiện được xử lý thận trọng. |
| Gợi ý phân công | Khi API lỗi, bộ xử lý nghiệp vụ tính và xếp tối đa ba ứng viên theo năng lực sẵn sàng, tải dự kiến, kỹ năng và tải hiện tại. Tính toán không phụ thuộc mô hình sinh văn bản. |

Gợi ý phân công không cộng thêm lần nữa ước lượng của nhiệm vụ đang nằm trong tải
của chính ứng viên. Thành viên không sẵn sàng hoặc sẽ vượt năng lực có cảnh báo.
Thiếu ứng viên hoặc ước lượng được nêu rõ, không tự sinh thành viên hoặc phân công mới.

Đây là trợ lý chuyên cho ba chức năng hiện có của phần mềm. Mô hình nhỏ chạy CPU có
khả năng diễn đạt thấp hơn dịch vụ AI lớn; bộ xử lý nghiệp vụ dùng quy tắc và dữ liệu,
không phải một mô hình ngôn ngữ thứ hai. Kết quả vẫn cần người dùng kiểm tra.

## Những tệp được thêm

- `services/local_brain_service.py`: tóm tắt có căn cứ, xếp hạng phân công, phân loại nguồn và kiểm định kết quả mô hình.
- `services/local_model_service.py`: quản lý mô hình CPU, tự khởi động, giới hạn thời gian, chỉ dùng địa chỉ nội bộ máy.
- `scripts/setup_local_brain.py`: tải phiên bản runtime và mô hình cố định, đối chiếu SHA-256 trước khi cài.
- `tests/test_local_brain.py`: kiểm thử chính sách API trước, lỗi API, mô hình, quyền, nguồn, lịch sử và lưu SQLite.
- `tests/run_local_brain_live.py`: kiểm thử mô hình thật với SQLite tạm; tùy chọn gọi API thật bằng dữ liệu giả lập.

Mô hình đã được cài tại `local_models/Qwen3-1.7B-Q8_0.gguf` (khoảng 1,83 GB).
Runtime nằm trong `runtime/local_ai/`; thông tin phiên bản, giấy phép và SHA-256
được lưu tại `runtime/local_ai/installation.json`. Hai thư mục lớn này được bỏ qua bởi Git.

Những điểm nối đã sửa: `ai_provider_service.py`, `ai_assistant_service.py`,
`ai_deadline.py`, `meeting_minutes_service.py`, `project_data_retriever.py`,
trạng thái quản trị, giao diện trợ lý, cấu hình mẫu và các runner kiểm thử.
Giao diện hiển thị nguồn tạo kết quả; `validation_json.engine` lưu nguồn và mã lỗi.
`ai_history.model_provider` ghi `gemini`, `local_llm`, `local_rules` hoặc tổ hợp thực tế.

## Cấu hình đang dùng

```dotenv
AI_PROVIDER=gemini
AI_CONFIG_SOURCE=env_file
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.6-flash
GEMINI_MEETING_MODEL=gemini-3.6-flash
AI_LOCAL_FALLBACK_ENABLED=true
AI_PRIMARY_BUDGET_SECONDS=30
LOCAL_AI_MODEL_ENABLED=true
LOCAL_AI_AUTOSTART=true
LOCAL_AI_PORT=18081
LOCAL_AI_TIMEOUT_SECONDS=45
AI_TOTAL_TIMEOUT_SECONDS=180
```

Cấu hình MySQL được giữ nguyên; khóa Gemini được đọc riêng từ GEMINI_API_KEY. Lần đầu chuyển sang mô hình
cục bộ sẽ mất thêm thời gian nạp mô hình. Sau đó runtime được giữ trong khi tiến trình
phần mềm còn chạy. Khi thoát bình thường, ứng dụng đóng runtime do chính nó tạo.
Nếu nhiều yêu cầu đến cùng lúc, yêu cầu không lấy được mô hình có thể dùng bộ xử lý
nghiệp vụ để không phải chờ hàng đợi dài. Phần nguồn nội bộ không được gửi qua proxy mạng.

Để tắt hoàn toàn dự phòng, đặt `AI_LOCAL_FALLBACK_ENABLED=false`. Để dùng dự phòng
nghiệp vụ mà không nạp mô hình, đặt `LOCAL_AI_MODEL_ENABLED=false`.
Với `AI_CONFIG_SOURCE=env_file`, cấu hình được đọc lại cho yêu cầu mới.

## Khởi chạy và kiểm thử

Chạy như trước trong thư mục dự án:

```powershell
python app.py
```

Nếu phần mềm đã chạy trước lúc sửa mã, cần khởi động lại tiến trình đó để nạp mã mới.
Khi chuyển phần mềm sang máy Windows x64 khác, cài lại mô hình một lần với Internet:

```powershell
python scripts/setup_local_brain.py
```

Các lần dùng cục bộ sau khi cài không cần Internet hoặc khóa API.

```powershell
python -B tests/run_isolated.py
python -B tests/browser_smoke.py
python -B tests/run_local_brain_live.py
# Tùy chọn này có gọi API thật bằng dữ liệu dự án kiểm thử:
python -B tests/run_local_brain_live.py --probe-primary
```

Các runner dùng SQLite tạm, không sửa cơ sở dữ liệu người dùng. Một số ca kiểm thử cũ
cố ý tắt fallback để kiểm tra lỗi API riêng; `test_local_brain.py` chủ động bật fallback
để kiểm tra chính sách mới. Bộ kiểm thử thường dùng API và mô hình giả lập có kiểm soát;
runner `run_local_brain_live.py` dùng mô hình thật đã cài.

Ứng dụng chính vẫn dùng MySQL như trước. SQLite chỉ dùng để kiểm thử theo yêu cầu,
không được tự bật làm cơ sở dữ liệu thay thế cho dữ liệu đang vận hành.

Kết quả kiểm thử mới nhất được lưu trong:

- `docs/qa-results-sqlite.json`
- `docs/qa-browser-results.json`
- `docs/qa-local-brain-live.json`
- `docs/BAO_CAO_TICH_HOP_BO_NAO_AI.md`

## Nguồn mô hình và runtime

- [Qwen3-1.7B-GGUF của Qwen](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF), giấy phép Apache-2.0.
- [llama.cpp](https://github.com/ggml-org/llama.cpp), giấy phép MIT.
- [Giao tiếp và đầu ra JSON của llama.cpp](https://github.com/ggml-org/llama.cpp/tree/master/tools/server).

Tệp cài đặt được ghim theo phiên bản/revision và SHA-256 trong script; không tự tải
model khác hoặc chạy chương trình cài đặt lấy từ nội dung ghi chú của người dùng.
