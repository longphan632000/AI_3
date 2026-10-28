# Đặc tả yêu cầu hệ thống

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

## Phạm vi và tác nhân

Ba vai trò hệ thống: Admin, Trưởng nhóm (PM), Member. `viewer` là quyền trong dự án, không phải vai trò hệ thống thứ tư. Dịch vụ AI là hệ thống hỗ trợ bên ngoài; không đọc MySQL trực tiếp, không xác nhận hay tự phân công.

## Yêu cầu chức năng

| ID | Yêu cầu nguồn | Mức | Use Case | Nguồn | Hiện trạng/giới hạn |
| --- | --- | --- | --- | --- | --- |
| FR-01 | Đăng nhập, đăng xuất và quản lý phiên; từ chối tài khoản bị khóa. | Bắt buộc | UC001 | [URD L0144](source/urd-extracted.txt) | Có triển khai; đối chiếu ca thử |
| FR-02 | Quản trị viên tạo/xem/cập nhật/khóa-mở tài khoản, gán vai trò, xem nhật ký; hệ thống phân quyền Trưởng nhóm, Thành viên và Người xem báo cáo theo dự án. | Bắt buộc | UC002 | [URD L0145](source/urd-extracted.txt) | Có triển khai; đối chiếu ca thử |
| FR-03 | Tạo, xem, sửa, lưu trữ dự án và quản lý trạng thái dự án. | Bắt buộc | UC003 | [URD L0146](source/urd-extracted.txt) | PARTIAL / cần chốt REQ-04 |
| FR-04 | Thêm/xóa thành viên; lưu vai trò, kỹ năng, mức sẵn sàng và năng lực làm việc dự kiến. | Bắt buộc | UC004 | [URD L0147](source/urd-extracted.txt) | Có triển khai; đối chiếu ca thử |
| FR-05 | Tạo, xem, sửa, xóa mềm nhiệm vụ; lưu người phụ trách, trạng thái, ưu tiên, hạn, ước lượng, nhãn, sprint và vướng mắc. | Bắt buộc | UC005 | [URD L0148](source/urd-extracted.txt) | PARTIAL / cần chốt REQ-04 |
| FR-06 | Hiển thị Kanban và chuyển nhiệm vụ qua Tồn đọng, Cần làm, Đang làm, Kiểm tra, Hoàn thành bằng kéo thả hoặc biểu mẫu. | Bắt buộc | UC005 | [URD L0149](source/urd-extracted.txt) | Có triển khai; đối chiếu ca thử |
| FR-07 | Trưởng nhóm tạo, xem, sửa, lưu trữ sprint/mốc tiến độ, gán nhiệm vụ và tính tỷ lệ hoàn thành; Thành viên chỉ xem. | Bắt buộc | UC006 | [URD L0150](source/urd-extracted.txt) | PARTIAL / cần chốt REQ-05 |
| FR-08 | Bình luận, đính kèm tệp/liên kết cho nhiệm vụ; tạo và lưu ghi chú họp làm đầu vào biên bản AI. | Bắt buộc | UC007 | [URD L0151](source/urd-extracted.txt) | Có triển khai; đối chiếu ca thử |
| FR-09 | Tìm kiếm, lọc, sắp xếp và phân trang nhiệm vụ theo người, trạng thái, sprint, hạn, ưu tiên và tình trạng trễ. | Bắt buộc | UC008 | [URD L0152](source/urd-extracted.txt) | Có triển khai; đối chiếu ca thử |
| FR-10 | Bảng điều khiển tiến độ theo dự án và sprint. | Bắt buộc | UC008 | [URD L0153](source/urd-extracted.txt) | Có triển khai; đối chiếu ca thử |
| FR-11 | Thống kê nhiệm vụ trễ và khối lượng công việc của từng thành viên. | Bắt buộc | UC008 | [URD L0154](source/urd-extracted.txt) | Có triển khai; đối chiếu ca thử |
| FR-12 | Trưởng nhóm chọn dự án và khoảng tuần để AI tóm tắt tiến độ từ dữ liệu nhiệm vụ. | Bắt buộc | UC009 | [URD L0155](source/urd-extracted.txt) | Có triển khai; đối chiếu ca thử |
| FR-13 | Trưởng nhóm hoặc Thành viên được phân quyền dùng ghi chú họp để AI tạo biên bản; được xem và chỉnh sửa bản nháp. | Bắt buộc | UC010 | [URD L0156](source/urd-extracted.txt) | Có triển khai; đối chiếu ca thử |
| FR-14 | AI gợi ý 1-3 người phụ trách theo kỹ năng, mức sẵn sàng và tải công việc; Trưởng nhóm quyết định cuối cùng. | Bắt buộc | UC011 | [URD L0157](source/urd-extracted.txt) | MỞ RỘNG theo C03/C04; giữ nhánh cũ 1–3 |
| FR-15 | Lưu lịch sử yêu cầu/kết quả AI, phiên bản prompt, dữ liệu tham chiếu và trạng thái xác nhận. | Nên có | UC012 | [URD L0158](source/urd-extracted.txt) | PARTIAL / cần chốt REQ-10 |
| FR-16 | Thông báo trong ứng dụng về việc được giao, sắp đến hạn và thay đổi quan trọng. | Nên có | UC013 | [URD L0159](source/urd-extracted.txt) | PARTIAL / cần chốt REQ-06 |
| FR-17 | Gửi email cảnh báo đến người phụ trách khi nhiệm vụ bị trễ theo BR-02. | Nên có | UC013 | [URD L0160](source/urd-extracted.txt) | Có code/test mô phỏng; SMTP thật NOT RUN trong lượt này |

## Yêu cầu phi chức năng

| ID | Nhóm | Tiêu chí nguồn | Nguồn | Minh chứng/cần kiểm |
| --- | --- | --- | --- | --- |
| NFR-01 | Hiệu năng | Mục tiêu đề xuất: thao tác thông thường và tìm kiếm phản hồi trong khoảng 2 giây ở bộ dữ liệu kiểm thử; tác vụ AI có kết quả hoặc lỗi rõ trong khoảng 30 giây. | [URD L0182](source/urd-extracted.txt) | REQ-07; chưa nghiệm thu 30 giây toàn yêu cầu |
| NFR-02 | Dễ sử dụng | Giao diện rõ ràng trên máy tính và điện thoại; thông báo lỗi bằng tiếng Việt; dữ liệu đang nhập được giữ lại khi có thể phục hồi. | [URD L0183](source/urd-extracted.txt) | Xem test-report.md và security-review.md; không suy rộng từ test pass |
| NFR-03 | Bảo mật | Mật khẩu được băm; quyền được kiểm tra ở máy chủ; kết nối được mã hóa; dữ liệu ngoài dự án/quyền bị từ chối. | [URD L0184](source/urd-extracted.txt) | REQ-08; TLS chưa xác minh |
| NFR-04 | Riêng tư | Chỉ gửi dữ liệu tối thiểu cần thiết tới dịch vụ AI; không gửi mật khẩu, khóa bí mật hoặc tài liệu ngoài quyền truy cập. | [URD L0185](source/urd-extracted.txt) | Xem test-report.md và security-review.md; không suy rộng từ test pass |
| NFR-05 | Tin cậy dữ liệu | Thay đổi quan trọng được ghi nhận; sao lưu theo lịch môi trường; trước nghiệm thu thử khôi phục ít nhất một bản sao lưu. | [URD L0186](source/urd-extracted.txt) | REQ-09; backup/restore cũ, lịch vận hành chưa xác minh |
| NFR-06 | An toàn AI | Kết quả AI là bản nháp, nêu dữ liệu thiếu/mâu thuẫn và phải được con người xem xét trước khi lưu, chia sẻ hoặc dùng để phân công. | [URD L0187](source/urd-extracted.txt) | Xem test-report.md và security-review.md; không suy rộng từ test pass |
| NFR-07 | Khả năng bảo trì | Giao diện, nghiệp vụ, dữ liệu và tích hợp AI được tách thành các mô-đun; thay nhà cung cấp AI không làm đổi quy tắc nghiệp vụ. | [URD L0188](source/urd-extracted.txt) | Xem test-report.md và security-review.md; không suy rộng từ test pass |
| NFR-08 | Kiểm thử | Có kiểm thử nhiệm vụ, sprint, thống kê và ba chức năng AI; kiểm tra phân quyền và một luồng từ tạo dự án đến báo cáo tuần. | [URD L0189](source/urd-extracted.txt) | Xem test-report.md và security-review.md; không suy rộng từ test pass |
| NFR-09 | Khả năng truy vết | Hệ thống lưu người thực hiện, thời điểm, hành động và đối tượng thay đổi; nhật ký không chứa mật khẩu hoặc khóa dịch vụ. | [URD L0190](source/urd-extracted.txt) | Xem test-report.md và security-review.md; không suy rộng từ test pass |
| NFR-10 | Khả năng mở rộng dữ liệu | Mục tiêu đề xuất: truy vấn vẫn đáp ứng yêu cầu hiệu năng với tối thiểu 10.000 nhiệm vụ trong bộ dữ liệu kiểm thử. | [URD L0191](source/urd-extracted.txt) | REQ-09; phép đo MySQL cũ, không chạy lại |
| NFR-11 | Khả năng thay thế AI | Nhà cung cấp/mô hình AI được cấu hình qua lớp tích hợp riêng; khi thay đổi không phải sửa chức năng quản lý dự án cốt lõi. | [URD L0192](source/urd-extracted.txt) | Xem test-report.md và security-review.md; không suy rộng từ test pass |

## Quy tắc nghiệp vụ

| ID | Tên | Nội dung nguồn | Nguồn |
| --- | --- | --- | --- |
| BR-01 | Trạng thái nhiệm vụ | Luồng mặc định: Tồn đọng (Backlog) → Cần làm (To do) → Đang làm (In progress) → Kiểm tra (Review) → Hoàn thành (Done). | [URD L0198](source/urd-extracted.txt) |
| BR-02 | Nhiệm vụ trễ | Nhiệm vụ trễ khi đã quá hạn, chưa Hoàn thành và chưa bị lưu trữ. | [URD L0199](source/urd-extracted.txt) |
| BR-03 | Sprint | Ngày bắt đầu không sau ngày kết thúc; một nhiệm vụ thuộc tối đa một sprint tại một thời điểm. | [URD L0200](source/urd-extracted.txt) |
| BR-04 | Tỷ lệ hoàn thành | Tỷ lệ = số nhiệm vụ Hoàn thành/tổng nhiệm vụ trong phạm vi; nếu không có nhiệm vụ thì hiển thị 0%. | [URD L0201](source/urd-extracted.txt) |
| BR-05 | Tải và quá tải | Tải = tổng ước lượng của nhiệm vụ chưa Hoàn thành trong sprint/khoảng lọc; quá tải khi tải vượt năng lực hoặc mức sẵn sàng đã cấu hình. | [URD L0202](source/urd-extracted.txt) |
| BR-06 | Xác nhận AI | AI chỉ tạo bản nháp/đề xuất; người có thẩm quyền phải xem lại, chỉnh sửa và xác nhận. | [URD L0203](source/urd-extracted.txt) |
| BR-07 | Dữ liệu AI | AI không tạo sự kiện, con số hoặc người phụ trách không có trong dữ liệu; phải nêu rõ phần thiếu/mâu thuẫn. | [URD L0204](source/urd-extracted.txt) |
| BR-08 | Xóa dữ liệu | Dự án và nhiệm vụ được lưu trữ hoặc xóa mềm để bảo toàn lịch sử; xóa vĩnh viễn theo quyền quản trị. | [URD L0205](source/urd-extracted.txt) |
| BR-09 | Email cảnh báo nhiệm vụ trễ | Khi nhiệm vụ thỏa BR-02, hệ thống gửi email cảnh báo đến địa chỉ email của tài khoản người phụ trách nhiệm vụ. | [URD L0206](source/urd-extracted.txt) |

## Quy tắc hiện trạng mở rộng

Kanban cho đổi hai chiều giữa các cột theo quyền; Done tương ứng 100%, mở lại Done đưa về 0 để người thực hiện khai báo lại. Tỷ lệ Done và trung bình phần trăm thực tế là hai chỉ số khác nhau. Tải mỗi người tính đầy đủ ước lượng việc mở mà họ là chính hoặc hỗ trợ, không đếm trùng cùng người/cùng việc.

Luồng staffing mới có source system/project, count 1–100, recruitment không cần task. Không đủ dữ liệu thì báo thiếu. Thêm người và giao việc đều do PM xác nhận riêng. Dự án đã lưu trữ chỉ Admin/người PM đã lưu trữ đọc/khôi phục; trường hợp không xác định archiver chỉ Admin.

Mọi khác biệt với URD còn lại nằm trong requirements-issues.md. Không xác nhận toàn bộ NFR chỉ vì bộ kiểm thử xanh.
