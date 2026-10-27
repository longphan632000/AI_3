import os
import sys
import mysql.connector

# Ensure UTF-8 output on Windows
if sys.stdout and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def main():
    print("=" * 65)
    print("  TIỆN ÍCH THIẾT LẬP VÀ LIÊN KẾT CƠ SỞ DỮ LIỆU MYSQL CHO DỰ ÁN 33")
    print("=" * 65)

    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = input(">> Vui lòng nhập mật khẩu tài khoản 'root' của MySQL Server: ").strip()

    host = '127.0.0.1'
    port = 3306
    user = 'root'
    db_name = 'ai_project_management'

    print(f"\n[*] Đang kiểm tra kết nối tới MySQL Server ({host}:{port}) với user '{user}'...")

    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            connect_timeout=5
        )
        if conn.is_connected():
            print(" [OK] Kết nối MySQL thành công!")
            conn.close()
    except Exception as e:
        print(f" [THẤT BẠI] Không thể kết nối với mật khẩu đã nhập: {e}")
        print("  -> Vui lòng kiểm tra lại mật khẩu MySQL Workbench hoặc Laragon/XAMPP của bạn.")
        sys.exit(1)

    # Cập nhật file .env
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    print(f"\n[*] Đang cập nhật tệp cấu hình: {env_path}...")

    env_lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            env_lines = f.readlines()

    new_lines = []
    found_pass = False
    for line in env_lines:
        if line.startswith('DB_PASSWORD='):
            new_lines.append(f"DB_PASSWORD={password}\n")
            found_pass = True
        else:
            new_lines.append(line)

    if not found_pass:
        new_lines.append(f"DB_PASSWORD={password}\n")

    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(" [OK] Đã ghi nhận DB_PASSWORD vào .env thành công.")

    # Chạy khởi tạo database và nạp dữ liệu mẫu
    print(f"\n[*] Đang khởi tạo CSDL '{db_name}' và nạp 13 bảng chuẩn 3NF...")
    from database.init_db import init_mysql
    # Cập nhật biến môi trường trực tiếp trong tiến trình
    os.environ['DB_PASSWORD'] = password
    
    success = init_mysql()
    if success:
        print("\n" + "=" * 65)
        print("  CHÚC MỪNG! HỆ THỐNG ĐÃ LIÊN KẾT 100% VỚI MYSQL THÀNH CÔNG!")
        print(f"  Database Name: {db_name}")
        print("  Tất cả các thao tác Kanban, Sprint, Nhiệm vụ giờ đây sẽ lưu")
        print("  trực tiếp và vĩnh viễn vào MySQL của bạn.")
        print("=" * 65 + "\n")
    else:
        print(" [!] Có lỗi xảy ra khi khởi tạo bảng MySQL. Vui lòng kiểm tra log bên trên.")

if __name__ == '__main__':
    main()
