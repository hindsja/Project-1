"""Reproducible checks for the revised model; no third-party packages."""
from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import json
import re
import unittest
import project1_model as m

ROOT = Path(__file__).resolve().parent

class FilingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current = None
        self.facts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'ix:nonfraction':
            self.current = dict(attrs)
            self.current['text'] = ''

    def handle_data(self, text):
        if self.current is not None:
            self.current['text'] += text

    def handle_endtag(self, tag):
        if tag.lower() == 'ix:nonfraction' and self.current is not None:
            self.facts.append(self.current)
            self.current = None


def source_check():
    path = ROOT / 'nvda-20260125.html'
    try:
        raw = path.read_text(encoding='utf-8')
        encoding = 'utf-8'
    except UnicodeDecodeError:
        raw = path.read_text(encoding='cp1252')
        encoding = 'cp1252 (saved filing encoding)'
    contexts = {}
    for context in re.findall(r'<(?:\w+:)?context\b.*?</(?:\w+:)?context>', raw, flags=re.S | re.I):
        identifier = re.search(r'\bid="([^"]+)"', context)
        if identifier and '2026-01-25' in context and 'explicitMember' not in context and 'typedMember' not in context:
            contexts[identifier.group(1)] = context
    parser = FilingParser()
    parser.feed(raw)
    checks = []
    expected = {
        'CashAndCashEquivalentsAtCarryingValue': 10605,
        'InventoryNet': 21403,
        'PropertyPlantAndEquipmentNet': 10383,
        'Assets': 206803,
        'Liabilities': 49510,
        'StockholdersEquity': 157293,
        'WeightedAverageNumberOfDilutedSharesOutstanding': 24514,
    }
    for concept, amount in expected.items():
        found = []
        for f in parser.facts:
            if f.get('name', '').split(':')[-1] != concept or f.get('contextref') not in contexts:
                continue
            try:
                value = float(f['text'].replace(',', '').replace('$', '').strip())
                value *= 10 ** int(f.get('scale', '0')) / 1_000_000
                if f.get('sign') == '-':
                    value *= -1
                found.append(value)
            except ValueError:
                continue
        ok = any(abs(v - amount) < .0001 for v in found)
        checks.append(dict(concept=concept, expected_millions=amount,
                           filing_values_millions=sorted(set(found)), passed=ok))
    return dict(source='NVIDIA FY2026 Form 10-K; local saved filing',
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                method='Independent extraction of consolidated inline-XBRL facts',
                decoding=encoding, checks=checks)


class ModelChecks(unittest.TestCase):
    def test_training_case(self):
        # Frozen Lab 05 inputs in dcf_old.py; rounded answer in Lab 06 training grid.
        cf, flows = 100., []
        for growth in [.08, .06, .05, .04, .03]:
            cf *= 1 + growth
            flows.append(cf)
        value = m.dcf(flows, .10, .03, 50, 300, 50)
        self.assertEqual(round(value['value_per_share'], 2), 27.50)

    def test_synthetic_answer(self):
        # Five 100 flows plus a zero-growth perpetuity at 10% equals EV=1000.
        value = m.dcf([100] * 5, .10, 0, 50, 200, 10)
        self.assertAlmostEqual(value['enterprise_value'], 1000)
        self.assertAlmostEqual(value['value_per_share'], 85)

    def test_statement_articulation_and_bridge(self):
        result = m.run()
        for row in result['statements']:
            self.assertAlmostEqual(m.balance_gap(row), 0, places=6)
            self.assertAlmostEqual(row['cash_flow_gap'], 0, places=6)
            # Cross-check FCFF against CFO plus the effective interest tax adjustment.
            tax_adjustment = max(row['operating_income'], 0)*.15 - row['tax']
            cross_fcff = row['cfo'] + row['interest_expense'] - tax_adjustment - row['capex']
            self.assertAlmostEqual(row['fcff'], cross_fcff, places=6)
        v = result['valuation']
        self.assertAlmostEqual(v['equity_value'], v['enterprise_value'] + v['excess_cash'] - v['debt'])
        self.assertAlmostEqual(v['equity_value'] / v['diluted_shares'], v['value_per_share'])

    def test_monotonicity(self):
        base = m.run()['valuation']['value_per_share']
        p = m.default_inputs()
        p['wacc'] += .01
        self.assertLess(m.run(p)['valuation']['value_per_share'], base)
        p = m.default_inputs()
        p['terminal_growth'] += .01
        self.assertGreater(m.run(p)['valuation']['value_per_share'], base)

    def test_bad_values_refused(self):
        for key, value in [('wacc', float('nan')), ('diluted_shares', 0),
                           ('terminal_growth', .16), ('gross_margin', 1.1)]:
            p = m.default_inputs()
            p[key] = value
            with self.assertRaises(ValueError):
                m.run(p)

    def test_tampered_cash_refused(self):
        p = m.default_inputs()
        rows = m.statements(p)
        rows[0]['cash'] += 100
        with self.assertRaises(ValueError):
            m.check_statements(rows, p)

    def test_failed_financing_refused(self):
        p = m.default_inputs()
        p['annual_share_buyback'] = 1e9
        with self.assertRaises(ValueError):
            m.run(p)

    def test_restore_base_and_reverse(self):
        p = m.default_inputs()
        before = deepcopy(p)
        first = m.run(p)
        m.cases()
        self.assertEqual(p, before)
        self.assertEqual(first, m.run(p))
        reverse = m.reverse_dcf()
        if 'solved_value' in reverse:
            self.assertAlmostEqual(reverse['solved_value'], p['market_price'], places=6)

    def test_filing_inputs(self):
        evidence = source_check()
        for item in evidence['checks']:
            self.assertTrue(item['passed'], item)

    def test_driver_panel_and_failure_recovery(self):
        from project1 import interactive_response
        html, status = interactive_response({})
        self.assertEqual(status, 200)
        self.assertIn('Driver panel', html)
        changed, status = interactive_response({'growth_shift':['5']})
        self.assertEqual(status, 200)
        self.assertNotEqual(changed, html)
        broken, status = interactive_response({'demo':['broken']})
        self.assertEqual(status, 400)
        self.assertIn('FAIL', broken)
        self.assertEqual(interactive_response({}), (html, 200))
        self.assertEqual(interactive_response({'wacc':['nan']})[1], 400)
        self.assertEqual(interactive_response({'margin':['99']})[1], 400)


if __name__ == '__main__':
    unittest.main(verbosity=2)
