# Incident response: claims-triage fairness flags

**Owner:** Model Risk (raises incidents) · **Approver:** Renee Okafor, Chief Actuary ·
**Applies to:** the claims-severity triage model and the monthly outputs of `monitor.py` and `analyzer.py`

Each monthly flag summary prints an **incident tier** (`SEV-1`, `SEV-2`, `SEV-3` or `None`).
That tier comes from the rules in section 1 and starts the clocks in section 2. Thresholds
are the values in `thresholds.json` as of this version. If a threshold changes there,
update this page in the same change.

Clocks are counted from when the Model Risk Analyst posts the monthly run, and they use
**business hours and days** (Mon–Fri, 8:00–18:00 local time of the paged person).
"Page" means a phone or on-call page, followed by an email with the flag summary
attached. "Notify" means email only.

---

## 1. Trigger table: which metric sets which tier

| # | Metric (tool) | Threshold | Tier |
|---|---|---|---|
| T1 | **Investigation impact ratio** (analyzer) **plus false-investigation gap** (analyzer), **same group** | Impact ratio < 0.80 and p < 0.05, with the gap still present after risk adjustment (CI lower bound > 1). **And** false-investigation rate ≥ 10 points above the best group's, p < 0.05 | **SEV-1** |
| T2 | Risk-adjusted referral ratio (monitor) **plus** investigation hit-rate ratio (monitor) | Both RED: ≥ 1.30 with CI excluding 1, and ≤ 0.67 with p < 0.05 | **SEV-1** |
| T3 | Risk-adjusted referral ratio (monitor) | ≥ 2.00 with CI excluding 1, whatever else is true | **SEV-1** |
| T4 | Investigation impact ratio (analyzer) | < 0.80, p < 0.05, gap still present after risk adjustment (no T1 partner) | SEV-2 |
| T5 | Fast-pay impact ratio (analyzer) | < 0.80, p < 0.05, risk-adjusted fast-pay CI entirely below 1 | SEV-2 |
| T6 | False-investigation gap (analyzer) | ≥ 10 points above the best group, p < 0.05 (no T1 partner) | SEV-2 |
| T7 | Drift against the rolling 3-month baseline (analyzer) | A group's rate moves ≥ 5 points with p < 0.05, **or** an impact ratio falls ≥ 0.10 | SEV-2 |
| T8 | Score stability, PSI (both) | ≥ 0.25 | SEV-2 |
| T9 | Claimant withdrawal ratio (monitor) | ≥ 2.00, p < 0.05 | SEV-2 |
| T10 | Proxy screen (monitor) | Any input flagged "likely proxy" in two consecutive runs | SEV-2 |
| D1 | **Unmapped claims** (analyzer Data flag) | ≥ 1% of the month's claims have no group label | SEV-2 (data) |
| D2 | Data quality (monitor) | Any blank required field, unknown queue or outcome value, or duplicate claim ID | SEV-2 (data) |
| W1 | Any WATCH (analyzer) or AMBER (monitor) | Near a threshold, or not yet statistically significant | SEV-3 |
| W2 | Same WATCH or AMBER, same metric and group, **two months running** | | upgrade to SEV-2 |

The higher tier wins when several rows fire. A data incident (D1, D2) is handled
alongside any fairness tier, and **no fairness conclusion from that month is circulated
until the data is fixed and the run repeated**.

---

## 2. Response table: who is paged, the response clock, and claimant protection

| Tier | Paged | Notified | Acknowledge | Interim claimant protection: what, and in place by | Investigation deliverable | Closes when |
|---|---|---|---|---|---|---|
| **SEV-1** | Model owner (Claims Analytics lead) · Renee Okafor, Chief Actuary · Chief Compliance Officer · SIU Director | VP Claims · General Counsel · AI Governance Committee chair | **4 business hours** | **Within 1 business day:** (a) second look on every model-routed investigation referral; (b) no investigation-based denial without SIU Director sign-off; (c) open investigations older than 30 days contacted, undisputed amounts paid. **Within 5 business days:** (d) the flagged proxy neutralised under emergency change control. Details in section 3 | Root-cause memo in **10 business days**. Committee special session in **10 business days**. Compliance decides any regulator notice in **5 business days**. Lookback list of affected claims in **15 business days** | Two consecutive monthly runs at SEV-3 or better **with interim controls still on**, then the committee votes to lift them |
| **SEV-2** | Model owner · Model Risk Analyst | Renee Okafor · SIU Director (investigation and false-investigation triggers) · Compliance (T5, T9) | **1 business day** | **Within 3 business days:** sample review (section 3e). If it fails, upgrade to SEV-1 | Written explanation in **5 business days**, on the next committee agenda | Next run below the trigger, or the committee accepts the explanation in its minutes |
| **SEV-2 (data)** | Claims data steward · Model Risk Analyst | Model owner | **1 business day** | **Immediately:** hold that month's summary. Fix the extract or `zip_reference.csv` and re-run within **2 business days** | Note of what was missing and why | Re-run shows < 1% unmapped and no data-quality issues |
| **SEV-3** | nobody | Model Risk Analyst records it in the minutes | at the next committee meeting | none | none | Next run clears it. Two in a row upgrades to SEV-2 (W2) |

**Missed clock:** if an acknowledgement or deliverable is late, the incident goes up one
tier and the Model Risk Analyst pages Renee Okafor directly.

---

## 3. Interim claimant protections

These controls protect claimants while the cause is investigated. They do not decide
anything about the model.

a. **Second look on referrals (SEV-1).** A senior adjuster reviews every claim the model
   sends to investigation, **in every area**, before the SIU contacts the claimant.
   Claims that would not be referred on their facts alone go back to the standard queue.
   The review covers all areas, not only the flagged ZIPs, so the control does not
   itself treat claimants differently by location. September volume was about 170
   referrals a month, so this is roughly 8–9 reviews a business day.

b. **No investigation-based adverse action without sign-off (SEV-1).** No denial,
   rescission or examination-under-oath request may rest on an investigation opened
   during the incident unless the SIU Director signs it.

c. **Unblock waiting claimants (SEV-1).** Every claimant whose investigation has been
   open more than 30 days gets a status contact within 1 business day. Any undisputed
   portion is paid now. Compliance confirms the prompt-pay deadlines for each of the
   four states.

d. **Neutralise the proxy (SEV-1).** Under emergency change control, set the flagged input
   (in this incident `zip_risk_index`) to its neutral value of 1.0 for every claim. Then
   re-score and re-run both tools on the current month. **Rolling back to the previous
   model version is not a fix by default.** In the sample data, v2.3 was SEV-1 as well.
   A rollback counts only if the re-run on the old version comes back below SEV-1.

e. **Sample review (SEV-2).** A senior adjuster reviews 30 of the affected group's
   investigated claims (or fast-pay denials, for T5) without seeing the ZIP or the model
   score. If 10 or more would not have been referred on their facts alone, upgrade to
   SEV-1.

f. **Remediation lookback (SEV-1).** List every claim in the affected group from the
   trigger month onward that was withdrawn, denied after investigation, or closed more
   than 30 days late. Compliance and Claims decide whether to re-open those claims.

---

## 4. Applying it to the September 2026 sample run

| Row | Fired? | Evidence |
|---|---|---|
| T1 | **Yes** | Investigation impact ratio 0.26, still 3.1× after risk adjustment (CI 2.47–3.81). False-investigation rate 90% against 68%, p < 0.05 |
| T2 | **Yes** | Risk-adjusted referral ratio 3.07 RED. Hit-rate ratio 0.32 RED |
| T3 | **Yes** | 3.07 ≥ 2.00 |
| T5 | No | Fast-pay impact ratio 0.57, but the risk-adjusted CI (0.65–1.01) touches 1, so it stays WATCH |
| T7 | No | The rolling baseline absorbed the July shift. **July** fired T7 (investigation rate 14.2% → 27.8%) |
| T10 | **Yes** | `zip_risk_index` was flagged in consecutive runs |

**Result: SEV-1.** Page the model owner, Renee Okafor, the Chief Compliance Officer and
the SIU Director. Controls (a) to (c) go in within one business day, and (d) within five.

On these rules the incident would have opened **before the July model refresh**:

| Month | Model | Tier | Why |
|---|---|---|---|
| 2026-04 | v2.3 | SEV-2 | T4: risk-adjusted referral ratio 1.75, RED. The hit-rate ratio (0.59) was only AMBER, so T1 and T2 did not fire |
| 2026-05 | v2.3 | **SEV-1** | T1 and T2: risk-adjusted ratio 1.79 and hit-rate ratio 0.42, both RED |
| 2026-06 | v2.3 | SEV-1 | T1, T2 and T3 (risk-adjusted ratio 2.22) |
| 2026-07 | v2.4 | SEV-1 | T1, T2, T3, plus T7 drift flags from the refresh |

The July refresh made the problem worse, but it did not create it. That is why control
(d) does not accept a rollback to v2.3 as a fix by default.
