"""Restore known sample names only when their stored Vietnamese characters are damaged."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database.connection import query_db, execute_db, transaction
from services.audit_service import log_audit

SAMPLE_NAMES = {
    'admin': 'Quản trị viên Hệ thống',
    'leader_long': 'Phan Chân Long (Trưởng nhóm 33)',
    'member_my': 'Lưu Trà My (Thành viên 33)',
    'member_khanh': 'Lê Nam Khánh (Thành viên 33)',
    'locked_user': 'Tài khoản Bị Khóa Kiểm Thử',
}


def repair(apply=False):
    repaired = []
    with transaction():
        admin = query_db('SELECT id FROM users WHERE username=%s', ('admin',), one=True)
        for username, full_name in SAMPLE_NAMES.items():
            row = query_db('SELECT id,full_name FROM users WHERE username=%s', (username,), one=True)
            if not row or not any(char in row['full_name'] for char in ('?', '\ufffd')):
                continue
            if apply:
                execute_db('UPDATE users SET full_name=%s WHERE id=%s', (full_name, row['id']))
                assert query_db('SELECT full_name FROM users WHERE id=%s', (row['id'],), one=True)['full_name'] == full_name
                log_audit(admin['id'] if admin else None, 'REPAIR_SAMPLE_NAME', 'USER', row['id'],
                          {'username':username,'source':'README sample profile; restored UTF-8 name'})
            repaired.append(username)
    return repaired


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    print(('Repaired' if args.apply else 'Would repair')+': '+', '.join(repair(args.apply)))
