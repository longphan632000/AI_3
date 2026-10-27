import os
import sys
import sqlite3
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import logging
import mysql.connector
from dotenv import load_dotenv

if sys.stdout and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', '3306'))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'ai_project_management')

_USE_MYSQL = True
_TRANSACTION = ContextVar('database_transaction', default=None)
_SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'fallback_database.sqlite3')


class DatabaseUnavailableError(RuntimeError):
    """The configured MySQL database cannot be reached."""

def reload_db_config():
    """Tải lại biến môi trường từ .env."""
    global DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, _USE_MYSQL
    load_dotenv(override=True)
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'ai_project_management')
    _USE_MYSQL = True

def test_mysql_connection():
    """Kiểm tra đúng database MySQL mà ứng dụng sẽ dùng."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connect_timeout=2
        )
        if conn.is_connected():
            conn.close()
            return True, "Kết nối MySQL thành công."
    except mysql.connector.Error as error:
        return False, f"Không kết nối được MySQL (mã {error.errno})."
    return False, "Không thể kết nối MySQL."

def get_database_status():
    """Kiểm tra và trả về trạng thái chi tiết của CSDL đang sử dụng."""
    if not _USE_MYSQL:
        return {'engine': 'sqlite', 'status': 'test_only', 'label': 'SQLite kiểm thử'}
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connect_timeout=2
        )
        if conn.is_connected():
            conn.close()
            return {
                'engine': 'mysql',
                'database': DB_NAME,
                'host': f"{DB_HOST}:{DB_PORT}",
                'user': DB_USER,
                'status': 'connected',
                'label': f'MySQL 8.0 ({DB_NAME})'
            }
    except mysql.connector.Error as error:
        return {
            'engine': 'mysql',
            'database': DB_NAME,
            'status': 'unavailable',
            'error': f"Không kết nối được MySQL (mã {error.errno}).",
            'label': 'MySQL không khả dụng'
        }

def get_db_connection():
    """
    Trả về MySQL cho ứng dụng. SQLite chỉ được dùng khi bộ kiểm thử bật rõ ràng.
    """
    if _USE_MYSQL:
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci',
                connect_timeout=2
            )
            return conn, 'mysql'
        except mysql.connector.Error as error:
            raise DatabaseUnavailableError(
                f"Không kết nối được MySQL (mã {error.errno}); thao tác chưa được lưu."
            ) from error
    
    # SQLite Fallback
    conn = sqlite3.connect(_SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn, 'sqlite'


@contextmanager
def transaction():
    """One connection/commit per business action; nested services join it."""
    if _TRANSACTION.get() is not None:
        yield
        return
    conn, engine = get_db_connection()
    state = {'connection': conn, 'engine': engine, 'callbacks': []}
    token = _TRANSACTION.set(state)
    committed = False
    try:
        if engine == 'mysql':
            conn.start_transaction()
        else:
            conn.execute('BEGIN IMMEDIATE')
        yield
        conn.commit()
        committed = True
    except BaseException:
        conn.rollback()
        raise
    finally:
        _TRANSACTION.reset(token)
        conn.close()
    if committed:
        for callback in state['callbacks']:
            try:
                callback()
            except Exception:
                logging.getLogger(__name__).exception('Post-commit action failed')


def atomic(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        with transaction():
            return function(*args, **kwargs)
    return wrapped


def after_commit(callback):
    state = _TRANSACTION.get()
    if state is None:
        callback()
    else:
        state['callbacks'].append(callback)


def _run(query, args, fetch=False, one=False, commit=True):
    state = _TRANSACTION.get()
    conn, engine = ((state['connection'], state['engine']) if state else get_db_connection())
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True) if engine == 'mysql' else conn.cursor()
        cursor.execute(query if engine == 'mysql' else query.replace('%s', '?'), args)
        if fetch:
            rows = cursor.fetchall()
            rows = rows if engine == 'mysql' else [dict(row) for row in rows]
            return (rows[0] if rows else None) if one else rows
        if not state and commit:
            conn.commit()
        is_insert = query.lstrip().upper().startswith(('INSERT', 'REPLACE'))
        return cursor.lastrowid if is_insert and cursor.lastrowid else cursor.rowcount
    except Exception:
        if not state:
            conn.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if not state:
            conn.close()


def query_db(query, args=(), one=False):
    return _run(query, args, fetch=True, one=one)


def execute_db(query, args=(), commit=True):
    return _run(query, args, commit=commit)


def set_engine_mode(mode='mysql'):
    global _USE_MYSQL
    _USE_MYSQL = (mode == 'mysql')
