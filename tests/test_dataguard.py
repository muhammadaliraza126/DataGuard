import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from dataguard import audit, render_html, validate_contract

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = {'columns': {'id': {'required': True, 'unique': True}, 'amount': {'type': 'number', 'required': True, 'min': 0}, 'kind': {'allowed': ['A', 'B']}}}

class DataGuardTests(unittest.TestCase):
    def run_audit(self, text, baseline=None):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'current.csv'
            p.write_text(text)
            b = Path(tmp)/'baseline.csv'
            if baseline is not None:
                b.write_text(baseline)
            return audit(p, CONTRACT, b if baseline is not None else None)

    def test_clean(self):
        r = self.run_audit('id,amount,kind\n1,10,A\n2,20,B\n')
        self.assertEqual(r['status'], 'passed')
        self.assertEqual(r['profile']['amount']['mean'], 15)

    def test_failures(self):
        r = self.run_audit('id,amount,kind\n1,-1,A\n1,NaN,C\n, ,B\n')
        checks = {(x['column'],x['check']):x['count'] for x in r['failures']}
        self.assertEqual(checks[('id','unique')],1)
        self.assertEqual(checks[('amount','min')],1)
        self.assertEqual(checks[('amount','type')],1)
        self.assertEqual(checks[('amount','required')],1)
        self.assertEqual(checks[('kind','allowed')],1)

    def test_known_comparison(self):
        r = self.run_audit('id,amount,kind\n1,20,B\n2,30,B\n','id,amount,kind\n1,10,A\n2,20,A\n')
        self.assertEqual(r['comparison']['columns']['kind']['total_variation'],1)
        self.assertEqual(r['comparison']['columns']['amount']['mean_change'],10)

    def test_identical_comparison(self):
        text='id,amount,kind\n1,10,A\n'
        r=self.run_audit(text,text)
        self.assertEqual(r['comparison']['columns']['kind']['total_variation'],0)
        self.assertEqual(r['comparison']['columns']['amount']['mean_change'],0)

    def test_empty_and_missing(self):
        r=self.run_audit('id\n')
        self.assertEqual(r['status'],'failed')
        self.assertTrue(any(x['check']=='missing_column' for x in r['failures']))

    def test_malformed_csv(self):
        for text in ['a,a\n1,2\n','id,amount,kind\n1,2\n','id,amount,kind\n"unclosed\n']:
            with self.subTest(text=text), self.assertRaises((ValueError, __import__('csv').Error)):
                self.run_audit(text)

    def test_contract_rejects_typos(self):
        for c in [{}, {'columns':{'a':{'minimum':0}}}, {'columns':{'a':{'required':'yes'}}}, {'columns':{'a':{'type':'number','min':2,'max':1}}}]:
            with self.subTest(contract=c), self.assertRaises(ValueError):
                validate_contract(c)

    def test_html_escapes_content(self):
        rendered=render_html({'column':'<script>alert(1)</script>'})
        self.assertNotIn('<script>', rendered)
        self.assertIn('&lt;script&gt;', rendered)

    def test_cli_and_overwrite_protection(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'result'
            command=[sys.executable,str(ROOT/'dataguard.py'),str(ROOT/'examples/current.csv'),'--contract',str(ROOT/'examples/contract.json'),'--baseline',str(ROOT/'examples/baseline.csv'),'--output-dir',str(output)]
            result=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout),json.loads((output/'report.json').read_text()))
            self.assertTrue((output/'report.html').exists())
            before=(output/'report.json').read_bytes()
            again=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(again.returncode,2)
            self.assertEqual((output/'report.json').read_bytes(),before)

if __name__=='__main__':
    unittest.main()
