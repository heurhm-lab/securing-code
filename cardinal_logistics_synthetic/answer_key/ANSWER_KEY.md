# ANSWER KEY: Cardinal Logistics Synthetic Dataset

> **SPOILERS.** Read this only after the analysis is finished.

## Files in this folder

| File | Contents |
|---|---|
| `ground_truth_people.csv` | One row per unique applicant. Holds the true race/ethnicity, gender, age, latent disability, latent qualification, whether the person actually engaged in PCA, the correct regular rate and overtime due, and a `;`-separated list of `issues` codes. |
| `ground_truth_discipline.csv` | One row per event: `narrative_class`, `nlra_risk`, `other_risk` and `dq_issue`. |
| `generate_dataset.py` | The generator. Seed `20261012`. |
| `key_stats.py` / `key_stats_output.txt` | Recomputes every number quoted below. |

Join to the public files on `applicant_id` and `event_id`. The numbers below are for unique applicants (1,240). The public file has 1,249 rows because of the planted duplicates.

---

## 1. AEDT and hiring: disparate impact

**How the score was built.** WorkFit Predict = job-relevant ability + penalties that have nothing to do with the job:

| Penalty | Size | Who it lands on |
|---|---|---|
| Age 40+ | −5.5 | Older applicants |
| Age 55+ | an extra −3 | Older applicants |
| Résumé gap | −0.30 per month, capped at 36 months | Women (caregiving) and people with disabilities |
| Commute over 8 miles | −0.60 per mile | Applicants from ZIP clusters B and C (mostly Black and Hispanic), because of residential segregation |
| Women in Forklift, Driver and Fleet Tech roles | −7 | Women |
| Accommodation requested during the assessment | −8 | Applicants with disabilities |

| Finding | Expected result |
|---|---|
| **Age (ADEA)** | Advance rate is 31.8% for 40+ vs 51.0% for under 40. **Impact ratio (IR) = 0.62.** By band, the IR falls steadily: 0.71 (40-49), 0.61 (50-59), 0.43 (60+). The hire IR is also 0.60. |
| **Age: recruiter override** | Even among people the tool advanced, 58% of those 40+ were hired vs 71% of those under 40. **28 notes use age-coded language**, for example "Overqualified", "more energy", "close to retiring" and "digital native". |
| **Age is not job-related** | The 90-day performance rating is *higher* for 40+ (3.58 vs 3.45). The score's correlation with performance (r ≈ 0.54) comes from real ability. **Commute and gap do not predict performance** (r ≈ 0.10 and −0.02). This is the validation evidence that defeats a "business necessity" defense. |
| **Race/ethnicity: proxy** | BISG Advance IR: Black 0.80, Hispanic 0.81. Both sit right at the four-fifths line, but both differences are statistically significant: two-proportion z ≈ −2.6 for Black and −2.5 for Hispanic, compared with White. |
| **Race/ethnicity: true** | Black 0.80, **Hispanic 0.72**. BISG misclassification (about 26% of rows) pulls the proxy estimate toward 1.0. This is a teaching point about using proxies. |
| **Mechanism** | `commute_miles` correlates with score at r ≈ −0.23 and is unrelated to performance. The Advance rate is 0.53 for ZIPs 7001x, 0.37 for 7002x, 0.33 for 7003x and 0.43 for 7004x. Commute stands in for race. |
| **The bottom line is not a defense** | At the *final hire* stage, Black applicants reach an IR of about 0.96 because referral and manager overrides fill the gap. Under *Connecticut v. Teal* (1982), the adverse impact at the AEDT step still counts. Hispanic applicants stay at an IR of 0.81 even at final hire. |
| **Referral overrides** | Of 95 "Do Not Advance" applicants with an employee referral, 39 were hired. Of 561 "Do Not Advance" applicants without one, 14 were hired. Referrals are concentrated among White applicants (17.7% vs 11-12% of Black and Hispanic applicants). **26 notes** document a manager override. |
| **Sex** | In Forklift, Driver and Fleet Tech roles, the true-gender IR is **0.57**. The name-inferred proxy shows only 0.83, plus a 0.62 IR for `Unknown`. Proxy error hides most of the effect. |
| **Disability (ADA screen-out)** | Applicants who requested an accommodation: Advance IR **0.30**, hire IR 0.40. **17 of the 44** were never scored and were auto-rejected ("could not be scored, moved on"). This is a failure to accommodate in the selection procedure (42 U.S.C. §12112(b)(5)-(7)). |
| **Gap-month penalty** | The Advance rate drops from 45% (gap of 3 months or less) to 28% (gap over 12 months). It falls on women and people with disabilities, and does not predict performance. |
| **Other notes** | **6** national-origin notes on CSR rejections ("Heavy accent"). **4** caregiver-coded notes ("ask about childcare"). **31** notes give legitimate rejection reasons (failed drug screen, DOT physical, and so on). These 31 are true negatives, not violations. |

ADEA caveat: the 7th and 11th Circuits (*Kleber*, *Villarreal*) hold that ADEA disparate-impact claims are not available to *applicants*. Disparate treatment, shown by the recruiter notes, still applies.

---

## 2. FLSA: classification and overtime

The estimated Q2 shortfall is calculated as follows:

- Overtime due = 1.5 × regular rate × OT hours, minus OT already paid.
- For misclassified salaried staff, regular rate = salary ÷ 2,080. This is an upper bound. Under the fluctuating-workweek method (0.5×) it would be about one third.

| Code (`issues`) | Count | What is wrong | Q2 shortfall (est.) |
|---|---|---|---|
| `salary_below_threshold` | 18 | Logistics Coordinators classified as Administrative-exempt at a salary below **$35,568** ($684/wk). The 2024 increase was vacated, so the 2019 level applies. They fail the salary test outright. Coordinators paid at or above $35,568 are **reasonably exempt**: their duties involve discretion over carrier selection and rate negotiation. Those are true negatives. | ≈ $31k |
| `dispatcher_admin_exemption_doubtful` | 29 (all Dispatchers) | Admin exemption, but the duties summary is "assigns loads using TMS recommendations… answers check-in calls". That is no discretion or independent judgment on matters of significance. **Likely misclassified**, although the duties need fact-finding. | ≈ $88k |
| `exec_exemption_fails_duties` | 4 | Job title "Shift Lead" coded as Executive-exempt. They have 0-1 direct reports, spend about 70% of their time on manual work, and have no hire/fire input. They fail the executive test (2+ FTE reports and hire/fire weight). Real Warehouse Supervisors with 6-20 reports are true negatives. | ≈ $25k |
| `mca_small_vehicle_misapplied` | 9 | Final-Mile Van Drivers in vans with a GVWR of 10,000 lbs or less, classified Motor Carrier Act exempt. The **small-vehicle exception** (SAFETEA-LU TCA 2008) makes them owed overtime. CDL-A linehaul drivers at 80,000 lbs on interstate routes are **properly exempt**. Those are true negatives, a deliberate trap. | ≈ $25k |
| `hourly_coded_exempt` | 1 (CL-105650) | Hourly Warehouse Associate coded `Exempt`, with no exemption basis. It is a data-entry error. This person has no Q2 payroll. | n/a |
| `ot_paid_straight_time` | 7 | Non-exempt employees whose OT was paid at 1.0× the base rate. | ≈ $2.4k |
| `ot_unpaid` | 2 | OT hours recorded but $0 OT paid. | ≈ $2.8k |
| `regular_rate_excludes_diff_bonus` | 52 | **All of Hub 2** computes OT on the base rate only. Night differential and nondiscretionary bonuses are left out (29 CFR 778.207(b), 778.208-.211). It is systemic but small per person. Hubs 1 and 3 calculate it correctly. | ≈ $3.4k |
| `off_the_clock_capped_40` | 30 | At **Hub 3**, Forklift and Fleet Tech staff, plus some Final-Mile drivers, have paid time **capped at 40.00 h/week** (period average 37.9-40.0, never above 40). Badge time exceeds paid time by about 6-18 h/week (median 9.5). For everyone else the gap is only the meal period, a tight 2.7-3.0 h/week, which is the expected baseline. Excess hours above 40 and pre- and post-shift time go unpaid. | ≈ $106k (upper bound) |

Other notes:

- `flsa_classification` uses 9 spellings: `Exempt`, `EXEMPT`, `exempt`, `E`, `Non-Exempt`, `NON-EXEMPT`, `Nonexempt`, `non exempt` and `NE`. Normalize them before analysis.
- Exempt employees who have OT hours but $0 OT pay are **not** a violation by themselves when the exemption is valid (Ops Managers, HR Generalists, real Supervisors, linehaul drivers).

---

## 3. NLRA: discipline narratives (203 events)

| `narrative_class` | n | Correct call |
|---|---|---|
| `pca` | 34 | **High NLRA risk** (Section 7 / 8(a)(1)). Themes: discussing wages or a wage-confidentiality rule; petitions or group letters about heat and safety; social-media posts with coworker engagement about working conditions; a group refusal over an unsafe dock plate or missing guard (also NLRA §502 / OSHA 11(c)); union cards or union talk on nonwork time in nonwork areas (*Republic Aviation*); union buttons or t-shirts; speaking "on behalf of the shift" ("negative attitude", "ringleader"); a group march to the GM; a blanket investigation-confidentiality order; a no-recording rule applied to a meeting about bonuses (*Stericycle* 2023 work-rule standard); telling the supervisor coworkers will go to the DOL (also FLSA §215(a)(3) retaliation). **Every PCA event skipped progressive-discipline steps**: none is a Verbal Warning, and 7 are Terminations. |
| `ambiguous` | 7 | **Medium.** Cases: a profane outburst in a group meeting where others shared the concern (setting-specific, *Lion Elastomers* 2023); a TikTok showing customer labels (a confidentiality interest may outweigh); one employee refusing OT "none of us are doing it" when no one else joined (is it concerted?); off-duty picket-line insults (*Clear Pine Mouldings*-type analysis). |
| `individual_gripe` | 6 | **Low.** A purely personal complaint, such as one's own schedule, being passed over for promotion, or "my supervisor is an idiot" with no coworker engagement. This is **not concerted**, so it tests precision. |
| `legit` | 135 | **None.** Real attendance, safety, performance and conduct violations, including a slur, theft, LOTO bypass and fuel-card misuse. |
| `fmla_interference` | 9 | No NLRA issue. They are **FMLA interference**: approved FMLA absences were counted as attendance occurrences (29 CFR 825.220(c)). All 9 were Final Written Warnings. |
| `accommodation_retaliation` | 12 | No NLRA issue. They are **ADA/PWFA** problems: discipline 10-60 days after an accommodation request, such as pick rate under a lifting restriction, sitting, pregnancy-related productivity, or lateness while a schedule change was "under review". |

**Statutory supervisors.** Two PCA-type events (DE-5150, DE-5179) involve real Warehouse Supervisors. Supervisors are excluded from NLRA coverage (§2(3), §2(11)), so the risk is **low** despite the content. Shift Leads with no authority are still covered employees.

**`pca_flag` quality**

| Measure | Result |
|---|---|
| True PCA employees left unflagged (`pca_unflagged`) | **7**. Five of their PCA narratives sit on unflagged employees. |
| Flagged with no PCA (`pca_flag_false_positive`) | **7** |
| Involuntary termination rate | 17.0% flagged vs 4.9% not flagged |
| Any-discipline rate | 57% flagged vs 35% not flagged |

The flag shows a **retaliation pattern** even before reading the narratives.

---

## 4. ADA / PWFA / FMLA / USERRA (non-NLRA)

| Code | IDs / count | Issue |
|---|---|---|
| `accommodation_denied_no_interactive_process` | CL-100105, CL-101497, CL-107471, CL-107512 | Accommodation denied with `interactive_process_documented = N`. |
| `accommodation_stale_pending` | CL-100247, CL-103029, CL-108326 | Request still `Pending` more than 60 days after it was made. |
| Accommodation → discipline | 12 events | See §3. |
| `fmla_denied_wrong_reason` | CL-105915 | Denied as "<12 months" although tenure at the leave start was over 12 months. Other "<12 months" denials are correct. |
| `userra_leave_denied` | none in this seed | The code exists in the generator but did not fire. |
| PWFA | among the accommodation-retaliation events | Pregnancy-related accommodation requests followed by a productivity warning. |

---

## 5. Disparate discipline (Title VII)

- Black employees have a higher base discipline rate in the generator. The observed share with any discipline is 42% for Black (BISG) vs 36% for White.
- Black employees are also bumped one step above the progressive-discipline step 45% of the time. On **first offenses**, 43% of Black employees got more than a Verbal Warning, vs 28% of White employees.
- The Hispanic and Asian groups show similar noise (n = 27 and 12). **Expect a modest signal that is not robust.** A careful analyst should report it as worth investigating, not as proven.
- `other_risk = "Severity above progressive-discipline step…"` marks 9 events.

---

## 6. Data-quality defects

| Code | IDs | Defect |
|---|---|---|
| `dq_exact_duplicate_row` | CL-100601, CL-102735, CL-103909, CL-105449, CL-107554, CL-108259 | Exact duplicate rows. |
| `dq_conflicting_duplicate_aedt_score` | CL-104284, CL-106172, CL-106477 | Same ID with a different `aedt_score` (+4 to +9). CL-104284 now reads 68.1 but is still marked `Do Not Advance`. |
| `dq_age_band_vs_grad_year` | 9 rows (see `issues`) | Age band shifted two bands from what `hs_grad_year` implies. |
| `dq_rejected_with_employee_record` | CL-103433, CL-108582 | `Rejected`, but with a hire date, Active status and FLSA class (an ATS/HRIS merge error). |
| `dq_impossible_hours` | CL-103935 | 2,184 hours in 13 weeks (168 h/week). |
| `dq_negative_ot_pay` | CL-106345 | Negative `overtime_pay_period`. |
| `dq_hours_components_dont_sum` | CL-107929 | Regular + OT does not equal hours worked (regular is +40). |
| `dq_missing_badge_hours` | CL-101497 | Badge hours are blank. |
| `dq_discipline_count_mismatch` | 5 employees | `discipline_event_count` does not match the events file. |
| `dq_discipline_before_hire` | DE-5100 (CL-104032), DE-5196 (CL-108225) | `event_date` is before the hire date. The narrative's own date differs from `event_date`. |

Other things to notice:

- `aedt_score` is blank for 41 applicants: 17 were left unscored because of an accommodation (§1) and the rest did not finish the assessment.
- `hs_grad_year` is blank for about 6% of applicants.
- Narratives use mixed date formats.

---

## Scoring rubric (suggested)

| Area | Full credit requires |
|---|---|
| AEDT | Age IR of about 0.6 by band; the commute → race mechanism; the accommodation screen-out; that the bottom line is not a defense; proxy attenuation of sex and race. |
| FLSA | The salary test (18); MCA small vehicles (9); Shift Leads (4); Hub 2 regular rate; the Hub 3 40.00 cap; Dispatchers flagged for duties review. Linehaul drivers, real supervisors and correctly paid coordinators **not** flagged. |
| NLRA | At least 30 of 34 PCA narratives flagged High. Gripes rated Low. Ambiguous cases rated Medium with reasons. The supervisor exclusion noted. FMLA and ADA events routed to the right statute. Flag precision and recall problems noted. |
| Data quality | At least 8 of the 10 DQ categories found. |
