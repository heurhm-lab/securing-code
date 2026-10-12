# Triage model flag summary: 2026-09

**🔴 ACTION NEEDED**  ·  1,007 claims  ·  groups compared by ZIP community group  ·  drift baseline: 2026-06 to 2026-08

**What to do:** Escalate to the model owner and the Chief Actuary. Ask for a written explanation of each flag and a remediation date before the next committee meeting.

## Flags

- 🔴 FLAG · *Disparity — investigation*: **higher-minority** claims are sent to investigation 3.9× as often as the least-investigated group (27.5% vs 7.0%); impact ratio 0.26. Fails the four-fifths rule. After adjusting for claim size, tenure, vehicle age and prior claims, the gap is still 3.1× (risk-adjusted ratio 3.07, 95% CI 2.47–3.81): the claims themselves do not explain it.
- 🔴 FLAG · *False investigations*: **higher-minority**: 90% of investigations found no fraud, against 68% for other (115 of 128 investigated claims). Honest claimants in this group are investigated far more often.
- 🟡 WATCH · *Disparity — fast-pay*: **higher-minority** claims reach fast-pay at 0.57× the rate of the best-treated group (20.2% vs 35.1%). Fails the four-fifths rule. However, after adjusting for claim size, tenure, vehicle age and prior claims the ratio is 0.81 (95% CI 0.65–1.01): a smaller gap may remain, but it is not statistically significant this month.
- 🟡 WATCH · *Drift*: **higher-minority** false-investigation rate moved from 84.1% (rolling 3-month baseline) to 89.8% this month (+5.8 points); not statistically significant.
- 🟡 WATCH · *Drift*: **other** false-investigation rate moved from 57.1% (rolling 3-month baseline) to 68.4% this month (+11.3 points); not statistically significant.

## Key numbers

| Group | Claims | Fast-pay | Investigated | Fast-pay ratio | Investigation ratio | Risk-adjusted inv. gap | Investigations with no fraud |
|---|--:|--:|--:|--:|--:|--:|--:|
| higher-minority | 466 | 20.2% | 27.5% | 0.57 | 0.26 | 3.07× | 90% |
| other | 541 | 35.1% | 7.0% | 1.00 | 1.00 | reference | 68% |

Model-score drift against the baseline: PSI 0.01 (below 0.10 is stable, 0.25 or more is a material shift).

## How to read this

- **Impact ratio** compares a group with the best-treated group. A ratio below 0.80 fails the four-fifths rule. For investigation, a ratio of 0.50 means a group is investigated twice as often.
- **Investigations with no fraud** is the share of investigated claims that ended paid or withdrawn. Almost all of these are honest claimants who were delayed and scrutinised.
- **Risk-adjusted inv. gap** compares investigation rates after accounting for claim size, tenure, vehicle age and prior claims. 1.00 means the raw gap is fully explained by those legitimate factors.
- **Drift** compares this month with the previous three months pooled. A rolling baseline absorbs a lasting change after about three months, so a drift flag that goes quiet does not mean the problem is fixed. Check the disparity flags too.
- 🔴 FLAG means the threshold was breached and the difference is statistically significant (p < 0.05). 🟡 WATCH means it is near the line or could still be chance.

Charts in this folder: `chart_selection_rates.png`, `chart_disparity_ratios.png`, `chart_false_investigation.png`, `chart_drift_vs_baseline.png`.
