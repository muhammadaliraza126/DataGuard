"""Local CSV contracts, profiling and transparent distribution comparisons."""
import argparse
from collections import Counter
import csv
import html
import json
import math
from pathlib import Path
import statistics


def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.reader(stream, strict=True)
        header = next(reader, None)
        if not header or any(not x.strip() for x in header) or len(header) != len(set(header)):
            raise ValueError('CSV requires unique, nonblank column names.')
        rows = []
        for index, values in enumerate(reader, 2):
            if len(values) != len(header):
                raise ValueError(f'Record {index}: field count differs from header.')
            rows.append(dict(zip(header, values)))
        return header, rows


def number(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('Expected a finite number.')
    return result


def validate_contract(contract):
    if not isinstance(contract, dict) or set(contract) != {'columns'} or not isinstance(contract['columns'], dict) or not contract['columns']:
        raise ValueError('Contract must contain a nonempty columns object only.')
    allowed = {'type', 'required', 'unique', 'min', 'max', 'allowed'}
    for name, rule in contract['columns'].items():
        if not isinstance(rule, dict) or set(rule) - allowed:
            raise ValueError(f'Invalid rules for {name}.')
        if rule.get('type', 'string') not in ('string', 'number', 'integer'):
            raise ValueError(f'Unsupported type for {name}.')
        for key in ('required', 'unique'):
            if key in rule and not isinstance(rule[key], bool):
                raise ValueError(f'{key} must be boolean.')
        for key in ('min', 'max'):
            if key in rule:
                if rule.get('type') not in ('number', 'integer') or isinstance(rule[key], bool) or not isinstance(rule[key], (int, float)):
                    raise ValueError('Bounds require numeric types and numeric values.')
                number(rule[key])
        if rule.get('min', -math.inf) > rule.get('max', math.inf):
            raise ValueError('Minimum exceeds maximum.')
        if 'allowed' in rule and (not isinstance(rule['allowed'], list) or not all(isinstance(x, str) for x in rule['allowed'])):
            raise ValueError('allowed must be a list of exact string values.')
    return contract['columns']


def profile(header, rows):
    result = {}
    for name in header:
        values = [r[name] for r in rows if r[name].strip()]
        numeric = []
        for value in values:
            try:
                numeric.append(number(value))
            except ValueError:
                pass
        item = {'blank_count': len(rows) - len(values), 'distinct_nonblank': len(set(values)), 'numeric_count': len(numeric)}
        if numeric:
            item.update(min=min(numeric), max=max(numeric), mean=statistics.fmean(numeric))
        result[name] = item
    return result


def audit(path, contract, baseline=None):
    rules = validate_contract(contract)
    header, rows = read_csv(path)
    failures = []
    def add(column, check, count):
        if count:
            failures.append({'column': column, 'check': check, 'count': count})
    add(None, 'empty_dataset', int(not rows))
    add(None, 'duplicate_records', len(rows) - len({tuple(r.values()) for r in rows}))
    for name, rule in rules.items():
        if name not in header:
            add(name, 'missing_column', 1)
            continue
        values = [r[name] for r in rows]
        nonblank = [v for v in values if v.strip()]
        if rule.get('required', False):
            add(name, 'required', len(values) - len(nonblank))
        if rule.get('unique', False):
            add(name, 'unique', len(nonblank) - len(set(nonblank)))
        if 'allowed' in rule:
            add(name, 'allowed', sum(v not in rule['allowed'] for v in nonblank))
        invalid = low = high = 0
        if rule.get('type') in ('number', 'integer'):
            for value in nonblank:
                try:
                    n = number(value)
                    if rule['type'] == 'integer' and not n.is_integer():
                        raise ValueError('Expected integer.')
                    low += n < rule.get('min', -math.inf)
                    high += n > rule.get('max', math.inf)
                except ValueError:
                    invalid += 1
            add(name, 'type', invalid)
            add(name, 'min', low)
            add(name, 'max', high)
    report = {'version': '0.1.0', 'status': 'failed' if failures else 'passed', 'row_count': len(rows),
              'failures': failures, 'profile': profile(header, rows), 'comparison': None}
    if baseline:
        old_header, old = read_csv(baseline)
        changes = {'baseline_rows': len(old), 'added_columns': sorted(set(header)-set(old_header)),
                   'removed_columns': sorted(set(old_header)-set(header)), 'columns': {}}
        for name in sorted(set(header) & set(old_header)):
            current = [r[name] for r in rows]
            previous = [r[name] for r in old]
            item = {'blank_rate_change': None, 'total_variation': None, 'mean_change': None}
            if current and previous:
                item['blank_rate_change'] = sum(not v.strip() for v in current)/len(current)-sum(not v.strip() for v in previous)/len(previous)
                if rules.get(name, {}).get('type') in ('number', 'integer'):
                    a, b = [], []
                    for values, target in [(current, a), (previous, b)]:
                        for value in values:
                            try:
                                target.append(number(value))
                            except ValueError:
                                pass
                    item['valid_numeric_counts'] = {'current': len(a), 'baseline': len(b)}
                    if a and b:
                        item['mean_change'] = statistics.fmean(a) - statistics.fmean(b)
                else:
                    a, b = Counter(current), Counter(previous)
                    item['total_variation'] = sum(abs(a[k]/len(current)-b[k]/len(previous)) for k in a.keys() | b.keys())/2
            changes['columns'][name] = item
        report['comparison'] = changes
    return report


def render_html(report):
    encoded = html.escape(json.dumps(report, indent=2, allow_nan=False))
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>DataGuard report</title>
<style>body{font:16px system-ui;background:#101827;color:#e5edf8;max-width:1000px;margin:40px auto;padding:24px}h1{color:#5eead4}pre{background:#1e293b;padding:24px;border-radius:12px;white-space:pre-wrap;overflow-wrap:anywhere}p{line-height:1.6}</style>
<h1>DataGuard / Quality report</h1><p>Local validation and descriptive dataset comparison. Comparison values are not statistical significance tests. No source rows are included.</p><pre>''' + encoded + '</pre></html>'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--contract', type=Path, required=True)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True, help='New directory; existing directories are rejected')
    args = parser.parse_args()
    try:
        contract = json.loads(args.contract.read_text(encoding='utf-8'))
        report = audit(args.csv, contract, args.baseline)
        json_report = json.dumps(report, indent=2, allow_nan=False)
        html_report = render_html(report)
        args.output_dir.mkdir(parents=True, exist_ok=False)
        (args.output_dir/'report.json').write_text(json_report+'\n', encoding='utf-8')
        (args.output_dir/'report.html').write_text(html_report, encoding='utf-8')
        print(json_report)
        return 1 if report['status'] == 'failed' else 0
    except (OSError, ValueError, csv.Error, OverflowError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    raise SystemExit(main())
