"""Run original assertions unchanged with a documented functional wait budget."""
import runpy
import sys
from pathlib import Path
ROOT=Path(r'D:\UNG DUNG AL_NAM3\Code Chuan')
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scratch/qa_audit_2026_10_27/browser_deps'))
from playwright.sync_api import expect
expect.set_options(timeout=15000)
runpy.run_path(str(ROOT/'tests/browser_workspace.py'),run_name='__main__')
