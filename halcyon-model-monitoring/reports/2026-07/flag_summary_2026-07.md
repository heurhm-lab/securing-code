# Triage model flag summary: 2026-07

**🔴 ACTION NEEDED**  ·  1,115 claims  ·  groups compared by ZIP community group  ·  drift baseline: 2026-04 to 2026-06

**What to do:** Escalate to the model owner and the Chief Actuary. Ask for a written explanation of each flag and a remediation date before the next committee meeting.

## Flags

- 🔴 FLAG · *Disparity — fast-pay*: **higher-minority** claims reach fast-pay at 0.58× the rate of the best-treated group (20.5% vs 35.3%). Fails the four-fifths rule. After adjusting for claim size, tenure, vehicle age and prior claims, the gap is still 1.4× (risk-adjusted ratio 0.71, 95% CI 0.58–0.88): the claims themselves do not explain it.
- 🔴 FLAG · *Disparity — investigation*: **higher-minority** claims are sent to investigation 4.5× as often as the least-investigated group (27.8% vs 6.1%); impact ratio 0.22. Fails the four-fifths rule. After adjusting for claim size, tenure, vehicle age and prior claims, the gap is still 3.0× (risk-adjusted ratio 2.97, 95% CI 2.44–3.62): the claims themselves do not explain it.
- 🔴 FLAG · *False investigations*: **higher-minority**: 86% of investigations found no fraud, against 67% for other (115 of 133 investigated claims). Honest claimants in this group are investigated far more often.
- 🔴 FLAG · *Drift*: **higher-minority** investigation rate moved from 14.2% (rolling 3-month baseline) to 27.8% this month (+13.7 points).
- 🔴 FLAG · *Drift*: **higher-minority** fast-pay rate moved from 25.8% (rolling 3-month baseline) to 20.5% this month (-5.3 points).
- 🔴 FLAG · *Drift*: **higher-minority** legitimate claims investigated moved from 11.7% (rolling 3-month baseline) to 25.0% this month (+13.3 points).
- 🔴 FLAG · *Drift*: **higher-minority** fast-pay impact ratio fell from 0.70 to 0.58 against the rolling baseline.
- 🔴 FLAG · *Drift*: **higher-minority** investigation impact ratio fell from 0.40 to 0.22 against the rolling baseline.
- 🟡 WATCH · *Drift*: **higher-minority** false-investigation rate moved from 80.6% (rolling 3-month baseline) to 86.5% this month (+5.9 points); not statistically significant.
- … and 1 more in `analyzer_metrics_2026-07.csv`.

## Key numbers

| Group | Claims | Fast-pay | Investigated | Fast-pay ratio | Investigation ratio | Risk-adjusted inv. gap | Investigations with no fraud |
|---|--:|--:|--:|--:|--:|--:|--:|
| higher-minority | 478 | 20.5% | 27.8% | 0.58 | 0.22 | 2.97× | 86% |
| other | 637 | 35.3% | 6.1% | 1.00 | 1.00 | reference | 67% |

Model-score drift against the baseline: PSI 0.06 (below 0.10 is stable, 0.25 or more is a material shift).

## How to read this

- **Impact ratio** compares a group with the best-treated group. A ratio below 0.80 fails the four-fifths rule. For investigation, a ratio of 0.50 means a group is investigated twice as often.
- **Investigations with no fraud** is the share of investigated claims that ended paid or withdrawn. Almost all of these are honest claimants who were delayed and scrutinised.
- **Risk-adjusted inv. gap** compares investigation rates after accounting for claim size, tenure, vehicle age and prior claims. 1.00 means the raw gap is fully explained by those legitimate factors.
- **Drift** compares this month with the previous three months pooled. A rolling baseline absorbs a lasting change after about three months, so a drift flag that goes quiet does not mean the problem is fixed. Check the disparity flags too.
- 🔴 FLAG means the threshold was breached and the difference is statistically significant (p < 0.05). 🟡 WATCH means it is near the line or could still be chance.

Charts in this folder: `chart_selection_rates.png`, `chart_disparity_ratios.png`, `chart_false_investigation.png`, `chart_drift_vs_baseline.png`.
