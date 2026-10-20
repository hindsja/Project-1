# Validation and AI-use record

**Prepared October 19, 2026. Target: NVIDIA common equity. Decision: watch/defer.** Financial amounts are USD millions unless otherwise stated. This record distinguishes the revised project's executed checks from the preserved Lab 11 exercise.

## 1. Evidence boundary and reproduced result

The accounting base is FY2026, ended January 25, 2026; the price reference is $218.36 on September 10, 2026, inherited from Lab 08. This is not a newly verified current price. WACC of 16% and terminal growth of 3% are assumptions with the historical derivation in Lab 06. Annual diluted weighted-average shares are a proxy, not a fully reconciled valuation-date share count.

The saved revised output has a **$66.22 base**, **$50.27-$87.17 combined-case range**, and **60.5% terminal-value share**. `outputs/project1-results.json` records exact inputs and results. `outputs/project1-report.html` makes them visible without execution.

## 2. Executed validation

The suite contains **10 test methods**, several with multiple assertions. All passed in the saved normal run and the fresh-environment run. The exact saved normal-run timestamp is `2026-10-19T00:10:57.045873+00:00`. Assertions below summarize actual checks; no student-performed execution is asserted.

| Check | Evidence / expected behavior | Result |
|---|---|---|
| Synthetic known answer | FCFF 100 annually; WACC 10%; g=0; EV=1000; equity/share=85. | PASS |
| Preserved course case | Lab 05 inputs reproduce the saved Lab 06 rounded $27.50 answer. | PASS; upstream reference still to be attached |
| Statements and FCFF | Five balance sheets balance; cash flows tie; FCFF reconciles to operating cash flow plus interest tax adjustment. | PASS |
| Enterprise/equity bridge | Equity = enterprise value + excess cash - debt; divide by share proxy. | PASS |
| DCF direction | WACC +1 percentage point reduces value; terminal growth +1 point increases value, other inputs held fixed. | PASS |
| Input domains | Nonfinite WACC, zero shares, terminal growth >= WACC and invalid margin are rejected. | PASS |
| Broken cash / financing | Cash altered by 100 is rejected; excessive buybacks exceeding financing capacity are rejected. | PASS |
| Reset and reverse DCF | Base inputs/results remain unchanged after cases; reverse result reconciles to target. | PASS |
| Filing extraction | Seven consolidated inline-XBRL inputs match the source, including cash, assets and diluted shares. | PASS |
| Driver panel | Change driver, reject invalid/broken inputs, and reset to identical base. | PASS |

The directional expectations are specified in the tests before the run. They are automated validation evidence and do not create a new historical locked prediction. The synthetic reconciliation is independently calculable: a perpetuity of 100 at 10% is worth 1000; (1000 + 50 - 200) / 10 = 85. The course-case check uses the frozen local `dcf_old.py` and the published-answer values preserved in `lab06_nvda.md`; the original upstream answer locator remains an evidence gap.

<!-- PAGEBREAK -->

## 3. Independent source and definition checks

The source extractor reads consolidated contexts in the saved NVIDIA 10-K and checks these figures. Cash/asset values are USD millions; diluted shares are millions of shares. The filing is decoded explicitly as Windows-1252 because the saved file is not valid UTF-8.

| Filing concept | Expected amount | Result |
|---|---:|---|
| CashAndCashEquivalentsAtCarryingValue | 10,605 | Match |
| InventoryNet | 21,403 | Match |
| PropertyPlantAndEquipmentNet | 10,383 | Match |
| Assets | 206,803 | Match |
| Liabilities | 49,510 | Match |
| StockholdersEquity | 157,293 | Match |
| WeightedAverageNumberOfDilutedSharesOutstanding | 24,514 | Match |

Source: NVIDIA FY2026 [Form 10-K](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm). SHA-256: `6289b57a75407d5eb41993aecb604918356f66f6f3254194e11408db054ad3d9`. These checks validate the named inputs, not every market fact or forecast assumption.

The additional operating-income identity is **153,463 gross profit - 18,497 R&D - 4,579 SG&A = 130,387 operating income**. It demonstrates why the functional-expense forecast must not subtract depreciation again. `outputs/project1-operating-income-check.json` records the source concepts and arithmetic.

## 4. Material output disposition

**Tool: Codex. Disposition: correct the earlier depreciation treatment; adopt the revised FCFF architecture subject to the stated limitations.** The correction uses the filing identity above and the independent cash-flow/accounting invariants. The analyst confirmed adoption of the prior analytical decisions on October 19, 2026. Adoption is a judgment decision; it does not change who performed a historical check or supply missing historical evidence.

Material work in the project revision comprised code inspection, model integration, automated checks, documentation and PDF preparation. A precise underlying model/version was not established in the saved local record. The correction improves internal financial consistency but does not independently substantiate growth, margin, WACC or terminal assumptions.

<!-- PAGEBREAK -->

## 5. Failure tests and cold run

The key technical risk is a plausible-looking valuation built from inconsistent statements or the wrong cash-flow/discount-rate combination. The revised engine derives FCFF from operating forecasts and uses WACC. Deliberately altering a copied cash balance by 100 causes the balance check to refuse valuation. A separate financing stress exceeds borrowing capacity and also fails.

`cold_run_project1.py` copies the required files into a fresh directory, creates a new Python environment without system packages, and runs the tests and report generation. The saved cold run is **PASS**, using Python 3.12.13, with both test execution and export exiting successfully. Exact commands, output, timestamp and source hashes are in `outputs/project1-cold-run.txt`. This is recorded execution evidence, not a claim that repository permissions were tested by a grader.

The initial source-reading failure was a UTF-8 decoding error. Explicit Windows-1252 decoding fixed it; the focused filing check passed without changing financial inputs.

## 6. Sensitivity, peer definitions and decision effect

The revised WACC/growth grid spans $58.64-$76.50 with operating forecasts fixed. The broader $50.27-$87.17 combined-case range changes operating and valuation assumptions jointly. A +5-percentage-point Data Center growth shift alone moves the revised model from $66.22 to **$76.63**; reset restores $66.22. This demonstration is separate from the old Lab 11 FCFE exercise below.

Lab 08 admits AMD and Broadcom only as qualified peers, uses consistent same-date closing prices and annual reported GAAP diluted EPS, and excludes NVIDIA from the peer median. Fiscal earnings windows and business mixes differ. P/E produces equity value per share directly; cash/debt must not be applied a second time. The required enterprise-value peer multiple is not completed in the existing evidence.

The decision remains watch/defer. Cases well below the historical price reference, large method disagreement and incomplete current evidence do not justify initiation. Later earnings and normalized cash-flow evidence, supported discount rates and a reconciled share basis could change the action. The condition is evidence-based; no automated trade threshold is asserted.

<!-- PAGEBREAK -->

## 7. Preserved Lab 11 changed-input evidence

The following is the existing local Lab 11 record, retained with its original stated September 29 timestamp and original FCFE results. It is not a new prediction or a run of the revised FCFF engine. A historical immutable precommit identifier is not present in the available local record and has not been reconstructed. The reference hash below identifies the current source file only; it is not a substitute for the original precommit.

Current source SHA-256: `ea814d2b3ac03a4e80d7f91a806bd247d1ad9de19643ad207d5e4ed224b22713`.

# Lab 11 — Locked Changed-Input Record

**Locked before the first changed-input run:** September 29, 2026, 4:59 p.m. EDT.

This record was saved before any lower or higher Lab 11 sensitivity case was run.
The unchanged Lab 10 base was run first and produced FY2031 operating income of
$303,302.5 million, FY2031 FCFE of $244,585.5 million, and value of $62.97 per
share, with all accounting checks passing.

## Inputs and prediction locked before execution

### Driver 1 — Data Center revenue growth

- Base FY2027–FY2031 path: 35%, 25%, 18%, 12%, 8%.
- Lower path: 30%, 20%, 13%, 7%, 3%, a 5-percentage-point decrease in every
  forecast year.
- Higher path: 40%, 30%, 23%, 17%, 13%, a 5-percentage-point increase in every
  forecast year.
- Range reason: Lab 10 labels the fading path as judgment and reports that
  historical Data Center growth slowed from 217% to 142% to 68%. A symmetric
  five-point shift tests meaningful forecast error without replacing the
  original fade pattern.
- Prediction: the lower path will reduce each later year's Data Center revenue,
  so the effect will compound through revenue, gross profit, operating income,
  net income, and FCFE. The higher path will reverse those directions. The
  FY2031 operating-income and FCFE effects should be in the tens of billions of
  dollars, and value per share could move by roughly $10–$20 in either direction.

### Driver 2 — Gross margin

- Base FY2027–FY2031 value: 72.5% each year.
- Lower value: 70.0% each year, a 2.5-percentage-point decrease.
- Higher value: 75.0% each year, a 2.5-percentage-point increase.
- Range reason: reported FY2024–FY2026 gross margins were 72.72%, 74.99%, and
  71.07%. The high case approximates the historical peak. The 70.0% low case is
  modestly below recent history and approximately applies the FY2026 filing's
  disclosed 2.6-percentage-point unfavorable effect from inventory and excess
  purchase-obligation provisions to the 72.5% base.
- Prediction: lower margin will reduce gross profit and operating income at the
  same revenue, with most of the after-tax effect flowing to FCFE; higher margin
  will reverse those directions. Because SG&A equals 3% of gross profit, the
  operating-income response will be slightly smaller than the direct gross-profit
  change. FY2031 operating income should move by roughly $12 billion in either
  direction, FCFE by roughly $10 billion, and value per share by roughly $3–$5.

### Predicted ranking

Over these chosen ranges, the Data Center growth path is expected to create the
larger span in final-year operating income, final-year FCFE, and value per share
because its five annual changes compound. This is a range-dependent prediction,
not a claim that growth is always intrinsically more important than margin.

## Post-run reconciliation

Added after executing `python lab11_nvda.py`:

| Driver and case | FY2031 operating income | Change from base | FY2031 FCFE | Change from base | Value/share | Change from base |
|---|---:|---:|---:|---:|---:|---:|
| Data Center growth — lower | $247,884.5 million | −$55,418.0 million | $202,671.9 million | −$41,913.6 million | $54.03 | −$8.94 |
| Data Center growth — base | $303,302.5 million | $0.0 | $244,585.5 million | $0.0 | $62.97 | $0.00 |
| Data Center growth — higher | $368,924.6 million | +$65,622.0 million | $293,666.5 million | +$49,081.0 million | $73.29 | +$10.32 |
| Gross margin — lower | $291,166.0 million | −$12,136.5 million | $233,967.2 million | −$10,618.3 million | $60.13 | −$2.85 |
| Gross margin — base | $303,302.5 million | $0.0 | $244,585.5 million | $0.0 | $62.97 | $0.00 |
| Gross margin — higher | $315,439.0 million | +$12,136.5 million | $255,203.8 million | +$10,618.3 million | $65.82 | +$2.85 |

The predicted direction and ranking were correct. The growth prediction correctly
anticipated effects in the tens of billions; its actual value-per-share change
was −$8.94 to +$10.32, near the lower edge of the predicted roughly $10–$20
change. The margin prediction was accurate for operating income (±$12.14
billion) and FCFE (±$10.62 billion), while the ±$2.85 per-share result was
slightly smaller than the predicted roughly $3–$5.

The higher growth case had a larger absolute gain than the lower case's loss
because changing a percentage growth path affects an expanding revenue base and
compounds multiplicatively across five years. That nonlinearity was not stated
in the initial prediction.

The result does not change the prior watch-defer valuation conclusion: even the
higher-growth case produces $73.29 per share, still far below the prior Lab 10
market observation of $224.58 on September 24, 2026. It does change the research
priority by making support for the Data Center growth path more important than
refining gross margin within the tested range. This conclusion is explicitly
limited to these ranges.


## 8. Limits that govern the committee action

Later quarterly financials and the interim valuation-date stub are not integrated. The normalized historical income/cash-flow bridge, point-in-time dilution, other claims, complete enterprise-multiple comparison and terminal reinvestment support remain unresolved. The assumption-challenge table in `docs/project1-model-notes.md` identifies the current values, basis, challenges and changing evidence; actual peer challenges require their existing evidence rather than invented attribution.

Passing accounting checks does not make the scenarios probable. The declared historical range is conditional model output. These limitations are part of the rationale for defer and remain visible in the memo, report and oral defense.
