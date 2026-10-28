"""Run acceptance tests on a newly created, disposable MySQL database.

Uses .env connection credentials, never the configured application DB as target.
Also validates repeatable migration, 10,000-task performance and JSON backup restore.
"""
import json
import hashlib
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import unittest
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ['SMTP_ENABLED']='false'
os.environ['DEADLINE_WORKER_ENABLED']='false'
os.environ['QA_TEST_ENGINE']='mysql'
os.environ['AI_PROVIDER']='deepseek'
os.environ['OPENAI_API_KEY']='your_openai_api_key'
os.environ['AI_CONFIG_SOURCE']='process'
os.environ['AI_LOCAL_FALLBACK_ENABLED']='false'
os.environ['LOCAL_AI_MODEL_ENABLED']='false'
from database import connection, init_db
import mysql.connector


def main():
    name='qa_repair_'+uuid4().hex[:12]
    original=connection.DB_NAME
    created=[]
    server=mysql.connector.connect(host=connection.DB_HOST,port=connection.DB_PORT,
        user=connection.DB_USER,password=connection.DB_PASSWORD,connect_timeout=5)
    cursor=server.cursor()
    checks=[]
    try:
        assert name != original and re.fullmatch(r'qa_repair_[a-f0-9]{12}',name)
        cursor.execute(f'CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
        created.append(name)
        connection.DB_NAME=init_db.DB_NAME=name
        connection.set_engine_mode('mysql')
        with tempfile.TemporaryDirectory() as directory:
            init_db.SQLITE_PATH=str(Path(directory)/'auxiliary.sqlite3')
            assert init_db.init_mysql(), 'Isolated MySQL initialization failed'
            from database.migrations import ensure_core_schema,ensure_ai_schema,ensure_account_approval_schema
            for _ in range(2):
                ensure_core_schema();ensure_ai_schema();ensure_account_approval_schema()
            checks.append({'name':'Fresh install and repeated migrations','passed':True})
            from tests.result_reporting import RecordedResult,write_results
            result=unittest.TextTestRunner(verbosity=2,resultclass=RecordedResult).run(unittest.defaultTestLoader.discover('tests',pattern='test_*.py'))
            write_results(result,'mysql')
            checks.append({'name':'MySQL regression suite','passed':result.wasSuccessful(),'tests':result.testsRun,
                           'failures':len(result.failures),'errors':len(result.errors)})
            # Explicit old-version fixture: remove only columns/tables created in this QA DB.
            # Full suite above validated current schema; separate legacy checks below use restore DB.
            from services.project_service import create_project
            from services.report_service import get_project_dashboard_metrics,get_member_workload_statistics
            from services.task_service import get_tasks_by_project
            ok,_,pid=create_project(2,'Performance fixture','10,000 tasks',project_code='QA-PERF',initial_member_ids=[3,4])
            assert ok
            conn,_=connection.get_db_connection()
            cur=conn.cursor()
            cur.executemany("""INSERT INTO tasks(project_id,task_code,title,reporter_id,assignee_id,status,progress_percent,estimated_hours)
                VALUES (%s,%s,%s,2,3,%s,%s,1)""",
                [(pid,f'PERF-{i}',f'Performance task {i}', 'done' if i%4==0 else 'todo',100 if i%4==0 else 0) for i in range(10000)])
            conn.commit();cur.close();conn.close()
            for label,operation in [('Task search/page',lambda:get_tasks_by_project(pid,keyword='Performance',limit=51)),
                                    ('Dashboard metrics',lambda:get_project_dashboard_metrics(pid)),
                                    ('Member workload',lambda:get_member_workload_statistics(pid))]:
                started=time.perf_counter();value=operation();elapsed=time.perf_counter()-started
                checks.append({'name':label,'task_count':10000,'seconds':round(elapsed,4),'passed':elapsed<=2})
            assert get_project_dashboard_metrics(pid)['total_tasks']==10000
            # Backup all fixture tables into JSON, then restore a separate empty QA database.
            conn,_=connection.get_db_connection();cur=conn.cursor()
            cur.execute('SHOW TABLES');tables=[row[0] for row in cur.fetchall()]
            snapshot=[]
            for table in tables:
                assert re.fullmatch(r'[A-Za-z0-9_]+',table)
                cur.execute(f'SHOW CREATE TABLE `{table}`');ddl=cur.fetchone()[1]
                cur.execute(f'SELECT * FROM `{table}` ORDER BY id');rows=cur.fetchall();columns=cur.column_names
                snapshot.append({'table':table,'ddl':ddl,'columns':columns,'rows':rows})
            cur.close();conn.close()
            backup_path=Path(directory)/'fixture_backup.json'
            backup_path.write_text(json.dumps(snapshot,ensure_ascii=False,default=str),encoding='utf-8')
            restore=name+'_restore'
            cursor.execute(f'CREATE DATABASE `{restore}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
            created.append(restore)
            cursor.execute(f'USE `{restore}`');cursor.execute('SET FOREIGN_KEY_CHECKS=0')
            restored=json.loads(backup_path.read_text(encoding='utf-8'))
            for item in restored:
                cursor.execute(item['ddl'])
            for item in restored:
                if item['rows']:
                    columns=','.join('`'+column+'`' for column in item['columns'])
                    placeholders=','.join(['%s']*len(item['columns']))
                    cursor.executemany(f"INSERT INTO `{item['table']}` ({columns}) VALUES ({placeholders})",item['rows'])
            cursor.execute('SET FOREIGN_KEY_CHECKS=1');server.commit()
            counts_match=True
            contents_match=True
            for item in restored:
                cursor.execute(f"SELECT COUNT(*) FROM `{item['table']}`")
                counts_match &= cursor.fetchone()[0] == len(item['rows'])
                cursor.execute(f"SELECT * FROM `{item['table']}` ORDER BY id")
                actual=json.dumps(cursor.fetchall(),ensure_ascii=False,default=str,separators=(',',':'))
                expected=json.dumps(item['rows'],ensure_ascii=False,separators=(',',':'))
                contents_match &= hashlib.sha256(actual.encode()).digest() == hashlib.sha256(expected.encode()).digest()
            cursor.execute('SELECT COUNT(*),SUM(status=\'done\') FROM tasks WHERE project_id=%s',(pid,))
            total,done=cursor.fetchone()
            checks.append({'name':'Backup and restore all fixture tables','passed':counts_match and contents_match and total==10000 and int(done)==2500,
                           'tables':len(restored),'all_rows_checksum_match':contents_match,'performance_tasks':total,'done':int(done)})
            # Simulate a previous deployment lacking the new fields. No app data is touched.
            cursor.execute('DROP TABLE email_deliveries');cursor.execute('DROP TABLE ai_draft_revisions')
            cursor.execute('ALTER TABLE ai_drafts DROP COLUMN version, DROP COLUMN validation_json')
            cursor.execute("SELECT CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS WHERE TABLE_SCHEMA=%s AND TABLE_NAME='tasks' AND CONSTRAINT_TYPE='CHECK'",(restore,))
            for (constraint,) in cursor.fetchall():
                assert re.fullmatch(r'[A-Za-z0-9_]+',constraint)
                cursor.execute(f'ALTER TABLE tasks DROP CHECK `{constraint}`')
            cursor.execute('ALTER TABLE tasks DROP COLUMN progress_percent')
            server.commit()
            connection.DB_NAME=restore
            ensure_core_schema();ensure_core_schema()
            cursor.execute('SELECT COUNT(*) FROM tasks WHERE project_id=%s AND status=\'done\' AND progress_percent=100',(pid,))
            migrated=cursor.fetchone()[0]
            checks.append({'name':'Upgrade legacy schema preserves rows/backfills Done','passed':migrated==2500,'backfilled':migrated})
        summary={'engine':'mysql','target':'disposable qa_repair database; application DB untouched','checks':checks,
                 'success':all(check['passed'] for check in checks)}
        output=ROOT/'scratch/qa_audit_2026_10_27/mysql_final_results.json'
        output.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
        (ROOT/'logstest/qa-system-checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(summary,ensure_ascii=False))
        return 0 if summary['success'] else 1
    finally:
        connection.DB_NAME=init_db.DB_NAME=original
        # Only drop exact names created in this process, after validating their prefix.
        cursor.execute('USE information_schema')
        for database_name in reversed(created):
            assert database_name != original and re.fullmatch(r'qa_repair_[a-f0-9]{12}(?:_restore)?',database_name)
            cursor.execute(f'DROP DATABASE `{database_name}`')
        cursor.close();server.close()


if __name__=='__main__':
    raise SystemExit(main())
