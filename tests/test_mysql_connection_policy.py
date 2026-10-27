import unittest
from unittest.mock import patch

import mysql.connector
from database import connection


class TestMySQLConnectionPolicy(unittest.TestCase):
    def test_mysql_failure_never_opens_sqlite(self):
        old_mode = connection._USE_MYSQL
        connection.set_engine_mode('mysql')
        try:
            with patch('database.connection.mysql.connector.connect',
                       side_effect=mysql.connector.Error(errno=2003)), \
                 patch('database.connection.sqlite3.connect') as sqlite_connect:
                with self.assertRaises(connection.DatabaseUnavailableError):
                    connection.get_db_connection()
                status = connection.get_database_status()
                self.assertEqual(status['engine'], 'mysql')
                self.assertEqual(status['status'], 'unavailable')
                sqlite_connect.assert_not_called()
        finally:
            connection._USE_MYSQL = old_mode
