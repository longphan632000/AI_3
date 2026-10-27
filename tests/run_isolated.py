"""Run the suite against a disposable SQLite database, never the app database."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ['DB_HOST'] = '127.0.0.2'
os.environ['GEMINI_API_KEY'] = ''
os.environ['KIRA_API_KEY'] = ''
os.environ['AI_PROVIDER'] = 'gemini'
os.environ['AI_CONFIG_SOURCE'] = 'process'
os.environ['SMTP_ENABLED'] = 'false'
os.environ['DEADLINE_WORKER_ENABLED'] = 'false'
os.environ['QA_TEST_ENGINE'] = 'sqlite'

from database import connection, init_db


def main():
    with tempfile.TemporaryDirectory() as directory:
        database_path = os.path.join(directory, 'test.sqlite3')
        connection._SQLITE_PATH = database_path
        connection.set_engine_mode('sqlite')
        init_db.SQLITE_PATH = database_path
        init_db.init_sqlite_fallback()
        suite = unittest.defaultTestLoader.discover('tests', pattern='test_*.py')
        from tests.result_reporting import RecordedResult, write_results
        result = unittest.TextTestRunner(verbosity=2, resultclass=RecordedResult).run(suite)
        write_results(result, 'sqlite')
        return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
