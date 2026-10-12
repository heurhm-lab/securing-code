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
The only requirements are Python 3.9+, `pandas` and `numpy`.

## Monthly routine

1. Drop the new month's extract into `data/claims.csv` (same columns; see below).
2. Run `python3 monitor.py`.
3. Open the HTML report. The banner gives the overall status, the findings in one
   sentence each, and the recommended action.
4. File the HTML and CSV with the meeting minutes.

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
- If the risk-adjusted ratio is green, the raw referral and fast-pay gaps are capped at amber. That gap is explained by the claims themselves.
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
