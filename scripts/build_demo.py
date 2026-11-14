"""Build a static explorer from real DataGuard audits of synthetic fixtures."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dataguard import audit  # noqa: E402


def build():
    contract = json.loads((ROOT / 'examples/contract.json').read_text(encoding='utf-8'))
    examples = ROOT / 'examples'
    output = ROOT / 'docs'
    output.mkdir(exist_ok=True)
    reports = {}
    for key, filename in [('clean', 'current.csv'), ('invalid', 'invalid.csv')]:
        reports[key] = audit(examples / filename, contract, examples / 'baseline.csv')
        (output / f'{key}-report.json').write_text(
            json.dumps(reports[key], indent=2, allow_nan=False) + '\n', encoding='utf-8')
    template = (ROOT / 'scripts/demo_template.html').read_text(encoding='utf-8')
    # Keep fixture data inert even if a future synthetic column contains markup.
    payload = json.dumps(reports, allow_nan=False).replace('<', '\\u003c')
    (output / 'index.html').write_text(template.replace('/*REPORT_DATA*/{}', payload), encoding='utf-8')
    (output / '.nojekyll').touch()
    print('Built docs/index.html and two reports from synthetic fixtures.')


if __name__ == '__main__':
    build()
