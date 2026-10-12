# Halcyon claims-triage fairness monitor

A lightweight monthly check the AI Governance Committee can run itself, with no
engineer needed. It reads the claims extract, checks whether the claims-severity
triage model treats claims from higher-minority ZIP areas differently from claims
elsewhere, and writes a plain-English HTML report with green / amber / red status.

```
python3 monitor.py                  # report on the latest month in data/claims.csv
python3 monitor.py --month 2026-08  # report on a specific month
```

The output goes to `reports/fairness_report_<month>.html` (open it in any browser)
and `reports/fairness_metrics_<month>.csv` (every number in the report, for the minutes).
Requirements: Python 3.9+ and `pip install -r requirements.txt` (pandas, numpy,
and matplotlib for the analyzer's charts).

## Monitoring analyzer: charts and one-page flag summary

```
python3 analyzer.py                    # latest month, comparing ZIP community groups
python3 analyzer.py --month 2026-07
python3 analyzer.py --group-col state  # compare the four states instead
```

It writes everything to `reports/<month>/`. Runs with `--group-col` go to a
`by_<column>/` subfolder so they don't overwrite the default run.

| Output | What it shows |
|---|---|
| `flag_summary_<month>.md` | **One-page plain-language flag summary**: overall status, each flag in a sentence, what to do, the key numbers |
| `chart_selection_rates.png` | Selection rate per group for each queue (fast-pay, standard, investigation) |
| `chart_disparity_ratios.png` | Four-fifths-rule impact ratios by month, with the 0.80 line |
| `chart_false_investigation.png` | False-investigation rate by group and month |
| `chart_drift_vs_baseline.png` | This month against the rolling 3-month baseline, per group and metric |
| `analyzer_metrics_<month>.csv` | Every number behind the summary, including the drift baselines and p-values |

**Definitions**

- **Selection rate**: the share of a group's claims routed to each queue.
- **Disparity ratio (four-fifths rule)**:
  - Fast-pay is a favourable outcome. The ratio is a group's fast-pay rate divided by
    the rate of the group that gets fast-pay most.
  - Investigation is an adverse outcome. The ratio is the least-investigated group's
    rate divided by this group's rate, so 0.50 means investigated twice as often.
  - Below 0.80 fails the rule. A FLAG also needs p < 0.05.
  - The four-fifths rule compares raw rates. So each disparity flag is also
    risk-adjusted, using the same method as `monitor.py`. A raw gap that disappears
    once claim size, tenure, vehicle age and prior claims are accounted for is
    shown as WATCH, not FLAG.
- **False-investigation rate**: of the claims a group had investigated, the share
  that did not end in confirmed fraud. It is flagged when it exceeds the best
  group's rate by 10 points or more and the difference is significant. The CSV also
  holds the share of each group's claims *not confirmed as fraud* that were investigated.
  That denominator is not "legitimate claims": fast-pay claims are never examined, so
  undetected fraud sits in it too.
- **Drift**: each metric above, and the model-score distribution (PSI), compared
  with the previous three months pooled. Rates are flagged when they move 5 points
  or more and the change is significant. Impact ratios are flagged when they fall
  by 0.10 or more. A month with fewer than three earlier months has no drift section.

**On the sample data**

- **July:** the v2.4 refresh trips drift flags against the April–June baseline. The
  higher-minority investigation rate goes from 14.2% to 27.8%, and its impact ratio
  from 0.40 to 0.22.
- **September:** the rolling baseline has absorbed the new level, so drift goes
  quiet, but the disparity flags stay red. Investigation impact ratio is 0.26, still
  3.1× after risk adjustment, and 90% of investigations found no fraud against 68%
  elsewhere. This is why the summary tells readers not to rely on drift alone.
- **Control data** (bias switched off) never reaches FLAG. Its raw four-fifths
  failures show as WATCH because the risk adjustment explains them.

All analyzer settings are in the `analyzer` section of `thresholds.json`.

## Incident response and walkthrough

- `INCIDENT_RESPONSE.md` is the trigger table. It sets which metric thresholds page
  whom, the response clocks, and the interim actions that protect claimants while a
  flag is investigated. Each flag summary prints its incident tier.
- `RECORDING_GUIDE.md` is the walkthrough for the Chief Actuary. It has the prompts
  used to build this, the defects caught and fixed, the live-run script, and what
  the numbers do **not** prove.

## Monthly routine

1. Drop the new month's extract into `data/claims.csv` (same columns; see below).
2. Run `python3 monitor.py`.
3. Run `python3 analyzer.py` for the charts and the one-page flag summary.
4. Open the HTML report and `reports/<month>/flag_summary_<month>.md`. Each
   gives the overall status, the findings one sentence apiece, and the
   recommended action.
5. File the reports, charts and CSVs with the meeting minutes.

## What it checks

All ratios compare **higher-minority ZIP3 areas** (≥ 40% minority population in
`zip_reference.csv`) with **all other ZIP3 areas**. The model never sees race. The
reference table lets the committee test whether location-based inputs reproduce a
protected-class disparity anyway.

| Check | Question it answers | Red when |
|---|---|---|
| Investigation referral ratio | Are these claims sent to investigation more often? | ≥ 1.50 |
| **Risk-adjusted referral ratio** | Does the gap remain after accounting for claim size, tenure, vehicle age and prior claims? | ≥ 1.30 and 95% CI excludes 1 |
| Fast-pay access ratio | Do these claimants get fast-pay less often? (four-fifths rule) | ≤ 0.80 |
| Investigation hit-rate ratio | Do investigations here confirm fraud less often? That is, are claims referred on weaker grounds? | ≤ 0.67 |
| Claimant withdrawal ratio | Do more honest claimants give up? | ≥ 2.00 |
| Score stability (PSI) | Has the score distribution shifted since the baseline month? | ≥ 0.25 |
| Proxy screen | Which model input separates the two groups strongly but does not track confirmed fraud? | flagged by name |

How the statuses are set, to avoid false alarms:

- A red needs statistical significance (p < 0.05, or a CI that excludes parity). An amber needs p < 0.10.
- The raw referral and fast-pay gaps are each capped at amber when their own risk adjustment shows no significant remaining gap. This is the same rule `analyzer.py` uses, so the two tools never disagree on one number.
- A group with fewer than 100 claims in the month shows grey (insufficient data).
- The proxy screen uses a trailing 6-month window, because one month has too few confirmed frauds.

Every threshold lives in `thresholds.json`, so the committee can change them without
touching code.

## Input data

`data/claims.csv` has one row per claim:

| column | meaning |
|---|---|
| `claim_id`, `claim_date`, `month` (YYYY-MM) | identifiers |
| `state`, `zip3` | location (ZIP3 is the ZIP-code proxy) |
| `claim_amount`, `vehicle_age_years`, `policy_tenure_years`, `prior_claims_3yr`, `zip_risk_index` | model inputs |
| `model_version`, `model_score` | model output (0–1) |
| `queue_assignment` | `fast_pay`, `standard` or `investigation` |
| `final_outcome` | `paid_in_full`, `paid_adjusted`, `denied_fraud_confirmed`, `withdrawn_by_claimant` |
| `paid_amount`, `days_to_close` | settlement |

`data/zip_reference.csv` maps `zip3` to `state`, `pct_minority_est` and
`community_group`. For production, replace the synthetic shares with ACS 5-year
estimates.

## The synthetic dataset and the planted bias

`data/` holds a **synthetic** dataset made by `generate_claims.py`: 6,308 claims,
April to September 2026, Ohio, Indiana, Kentucky and Michigan, 40 ZIP3 areas (10 of
them higher-minority). The seed is fixed (`--seed`), so the data can be rebuilt exactly.

The proxy-bias pathway was designed in on purpose, so there is something real to detect:

1. **True fraud never depends on ZIP.** It is driven only by claim size, new policies
   (tenure < 1 year), prior claims and vehicle age. The latent flag is in
   `data/answer_key.csv`, for validation only. The monitor never reads it.
2. **`zip_risk_index` is the proxy.** It is the historical SIU referral rate for the
   ZIP3. Legacy referral practice inflated it to about 1.8 in higher-minority areas,
   against about 1.0 elsewhere. That reflects past scrutiny, not past fraud.
3. **The model weights that feature.** Claims from those areas score higher, go to
   investigation more often and to fast-pay less often. When investigated, they
   confirm fraud less often, and more honest claimants withdraw.
4. **The model refresh makes it worse.** On 2026-07-01, `triage-v2.4` increased the
   weight on `zip_risk_index`. The risk-adjusted ratio rises from about 1.8 to about 3.0.
5. **There is also a legitimate confound.** Higher-minority areas have slightly older
   vehicles, shorter tenure and larger claims (urban repair labour costs), and those
   factors do raise fraud risk. A raw comparison overstates the bias. The
   risk-adjusted ratio is there to separate the two.

`python3 generate_claims.py --no-bias --out-dir <dir>` builds control data with steps
2–4 switched off. On that data the monitor reports amber for the raw gap (explained by
the confound), green for the risk-adjusted ratio, and no proxy. The tests check both
directions:

```
python3 -m unittest discover -s tests -v
```

## Results on the sample data (September 2026)

Overall status: **Escalate**. Claims from higher-minority areas went to investigation
3.9× as often (27.5% vs 7.0%). The gap is still 3.1× after risk adjustment (95% CI
2.5–3.8). Those investigations confirmed fraud 10% of the time, against 32% elsewhere.
The proxy screen names `zip_risk_index` and nothing else. Every month is red, and
the ratio steps up at the v2.4 refresh. See `reports/fairness_report_2026-09.html`.

## Limitations

- ZIP3 community labels are an area-level proxy. They are not individual demographics.
- Risk adjustment covers only the legitimate factors in the extract. A gap could
  still reflect a legitimate factor that is missing from the extract.
- Confirmed fraud is only observed on claims someone looked at. The hit-rate check
  compares groups within the investigation queue, so it is not affected by this.
- One month is about 1,000 claims, so expect some month-to-month noise. Read the
  trend table, not a single month.
