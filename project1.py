"""Run/export the Project 1 model, or serve its local driver panel."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
import io
import json
from pathlib import Path
import unittest
from urllib.parse import parse_qs, urlparse
import project1_model as model
from test_project1 import ModelChecks, source_check

ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / 'outputs'
LIMITATIONS = [
    'Working historical model, not a completed current investment recommendation.',
    'Market reference: September 10, 2026 close from Lab 08; not reverified in this revision.',
    'Opening statements: FY2026. Later FY2027 information is not incorporated.',
    'Five full annual end-of-period cash flows; no valuation-date stub-period adjustment. Timing must be aligned before relying on the range.',
    'WACC and operating ranges are inherited judgments; the market inputs supporting WACC require date-consistent verification.',
    'Diluted weighted-average shares are a fixed proxy, not a complete valuation-date dilution schedule.',
    'Working capital, stock compensation, intangible amortization, leases and other nonoperating claims remain simplified.',
    'Peer enterprise-value multiple and final normalization/assumption evidence remain incomplete.',
]


def table(headers, rows):
    return '<table><thead><tr>' + ''.join('<th>'+escape(str(x))+'</th>' for x in headers) + '</tr></thead><tbody>' + ''.join(
        '<tr>' + ''.join('<td>'+escape(str(x))+'</td>' for x in row) + '</tr>' for row in rows) + '</tbody></table>'


def render(result, bundle=None, error=None, interactive=False):
    p, v = result['inputs'], result['valuation']
    css = 'body{font:16px system-ui;margin:32px auto;max-width:1150px;padding:0 20px;color:#172d3a;background:#f4f7fa}section{background:white;padding:20px;margin:18px 0;border-radius:10px}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:8px;border-bottom:1px solid #ddd;text-align:right}td:first-child,th:first-child{text-align:left}h1,h2{color:#153e60}.warning{border-left:5px solid #b57413}.error{border-left:5px solid #b52323}.ok{color:#176535}label{display:inline-block;margin:10px}input{display:block;padding:8px;width:130px}button,a.button{padding:10px;background:#153e60;color:white;border:0;border-radius:4px}a{color:#175f97}.scroll{overflow:auto}'
    body = ('<h1>NVIDIA valuation workbench</h1>'
            '<p><strong>Committee action: WATCH / DEFER; do not initiate on the present evidence.</strong> '
            'Reconsider after updated filings and date-aligned market inputs support the downside case at the observed price. '
            'Materially weaker Data Center demand or margins would reinforce do not initiate.</p>'
            '<p>USD millions, except value per diluted share. Historical working model.</p>')
    if error:
        body += '<section class="error"><h2>FAIL — calculation refused</h2><p>'+escape(error)+'</p><a href="/">Reset to base</a></section>'
    if interactive:
        shift = (p['data_center_growth'][2027] - model.default_inputs()['data_center_growth'][2027])*100
        controls = [('growth_shift','Data Center growth shift (percentage points)',shift,-10,10,.5),
                    ('margin','Gross margin (%)',p['gross_margin']*100,65,80,.5),
                    ('wacc','WACC (%)',p['wacc']*100,10,25,.5),
                    ('growth','Terminal growth (%)',p['terminal_growth']*100,0,5,.25)]
        body += '<section><h2>Driver panel</h2><form action="/" method="get">'
        for name, label, value, low, high, step in controls:
            body += f'<label>{escape(label)}<input type="number" name="{name}" min="{low}" max="{high}" step="{step}" value="{value:.2f}" required></label>'
        body += '<button>Recalculate</button> <a href="/">Reset base</a></form><p>Bounds are exploration limits, not probability intervals. The assumption record must justify the final submitted limits.</p><a href="/?demo=broken">Demonstrate a broken cash reconciliation</a></section>'
    body += '<section><h2>Valuation and checks</h2>'
    body += table(['Measure','Result'],[
        ['Value per diluted share',f"${v['value_per_share']:,.2f}"],
        ['Enterprise value',f"{v['enterprise_value']:,.1f}"],
        ['Cash and marketable securities',f"{v['cash_and_securities']:,.1f}"],
        ['Less operating cash reserve',f"{v['operating_cash_reserve']:,.1f}"],
        ['Less debt',f"{v['debt']:,.1f}"],
        ['Equity value',f"{v['equity_value']:,.1f}"],
        ['Diluted share proxy (millions)',f"{v['diluted_shares']:,.1f}"],
        ['Terminal value / enterprise value',f"{v['terminal_value_share']:.1%}"],
        ['Historical market reference',f"${p['market_price']:.2f} on {p['market_date']}"],
    ])
    body += '<p class="ok">PASS: opening balance, all five balance sheets, cash reconciliation, and financing constraints.</p></section>'
    for title, fields in [
        ('Income statement', [('Data Center revenue','data_center_revenue'),('Other revenue','other_revenue'),('Revenue','revenue'),('Gross profit','gross_profit'),('R&D','research_and_development'),('SG&A','sga'),('Operating income','operating_income'),('Interest expense','interest_expense'),('Tax','tax'),('Net income','net_income')]),
        ('Balance sheet', [('Cash','cash'),('Marketable securities','marketable_securities'),('Inventory','inventory'),('PP&E','ppe'),('Other assets','other_assets'),('Total assets','total_assets'),('Term debt','term_debt'),('Short-term borrowing','short_term_borrowing'),('Other liabilities','other_liabilities'),('Equity','equity'),('Liabilities + equity','total_liabilities_equity'),('Balance gap','balance_gap')]),
        ('Cash flow and FCFF', [('Opening cash','opening_cash'),('Operating cash flow','cfo'),('Investing cash flow','cfi'),('Financing cash flow','cff'),('Closing cash','cash'),('Cash reconciliation gap','cash_flow_gap'),('After-tax operating income','nopat'),('Depreciation addback','depreciation'),('Capital spending','capex'),('Inventory change','inventory_change'),('Other working-capital change','other_working_capital_change'),('Free cash flow to firm','fcff')]),
    ]:
        body += '<section class="scroll"><h2>'+title+'</h2>'+table(['Item']+[f"FY{r['year']}E" for r in result['statements']],
                     [[label]+[f'{r[key]:,.1f}' for r in result['statements']] for label,key in fields])+'</section>'
    body += '<section><h2>Inputs</h2><pre>'+escape(json.dumps(p,indent=2))+'</pre></section>'
    if bundle:
        body += '<section><h2>Named cases</h2>'+table(['Case','Value/share'], [[label,f"${x['valuation']['value_per_share']:.2f}"] for label,x in bundle['cases'].items()])+'</section>'
        body += '<section><h2>WACC–growth sensitivity</h2>'+table(['WACC','Terminal growth','Value/share'], [[f"{x['wacc']:.1%}",f"{x['terminal_growth']:.1%}",f"${x['value_per_share']:.2f}"] for x in bundle['sensitivity']])+'</section>'
        body += '<section><h2>Market-implied expectation</h2><pre>'+escape(json.dumps(bundle['reverse_dcf'],indent=2))+'</pre><p>All inputs other than the Data Center growth path are held fixed; this is conditional model inference.</p></section>'
    body += '<section class="warning"><h2>Limits on interpretation</h2><ul>'+''.join('<li>'+escape(x)+'</li>' for x in LIMITATIONS)+'</ul></section>'
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NVIDIA valuation workbench</title><style>'+css+'</style><body>'+body+'</body></html>'


def build_bundle():
    return dict(generated_utc=datetime.now(timezone.utc).isoformat(),base=model.run(),
                cases=model.cases(),sensitivity=model.sensitivity(),reverse_dcf=model.reverse_dcf(),
                limitations=LIMITATIONS)


def export():
    OUTPUTS.mkdir(exist_ok=True)
    bundle = build_bundle()
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ModelChecks)
    result = unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    evidence = dict(executed_utc=datetime.now(timezone.utc).isoformat(), tests_run=result.testsRun,
                    all_passed=result.wasSuccessful(), test_log=stream.getvalue(), filing_check=source_check(),
                    limitations=LIMITATIONS,
                    known_answer_reference='dcf_old.py frozen Lab 05 inputs and lab06_nvda.md training grid; published upstream reference still needs confirmation')
    (OUTPUTS/'project1-validation.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    if not result.wasSuccessful():
        raise SystemExit(stream.getvalue())
    (OUTPUTS/'project1-results.json').write_text(json.dumps(bundle,indent=2),encoding='utf-8')
    (OUTPUTS/'project1-report.html').write_text(render(bundle['base'],bundle),encoding='utf-8')
    print('Saved outputs/project1-report.html, project1-results.json and project1-validation.json')
    print(f'{result.testsRun} model/source checks passed.')


def interactive_response(query):
    p = model.default_inputs()
    fields = {'growth_shift':(-10,10), 'margin':(65,80), 'wacc':(10,25), 'growth':(0,5)}
    values = {}
    try:
        for name,(low,high) in fields.items():
            if name in query:
                value = float(query[name][0])
                if not low <= value <= high:
                    raise ValueError(f'{name} must be between {low} and {high}.')
                values[name] = value
        if 'growth_shift' in values:
            p['data_center_growth'] = {y:g+values['growth_shift']/100 for y,g in p['data_center_growth'].items()}
        for name,key in [('margin','gross_margin'),('wacc','wacc'),('growth','terminal_growth')]:
            if name in values:
                p[key] = values[name]/100
        result = model.run(p)
        if query.get('demo') == ['broken']:
            broken = deepcopy(result['statements'])
            broken[0]['cash'] += 100
            model.check_statements(broken,p)
        return render(result,interactive=True),200
    except (ValueError, OverflowError) as error:
        return render(model.run(),error=str(error),interactive=True),400


def serve(port):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if urlparse(self.path).path != '/':
                self.send_error(404)
                return
            html,status = interactive_response(parse_qs(urlparse(self.path).query))
            data = html.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Length',str(len(data)))
            self.end_headers()
            self.wfile.write(data)
    print(f'Open http://127.0.0.1:{port} in a browser. Ctrl+C stops the local server.',flush=True)
    HTTPServer(('127.0.0.1',port),Handler).serve_forever()


def submission_check():
    required = ['submission/Research-Evolution.pdf','submission/Decision-Memo.pdf',
                'submission/Validation-and-AI-Use.pdf','submission/manifest.json',
                'README.md','project1.py','project1_model.py','test_project1.py',
                'requirements.txt','outputs/project1-report.html','outputs/project1-validation.json',
                'outputs/project1-cold-run.txt']
    missing = []
    for name in required:
        p = ROOT/name
        ok = p.is_file() and p.stat().st_size > 0
        if name.endswith('Decision-Memo.pdf'):
            ok = ok or (ROOT/'submission/Decision-Deck.pdf').is_file()
        print(('FOUND  ' if ok else 'MISSING')+' '+name)
        if not ok:
            missing.append(name)
    manifest = ROOT/'submission/manifest.json'
    if manifest.exists():
        data = json.loads(manifest.read_text(encoding='utf-8'))
        if not data.get('repository_url'):
            missing.append('manifest repository URL')
            print('MISSING manifest repository URL')
    print('File presence does not certify content, instructor access, or financial completeness.')
    return bool(missing)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serve',action='store_true')
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--check-submission',action='store_true')
    args = parser.parse_args()
    if args.check_submission:
        raise SystemExit(2 if submission_check() else 0)
    elif args.serve:
        serve(args.port)
    else:
        export()
