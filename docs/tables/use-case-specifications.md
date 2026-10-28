# Đặc tả 13 Use Case

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

## UC001 Đăng nhập, đăng xuất

| Mục | Nội dung |
| --- | --- |
| Mục đích | Đăng nhập, đăng xuất an toàn và chỉ truy cập dữ liệu đúng vai trò. |
| Mô tả | Đăng nhập, đăng xuất và quản lý phiên; từ chối tài khoản bị khóa. |
| Tác nhân | Tất cả người dùng |
| Điều kiện trước | Người dùng có tài khoản hợp lệ. |
| Điều kiện sau | Đăng nhập đúng thì vào hệ thống; đăng xuất làm phiên hết hiệu lực. |
| Basic flow | 1. Người dùng nhập thông tin<br>2. Hệ thống xác thực<br>3. Truy cập thành công. |
| Alternative flow | 1. Phiên hết hạn và tài khoản khóa bị từ chối mà không lộ thông tin nhạy cảm. |
| Phân quyền hiện trạng | người có tài khoản |
| Nguồn | [URD L0245](../source/urd-extracted.txt); đặc tả UC trong source/urd-extracted.txt |
| Mô-đun thực hiện | routes/auth_routes.py, services/auth_service.py |
| Điều chỉnh có căn cứ | Xem requirements-decisions.md |

## UC002 Quản lý tài khoản

| Mục | Nội dung |
| --- | --- |
| Mục đích | Quản lý tài khoản, khóa/mở tài khoản, gán vai trò và xem nhật ký. |
| Mô tả | Tạo/xem/cập nhật/khóa-mở tài khoản, gán vai trò, xem nhật ký hệ thống. |
| Tác nhân | Quản trị viên |
| Điều kiện trước | Đăng nhập với quyền Quản trị viên. |
| Điều kiện sau | Thao tác quản trị được ghi nhật ký, dữ liệu được phân quyền theo dự án. |
| Basic flow | 1. Quản trị viên chọn tài khoản<br>2. Thực hiện cập nhật/phân quyền<br>3. Hệ thống lưu. |
| Alternative flow | 1. Người dùng không thể đọc hoặc sửa dữ liệu ngoài quyền, kể cả gọi API. |
| Phân quyền hiện trạng | Admin |
| Nguồn | [URD L0246](../source/urd-extracted.txt); đặc tả UC trong source/urd-extracted.txt |
| Mô-đun thực hiện | routes/admin_routes.py, services/account_service.py, services/audit_service.py |
| Điều chỉnh có căn cứ | Xem requirements-decisions.md |

## UC003 Quản lý dự án

| Mục | Nội dung |
| --- | --- |
| Mục đích | Tập trung thông tin dự án, thành viên trên một hệ thống. |
| Mô tả | Tạo, xem, sửa, lưu trữ dự án và quản lý trạng thái dự án. |
| Tác nhân | Trưởng nhóm |
| Điều kiện trước | Đăng nhập với quyền Trưởng nhóm. |
| Điều kiện sau | Tên, thời gian, trạng thái và dữ liệu bắt buộc được kiểm tra, lưu thành công. |
| Basic flow | 1. Trưởng nhóm tạo dự án<br>2. Khai báo thông tin cơ bản<br>3. Dự án được tạo. |
| Alternative flow | 1. Dữ liệu thiếu hoặc sai định dạng bị hệ thống báo lỗi. |
| Phân quyền hiện trạng | PM |
| Nguồn | [URD L0247](../source/urd-extracted.txt); đặc tả UC trong source/urd-extracted.txt |
| Mô-đun thực hiện | routes/project_routes.py, services/project_service.py, database/archive_schema.py |
| Điều chỉnh có căn cứ | C05 cho lưu trữ |

## UC004 Quản lý thành viên

| Mục | Nội dung |
| --- | --- |
| Mục đích | Quản lý thành viên dự án, đánh giá khối lượng công việc. |
| Mô tả | Thêm/xóa thành viên; lưu vai trò, kỹ năng, mức sẵn sàng và năng lực. |
| Tác nhân | Trưởng nhóm |
| Điều kiện trước | Dự án đã được tạo, Trưởng nhóm truy cập dự án. |
| Điều kiện sau | Danh sách và năng lực thành viên được cập nhật làm cơ sở thống kê tải. |
| Basic flow | 1. Trưởng nhóm thêm thành viên<br>2. Ghi nhận kỹ năng, năng lực<br>3. Lưu danh sách. |
| Alternative flow | 1. Xóa thành viên nhưng giữ lại lịch sử công việc cũ. |
| Phân quyền hiện trạng | PM/Member theo quyền |
| Nguồn | [URD L0248](../source/urd-extracted.txt); đặc tả UC trong source/urd-extracted.txt |
| Mô-đun thực hiện | routes/project_routes.py, services/project_member_service.py, services/member_profile_service.py |
| Điều chỉnh có căn cứ | Xem requirements-decisions.md |

## UC005 Quản lý nhiệm vụ

| Mục | Nội dung |
| --- | --- |
| Mục đích | Làm rõ người phụ trách, hạn, ưu tiên và theo dõi trạng thái nhiệm vụ. |
| Mô tả | Tạo, sửa, xóa mềm nhiệm vụ; cập nhật Kanban (Tồn đọng, Cần làm, Đang làm, Kiểm tra, Hoàn thành). |
| Tác nhân | Trưởng nhóm, Thành viên |
| Điều kiện trước | Thuộc dự án, có quyền truy cập. |
| Điều kiện sau | Nhiệm vụ được cập nhật đúng cột Kanban, lưu người phụ trách và lịch sử thay đổi. |
| Basic flow | 1. Người dùng thực hiện tạo/sửa nhiệm vụ<br>2. Cập nhật trạng thái bằng kéo thả<br>3. Hệ thống cập nhật Kanban, việc trễ và tải<br>4. Nếu nhiệm vụ thỏa BR-02, hệ thống kích hoạt gửi email cảnh báo đến người phụ trách. |
| Alternative flow | 1. Thao tác sai quyền bị máy chủ từ chối và giữ nguyên dữ liệu trước đó. |
| Phân quyền hiện trạng | PM/Member được giao hoặc hỗ trợ |
| Nguồn | [URD L0249](../source/urd-extracted.txt); đặc tả UC trong source/urd-extracted.txt |
| Mô-đun thực hiện | routes/task_routes.py, services/task_service.py, static/js/kanban.js |
| Điều chỉnh có căn cứ | Xem requirements-decisions.md |

## UC006 Quản lý Sprint/Mốc

| Mục | Nội dung |
| --- | --- |
| Mục đích | Lập kế hoạch theo dõi các đợt làm việc ngắn hạn. |
| Mô tả | Trưởng nhóm tạo, xem, sửa sprint, mốc tiến độ, tính tỷ lệ hoàn thành. |
| Tác nhân | Trưởng nhóm |
| Điều kiện trước | Truy cập dự án hợp lệ. |
| Điều kiện sau | Ngày sprint và tiêu chí hoàn thành hợp lệ; tỷ lệ được tính = nhiệm vụ Hoàn thành/Tổng. |
| Basic flow | 1. Trưởng nhóm tạo sprint/mốc<br>2. Chọn ngày và mục tiêu<br>3. Gán nhiệm vụ. |
| Alternative flow | 1. Ngày bắt đầu sau ngày kết thúc hệ thống sẽ từ chối. |
| Phân quyền hiện trạng | PM/Member chỉ xem |
| Nguồn | [URD L0250](../source/urd-extracted.txt); đặc tả UC trong source/urd-extracted.txt |
| Mô-đun thực hiện | routes/sprint_routes.py, services/sprint_service.py |
| Điều chỉnh có căn cứ | Xem requirements-decisions.md |

## UC007 Cộng tác

| Mục | Nội dung |
| --- | --- |
| Mục đích | Trao đổi công việc, lưu bằng chứng và ghi chú họp. |
| Mô tả | Bình luận, đính kèm tệp/liên kết cho nhiệm vụ; tạo ghi chú họp. |
| Tác nhân | Trưởng nhóm, Thành viên |
| Điều kiện trước | Có quyền truy cập nhiệm vụ/dự án. |
| Điều kiện sau | Nội dung lưu cùng tác giả và thời điểm, đúng dự án. |
| Basic flow | 1. Người dùng nhập nội dung hoặc đính kèm tệp<br>2. Hệ thống lưu. |
| Alternative flow | 1. Tệp sai loại/dung lượng hoặc người sai quyền bị chặn. |
| Phân quyền hiện trạng | PM/Member; Admin/Viewer chỉ xem |
| Nguồn | [URD L0251](../source/urd-extracted.txt); đặc tả UC trong source/urd-extracted.txt |
| Mô-đun thực hiện | routes/collaboration_routes.py, services/collaboration_service.py, services/attachment_service.py |
| Điều chỉnh có căn cứ | Xem requirements-decisions.md |

## UC008 Tra cứu & Báo cáo

| Mục | Nội dung |
| --- | --- |
| Mục đích | Theo dõi tiến độ, tỷ lệ hoàn thành, việc trễ và khối lượng của từng thành viên. |
| Mô tả | Tìm kiếm, lọc nhiệm vụ; Bảng điều khiển tiến độ; Thống kê nhiệm vụ trễ và tải công việc. |
| Tác nhân | Trưởng nhóm, Thành viên (chỉ xem) |
| Điều kiện trước | Có dữ liệu nhiệm vụ trong hệ thống. |
| Điều kiện sau | Kết quả hiển thị đúng phạm vi dự án và quyền truy cập. |
| Basic flow | 1. Người dùng nhập bộ lọc<br>2. Hệ thống truy xuất, tính tải công việc và số liệu hoàn thành<br>3. Hiển thị. |
| Alternative flow | 1. Cảnh báo quá tải khi tải vượt năng lực cấu hình. |
| Phân quyền hiện trạng | người có quyền dự án |
| Nguồn | [URD L0252](../source/urd-extracted.txt); đặc tả UC trong source/urd-extracted.txt |
| Mô-đun thực hiện | routes/report_routes.py, services/report_service.py, static/js/reports.js |
| Điều chỉnh có căn cứ | Xem requirements-decisions.md |

## UC009 AI Tóm tắt tiến độ

| Mục | Nội dung |
| --- | --- |
| Mục đích | Dùng AI tổng hợp tiến độ tuần, chỉ ra việc ưu tiên, rủi ro. |
| Mô tả | Yêu cầu AI tóm tắt tiến độ từ dữ liệu nhiệm vụ; đối chiếu và xác nhận. |
| Tác nhân | Trưởng nhóm |
| Điều kiện trước | Cấu hình AI hoạt động, có dữ liệu nhiệm vụ. |
| Điều kiện sau | Kết quả tóm tắt được đối chiếu và lưu chính thức, không tạo thông tin ngoài nguồn. |
| Basic flow | 1. Trưởng nhóm yêu cầu tóm tắt<br>2. Hệ thống kiểm tra dữ liệu và gửi yêu cầu<br>3. Dịch vụ AI tạo bản nháp<br>4. Trưởng nhóm đối chiếu, sửa, xác nhận. |
| Alternative flow | 1. AI nêu rõ dữ liệu thiếu/mâu thuẫn. Nếu AI lỗi thì báo lỗi 30s. |
| Phân quyền hiện trạng | PM |
| Nguồn | [URD L0253](../source/urd-extracted.txt); đặc tả UC trong source/urd-extracted.txt |
| Mô-đun thực hiện | routes/ai_routes.py, services/ai_assistant_service.py, services/project_data_retriever.py |
| Điều chỉnh có căn cứ | Xem requirements-decisions.md |

## UC010 AI Sinh biên bản họp

| Mục | Nội dung |
| --- | --- |
| Mục đích | Tạo bản nháp biên bản họp nhanh chóng từ ghi chú rời rạc. |
| Mô tả | Trưởng nhóm hoặc TV dùng ghi chú họp để AI tạo biên bản, chỉnh sửa bản nháp. |
| Tác nhân | Trưởng nhóm, Thành viên có quyền |
| Điều kiện trước | Có ghi chú họp lưu trong hệ thống. |
| Điều kiện sau | Biên bản chỉ lưu chính thức sau khi người có thẩm quyền xác nhận. |
| Basic flow | 1. Người dùng gửi ghi chú<br>2. AI tạo bản nháp có quyết định, việc cần làm<br>3. Người dùng sửa và xác nhận. |
| Alternative flow | 1. Không tự sinh dữ liệu người phụ trách nếu ghi chú không có. |
| Phân quyền hiện trạng | PM/Member được cấp quyền |
| Nguồn | [URD L0254](../source/urd-extracted.txt); đặc tả UC trong source/urd-extracted.txt |
| Mô-đun thực hiện | routes/ai_routes.py, services/meeting_minutes_service.py, services/ai_draft_service.py, services/ai_confirmation_service.py |
| Điều chỉnh có căn cứ | Xem requirements-decisions.md |

## UC011 AI Gợi ý phân công

| Mục | Nội dung |
| --- | --- |
| Mục đích | Đề xuất người phù hợp để cân bằng công việc dựa trên kỹ năng. |
| Mô tả | Nhận 1-3 gợi ý phân công theo kỹ năng, mức sẵn sàng và tải; xem lý do/cảnh báo. |
| Tác nhân | Trưởng nhóm |
| Điều kiện trước | Hệ thống có đủ thông tin năng lực và tải của thành viên. |
| Điều kiện sau | Kết quả xếp hạng ứng viên, nêu lý do. Trưởng nhóm quyết định cuối cùng. |
| Basic flow | 1. Trưởng nhóm yêu cầu AI đề xuất<br>2. Hệ thống gửi kỹ năng, tải<br>3. AI trả 1-3 gợi ý<br>4. Trưởng nhóm xem xét và quyết định phân công. |
| Alternative flow | 1. AI cảnh báo nếu tất cả đều quá tải. Hệ thống không tự gán. |
| Phân quyền hiện trạng | PM |
| Nguồn | [URD L0255](../source/urd-extracted.txt); đặc tả UC trong source/urd-extracted.txt |
| Mô-đun thực hiện | routes/ai_routes.py, services/staffing_service.py, static/js/staffing.js |
| Điều chỉnh có căn cứ | C03/C04 |

## UC012 Lịch sử AI

| Mục | Nội dung |
| --- | --- |
| Mục đích | Kiểm tra, truy vết ai yêu cầu AI, dùng dữ liệu nào và kết quả nào. |
| Mô tả | Lưu lịch sử yêu cầu/kết quả AI, phiên bản prompt, tham chiếu. |
| Tác nhân | Quản trị viên, Trưởng nhóm |
| Điều kiện trước | Đã có tương tác với AI trước đó. |
| Điều kiện sau | Truy vết được dữ liệu mà không lưu khóa bí mật. |
| Basic flow | 1. Người dùng vào lịch sử AI<br>2. Hệ thống hiển thị bản ghi<br>3. Xem chi tiết. |
| Alternative flow | 1. Không tìm thấy dữ liệu nếu dự án trống. |
| Phân quyền hiện trạng | Admin/PM |
| Nguồn | [URD L0256](../source/urd-extracted.txt); đặc tả UC trong source/urd-extracted.txt |
| Mô-đun thực hiện | routes/ai_routes.py, services/ai_history_service.py |
| Điều chỉnh có căn cứ | Xem requirements-decisions.md |

## UC013 Nhận thông báo

| Mục | Nội dung |
| --- | --- |
| Mục đích | Cập nhật nhanh việc được giao, sắp đến hạn và cảnh báo qua email khi nhiệm vụ bị trễ. |
| Mô tả | Thông báo trong ứng dụng về sự kiện quan trọng; gửi email cảnh báo đến người phụ trách khi nhiệm vụ bị trễ theo BR-02. |
| Tác nhân | Tất cả người dùng; người phụ trách nhiệm vụ là người nhận email trễ hạn. |
| Điều kiện trước | Người dùng đang trong dự án; đối với email trễ hạn, nhiệm vụ có người phụ trách và tài khoản có địa chỉ email. |
| Điều kiện sau | Người dùng nhận đúng thông báo trong ứng dụng và có thể đánh dấu đã đọc; khi nhiệm vụ bị trễ, người phụ trách nhận email cảnh báo. |
| Basic flow | 1. Hệ thống tạo thông báo khi có sự kiện (giao việc, sắp hạn)<br>2. Gửi thông báo trong ứng dụng. Khi hệ thống xác định nhiệm vụ thỏa BR-02<br>3. Lấy email tài khoản người phụ trách<br>4. Gửi email cảnh báo nhiệm vụ trễ. |
| Alternative flow | 1. Thông báo trong ứng dụng bị ẩn khi người dùng chọn đánh dấu đã đọc. Nếu nhiệm vụ chưa trễ hoặc đã Hoàn thành thì không gửi email trễ hạn. |
| Phân quyền hiện trạng | người liên quan |
| Nguồn | [URD L0257](../source/urd-extracted.txt); đặc tả UC trong source/urd-extracted.txt |
| Mô-đun thực hiện | routes/notification_routes.py, services/notification_service.py, services/email_service.py, services/deadline_worker.py |
| Điều chỉnh có căn cứ | Xem requirements-decisions.md |
