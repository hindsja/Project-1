"""NVIDIA linked statements and FCFF valuation. USD millions except per share.

Input provenance and limitations: docs/project1-model-notes.md.
Historical lab scripts are preserved. This is the revised project engine.
"""
from copy import deepcopy
from math import isfinite
from lab11_nvda import BASE_INPUTS


def default_inputs():
    inputs = deepcopy(BASE_INPUTS)
    inputs.update(wacc=0.16, market_price=218.36, market_date='2026-09-10',
                  information_period='FY2026, ended 2026-01-25',
                  minimum_cash=10_000.0, marketable_securities=51_951.0,
                  operating_cash_reserve=10_605.0)
    inputs['opening']['cash'] = 10_605.0
    inputs['opening']['marketable_securities'] = 51_951.0
    return inputs


def validate_inputs(p):
    def finite(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)
    for key, value in p.items():
        if isinstance(value, dict):
            if any(not finite(v) for v in value.values()):
                raise ValueError(f'{key}: every numeric input must be finite.')
        elif not isinstance(value, str) and not finite(value):
            raise ValueError(f'{key}: input must be finite.')
    if not 0 < p['wacc'] < 1 or not -0.10 < p['terminal_growth'] < p['wacc']:
        raise ValueError('WACC must be positive and terminal growth must be below WACC.')
    if p['diluted_shares'] <= 0 or p['market_price'] <= 0:
        raise ValueError('Share count and market price must be positive.')
    if not 0 < p['gross_margin'] < 1 or not 0 <= p['tax_rate'] < 1:
        raise ValueError('Gross margin and tax rate must be valid fractions.')
    if p['capex_to_revenue'] < 0 or not 0 < p['inventory_days'] <= 365:
        raise ValueError('Capital spending must be nonnegative; inventory days must be in (0,365].')
    years = set(range(2027, 2032))
    for key in ['data_center_growth', 'other_revenue_growth', 'r_and_d_to_revenue',
                'sga_to_gross_profit', 'debt_repayment']:
        if set(p[key]) != years:
            raise ValueError(f'{key}: exactly FY2027-FY2031 are required.')
    for key in ['data_center_growth', 'other_revenue_growth']:
        if any(v <= -1 for v in p[key].values()):
            raise ValueError('Revenue growth must be above -100%.')
    for key in ['minimum_cash', 'operating_cash_reserve', 'annual_share_buyback',
                'annual_dividend', 'short_term_borrowing_limit', 'depreciation_to_opening_ppe']:
        if p[key] < 0:
            raise ValueError(f'{key} must be nonnegative.')
    if p['operating_cash_reserve'] > p['opening']['cash']:
        raise ValueError('Operating reserve cannot exceed opening cash.')
    if any(v < 0 for v in p['debt_repayment'].values()):
        raise ValueError('Debt repayments must be nonnegative.')


def balance_gap(row):
    return (row['cash'] + row['marketable_securities'] + row['inventory'] + row['ppe']
            + row['other_assets'] - row['term_debt'] - row['short_term_borrowing']
            - row['other_liabilities'] - row['equity'])


def statements(p):
    """Cash follows operating/investing/financing flows; no balance-sheet plug."""
    validate_inputs(p)
    prior = deepcopy(p['opening'])
    if abs(balance_gap(prior)) > 0.05:
        raise ValueError('Opening balance sheet does not reconcile.')
    rows = []
    for year in range(2027, 2032):
        dc = prior['data_center_revenue'] * (1 + p['data_center_growth'][year])
        other = prior['other_revenue'] * (1 + p['other_revenue_growth'][year])
        revenue = dc + other
        gross_profit = revenue * p['gross_margin']
        rd = revenue * p['r_and_d_to_revenue'][year]
        sga = gross_profit * p['sga_to_gross_profit'][year]
        depreciation = prior['ppe'] * p['depreciation_to_opening_ppe']
        # Gross margin and functional expenses already include depreciation.
        ebit = gross_profit - rd - sga
        interest = (prior['term_debt'] * p['term_debt_rate']
                    + prior['short_term_borrowing'] * p['short_term_borrowing_rate'])
        pretax = ebit - interest
        tax = max(pretax, 0) * p['tax_rate']
        ni = pretax - tax
        capex = revenue * p['capex_to_revenue']
        inventory = (revenue - gross_profit) * p['inventory_days'] / 365
        delta_inventory = inventory - prior['inventory']
        delta_other_wc = (revenue - prior['revenue']) * p['other_working_capital_to_revenue_change']
        cfo = ni + depreciation - delta_inventory - delta_other_wc
        repayment = min(prior['term_debt'], p['debt_repayment'][year])
        cfi = -capex
        cff_before_borrowing = -repayment - p['annual_share_buyback'] - p['annual_dividend']
        cash_before_borrowing = prior['cash'] + cfo + cfi + cff_before_borrowing
        if cash_before_borrowing < p['minimum_cash']:
            borrowing = min(p['short_term_borrowing_limit'] - prior['short_term_borrowing'],
                            p['minimum_cash'] - cash_before_borrowing)
        else:
            borrowing = -min(prior['short_term_borrowing'], cash_before_borrowing - p['minimum_cash'])
        cff = cff_before_borrowing + borrowing
        nopat = ebit - max(ebit, 0) * p['tax_rate']
        fcff = nopat + depreciation - capex - delta_inventory - delta_other_wc
        row = dict(year=year, data_center_revenue=dc, other_revenue=other, revenue=revenue,
                   gross_profit=gross_profit, research_and_development=rd, sga=sga,
                   depreciation=depreciation, operating_income=ebit, interest_expense=interest,
                   pretax_income=pretax, tax=tax, net_income=ni, nopat=nopat,
                   opening_cash=prior['cash'], cash=prior['cash'] + cfo + cfi + cff,
                   marketable_securities=prior['marketable_securities'], inventory=inventory,
                   ppe=prior['ppe'] + capex - depreciation,
                   other_assets=prior['other_assets'] + delta_other_wc,
                   term_debt=prior['term_debt'] - repayment,
                   short_term_borrowing=prior['short_term_borrowing'] + borrowing,
                   other_liabilities=prior['other_liabilities'],
                   equity=prior['equity'] + ni - p['annual_share_buyback'] - p['annual_dividend'],
                   inventory_change=delta_inventory, other_working_capital_change=delta_other_wc,
                   capex=capex, debt_repayment=repayment, borrowing=borrowing,
                   cfo=cfo, cfi=cfi, cff=cff, fcff=fcff)
        row['balance_gap'] = balance_gap(row)
        row['cash_flow_gap'] = row['cash'] - row['opening_cash'] - cfo - cfi - cff
        row['total_assets'] = sum(row[k] for k in ['cash', 'marketable_securities', 'inventory', 'ppe', 'other_assets'])
        row['total_liabilities_equity'] = sum(row[k] for k in ['term_debt', 'short_term_borrowing', 'other_liabilities', 'equity'])
        rows.append(row)
        prior = row
    check_statements(rows, p)
    return rows


def check_statements(rows, p):
    for row in rows:
        if any(not isfinite(value) for value in row.values()):
            raise ValueError('Nonfinite statement result.')
        if abs(balance_gap(row)) > 0.05:
            raise ValueError(f"FY{row['year']}: balance sheet failed.")
        if abs(row['cash'] - row['opening_cash'] - row['cfo'] - row['cfi'] - row['cff']) > 0.05:
            raise ValueError(f"FY{row['year']}: cash-flow reconciliation failed.")
        if row['cash'] < p['minimum_cash'] - 0.05 or row['ppe'] < 0:
            raise ValueError(f"FY{row['year']}: financing capacity or asset constraint failed.")


def dcf(cash_flows, wacc, growth, cash, debt, shares, securities=0, reserve=0):
    """Five end-of-year FCFFs, Gordon terminal value, then equity bridge."""
    values = [*cash_flows, wacc, growth, cash, debt, shares, securities, reserve]
    if any(not isinstance(x, (int, float)) or isinstance(x, bool) or not isfinite(x) for x in values):
        raise ValueError('DCF inputs must be finite numbers.')
    if len(cash_flows) != 5 or not 0 < wacc or not -1 < growth < wacc or shares <= 0:
        raise ValueError('DCF requires five flows, positive shares/WACC and growth below WACC.')
    if cash_flows[-1] <= 0:
        raise ValueError('A perpetually negative terminal FCFF needs a different terminal model.')
    explicit = sum(cf / (1 + wacc)**n for n, cf in enumerate(cash_flows, 1))
    terminal = cash_flows[-1] * (1 + growth) / (wacc - growth)
    pv_terminal = terminal / (1 + wacc)**5
    ev = explicit + pv_terminal
    excess_cash = cash + securities - reserve
    equity = ev + excess_cash - debt
    return dict(pv_explicit_fcff=explicit, terminal_value=terminal, pv_terminal=pv_terminal,
                enterprise_value=ev, cash_and_securities=cash + securities,
                operating_cash_reserve=reserve, excess_cash=excess_cash, debt=debt,
                equity_value=equity, diluted_shares=shares, value_per_share=equity / shares,
                terminal_value_share=pv_terminal / ev if ev else None)


def run(p=None):
    p = default_inputs() if p is None else deepcopy(p)
    rows = statements(p)
    valuation = dcf([r['fcff'] for r in rows], p['wacc'], p['terminal_growth'],
                    p['opening']['cash'], p['opening']['term_debt'], p['diluted_shares'],
                    securities=p['opening']['marketable_securities'], reserve=p['operating_cash_reserve'])
    return dict(inputs=p, statements=rows, valuation=valuation)


def cases():
    results = {}
    for label, shift, margin, capex, wacc in [
        ('Downside: slower demand, pricing pressure, heavier reinvestment', -.05, .70, .04, .17),
        ('Base: growth fades and margin stabilizes', 0, .725, .03, .16),
        ('Upside: stronger demand and operating leverage', .05, .75, .03, .15),
    ]:
        p = default_inputs()
        p['data_center_growth'] = {y: v + shift for y, v in p['data_center_growth'].items()}
        p.update(gross_margin=margin, capex_to_revenue=capex, wacc=wacc)
        results[label] = run(p)
    return results


def sensitivity():
    values = []
    for wacc in [.15, .16, .17]:
        for growth in [.02, .03, .04]:
            p = default_inputs()
            p.update(wacc=wacc, terminal_growth=growth)
            values.append(dict(wacc=wacc, terminal_growth=growth,
                               value_per_share=run(p)['valuation']['value_per_share']))
    return values


def reverse_dcf():
    """Solve Data Center growth shift; held-fixed assumptions stay explicit."""
    lo, hi = -.05, .50
    target = default_inputs()['market_price']
    def price(shift):
        p = default_inputs()
        p['data_center_growth'] = {y: v + shift for y, v in p['data_center_growth'].items()}
        return run(p)['valuation']['value_per_share']
    if not price(lo) <= target <= price(hi):
        return dict(status='No solution inside the tested growth-shift bracket', bounds=[lo, hi])
    for _ in range(80):
        mid = (lo + hi) / 2
        if price(mid) < target:
            lo = mid
        else:
            hi = mid
    shift = (lo + hi) / 2
    return dict(status='Solved conditional expectation, not a forecast', target_price=target,
                data_center_growth_shift=shift, solved_value=price(shift),
                implied_growth_path=[v + shift for v in default_inputs()['data_center_growth'].values()])
