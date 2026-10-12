# Triage model flag summary: 2026-09

**🔴 ACTION NEEDED**  ·  1,007 claims  ·  groups compared by state  ·  drift baseline: 2026-06 to 2026-08

**What to do:** Escalate to the model owner and the Chief Actuary. Ask for a written explanation of each flag and a remediation date before the next committee meeting.

## Flags

- 🔴 FLAG · *Disparity — investigation*: **IN** claims are sent to investigation 1.7× as often as the least-investigated group (16.0% vs 9.2%); impact ratio 0.58. Fails the four-fifths rule. After adjusting for claim size, tenure, vehicle age and prior claims, the gap is still 2.1× (risk-adjusted ratio 2.06, 95% CI 1.22–3.48): the claims themselves do not explain it.
- 🔴 FLAG · *Disparity — investigation*: **OH** claims are sent to investigation 2.1× as often as the least-investigated group (19.1% vs 9.2%); impact ratio 0.48. Fails the four-fifths rule. After adjusting for claim size, tenure, vehicle age and prior claims, the gap is still 1.7× (risk-adjusted ratio 1.67, 95% CI 1.02–2.73): the claims themselves do not explain it.
- 🔴 FLAG · *Drift*: **IN** investigation impact ratio fell from 0.71 to 0.58 against the rolling baseline.
- 🔴 FLAG · *Drift*: **MI** fast-pay rate moved from 26.4% (rolling 3-month baseline) to 19.1% this month (-7.3 points).
- 🔴 FLAG · *Drift*: **MI** fast-pay impact ratio fell from 0.81 to 0.58 against the rolling baseline.
- 🔴 FLAG · *Drift*: **MI** investigation impact ratio fell from 0.56 to 0.46 against the rolling baseline.
- 🔴 FLAG · *Drift*: **OH** investigation impact ratio fell from 0.59 to 0.48 against the rolling baseline.
- 🟡 WATCH · *Disparity — fast-pay*: **MI** claims reach fast-pay at 0.58× the rate of the best-treated group (19.1% vs 32.7%). Fails the four-fifths rule. However, after adjusting for claim size, tenure, vehicle age and prior claims the ratio is 0.84 (95% CI 0.57–1.24): a smaller gap may remain, but it is not statistically significant this month.
- 🟡 WATCH · *Disparity — investigation*: **MI** claims are sent to investigation 2.2× as often as the least-investigated group (20.1% vs 9.2%); impact ratio 0.46. Fails the four-fifths rule. However, after adjusting for claim size, tenure, vehicle age and prior claims the ratio is 1.55 (95% CI 0.94–2.57): a smaller gap may remain, but it is not statistically significant this month.
- … and 4 more in `analyzer_metrics_2026-09.csv`.

## Key numbers

| Group | Claims | Fast-pay | Investigated | Fast-pay ratio | Investigation ratio | Risk-adjusted inv. gap | Investigations with no fraud |
|---|--:|--:|--:|--:|--:|--:|--:|
| IN | 250 | 30.4% | 16.0% | 0.93 | 0.58 | 2.06× | 85% |
| KY | 217 | 32.7% | 9.2% | 1.00 | 1.00 | reference | 80% |
| MI | 278 | 19.1% | 20.1% | 0.58 | 0.46 | 1.55× | 84% |
| OH | 262 | 32.1% | 19.1% | 0.98 | 0.48 | 1.67× | 88% |

Model-score drift against the baseline: PSI 0.01 (below 0.10 is stable, 0.25 or more is a material shift).

## How to read this

- **Impact ratio** compares a group with the best-treated group. A ratio below 0.80 fails the four-fifths rule. For investigation, a ratio of 0.50 means a group is investigated twice as often.
- **Investigations with no fraud** is the share of investigated claims that ended paid or withdrawn. Almost all of these are honest claimants who were delayed and scrutinised.
- **Risk-adjusted inv. gap** compares investigation rates after accounting for claim size, tenure, vehicle age and prior claims. 1.00 means the raw gap is fully explained by those legitimate factors.
- **Drift** compares this month with the previous three months pooled. A rolling baseline absorbs a lasting change after about three months, so a drift flag that goes quiet does not mean the problem is fixed. Check the disparity flags too.
- 🔴 FLAG means the threshold was breached and the difference is statistically significant (p < 0.05). 🟡 WATCH means it is near the line or could still be chance.

Charts in this folder: `chart_selection_rates.png`, `chart_disparity_ratios.png`, `chart_false_investigation.png`, `chart_drift_vs_baseline.png`.
