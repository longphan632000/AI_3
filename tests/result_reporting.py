"""Machine-readable evidence for the report; success is recorded only after assertions."""
import json
from pathlib import Path
import time
import unittest
from datetime import datetime, timezone, timedelta


class RecordedResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.records=[]
        self.started={}

    def startTest(self,test):
        self.started[test.id()]=time.perf_counter()
        super().startTest(test)

    def record(self,test,passed,error=None):
        method=getattr(test,'_testMethodName',test.id())
        evidence=getattr(test.__class__,'evidence',{}).get(method,{})
        self.records.append({'test':test.id(),'method':method,
            'description':test.shortDescription() or method,
            'result':'Thành công' if passed else 'Thất bại',
            'seconds':round(time.perf_counter()-self.started.get(test.id(),time.perf_counter()),4),
            'evidence':evidence, 'error':error})

    def addSuccess(self,test):
        self.record(test,True)
        super().addSuccess(test)

    def addFailure(self,test,err):
        self.record(test,False,self._exc_info_to_string(err,test))
        super().addFailure(test,err)

    def addError(self,test,err):
        self.record(test,False,self._exc_info_to_string(err,test))
        super().addError(test,err)


def write_results(result,engine):
    root=Path(__file__).resolve().parents[1]
    output=root/'docs'
    output.mkdir(exist_ok=True)
    payload={'engine':engine,'timestamp':datetime.now(timezone(timedelta(hours=7))).isoformat(),
             'tests_run':result.testsRun,'successful':result.wasSuccessful(),
             'passed':sum(row['result']=='Thành công' for row in result.records),
             'failed':sum(row['result']=='Thất bại' for row in result.records),
             'records':result.records}
    (output/f'qa-results-{engine}.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
