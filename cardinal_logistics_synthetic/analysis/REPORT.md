# Cardinal Logistics: Compliance Screen of the Synthetic Dataset

**Scope.** This report covers four screens:
- four-fifths-rule selection-rate ratios for the AEDT;
- FLSA classification and overtime-pay patterns;
- accommodation and leave requests followed by discipline;
- NLRA Section 7 risk in the discipline narratives.

**Inputs.** Only `data/cardinal_applicants_employees.csv`, `data/cardinal_discipline_events.csv` and `README.md` were used. **Nothing in `answer_key/` was opened.** One disclosure: the analyst also generated this dataset, so this is not a blind review. To limit that, every decision rule is fixed in `run_analysis.py` and applied to every group and record, not only where problems were expected.

**Reproduce:** `python3 cardinal_logistics_synthetic/analysis/run_analysis.py`. It needs pandas, scipy and statsmodels. The full console output is in `outputs_console.txt` and the record-level flags are in `outputs/*.csv`.

This is a statistical and documentary screen, not legal advice. Every flag below is a lead for counsel to investigate, not a finding of liability.

---

## Key findings

| # | Area | Finding | Strength |
|---|---|---|---|
| 1 | AEDT, age | Applicants 40+ advance at 0.63× the under-40 rate (n = 444 vs 752, p < 1e-9). The ratio falls with each age band, down to 0.43 for 60+. The score *under-predicts* how older hires actually perform. | Strong |
| 2 | AEDT, disability | Applicants who requested an accommodation advance at **0.30×** the rate of everyone else (n = 44, p < 1e-4). 19 of the 44 got **no score** and none of those 19 was hired. | Strong |
| 3 | AEDT, race | The BISG proxy gives Black 0.80× and Hispanic 0.78× the White rate among scored applicants (Holm p = 0.030 and 0.015). Counting unscored applicants as rejected gives 0.80× and 0.81× (Holm p = 0.037 and 0.044). Commute distance drives this, and commute does not predict performance. | Moderate (borderline ratio, significant) |
| 4 | AEDT, sex | No overall impact on the name-based proxy. In physical roles, women advance at 0.80× (n = 50, p = 0.28). | Inconclusive; the proxy is weak |
| 5 | FLSA, classification | 18 Logistics Coordinators are below the $35,568 salary floor. 9 van drivers are exempt under the MCA despite vehicles of 10,000 lbs or less. 4 Shift Leads with fewer than 2 reports are classified Executive. All 29 Dispatchers need a duties review. | Strong (first three); review (Dispatchers) |
| 6 | FLSA, overtime | Hub 2 leaves shift differential and bonuses out of the regular rate (51 of 54 at-risk employees, p ≈ 2e-31). Hub 3 caps paid time at 40 h/week while badge data shows about 7 more hours (30 employees). 7 employees were paid straight time for OT and 2 got no OT pay. | Strong |
| 7 | ADA / PWFA | The discipline rate in the 90 days after an accommodation request is **5.2×** the baseline (exact p = 7e-7). 12 of those events cite the condition itself. | Strong |
| 8 | FMLA | The discipline rate in the 60 days after approved FMLA leave is **17.7×** the baseline (p = 2e-12). All 9 attendance write-ups that cite a family or medical reason assess points for absences that fall **inside approved FMLA leave**. | Strong |
| 9 | NLRA | 33 events are High risk and 6 are Medium. **Every High-risk first offense started above a Verbal Warning, against 25% of other first offenses** (p ≈ 1e-11). `pca_flag` employees have higher involuntary-termination rates (17.0% vs 4.9%, p = 0.005). | Strong |

---

## 0. Data preparation and data-quality findings

| Step / issue | Detail | How it was handled |
|---|---|---|
| Exact duplicate rows | 6: CL-100601, CL-102735, CL-103909, CL-105449, CL-107554, CL-108259 | Dropped |
| Same ID with conflicting AEDT scores | 3: CL-104284 (64.0 and 68.1, both labeled `Do Not Advance`), CL-106172, CL-106477 | Excluded from the AEDT analysis, because the right row is unknown |
| Recommendation matches score ≥ 65 | Matches in every remaining row | None needed |
| `flsa_classification` spellings | 9 variants (`Exempt`, `EXEMPT`, `exempt`, `E`, `Non-Exempt`, `NE`, …) | Normalized to Exempt / Non-Exempt |
| `age_band` inconsistent with `hs_grad_year` by 2 or more bands | 8 applicants | Kept. A sensitivity run without them gives an age IR of 0.63, unchanged |
| Rejected applicant with an employee record | CL-103433, CL-108582 | Excluded from the employee analyses |
| Impossible hours | CL-103935: 2,184 h in 13 weeks, and the components don't sum | Excluded from the payroll tests |
| Regular + OT ≠ hours worked | CL-107929 | Excluded from the payroll tests |
| Negative OT pay | CL-106345 (−$312.75) | Excluded from the payroll tests |
| Badge hours missing | CL-101497 | Excluded from the off-the-clock test only |
| Discipline event dated before hire | DE-5100 (CL-104032), DE-5196 (CL-108225) | Excluded from the sequence tests, kept in the NLRA text screen |
| `discipline_event_count` ≠ events file | CL-100123, CL-102680, CL-104092, CL-104225, CL-107134 | The events file is treated as authoritative |
| Hourly associate coded Exempt with no exemption basis | CL-105650 (no Q2 payroll) | Flagged |

**Final analysis sets:**
- 1,237 unique applicants, of whom 1,196 have a score.
- 418 employees.
- 314 employees with clean Q2 payroll and badge data. 180 of these are non-exempt hourly.
- 203 discipline events.

---

## 1. AEDT four-fifths analysis

### Method and assumptions
- **Selection event:** `aedt_recommendation == "Advance"` (score ≥ 65). Three populations:
  - **A:** scored applicants only. This is the primary view.
  - **B:** all applicants, with unscored applicants counted as not selected. This captures screen-out by non-scoring.
  - **C:** final hire decision, with withdrawn applicants excluded.
- **Comparator:** the group with the highest selection rate (29 CFR 1607.4(D)), **counting only groups with n ≥ 30**. The Other/Multiracial group (n = 25) has the highest rate but is too small to be a stable comparator. It is reported but not used as one.
  - Age uses the conventional "<40" comparator.
  - Accommodation uses "No request".
- **Tests:**
  - Two-sided Fisher exact test for each group against the comparator.
  - Pooled two-proportion z-test.
  - Holm adjustment within each attribute × population family.
- **Shortfall:** the number of additional selections the group would need to match the comparator's rate.
- **Protected-class data are proxies only:**
  - Race is BISG. Misclassification usually pulls impact ratios toward 1.0, so ratios here are likely conservative.
  - Sex is inferred from first name.
  - Age is the self-reported band.
  - Disability is approximated by "requested an accommodation during the assessment", which undercounts disability.

### Selection-rate ratios (population A: scored applicants, unless noted)

| Attribute | Group | n | Advanced | Rate | Comparator | **IR** | z | Fisher p | Holm p | Shortfall |
|---|---|---|---|---|---|---|---|---|---|---|
| Age | 40+ | 444 | 148 | 33.3% | <40 (52.5%, n = 752) | **0.63** | −6.44 | <1e-9 | <1e-9 | 85 |
| Age band | 18-24 | 235 | 123 | 52.3% | 25-39 (52.6%, n = 517) | 0.99 | −0.07 | 1.00 | 1.00 | 1 |
| | 40-49 | 213 | 80 | 37.6% | 25-39 | **0.71** | −3.70 | 2e-4 | 5e-4 | 32 |
| | 50-59 | 161 | 52 | 32.3% | 25-39 | **0.61** | −4.51 | <1e-5 | <1e-4 | 33 |
| | 60+ | 70 | 16 | 22.9% | 25-39 | **0.43** | −4.67 | <1e-5 | <1e-4 | 21 |
| Race (BISG) | Black | 250 | 100 | 40.0% | White (49.7%, n = 585) | 0.80 | −2.58 | 0.010 | **0.030** | 24 |
| | Hispanic | 264 | 103 | 39.0% | White | **0.78** | −2.90 | 0.004 | **0.015** | 28 |
| | Asian | 72 | 32 | 44.4% | White | 0.89 | −0.85 | 0.45 | 0.45 | 4 |
| | Other/Multi | 25* | 17 | 68.0% | White | 1.37 | 1.79 | 0.10 | 0.20 | — |
| Sex (name proxy) | M | 739 | 336 | 45.5% | F (46.3%, n = 378) | 0.98 | −0.26 | 0.80 | 0.80 | 6 |
| | Unknown | 79 | 32 | 40.5% | F | 0.87 | −0.94 | 0.39 | 0.77 | 5 |
| Sex, physical roles† | F | 50 | 18 | 36.0% | M (44.8%, n = 306) | 0.80 | −1.16 | 0.28 | 0.28 | 4 |
| | Unknown | 25* | 7 | 28.0% | M | 0.63 | −1.63 | 0.14 | 0.28 | 4 |
| Accommodation | Requested (scored only) | 25* | 6 | 24.0% | No request (45.9%, n = 1,171) | 0.52 | −2.17 | 0.041 | 0.041 | 5 |
| **Accommodation, pop. B** | Requested (all) | 44 | 6 | 13.6% | No request (45.0%, n = 1,193) | **0.30** | −4.12 | <1e-4 | <1e-4 | 14 |

\* n < 30: unstable, so read the IR with caution. † Forklift Operator, Driver and Fleet Maintenance Technician.

**Population B** (unscored counted as rejected): age 40+ IR 0.62; Black 0.80 (Holm p = 0.037); Hispanic 0.81 (Holm p = 0.044). The conclusions are the same as for A.

**Population C, final hire:**

| Group | IR | Holm p |
|---|---|---|
| Age 40+ | 0.60 | <1e-7 |
| Age 40-49 / 50-59 / 60+ | 0.69 / 0.53 / 0.46 | — |
| Accommodation requested | 0.40 | 0.004 |
| Black (BISG) | 0.93 | 1.0 |
| Hispanic (BISG) | 0.81 | 0.76 |

At the hire stage the comparator is Asian (n = 72), the highest-rate group with n ≥ 30. A good final-hire ratio for Black applicants **does not cure** the adverse impact at the AEDT step (*Connecticut v. Teal*, 1982).

**Age within job group** (40+ vs <40, population A). The IR is below 0.8 in 8 of 10 groups. It is significant in:

| Job group | IR | p |
|---|---|---|
| Warehouse Associate | 0.71 | 0.001 |
| CSR | 0.48 | 0.003 |
| Driver | 0.54 | 0.003 |
| Fleet Tech | 0.35 | 0.004 |

Forklift Operators are the exception (IR 0.97, p = 1.0).

### What drives the score (OLS on scored applicants, n = 1,196)
- Holding the other factors constant, the score is lower by:
  - **5.0 points** for ages 40-49, **6.0** for 50-59 and **9.6** for 60+ (all p < 1e-6);
  - **0.48 points per commute mile** (p < 1e-13);
  - **0.29 points per résumé-gap month** (p < 1e-4);
  - **6.0 points** for requesting an accommodation (p = 0.013).
- The race and sex proxy coefficients are **not** significant once commute is in the model. The race disparity runs **through commute distance**: mean commute is 16.4 mi for the Black proxy group and 15.5 for Hispanic, against 11.2 for White.
- Résumé gaps run longer for applicants inferred female (5.0 months vs 2.9), so the gap penalty is a likely sex and caregiver proxy.

### Job-relatedness check (hires with a 90-day rating, n = 393)
- The score does predict performance: r = 0.54, p < 1e-30.
- In a regression of rating on score, commute, gap and age (40+ vs <40):
  - Commute has a **positive** coefficient (+0.031 per mile, p < 1e-6). At the same score, long-commute hires perform *better*, so the commute penalty is miscalibrated rather than job-related.
  - Hires under 40 rate **0.36 points lower** than hires 40+ with the same score (p < 1e-4). The score under-predicts older workers.
  - The gap coefficient is not significant (p = 0.15). The penalty has no support.
- This is differential prediction against older and long-commute applicants. It cuts against a business-necessity or job-relatedness defense for those features.
- Caveat: ratings exist only for hires (range restriction), and supervisor ratings can carry their own bias.

### Related signals
- **Recruiter overrides after the AEDT:**
  - Among applicants the AEDT advanced, 62.8% of those 40+ were hired vs 74.8% of those under 40 (n = 137 / 373, Fisher p = 0.011).
  - **28 recruiter notes use age-coded language** ("overqualified", "more energy", "close to retiring", "digital native", "young and hungry").
- **Referral overrides:** among "Do Not Advance" applicants, 41.9% of referred applicants were hired vs 2.6% of everyone else (n = 93 / 534, p < 1e-24). Referrals come from White applicants 17.7% of the time, against 11.0% for Black and 12.0% for Hispanic, so the override channel favors White applicants.
- **Other notes:** 6 notes cite an applicant's accent (CSR, national origin). 4 ask about childcare or kids. 17 record applicants rejected because their accommodation request left them unscored.

All flagged notes are in `outputs/recruiter_notes_flagged.csv`.

---

## 2. FLSA classification and overtime

### Assumptions
- Federal FLSA only, as the README specifies.
- **Salary floor:** $684/week, which is $35,568/year (29 CFR 541.600). The 2024 increase was vacated.
- **Executive exemption:** requires 2 or more full-time direct reports. `direct_reports` is assumed to count FTEs.
- **MCA small-vehicle exception:** applies when GVWR is 10,000 lbs or less, assuming the driver uses no heavier vehicle in the same workweek.
- **Duties:** judged only from `primary_duties_summary`, which is HR's description, not observed duties.
- **Regular rate:** (base × hours + shift differential + nondiscretionary bonus) ÷ hours, per 29 CFR 778.207(b) and 778.208-.211. The bonus is treated as earned within the period. OT due = 1.5 × regular rate × OT hours. Tolerance is $0.50.
- **Meal deduction:** 5 shifts × 30 minutes = 2.5 h/week (README). A badge-minus-paid gap above **4.0 h/week** is flagged.
- **Exposure:**
  - Q2 2026 only (13 weeks), not the 2-3 year lookback.
  - Liquidated damages are not included.
  - Misclassified salaried staff are shown as a range. Low is fluctuating-workweek half-time on salary ÷ hours worked. High is 1.5 × (salary ÷ 40) per OT hour.

### Classification flags (all 418 employees; exposure for those with clean Q2 payroll)

| Flag | Employees | Detail | Q2 OT hours | Q2 exposure (low–high) |
|---|---|---|---|---|
| F1 Salary below $35,568, Admin-exempt | **18** Logistics Coordinators | Salaries run $33,200-$35,500. The 12 coordinators at $35,600 or more pass the salary test, and their duties (carrier selection, rate negotiation within budget) plausibly meet the admin test. | 1,268 (n = 16) | $8.9k – $31.2k |
| F4 Executive with fewer than 2 reports | **4** Shift Leads | 0-1 reports. The duties text says about 70% floor work and no hire/fire input, which fails 541.100 on two prongs. | 696 (n = 4) | $6.1k – $24.9k |
| F5 MCA claimed, vehicle ≤ 10,000 lbs | **9** Final-Mile Van Drivers | GVWR 8,550-9,990. Hourly pay, $0 OT paid. | 631 (n = 8) | $24.9k |
| F6 Admin duties look clerical (needs review) | **29** Dispatchers | The duties text ("assigns loads using TMS routing recommendations… answers check-in calls") suggests following set procedures rather than discretion on matters of significance. Salary $40k-$47k passes the salary test. | 2,822 (n = 25; average 49 h/week) | $23.6k – $88.2k |
| F2 / F3 Hourly pay or no basis, coded Exempt | **1** (CL-105650) | Likely a data-entry error. No Q2 payroll. | — | — |

**Not flagged:** 46 CDL-A linehaul drivers (80,000 lbs, interstate, MCA plausible), 16 Warehouse Supervisors (6-20 reports), 12 Operations Managers, 10 HR Generalists and 12 Logistics Coordinators at or above the floor.

### Overtime-pay patterns (non-exempt hourly, clean Q2 payroll, n = 180)

| Pattern | Hub 1 | Hub 2 | Hub 3 | Total | Q2 shortfall |
|---|---|---|---|---|---|
| Correct (1.5 × regular rate) | 61 | 8 | 19 | 88 | $0 |
| **1.5 × base rate (differential/bonus excluded)** | 0 | **51** | 0 | 51 | $3,270 |
| **Straight time (1.0×)** | 4 | 3 | 0 | 7 | $2,448 |
| **OT hours, $0 paid** | 1 | 1 | 0 | 2 | $2,824 |
| No OT hours | 2 | 1 | 29 | 32 | — |

- **Hub 2 regular-rate exclusion:** of employees with OT and some differential or bonus, 51 of 54 at Hub 2 show the exclusion pattern, against 0 of 69 at Hubs 1 and 3 (Fisher p ≈ 2e-31). It is a payroll-configuration problem. The dollars per person are small, but every person affected counts, and the problem continues every pay period.
- **Hub 3 records far less paid OT than the other hubs:** 29 of 48 non-exempt employees (60%) have no OT hours, against 3 of 132 (2%) at Hubs 1 and 2. The off-the-clock test below explains why.

### Off-the-clock work (badge vs paid, n = 314)
- **Baseline:** the badge-minus-paid gap is very tight, with a median of 2.76 h/week (range 2.51-2.97 for the 284 unflagged employees). That matches the 2.5 h/week meal deduction plus clock-in and clock-out time.
- **30 employees exceed 4.0 h/week, all at Hub 3:** 18 of 18 Fleet Maintenance Technicians, 10 of 10 Forklift Operators and 2 of 6 Final-Mile Van Drivers (Hub 3 vs other hubs: Fisher p ≈ 9e-18).
- **Their gap** has a median of 9.5 h/week (range 5.8-18.0).
- **Their paid hours** average 39.6 h/week, **never exceed 40.00** in any period average, and record **0 OT hours**. That is consistent with paid time being capped at 40.
- **Estimated unpaid time:** about 2,578 hours in Q2, worth **$70.8k (straight time) to $106.2k (all at 1.5×)**. Most of it is likely over 40 hours, so the upper figure is more realistic.

Record-level detail is in `outputs/flsa_*.csv`.

---

## 3. Accommodation and leave requests followed by discipline

### Method and assumptions
- **Windows:** 90 days after `accommodation_request_date`, and 60 days after `leave_end_date` for **approved FMLA** leave.
- **Rate test:** events inside the windows vs all other employee time (hire date to termination or snapshot). The test is one-sided and exact (conditional binomial).
- **Narrative dates:** dates written inside narratives were parsed (formats m/d/yy, mm/dd/yyyy, "Mon dd"; year-less dates take the event year) to check overlap with leave dates.
- **FMLA eligibility:** tenure is checked from `hire_date`. The 1,250-hour test **cannot** be verified because there are no hours before Q2.
- **What timing shows:** timing alone does not establish retaliation. Each event was also checked for whether the narrative cites the condition, restriction or absence itself.

### Accommodation → discipline (ADA / PWFA)
- **33 employees** requested an accommodation: 16 Granted, 6 Withdrawn, 6 Pending, 5 Denied.
- **Rate test:** the 90-day windows hold 15 events in 2,093 person-days (**2.62 per person-year**). The rest of the workforce has 186 events in 134,406 person-days (**0.51 per person-year**). **Rate ratio 5.2, p = 6.6e-7.**
- **20 events** follow a request. **12 discipline the employee for the limitation itself**: Performance write-ups about pick rate under a lifting restriction, being seen sitting after asking to sit, "productivity below standard since disclosure of pregnancy", and lateness while a schedule change was "under review". These are high-priority failure-to-accommodate or retaliation leads:

| Event | Employee | Request | Outcome | Days after request | Action |
|---|---|---|---|---|---|
| DE-5123 | CL-105297 | Modified duty | Withdrawn | 10 | Final Written |
| DE-5060 | CL-102159 | Ergonomic equipment | Withdrawn | 12 | Written |
| DE-5159 | CL-106878 | Schedule modification | Granted | 14 | Written |
| **DE-5175** | CL-107471 | Modified duty | **Denied, no interactive process** | 19 | **Termination** |
| DE-5001 | CL-100013 | Pregnancy (PWFA) | Denied | 22 | Written |
| DE-5120 | CL-105080 | Lifting restriction | Granted | 31 | Final Written |
| DE-5107 | CL-104323 | Ergonomic equipment | Granted | 35 | Written |
| **DE-5031** | CL-101211 | Schedule modification | Granted | 38 | **Termination** |
| DE-5042 | CL-101593 | Lifting restriction | Withdrawn | 39 | Final Written |
| DE-5168 | CL-107175 | Ergonomic equipment | Granted | 47 | Written |
| DE-5078 | CL-103029 | Schedule modification | **Pending (stale)** | 56 | Written |
| DE-5177 | CL-107512 | Lifting restriction | **Denied, no interactive process** | 57 | Written |

- **The other 8 post-request events, after reading the narratives:**
  - **Unrelated and legitimate:** DE-5006 (slur → termination), DE-5034 and DE-5184 (threat or altercation).
  - **Raise a different statute:** DE-5170 and DE-5081 are Section 7 events (see §4). DE-5079, DE-5080 and DE-5185 are FMLA attendance events (see below).
- **CL-103029 is a chain:**
  1. Schedule-modification request, still pending after 176 days.
  2. Approved FMLA family-care leave.
  3. Written warning.
  4. Attendance points for absences during the FMLA leave.
  5. Final warning.
  6. Termination (DE-5081) for delivering a group letter about heat.
- **Process gaps:**
  - Denied with no documented interactive process: CL-100105, CL-101497, CL-107471, CL-107512.
  - Pending more than 60 days at the snapshot: CL-100247 (since 2025-07-13), CL-103029, CL-108326.
- **Every narrative that mentions a restriction, medical issue or pregnancy (12) belongs to an employee with an accommodation request on file.** There is no sign of missed-notice cases. A first version of the keyword pattern also matched "schedule changes" in six group-meeting narratives. Those were false positives and the pattern was corrected.

### FMLA leave → discipline
- **112 employees requested leave.** FMLA requests: 15 approved, 55 denied. Almost all denials cite "Not FMLA eligible (<12 months)", and tenure confirms it for every case but one.
- **Rate test:** the 60-day post-leave windows hold 13 events in 530 person-days (**8.95 per person-year**), against **0.50 per person-year** for the rest. **Rate ratio 17.7, p = 2.2e-12.**
- **All 9 attendance events that cite a family or medical reason** ("caring for parent after surgery", "with newborn", "flare-up of condition", "doctor's note… occurrences still assessed") are for employees with **approved FMLA leave whose dates cover the absences**. Each assessed attendance points. **8 of the 9 are Final Written Warnings.** Counting FMLA-protected absences under a no-fault policy is interference (29 CFR 825.220(c)). Events: DE-5052, DE-5075, DE-5079, DE-5080, DE-5092, DE-5113, DE-5135, DE-5172, DE-5185. The first eight came 1-14 days after leave ended or during it; DE-5185 came 4 days after.
- **Wrong denial:** CL-105915's FMLA bonding leave was denied as "<12 months", but tenure at the leave start was **541 days**. If the 1,250-hour test was met, that is a wrongful denial (interference).
- **USERRA:** all 7 military leave requests were approved, so no issue.

Record-level detail is in `outputs/ada_fmla_sequences.csv`.

---

## 4. NLRA Section 7 screen of the discipline narratives (203 events)

### Coding rules (fixed in code before review, then every non-"None" event read by hand)
1. **Section 7 subject:** wages or pay; hours, OT or scheduling; safety or heat; union activity; a complaint to a government agency; discussing a workplace investigation.
2. **Concertedness indicator:** words such as coworkers, others, group, on behalf of, petition or signatures, signed letter, "who's with me", "several of the …", a group chat or group text, or a count of named coworkers. Discussing wages and union activity are treated as inherently concerted.
3. **Individual-only indicator:** "No other employees involved", "No coworker engagement", "personal dispute", "own schedule" → **Low**.
4. **Aggravating conduct:** profanity, throwing objects, exposing customer information → downgrades **High** to **Medium**, because whether the conduct loses protection depends on the setting.
5. **Statutory supervisors:** Warehouse Supervisor or Operations Manager with 2 or more reports → **Low**. Supervisors are outside NLRA coverage under §2(3) and §2(11). Shift Leads without authority stay covered.
6. The company rule each narrative relies on was tagged, as a lead for a handbook review. Under the *Stericycle* (2023) framework, rules that chill Section 7 activity are suspect. The Board standard can change, so confirm the current law.

### Results

| Risk | Events | Actions taken |
|---|---|---|
| **High** | **33** | 18 Final Written, 8 Written, **7 Terminations**, 0 Verbal |
| **Medium** | 6 | 3 Verbal, 3 Written |
| Low (individual complaint) | 5 | 5 Verbal |
| Low (statutory supervisor) | 2 | DE-5150 (outburst), DE-5179 (posting coworker wages) |
| None | 157 | Attendance, safety, performance and misconduct with no Section 7 subject |

**High-risk themes:**

| Theme | Events | Rule relied on |
|---|---|---|
| Recording a meeting about bonus changes and sharing it with coworkers | 8 | No-recording rule |
| Telling the supervisor coworkers will contact the DOL about unpaid pre-shift time | 5 | "Threatening / insubordinate". This is also FLSA §215(a)(3) retaliation, and the underlying claim matches the off-the-clock finding in §2. |
| Discussing an ongoing investigation with coworkers | 4 | Blanket confidentiality instruction |
| Group letter or petition about heat, water or fans | 5 | "Chain of command", "undermining mgmt" |
| Discussing or comparing pay | 2, plus 1 supervisor | Pay-confidentiality rule. Also a likely 8(a)(1) violation in the rule itself. |
| Group refusal to load over a damaged dock plate (spokesperson) | 2 | Insubordination. Also NLRA §502 and OSHA 11(c). |
| Social-media post about cut breaks with coworker replies ("who's with me") | 3 | "Disparaging the company" |
| Union authorization cards in the parking lot before shift | 2 | No-solicitation (nonwork time, nonwork area: *Republic Aviation*) |
| Group chat comparing pay and schedules | 1 | "Unofficial work communications" |
| Questioning mandatory Saturday OT "on behalf of the whole shift" | 1 | "Negative attitude" |

**Medium (judgment calls):**
- 5 profane outbursts with a thrown clipboard in a group meeting about schedule changes where "others had raised the same concerns". Whether the conduct loses protection depends on the setting.
- 1 TikTok complaining about short staffing that shows customer labels. The confidentiality interest may outweigh the protection.

**Low:**
- 3 "my supervisor is an idiot" posts with no coworker engagement.
- 2 refusals of an individual's own schedule with "no other employees involved".

**Discipline severity:**
- Among **first offenses**, 21 of 21 High-risk events started above a Verbal Warning (100%), against 34 of 136 other first offenses (25%) (Fisher p ≈ 1e-11).
- Section 7 events skip progressive discipline. Combined with the employer's own rule citations, that is evidence of animus or disparate treatment.

**`pca_flag` cross-check (418 employees):**

| | No High-risk narrative | Has High-risk narrative |
|---|---|---|
| `pca_flag` = 0 | 366 | **5** |
| `pca_flag` = 1 | 27 | 20 |

- **Under-flagging:** 5 employees with clear Section 7 discipline are not flagged: CL-103648, CL-104243, CL-104880, CL-107007, CL-108125.
- **27 flagged employees with no Section 7 narrative:** this does not mean they were wrongly flagged. Protected activity need not produce discipline, and the data has no activity dates.
- **Outcomes for flagged employees:**
  - Any discipline: 59.6% vs 34.8% (p = 0.001).
  - Involuntary termination: **17.0% vs 4.9%** (n = 47 / 371, Fisher p = 0.005).
- **Limit:** without the date of the protected activity, timing between activity and discipline cannot be tested.

Record-level detail is in `outputs/nlra_narrative_screen.csv`, one row per event with the subject, concertedness, rule invoked, supervisor status and risk.

---

## Assumptions (consolidated)

1. **Law:** federal only (README). Thresholds as stated in §2.
2. **Proxies:** BISG race, name-inferred sex, self-reported age band and requested accommodation (for disability) are imperfect proxies. Proxy error usually *understates* disparities.
3. **AEDT comparator:** the highest-rate group with n ≥ 30. Fisher exact two-sided tests, Holm-adjusted within each family. The four-fifths rule is a rule of thumb, so statistical significance and practical shortfall are both reported.
4. **Unscored applicants:** reported both ways (population A excludes them, population B counts them as not selected).
5. **Excluded IDs:** conflicting-duplicate IDs are excluded from the AEDT analysis. Rejected applicants who carry employee records are excluded from the employee analyses. Payroll rows with defects are excluded from the payroll tests.
6. **Duties:** judged only from HR's job-description summary. Dispatchers need fact-finding on actual duties before any conclusion.
7. **Regular rate:** includes the shift differential and the full period's nondiscretionary bonus. The bonus is treated as earned within the period and spread evenly.
8. **Meal deduction:** 2.5 h/week. Off-the-clock time is badge time minus paid time minus the meal deduction. This assumes badge time approximates time worked and that the meal period was actually taken.
9. **Exposure figures:** Q2 2026 only. No lookback, liquidated damages, interest or state law.
10. **Sequence windows:** 90 days (accommodation) and 60 days (FMLA). The baseline is all other employee-days. The tests are one-sided, because the hypothesis is directional.
11. **FMLA eligibility:** the 1,250-hour requirement is not verifiable from the data.
12. **NLRA coding:** rule-based, then checked by hand. "None" events that mention coworkers were reviewed and are all altercation or threat cases. Risk ratings are screening judgments, not predictions of NLRB outcomes. Board standards (for example *Stericycle* and *Lion Elastomers*) are subject to change.
13. **Narrative dates without a year:** given the event's year, moved back a year if that put them more than 31 days after the event.
