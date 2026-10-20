# NVIDIA corporate-finance project

Decision: whether an investment committee with no existing position should
initiate, watch/defer, or decline NVIDIA common stock. The working conclusion
remains watch/defer pending the unresolved evidence described below. This is
a historical course analysis, not a current trading recommendation.

## Run

Use Python 3.12. No third-party packages or credentials are required.

```powershell
python project1.py
python -m unittest test_project1 -v
python cold_run_project1.py
python project1.py --serve
```

For the driver panel, open `http://127.0.0.1:8765` after starting the server.
Change a driver and select Recalculate; Reset base restores the original case.
The failure demonstration deliberately alters a copied cash balance and shows
the check refusing it. It does not change stored inputs. Ctrl+C stops the server.

Open [the saved report](outputs/project1-report.html) directly to inspect the
inputs, statements, valuation bridge, scenarios and sensitivity without Python.

## Files and data flow

- `lab11_nvda.py`: preserved historical lab; supplies the original assumption dictionary.
- `project1_model.py`: revised statement engine, FCFF, DCF, bridge and scenarios.
- `project1.py`: run/export command, local driver panel, submission file checker.
- `test_project1.py`: financial invariants, refusal tests, known-answer checks and filing extraction.
- `cold_run_project1.py`: copies required inputs/code into a fresh environment and saves the actual run log.
- `nvda-20260125.html`: saved primary filing used by source checks.
- `docs/project1-model-notes.md`: definitions, changes and unresolved finance work.
- `outputs/project1-results.json`: exact numeric inputs and results.
- `outputs/project1-validation.json`: timestamped test output and source evidence.
- `PROJECT1-SUBMIT.md`: remaining submission instructions, kept outside the analytical deliverables.

Data flow: saved inputs -> three linked statements -> FCFF -> WACC/terminal DCF
-> enterprise/equity/share bridge -> scenario comparisons and visible output.
The legacy `dcf.py`, `proforma.py`, and Lab 10/11 valuation routines are not the
new project entry point. `proforma.py` is the ABG training case, not NVIDIA.

## Evidence and limitations

The opening financials are FY2026, ended January 25, 2026, from NVIDIA's
[Form 10-K](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm).
Market price is the September 10, 2026 close preserved in `lab08_nvda.md`;
discount-rate provenance is preserved in `lab06_nvda.md`. Those historical
market inputs were not refreshed in this revision. Prior documents retain
their original dates and outputs; the new report is a distinct revised model.

The valuation uses five full annual end-of-year periods. It has not been
aligned to the interim market observation with a stub-period calculation or
updated opening balance sheet. The dilution schedule, company-specific
normalization, current information boundary, enterprise-value peer multiple,
and complete assumption-challenge evidence still require completion. Do not
present the generated case range as a fully defended current fair-value range.

## Submission audit

```powershell
python project1.py --check-submission
```

Exit code 2 means required files/links are missing. A successful presence check
does not prove financial completeness or that instructors can access the links.
