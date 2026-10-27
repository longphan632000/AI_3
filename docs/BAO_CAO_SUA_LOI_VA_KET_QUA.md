# Kết quả chỉnh sửa và kiểm thử

Ngày báo cáo: 27/10/2026. Căn cứ: Detai33.docx và kế hoạch đã được người dùng duyệt.

> **Cập nhật Gemini thật:** Đã sửa phân loại lỗi mạng và chạy lại máy chủ ngoài sandbox;
> metadata Gemini truy cập được từ chính ứng dụng. Hồi quy mới đạt 145/145 ca trên mỗi
> engine và 23/23 nhóm Edge. Tuy nhiên ba ca sinh nội dung thật đều timeout; yêu cầu tối
> giản nhận thêm HTTP 503 UNAVAILABLE do model đang có nhu cầu cao. Xem
> [báo cáo kết nối Gemini](BAO_CAO_LOI_KET_NOI_GEMINI.md) và qa-gemini-live-results.json.
> Không dùng kết quả test giả lập để đánh dấu ba chức năng AI thật đã đạt.

## Cập nhật theo lỗi giao diện, Gemini và đồng bộ

Đã đọc lại FR-01–17, BR-01–09 và NFR-01–11 trong `Detai33.docx`. Các thay đổi dưới
đây giữ nguyên quyền theo tài liệu: PM/Trưởng nhóm quản lý dự án và xác nhận AI;
member thực hiện trong phạm vi được giao; viewer chỉ đọc; Admin duyệt/quản trị tài khoản.
Đồng bộ dữ liệu không có nghĩa mọi vai trò được cấp cùng quyền ghi.

| Vấn đề đã tái hiện | Nguyên nhân | Chỉnh sửa và kiểm chứng |
| --- | --- | --- |
| Tên tiếng Việt chứa dấu `?` | Tên bốn tài khoản mẫu đã bị mất ký tự trước khi ghi MySQL, không phải chỉ thiếu font. | Công cụ UTF-8 khôi phục đúng tên mẫu đã biết khi phát hiện hỏng dấu; giữ ID, mật khẩu và dữ liệu dự án. API roundtrip Unicode đạt trên hai engine; bổ sung font hệ thống dự phòng. |
| Tạo dự án chưa chọn được nhân viên | Form không có bộ chọn và không gửi member_ids, dù service có tham số ban đầu. | Thêm tìm kiếm/checkbox nhân viên đã được duyệt, số lượng đã chọn và gửi cùng yêu cầu tạo dự án. Kiểm tra tất cả ID trước khi ghi; tài khoản sai/khóa làm toàn bộ yêu cầu bị từ chối. Đã thao tác form thật trong Edge. |
| Biên bản/tuần còn gọi Kira | Tiến trình đang chạy giữ AI_PROVIDER và model cũ; .env có thể bị biến môi trường cũ ghi đè. | .env và .env.example chọn Gemini 3.8 Flash cho cả hai model; bỏ cấu hình Kira khỏi .env. Người dùng đã nhập key; lượt sửa kết nối giữ nguyên key. AI_CONFIG_SOURCE=env_file nạp cấu hình mới cho mỗi yêu cầu; key rỗng không khôi phục key cũ. Adapter không ghép thought vào JSON và bỏ tham số sampling cũ. |
| Member chờ duyệt không xuất hiện ở Admin | Backend đã tạo pending nhưng giao diện lọc riêng role=leader. | Danh sách chờ duyệt và nút duyệt áp dụng cho cả member/leader. Đã kiểm tra đăng ký member qua UI, đăng nhập trước duyệt bị 401, Admin duyệt rồi đăng nhập thành công. |
| Dữ liệu trang/máy khách cũ sau thay đổi | Các trang chỉ tải dữ liệu lúc mở, không có cơ chế phát hiện thay đổi chung. | API token thay đổi mỗi 5 giây và khi focus/online; các trang tải lại dữ liệu theo quyền. API no-store và phiên bản CSS/JS chống cache cũ. Giữ ghi chú/biểu mẫu đang nhập; khóa tài khoản thu hồi phiên ở yêu cầu kế tiếp. |
| Menu trên màn hình nhỏ không hoạt động | JavaScript tìm ID sidebar/backdrop nhưng template thiếu các phần tử tương ứng. | Bổ sung ID, nút menu, backdrop và trạng thái ARIA. Kiểm thử mở/đóng menu qua Edge ở các viewport nhỏ. |
| Thiếu thao tác trạng thái trên cảm ứng | Kéo thả không phải thao tác thuận tiện trên mọi thiết bị. | Bổ sung chọn và lưu trạng thái trong chi tiết task cho đúng người có quyền; thử đổi sang Review tại bốn viewport. |
| Trang AI tràn ở 320px | Hai ô ngày trong grid giữ kích thước tối thiểu lớn hơn vùng nội dung. | Stack grid nhỏ, min-width phù hợp, wrap nội dung và nút; kiểm tra không tràn ngang body ở bốn kích thước. |
| Ghi chú họp đã lưu không chọn lại được | Thiếu select ghi chú và JS dùng ID không thống nhất. | Bổ sung bộ chọn; lưu ghi chú từ form xong tự chọn làm nguồn AI. Kiểm thử thao tác thật qua Edge. |
| Có thể dùng khóa phát triển công khai để ký phiên | SECRET_KEY mẫu cố định còn được dùng cho local. | Sinh khóa riêng trong .env, bỏ fallback công khai trong app. Cookie giả ký bằng khóa mẫu bị 401. Các phiên cũ cần đăng nhập lại sau khởi động mới. |

Máy chủ đã được khởi động lại với mã mới, lắng nghe `0.0.0.0:5000`. Đã kiểm tra
HTTP qua địa chỉ LAN `http://192.168.1.39:5000` từ chính máy chủ: health HEALTHY,
MySQL sẵn sàng, đăng nhập Admin 200, trạng thái AI dùng cả hai model
`gemini-3.8-flash`. Sau khi người dùng nhập key và máy chủ chạy ngoài sandbox,
API chẩn đoán của ứng dụng xác nhận metadata truy cập được; tạo nội dung thật vẫn
timeout/503 dịch vụ như báo cáo mới. Đây chưa phải phép thử trên thiết bị vật lý khác.
Địa chỉ LAN có thể đổi khi mạng cấp IP mới. SMTP và worker tự động đang tắt trong
tiến trình local kiểm thử để không phát sinh gửi email hoặc ghi cảnh báo nền.

## Thay đổi đã thực hiện

- Khôi phục cú pháp JavaScript dùng chung và Dashboard; hoàn thiện các nút/form sửa dự án, tài khoản, thành viên, sprint và nhiệm vụ.
- DELETE dự án mặc định lưu trữ; chỉ admin được xóa vĩnh viễn. Dữ liệu lưu trữ chỉ đọc, có API/giao diện khôi phục. Không xóa trưởng nhóm cuối cùng qua luồng xóa thành viên.
- Chặn viewer ghi dữ liệu; kiểm tra phạm vi dự án khi quét email và khi phân công cả người phụ trách lẫn hỗ trợ. Người bị khóa/ngoài dự án không được phân công mới.
- Transaction bao trùm nghiệp vụ nhiều bước, kể cả audit và thông báo. Email được xử lý sau commit; lỗi email không biến một cập nhật đã commit thành phản hồi thất bại sai lệch.
- Kiểm tra JSON object, kiểu, độ dài, số hữu hạn không âm, ngày hợp lệ và khoảng thời gian. Mã tài khoản tự sinh không còn dùng COUNT; API giữ mã tùy chỉnh.
- Bổ sung lọc ưu tiên/hạn/trạng thái, chọn sắp xếp và phân trang Kanban; điều kiện quá hạn được áp dụng trước LIMIT.
- Đồng bộ trạng thái/phần trăm: 100% là Done; mở lại task Done giảm từ 100 xuống 80 theo quy ước đã có. Cho phép chuyển giữa năm trạng thái, không áp đặt phải đi tuần tự.
- Tải hỗ trợ được tính thống nhất giữa báo cáo và AI; capacity 0 được giữ nguyên. Giờ khả dụng = capacity × tỷ lệ sẵn sàng / 100. Dữ liệu sẵn sàng cũ không rõ tỷ lệ có cảnh báo cần cập nhật.
- Bổ sung upload/list/download tài liệu và liên kết; kiểm tra quyền, loại/dung lượng/chữ ký cơ bản và chống lưu đường dẫn do client chỉ định. Tệp lưu ngoài static.
- Bổ sung đọc/sửa draft, phiên bản và lịch sử chỉnh sửa; chặn ghi đè phiên bản cũ. Xác nhận dùng nội dung đã sửa và chỉ dành cho trưởng nhóm đúng dự án.
- Kiểm định số liệu tóm tắt với snapshot nguồn; số liệu tổng hợp được tính bởi hệ thống. Đề xuất phân công ngoài giới hạn 1–3 người hoặc thiếu lý do cần xác minh. AI vẫn cần con người đối chiếu nội dung.
- Thêm ngân sách thời gian dùng chung cho retry/chunk AI, mặc định 30 giây. Cấu hình timeout cho từng nhà cung cấp vẫn được giữ, nhưng không vượt ngân sách còn lại của yêu cầu.
- Cảnh báo có cơ chế tự quét, lưu lease chống xử lý trùng giữa tiến trình, retry thất bại có giới hạn và trạng thái gửi/mô phỏng/thất bại riêng. SMTP mặc định tắt để tránh gửi thật ngoài ý muốn.
- Đồng bộ schema cài mới/migration; thêm các bảng phân công, revision draft và trạng thái email; nâng trường văn bản cần thiết lên LONGTEXT để giữ ghi chú tiếng Việt dài.
- Sửa khác biệt MySQL/SQLite: số tổng hợp Decimal của Dashboard được chuyển đúng kiểu; ngày trả về từ MySQL có định dạng ISO.
- Khai báo dependency SDK Kira; kiểm thử adapter với SDK thật và HTTP transport giả lập. Sửa các tài nguyên PWA bị thiếu đường phục vụ.

## Kết quả đã thực thi

| Nhóm | Kết quả |
| --- | --- |
| Hồi quy SQLite cách ly | 145/145 Thành công |
| Hồi quy MySQL cách ly | 145/145 Thành công |
| Bảng nghiệm thu chi tiết | 67 kịch bản, mỗi kịch bản có bằng chứng trên cả hai engine |
| Edge headless, luồng chức năng và bố cục | 23/23 nhóm kiểm tra Thành công; không có lỗi JavaScript runtime |
| Tạo nội dung Gemini thật | 0/3 Thành công; cả ba ca AI_TIMEOUT, xem báo cáo kết nối Gemini |
| Vai trò/kích thước màn hình | 76 lượt mở trang: PM, member, Admin × 1366/768/390/320px; không tràn ngang body |
| Tạo dự án/chọn nhân viên | Thao tác thật qua Edge; kiểm tra form ở bốn viewport |
| Cảm ứng mô phỏng | Tap mở task và lưu trạng thái ở 390/768px với has_touch=true: Thành công |
| Đồng bộ nhiều máy khách mô phỏng | Các browser context độc lập đọc cùng task/dự án; Dashboard tự cập nhật; giữ ghi chú đang nhập |
| Biên bản Word trên trình duyệt | Upload DOCX → trích xuất → adapter Gemini HTTP giả lập → hiển thị draft: Thành công |
| Cài MySQL mới, lặp migration | Thành công |
| Nâng schema cũ thiếu trường mới | Thành công; giữ dữ liệu và backfill 2.500 task Done |
| Tìm kiếm/phân trang 10.000 task | 0,0823 giây, Thành công |
| Thống kê Dashboard 10.000 task | 0,1049 giây, Thành công |
| Tải thành viên với 10.000 task | 0,1971 giây, Thành công |
| Sao lưu/khôi phục | 16 bảng; checksum toàn bộ hàng dữ liệu khớp; Thành công |
| Cú pháp JS và HTML đã render | 17 đoạn script không có lỗi cú pháp |

Số đo hiệu năng là thời gian gọi service trên máy/môi trường kiểm thử này, không phải cam kết độ trễ từ trình duyệt hoặc khi có nhiều người dùng đồng thời. 145 ca trên hai engine là hai lượt thực thi cùng bộ kịch bản, không phải 290 kịch bản khác nhau. 23 nhóm trình duyệt là bộ bổ sung riêng, gồm cả kiểm tra luồng và bố cục. Ba ca Gemini thật là bộ riêng, đang thất bại do timeout.

Hai test cũ đã được điều chỉnh để phản ánh yêu cầu đúng: admin được hard delete thay cho trưởng nhóm, và số cảnh báo được tính cả cảnh báo tự động đã phát sinh trước lượt quét thủ công. Những thay đổi này không bỏ kiểm tra phân quyền hoặc chống gửi lặp.

## Quy ước nghiệp vụ được áp dụng

- Lưu trữ là chỉ đọc; khôi phục là thao tác riêng.
- Member giữ phạm vi cập nhật task đang phụ trách/hỗ trợ; leader quản lý phân công. Viewer chỉ đọc.
- Mốc tiến độ có thể biểu diễn bằng sprint có ngày bắt đầu/kết thúc trùng nhau; không thêm một mô hình dữ liệu mốc riêng.
- Capacity là số giờ nền; availability là tỷ lệ 0–100%. Giao diện cho nhập rõ hai giá trị.
- Mặc định quét hạn mỗi 60 giây, nhắc lại sau 24 giờ, retry lỗi sau 300 giây với tối đa ba lần trong chu kỳ; các mốc này có thể cấu hình.
- Gửi email thật cần bật SMTP_ENABLED và cung cấp tài khoản SMTP hợp lệ. Chế độ mô phỏng không được hiển thị là đã gửi thật.

## Phạm vi chưa xác minh thực tế

- Công cụ điều khiển cửa sổ desktop không kết nối được; đã dùng Microsoft Edge headless qua Playwright để kiểm tra giao diện và tương tác thật ở bốn viewport. Chưa nghiệm thu Safari/iOS/Android trên điện thoại hoặc máy tính bảng vật lý, chưa xác minh kéo thả bằng cảm ứng thật.
- AI/email trong hồi quy được giả lập. Đã bổ sung ba ca Gemini thật: đều timeout; metadata/key được chấp nhận nhưng chưa nghiệm thu tạo nội dung thật thành công. Chưa gửi email qua SMTP thật.
- Sao lưu/khôi phục chạy trên dữ liệu fixture MySQL cách ly; chưa thực hiện khôi phục dữ liệu người dùng đang sử dụng.
- Chưa đo tải đồng thời, độ trễ mạng, cấu hình HTTPS hoặc vận hành worker trên máy triển khai thực tế.
- Chưa kiểm tra từ máy vật lý thứ hai qua Wi-Fi; kiểm tra IP LAN thực hiện trên máy chủ. Tường lửa, Wi-Fi khách/cô lập thiết bị vẫn phụ thuộc môi trường mạng.
- Người dùng đã nhập Gemini API key; lượt sửa kết nối giữ nguyên .env. API_METADATA đọc được; tạo nội dung thật đang gặp timeout/503 dịch vụ, chưa xác minh quota tạo nội dung hoạt động.

## Tệp kết quả và cách chạy lại

- `TEST_CASES_SAU_CHINH_SUA.md`: bảng 67 kịch bản để đọc/sao chép.
- `TEST_CASES_SAU_CHINH_SUA.csv`: bảng UTF-8 có BOM, mở bằng Excel hoặc nhập vào tài liệu.
- `TEST_CASES_SAU_CHINH_SUA.html`: bảng có định dạng để mở và sao chép sang Word, có chế độ in A4 ngang.
- `qa-results-sqlite.json`, `qa-results-mysql.json`: kết quả từng ca trong toàn bộ bộ test.
- `qa-system-checks.json`: bằng chứng cài đặt/migration, hiệu năng và khôi phục.
- `qa-browser-results.json`: 23 nhóm kiểm tra Edge và các viewport; `qa-screenshots/` chứa ảnh form tạo dự án và chi tiết task sau kiểm tra.
- `qa-gemini-live-results.json`: kết quả ba ca tạo nội dung thật bằng dữ liệu QA tổng hợp, hiện 0/3 đạt.
- `HUONG_DAN_CHAY_LAN_VA_GEMINI.md`: cấu hình LAN, Gemini, duyệt tài khoản, chọn nhân viên và cơ chế đồng bộ.

```powershell
python -B tests/run_isolated.py
python -B tests/run_mysql_isolated.py
python -B tests/export_test_cases.py
python -B tests/browser_smoke.py
```

Runner MySQL tạo database tên ngẫu nhiên bắt đầu bằng `qa_repair_`, dùng để kiểm thử rồi xóa đúng database nó đã tạo. Không dùng database ứng dụng làm đích ghi test.

Khởi động lại ứng dụng để nạp mã mới. Startup migration bổ sung cấu trúc cần thiết và giữ dữ liệu hiện có; nên sao lưu database đang dùng trước khi triển khai bản mới. Không cần chạy lại seed để sửa dữ liệu người dùng.
