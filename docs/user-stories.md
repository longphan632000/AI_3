# User stories truy vết yêu cầu

Bổ sung hồ sơ sau triển khai lúc 2026-10-28T21:25:16+07:00; bản mã `d81c548`. Phản ánh implementation hiện tại; không xác nhận thay nhóm các Human Gate trước đây.

| Story | Là ai | Tôi muốn | Để | FR | UC | Nguồn |
| --- | --- | --- | --- | --- | --- | --- |
| US-01 | người có tài khoản | Đăng nhập, đăng xuất và quản lý phiên; từ chối tài khoản bị khóa. | Dữ liệu đúng quyền, theo dõi/quyết định từ nguồn thực | FR-01 | UC001 | [URD L0144](source/urd-extracted.txt) |
| US-02 | Admin | Quản trị viên tạo/xem/cập nhật/khóa-mở tài khoản, gán vai trò, xem nhật ký; hệ thống phân quyền Trưởng nhóm, Thành viên và Người xem báo cáo theo dự án. | Dữ liệu đúng quyền, theo dõi/quyết định từ nguồn thực | FR-02 | UC002 | [URD L0145](source/urd-extracted.txt) |
| US-03 | PM | Tạo, xem, sửa, lưu trữ dự án và quản lý trạng thái dự án. | Dữ liệu đúng quyền, theo dõi/quyết định từ nguồn thực | FR-03 | UC003 | [URD L0146](source/urd-extracted.txt) |
| US-04 | PM/Member theo quyền | Thêm/xóa thành viên; lưu vai trò, kỹ năng, mức sẵn sàng và năng lực làm việc dự kiến. | Dữ liệu đúng quyền, theo dõi/quyết định từ nguồn thực | FR-04 | UC004 | [URD L0147](source/urd-extracted.txt) |
| US-05 | PM/Member được giao hoặc hỗ trợ | Tạo, xem, sửa, xóa mềm nhiệm vụ; lưu người phụ trách, trạng thái, ưu tiên, hạn, ước lượng, nhãn, sprint và vướng mắc. | Dữ liệu đúng quyền, theo dõi/quyết định từ nguồn thực | FR-05 | UC005 | [URD L0148](source/urd-extracted.txt) |
| US-06 | PM/Member được giao hoặc hỗ trợ | Hiển thị Kanban và chuyển nhiệm vụ qua Tồn đọng, Cần làm, Đang làm, Kiểm tra, Hoàn thành bằng kéo thả hoặc biểu mẫu. | Dữ liệu đúng quyền, theo dõi/quyết định từ nguồn thực | FR-06 | UC005 | [URD L0149](source/urd-extracted.txt) |
| US-07 | PM/Member chỉ xem | Trưởng nhóm tạo, xem, sửa, lưu trữ sprint/mốc tiến độ, gán nhiệm vụ và tính tỷ lệ hoàn thành; Thành viên chỉ xem. | Dữ liệu đúng quyền, theo dõi/quyết định từ nguồn thực | FR-07 | UC006 | [URD L0150](source/urd-extracted.txt) |
| US-08 | PM/Member; Admin/Viewer chỉ xem | Bình luận, đính kèm tệp/liên kết cho nhiệm vụ; tạo và lưu ghi chú họp làm đầu vào biên bản AI. | Dữ liệu đúng quyền, theo dõi/quyết định từ nguồn thực | FR-08 | UC007 | [URD L0151](source/urd-extracted.txt) |
| US-09 | người có quyền dự án | Tìm kiếm, lọc, sắp xếp và phân trang nhiệm vụ theo người, trạng thái, sprint, hạn, ưu tiên và tình trạng trễ. | Dữ liệu đúng quyền, theo dõi/quyết định từ nguồn thực | FR-09 | UC008 | [URD L0152](source/urd-extracted.txt) |
| US-10 | người có quyền dự án | Bảng điều khiển tiến độ theo dự án và sprint. | Dữ liệu đúng quyền, theo dõi/quyết định từ nguồn thực | FR-10 | UC008 | [URD L0153](source/urd-extracted.txt) |
| US-11 | người có quyền dự án | Thống kê nhiệm vụ trễ và khối lượng công việc của từng thành viên. | Dữ liệu đúng quyền, theo dõi/quyết định từ nguồn thực | FR-11 | UC008 | [URD L0154](source/urd-extracted.txt) |
| US-12 | PM | Trưởng nhóm chọn dự án và khoảng tuần để AI tóm tắt tiến độ từ dữ liệu nhiệm vụ. | Dữ liệu đúng quyền, theo dõi/quyết định từ nguồn thực | FR-12 | UC009 | [URD L0155](source/urd-extracted.txt) |
| US-13 | PM/Member được cấp quyền | Trưởng nhóm hoặc Thành viên được phân quyền dùng ghi chú họp để AI tạo biên bản; được xem và chỉnh sửa bản nháp. | Dữ liệu đúng quyền, theo dõi/quyết định từ nguồn thực | FR-13 | UC010 | [URD L0156](source/urd-extracted.txt) |
| US-14 | PM | AI gợi ý 1-3 người phụ trách theo kỹ năng, mức sẵn sàng và tải công việc; Trưởng nhóm quyết định cuối cùng. | Dữ liệu đúng quyền, theo dõi/quyết định từ nguồn thực | FR-14 | UC011 | [URD L0157](source/urd-extracted.txt) |
| US-15 | Admin/PM | Lưu lịch sử yêu cầu/kết quả AI, phiên bản prompt, dữ liệu tham chiếu và trạng thái xác nhận. | Dữ liệu đúng quyền, theo dõi/quyết định từ nguồn thực | FR-15 | UC012 | [URD L0158](source/urd-extracted.txt) |
| US-16 | người liên quan | Thông báo trong ứng dụng về việc được giao, sắp đến hạn và thay đổi quan trọng. | Dữ liệu đúng quyền, theo dõi/quyết định từ nguồn thực | FR-16 | UC013 | [URD L0159](source/urd-extracted.txt) |
| US-17 | người liên quan | Gửi email cảnh báo đến người phụ trách khi nhiệm vụ bị trễ theo BR-02. | Dữ liệu đúng quyền, theo dõi/quyết định từ nguồn thực | FR-17 | UC013 | [URD L0160](source/urd-extracted.txt) |

Các story mở rộng C03–C06 giữ trong customer-requirement.md; không thay chữ yêu cầu gốc.
