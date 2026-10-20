"""Lab 11: one-at-a-time sensitivity for the NVIDIA Lab 10 pro-forma.

All monetary amounts are USD millions except per-share values. Every case
starts from a deep copy of BASE_INPUTS, changes one independent driver, and
reruns the full linked FY2027-FY2031 model. Run with: python lab11_nvda.py
"""

from copy import deepcopy


YEARS = list(range(2027, 2032))
TOLERANCE = 0.05

BASE_INPUTS = {
    "data_center_growth": dict(zip(YEARS, [0.35, 0.25, 0.18, 0.12, 0.08])),
    "other_revenue_growth": dict(zip(YEARS, [0.10, 0.10, 0.09, 0.08, 0.07])),
    "gross_margin": 0.725,
    "r_and_d_to_revenue": dict(zip(YEARS, [0.085, 0.083, 0.081, 0.080, 0.080])),
    "sga_to_gross_profit": dict(zip(YEARS, [0.030] * 5)),
    "depreciation_to_opening_ppe": 2_400.0 / 10_383.0,
    "capex_to_revenue": 0.030,
    "tax_rate": 0.150,
    "inventory_days": 120.0,
    "other_working_capital_to_revenue_change": 0.050,
    "minimum_liquidity": 40_000.0,
    "short_term_borrowing_limit": 25_000.0,
    "short_term_borrowing_rate": 0.050,
    "debt_repayment": {
        2027: 1_000.0,
        2028: 0.0,
        2029: 1_250.0,
        2030: 0.0,
        2031: 1_500.0,
    },
    "annual_share_buyback": 40_000.0,
    "annual_dividend": 1_000.0,
    "term_debt_rate": 259.0 / ((8_468.0 + 8_463.0) / 2.0),
    "cost_of_equity": 0.1593,
    "terminal_growth": 0.030,
    "diluted_shares": 24_514.0,
    "opening": {
        "data_center_revenue": 193_737.0,
        "other_revenue": 22_201.0,
        "revenue": 215_938.0,
        "inventory": 21_403.0,
        "ppe": 10_383.0,
        "other_assets": 112_461.0,
        "cash": 62_556.0,
        "term_debt": 8_468.0,
        "short_term_borrowing": 0.0,
        "other_liabilities": 41_042.0,
        "equity": 157_293.0,
    },
}

DATA_CENTER_CASES = {
    "Lower": dict(zip(YEARS, [0.30, 0.20, 0.13, 0.07, 0.03])),
    "Base": deepcopy(BASE_INPUTS["data_center_growth"]),
    "Higher": dict(zip(YEARS, [0.40, 0.30, 0.23, 0.17, 0.13])),
}

GROSS_MARGIN_CASES = {
    "Lower": 0.700,
    "Base": BASE_INPUTS["gross_margin"],
    "Higher": 0.750,
}

DRIVERS = [
    {
        "name": "Data Center revenue growth",
        "key": "data_center_growth",
        "units": "annual growth rate; five-year path",
        "affected_years": "FY2027-FY2031",
        "cases": DATA_CENTER_CASES,
        "reason": (
            "Judgment range: shift each Lab 10 annual rate by +/-5 percentage "
            "points while preserving the fading path."
        ),
    },
    {
        "name": "Gross margin",
        "key": "gross_margin",
        "units": "% of revenue",
        "affected_years": "FY2027-FY2031",
        "cases": GROSS_MARGIN_CASES,
        "reason": (
            "Judgment range: 70.0%-75.0% around the 72.5% base, informed by "
            "the 71.1%-75.0% FY2024-FY2026 reported range and the disclosed "
            "2.6-point FY2026 provision headwind."
        ),
    },
]


def project(inputs):
    """Run the linked income statement, balance sheet, and cash flow model."""
    inputs = deepcopy(inputs)
    projections = []
    prior = inputs["opening"].copy()

    for year in YEARS:
        data_center_revenue = prior["data_center_revenue"] * (
            1 + inputs["data_center_growth"][year]
        )
        other_revenue = prior["other_revenue"] * (
            1 + inputs["other_revenue_growth"][year]
        )
        revenue = data_center_revenue + other_revenue
        gross_profit = revenue * inputs["gross_margin"]
        research_and_development = revenue * inputs["r_and_d_to_revenue"][year]
        sga = gross_profit * inputs["sga_to_gross_profit"][year]
        depreciation = prior["ppe"] * inputs["depreciation_to_opening_ppe"]
        operating_income = (
            gross_profit - research_and_development - sga - depreciation
        )
        interest_expense = (
            prior["term_debt"] * inputs["term_debt_rate"]
            + prior["short_term_borrowing"]
            * inputs["short_term_borrowing_rate"]
        )
        pretax_income = operating_income - interest_expense
        tax = max(0.0, pretax_income) * inputs["tax_rate"]
        net_income = pretax_income - tax

        revenue_change = revenue - prior["revenue"]
        other_working_capital_change = (
            inputs["other_working_capital_to_revenue_change"] * revenue_change
        )
        inventory = (
            (revenue - gross_profit) * inputs["inventory_days"] / 365.0
        )
        capex = revenue * inputs["capex_to_revenue"]
        ppe = prior["ppe"] + capex - depreciation
        other_assets = prior["other_assets"] + other_working_capital_change
        debt_repayment = min(inputs["debt_repayment"][year], prior["term_debt"])
        term_debt = prior["term_debt"] - debt_repayment
        other_liabilities = prior["other_liabilities"]
        equity = (
            prior["equity"]
            + net_income
            - inputs["annual_share_buyback"]
            - inputs["annual_dividend"]
        )

        inventory_change = inventory - prior["inventory"]
        fcfe = (
            net_income
            + depreciation
            - capex
            - inventory_change
            - other_working_capital_change
            - debt_repayment
        )
        liquidity_before_borrowing = (
            prior["cash"]
            + fcfe
            - inputs["annual_share_buyback"]
            - inputs["annual_dividend"]
        )

        if liquidity_before_borrowing < inputs["minimum_liquidity"]:
            borrowing_draw = min(
                inputs["short_term_borrowing_limit"]
                - prior["short_term_borrowing"],
                inputs["minimum_liquidity"] - liquidity_before_borrowing,
            )
            short_term_borrowing = prior["short_term_borrowing"] + borrowing_draw
            cash = liquidity_before_borrowing + borrowing_draw
        else:
            borrowing_repayment = min(
                prior["short_term_borrowing"],
                liquidity_before_borrowing - inputs["minimum_liquidity"],
            )
            borrowing_draw = -borrowing_repayment
            short_term_borrowing = (
                prior["short_term_borrowing"] - borrowing_repayment
            )
            cash = liquidity_before_borrowing - borrowing_repayment

        total_assets = cash + inventory + ppe + other_assets
        total_liabilities_and_equity = (
            term_debt
            + short_term_borrowing
            + other_liabilities
            + equity
        )

        result = {
            "year": year,
            "data_center_growth": inputs["data_center_growth"][year],
            "gross_margin": inputs["gross_margin"],
            "data_center_revenue": data_center_revenue,
            "other_revenue": other_revenue,
            "revenue": revenue,
            "gross_profit": gross_profit,
            "research_and_development": research_and_development,
            "sga": sga,
            "depreciation": depreciation,
            "operating_income": operating_income,
            "interest_expense": interest_expense,
            "pretax_income": pretax_income,
            "tax": tax,
            "net_income": net_income,
            "cash": cash,
            "inventory": inventory,
            "ppe": ppe,
            "other_assets": other_assets,
            "total_assets": total_assets,
            "term_debt": term_debt,
            "short_term_borrowing": short_term_borrowing,
            "other_liabilities": other_liabilities,
            "equity": equity,
            "total_liabilities_and_equity": total_liabilities_and_equity,
            "inventory_change": inventory_change,
            "other_working_capital_change": other_working_capital_change,
            "capex": capex,
            "debt_repayment": debt_repayment,
            "share_buyback": inputs["annual_share_buyback"],
            "dividend": inputs["annual_dividend"],
            "borrowing_draw": borrowing_draw,
            "fcfe": fcfe,
        }
        projections.append(result)
        prior = {
            "data_center_revenue": data_center_revenue,
            "other_revenue": other_revenue,
            "revenue": revenue,
            "inventory": inventory,
            "ppe": ppe,
            "other_assets": other_assets,
            "cash": cash,
            "term_debt": term_debt,
            "short_term_borrowing": short_term_borrowing,
            "other_liabilities": other_liabilities,
            "equity": equity,
        }

    return projections


def recompute_balance_gap(item):
    assets = item["cash"] + item["inventory"] + item["ppe"] + item["other_assets"]
    liabilities_and_equity = (
        item["term_debt"]
        + item["short_term_borrowing"]
        + item["other_liabilities"]
        + item["equity"]
    )
    return assets - liabilities_and_equity


def validate_model(projections, inputs):
    """Refuse a case if any accounting or minimum-liquidity check fails."""
    for item in projections:
        gap = recompute_balance_gap(item)
        if abs(gap) > TOLERANCE:
            raise ValueError(
                f"FY{item['year']} balance check failed: gap = {gap:.1f}"
            )
        if item["cash"] < inputs["minimum_liquidity"]:
            raise ValueError(
                f"FY{item['year']} liquidity check failed: "
                f"{item['cash']:.1f} < {inputs['minimum_liquidity']:.1f}"
            )


def value_equity(projections, inputs):
    """Value the linked FCFE stream using the unchanged Lab 10 method."""
    if inputs["terminal_growth"] >= inputs["cost_of_equity"]:
        raise ValueError("Terminal growth must be below cost of equity")
    present_value_fcfe = sum(
        item["fcfe"] / (1 + inputs["cost_of_equity"]) ** period
        for period, item in enumerate(projections, start=1)
    )
    terminal_fcfe = projections[-1]["fcfe"] + projections[-1]["debt_repayment"]
    terminal_value = (
        terminal_fcfe
        * (1 + inputs["terminal_growth"])
        / (inputs["cost_of_equity"] - inputs["terminal_growth"])
    )
    present_value_terminal = terminal_value / (1 + inputs["cost_of_equity"]) ** 5
    equity_value = present_value_fcfe + present_value_terminal
    return {
        "equity_value": equity_value,
        "value_per_share": equity_value / inputs["diluted_shares"],
        "terminal_value_share": present_value_terminal / equity_value,
    }


def changed_independent_inputs(candidate):
    """Return top-level inputs that differ from the preserved base set."""
    return [key for key in BASE_INPUTS if candidate[key] != BASE_INPUTS[key]]


def run_case(driver_key, case_name, case_value):
    """Create a fresh base copy, change at most one driver, and run the model."""
    inputs = deepcopy(BASE_INPUTS)
    inputs[driver_key] = deepcopy(case_value)
    expected_changes = [] if case_name == "Base" else [driver_key]
    actual_changes = changed_independent_inputs(inputs)
    if actual_changes != expected_changes:
        return {
            "valid": False,
            "error": (
                f"independent-input check failed; expected {expected_changes}, "
                f"found {actual_changes}"
            ),
            "inputs": inputs,
            "changed_inputs": actual_changes,
        }

    try:
        projections = project(inputs)
        validate_model(projections, inputs)
        valuation = value_equity(projections, inputs)
    except ValueError as error:
        return {
            "valid": False,
            "error": str(error),
            "inputs": inputs,
            "changed_inputs": actual_changes,
            "projections": locals().get("projections"),
        }

    final_year = projections[-1]
    return {
        "valid": True,
        "error": "",
        "inputs": inputs,
        "changed_inputs": actual_changes,
        "projections": projections,
        "valuation": valuation,
        "operating_income": final_year["operating_income"],
        "fcfe": final_year["fcfe"],
        "value_per_share": valuation["value_per_share"],
        "max_abs_balance_gap": max(
            abs(recompute_balance_gap(item)) for item in projections
        ),
        "all_liquidity_checks_pass": all(
            item["cash"] >= inputs["minimum_liquidity"] for item in projections
        ),
    }


def run_plain_base():
    """Run an untouched base directly from a new independent copy."""
    inputs = deepcopy(BASE_INPUTS)
    projections = project(inputs)
    validate_model(projections, inputs)
    valuation = value_equity(projections, inputs)
    return {
        "inputs": inputs,
        "projections": projections,
        "operating_income": projections[-1]["operating_income"],
        "fcfe": projections[-1]["fcfe"],
        "value_per_share": valuation["value_per_share"],
    }


def format_input(value):
    if isinstance(value, dict):
        return ", ".join(f"FY{year} {value[year]:.1%}" for year in YEARS)
    return f"{value:.1%}"


def print_base(label, result):
    print(f"\n{label}")
    print("Inputs: preserved Lab 10 base input set")
    print(f"FY2031 operating income: ${result['operating_income']:,.1f} million")
    print(f"FY2031 FCFE: ${result['fcfe']:,.1f} million")
    print(f"Value per share: ${result['value_per_share']:,.2f}")


def print_driver_table(driver, results, base_before):
    print(f"\nDriver: {driver['name']}")
    print(f"Units: {driver['units']}; affected years: {driver['affected_years']}")
    print(f"Range reason: {driver['reason']}")
    for case_name, case_value in driver["cases"].items():
        print(f"  {case_name} actual input: {format_input(case_value)}")

    header = (
        f"{'Case':<8}{'FY2031 op. income':>21}{'Change':>15}"
        f"{'FY2031 FCFE':>18}{'Change':>15}"
        f"{'Value/share':>15}{'Change':>12}{'Status':>10}"
    )
    print(header)
    print("-" * len(header))
    for case_name in ("Lower", "Base", "Higher"):
        result = results[case_name]
        if not result["valid"]:
            print(f"{case_name:<8}{'unavailable':>21}{'':>15}{'':>18}{'':>15}"
                  f"{'':>15}{'':>12}{'INVALID':>10}")
            print(f"  Reason: {result['error']}")
            continue
        print(
            f"{case_name:<8}"
            f"{result['operating_income']:>21,.1f}"
            f"{result['operating_income'] - base_before['operating_income']:>+15,.1f}"
            f"{result['fcfe']:>18,.1f}"
            f"{result['fcfe'] - base_before['fcfe']:>+15,.1f}"
            f"{result['value_per_share']:>15,.2f}"
            f"{result['value_per_share'] - base_before['value_per_share']:>+12,.2f}"
            f"{'PASS':>10}"
        )

    if all(result["valid"] for result in results.values()):
        print("Output spans (maximum minus minimum across valid cases):")
        print(
            "  FY2031 operating income: "
            f"${max(r['operating_income'] for r in results.values()) - min(r['operating_income'] for r in results.values()):,.1f} million"
        )
        print(
            "  FY2031 FCFE: "
            f"${max(r['fcfe'] for r in results.values()) - min(r['fcfe'] for r in results.values()):,.1f} million"
        )
        print(
            "  Value per share: "
            f"${max(r['value_per_share'] for r in results.values()) - min(r['value_per_share'] for r in results.values()):,.2f}"
        )
    else:
        print("Ranking withheld because at least one run is invalid.")


def print_run_controls(all_results):
    print("\nPer-run controls")
    header = (
        f"{'Driver':<29}{'Case':<9}{'Changed independent input':<29}"
        f"{'Max balance gap':>18}{'Liquidity':>12}"
    )
    print(header)
    print("-" * len(header))
    for driver in DRIVERS:
        for case_name in ("Lower", "Base", "Higher"):
            result = all_results[driver["key"]][case_name]
            changed = ", ".join(result["changed_inputs"]) or "none"
            if result["valid"]:
                gap = f"{result['max_abs_balance_gap']:.1f}"
                liquidity = (
                    "PASS" if result["all_liquidity_checks_pass"] else "FAIL"
                )
            else:
                gap = "INVALID"
                liquidity = "INVALID"
            print(
                f"{driver['name']:<29}{case_name:<9}{changed:<29}"
                f"{gap:>18}{liquidity:>12}"
            )


def print_selected_trace(result):
    print("\nSelected trace: Higher Data Center growth case (USD millions)")
    header = (
        f"{'Year':<8}{'DC growth':>11}{'DC revenue':>15}{'Revenue':>14}"
        f"{'Gross profit':>15}{'Op. income':>15}{'Net income':>15}"
        f"{'Capex':>13}{'Inventory change':>19}{'Other WC change':>18}"
        f"{'FCFE':>15}{'Balance gap':>15}"
    )
    print(header)
    print("-" * len(header))
    for item in result["projections"]:
        print(
            f"FY{item['year']}E"
            f"{item['data_center_growth']:>11.1%}"
            f"{item['data_center_revenue']:>15,.1f}"
            f"{item['revenue']:>14,.1f}"
            f"{item['gross_profit']:>15,.1f}"
            f"{item['operating_income']:>15,.1f}"
            f"{item['net_income']:>15,.1f}"
            f"{item['capex']:>13,.1f}"
            f"{item['inventory_change']:>19,.1f}"
            f"{item['other_working_capital_change']:>18,.1f}"
            f"{item['fcfe']:>15,.1f}"
            f"{recompute_balance_gap(item):>15,.1f}"
        )


def main():
    base_before = run_plain_base()
    print("LAB 11 - NVIDIA ONE-AT-A-TIME PRO-FORMA SENSITIVITY")
    print("Monetary outputs are USD millions except value per share.")
    print_base("Base before sensitivity", base_before)

    lab10_targets = {
        "operating_income": 303_302.5,
        "fcfe": 244_585.5,
        "value_per_share": 62.97,
    }
    for key, target in lab10_targets.items():
        allowed = 0.01 if key == "value_per_share" else TOLERANCE
        if abs(base_before[key] - target) > allowed:
            raise AssertionError(
                f"Base does not reproduce Lab 10 {key}: "
                f"{base_before[key]:.4f} versus {target:.4f}"
            )

    all_results = {}
    for driver in DRIVERS:
        results = {
            case_name: run_case(driver["key"], case_name, case_value)
            for case_name, case_value in driver["cases"].items()
        }
        all_results[driver["key"]] = results
        print_driver_table(driver, results, base_before)

    print_run_controls(all_results)
    selected = all_results["data_center_growth"]["Higher"]
    if selected["valid"]:
        print_selected_trace(selected)

    base_after = run_plain_base()
    print_base("Restored base after sensitivity", base_after)
    input_match = base_after["inputs"] == base_before["inputs"] == BASE_INPUTS
    output_match = all(
        abs(base_after[key] - base_before[key]) <= 1e-9
        for key in ("operating_income", "fcfe", "value_per_share")
    )
    print("\nRestored-base check")
    print(f"Inputs exactly match first base: {'PASS' if input_match else 'FAIL'}")
    print(f"Outputs exactly match first base: {'PASS' if output_match else 'FAIL'}")
    if not input_match or not output_match:
        raise AssertionError("Restored base does not match the first base run")


if __name__ == "__main__":
    main()
