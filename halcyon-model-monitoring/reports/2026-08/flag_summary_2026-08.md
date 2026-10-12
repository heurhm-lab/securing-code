# Triage model flag summary: 2026-08

**🔴 ACTION NEEDED**  ·  incident tier **SEV-1** (see `INCIDENT_RESPONSE.md`)  ·  1,005 claims  ·  groups compared by ZIP community group  ·  drift baseline: 2026-05 to 2026-07

**What to do:** Escalate to the model owner and the Chief Actuary. Ask for a written explanation of each flag and a remediation date before the next committee meeting.

## Flags

- 🔴 FLAG · *Disparity — fast-pay*: **higher-minority** claims reach fast-pay at 0.43× the rate of the best-treated group (16.0% vs 36.9%). Fails the four-fifths rule. After adjusting for claim size, tenure, vehicle age and prior claims, the gap is still 1.8× (risk-adjusted ratio 0.55, 95% CI 0.43–0.70): the claims themselves do not explain it.
- 🔴 FLAG · *Disparity — investigation*: **higher-minority** claims are sent to investigation 4.0× as often as the least-investigated group (28.9% vs 7.2%); impact ratio 0.25. Fails the four-fifths rule. After adjusting for claim size, tenure, vehicle age and prior claims, the gap is still 2.8× (risk-adjusted ratio 2.75, 95% CI 2.24–3.39): the claims themselves do not explain it.
- 🔴 FLAG · *False investigations*: **higher-minority**: 83% of investigations found no fraud, against 53% for other (114 of 137 investigated claims). Honest claimants in this group are investigated far more often.
- 🔴 FLAG · *Drift*: **higher-minority** investigation rate moved from 18.2% (rolling 3-month baseline) to 28.9% this month (+10.7 points).
- 🔴 FLAG · *Drift*: **higher-minority** fast-pay rate moved from 24.2% (rolling 3-month baseline) to 16.0% this month (-8.2 points).
- 🔴 FLAG · *Drift*: **higher-minority** investigated, of claims not confirmed as fraud moved from 15.8% (rolling 3-month baseline) to 25.3% this month (+9.5 points).
- 🔴 FLAG · *Drift*: **higher-minority** fast-pay impact ratio fell from 0.65 to 0.43 against the rolling baseline.
- 🟡 WATCH · *Drift*: **other** false-investigation rate moved from 59.6% (rolling 3-month baseline) to 52.6% this month (-7.0 points); not statistically significant.

## Key numbers

| Group | Claims | Fast-pay | Investigated | Fast-pay ratio | Investigation ratio | Risk-adjusted inv. gap | Investigations with no fraud |
|---|--:|--:|--:|--:|--:|--:|--:|
| higher-minority | 474 | 16.0% | 28.9% | 0.43 | 0.25 | 2.75× | 83% |
| other | 531 | 36.9% | 7.2% | 1.00 | 1.00 | reference | 53% |

Model-score drift against the baseline: PSI 0.06 (below 0.10 is stable, 0.25 or more is a material shift).

## How to read this

- **Impact ratio** compares a group with the best-treated group. A ratio below 0.80 fails the four-fifths rule. For investigation, a ratio of 0.50 means a group is investigated twice as often.
- **Investigations with no fraud** is the share of investigated claims that ended paid or withdrawn. Almost all of these are honest claimants who were delayed and scrutinised.
- **Risk-adjusted inv. gap** compares investigation rates after accounting for claim size, tenure, vehicle age and prior claims. 1.00 means the raw gap is fully explained by those legitimate factors.
- **Drift** compares this month with the previous three months pooled. A rolling baseline absorbs a lasting change after about three months, so a drift flag that goes quiet does not mean the problem is fixed. Check the disparity flags too.
- 🔴 FLAG means the threshold was breached and the difference is statistically significant (p < 0.05). 🟡 WATCH means it is near the line or could still be chance.

Charts in this folder: `chart_selection_rates.png`, `chart_disparity_ratios.png`, `chart_false_investigation.png`, `chart_drift_vs_baseline.png`.
