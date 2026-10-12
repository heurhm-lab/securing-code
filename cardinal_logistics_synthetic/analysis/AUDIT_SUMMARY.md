# Cardinal Logistics: Ranked Audit Summary

Synthetic dataset · Analysis of `data/` only (the answer key was not read) · Source report: `analysis/REPORT.md` · Snapshot 2026-06-30

This is a compliance screen, not legal advice. Each item is a lead for counsel to verify.

## How findings are scored

Each finding is scored 1-5 on three scales. **Priority = Likelihood × Severity × Reversibility** (range 1-125). Multiplying means a finding has to score on all three to rise, and one low factor pulls it down. Ties are broken by severity, then likelihood. The scores are ordinal judgments, not probabilities or dollar values.

**Likelihood**

| Score | Label | Meaning |
|---|---|---|
| 5 | Near-certain | The violation shows on the face of the records (e.g., a salary below the legal floor), or a statistically significant pattern is corroborated by documents. |
| 4 | Likely | Strong statistical or documentary evidence. An innocent explanation is possible but would need specific facts the records do not show. |
| 3 | Possible | A significant but proxy-dependent or borderline result, or a documentary lead without corroboration. |
| 2 | Uncertain | Not statistically significant, small samples, or a judgment call that could go either way. |
| 1 | Remote | Speculative. Included only for completeness. |

**Severity**

| Score | Label | Meaning |
|---|---|---|
| 5 | Critical | Loss of a job or job opportunity, discipline or termination for protected activity, or a systemic violation across a whole group where willfulness or liquidated damages are likely. |
| 4 | High | Adverse action against identifiable individuals (discipline, rejection), or pay loss over $50k per quarter. |
| 3 | Moderate | Pay loss of $5k-$50k per quarter, or process failures with real but limited individual impact. |
| 2 | Low | Under $5k per quarter, or a technical violation. |
| 1 | Minimal | Record-keeping or data integrity with no direct harm to individuals. |

**Reversibility (5 = hardest to reverse)**

| Score | Label | Meaning |
|---|---|---|
| 5 | Irreversible | The harm is complete and the people affected cannot realistically be found or made whole. |
| 4 | Hard to reverse | Needs reinstatement offers, re-contacting rejected applicants, or individual back-pay work, and part of the harm (a lost job, chilled activity) cannot be fully undone. |
| 3 | Partly reversible | Records and discipline can be rescinded, but later decisions built on them have to be traced and corrected. |
| 2 | Reversible at a cost | Fixed by paying current employees what they are owed. The limitations clock keeps running until it is fixed. |
| 1 | Easily reversed | A data, configuration or policy fix going forward. |

**Action tiers** (proportionate response): Act now = priority 60 or more; Act this quarter = 30-59; Schedule = 15-29; Housekeeping = under 15. Separately, an item marked **Ongoing** keeps causing harm every pay period or every applicant until it is stopped. Whatever its rank, an ongoing item should get its containment step (stopping the practice) right away; the full remediation can then follow at its tier's pace.

Remediation is scaled to the evidence:

- Likelihood 4-5: correct and make people whole.
- Likelihood 3: investigate first, contain if cheap.
- Likelihood 2 or less: collect better data before acting.

## Ranked findings

| Rank | ID | Area | Finding | L | S | R | Priority | Tier | Ongoing |
|---|---|---|---|---|---|---|---|---|---|
| 1 | F02 | AEDT / ADEA | AEDT screens out applicants 40+ | 5 | 5 | 4 | **100** | Act now | Yes |
| 2 | F03 | AEDT / ADA | Applicants who asked for an assessment accommodation were screened out | 5 | 5 | 4 | **100** | Act now | Yes |
| 3 | F01 | NLRA | Discipline imposed for Section 7 activity | 4 | 5 | 4 | **80** | Act now | No |
| 4 | F06 | FLSA retaliation | Discipline for saying coworkers would complain to the DOL | 4 | 5 | 4 | **80** | Act now | No |
| 5 | F07 | ADA / PWFA | Discipline for the limitation an accommodation was meant to address | 4 | 5 | 4 | **80** | Act now | No |
| 6 | F16 | ADEA | Age-coded recruiter notes and post-AEDT age gap | 4 | 4 | 4 | **64** | Act now | Yes |
| 7 | F15 | AEDT / Title VII | AEDT race disparity through commute distance | 3 | 5 | 4 | **60** | Act now | Yes |
| 8 | F04 | FMLA | Attendance points assessed for approved FMLA absences | 5 | 4 | 3 | **60** | Act now | Yes |
| 9 | F21 | NLRA | 'PCA flag' tracks protected activity and predicts termination | 4 | 4 | 3 | **48** | Act this quarter | Yes |
| 10 | F18 | Title VII | Accent cited in CSR rejections | 3 | 4 | 4 | **48** | Act this quarter | No |
| 11 | F08 | FLSA | Off-the-clock work at Hub 3 | 4 | 5 | 2 | **40** | Act this quarter | Yes |
| 12 | F19 | Title VII / ADA | Résumé-gap penalty and caregiver-coded notes | 3 | 3 | 4 | **36** | Act this quarter | Yes |
| 13 | F05 | NLRA | Work rules that restrict Section 7 activity | 4 | 4 | 2 | **32** | Act this quarter | Yes |
| 14 | F20 | AEDT / Title VII | Possible sex impact in physical roles (inconclusive) | 2 | 4 | 4 | **32** | Act this quarter | Yes |
| 15 | F10 | FLSA | Logistics Coordinators paid below the exempt salary floor | 5 | 3 | 2 | **30** | Act this quarter | Yes |
| 16 | F11 | FLSA | Van drivers wrongly treated as Motor Carrier Act exempt | 5 | 3 | 2 | **30** | Act this quarter | Yes |
| 17 | F17 | Title VII | Referral overrides favor White applicants | 3 | 3 | 3 | **27** | Schedule | Yes |
| 18 | F23 | FMLA | FMLA leave denied as '<12 months' with 541 days' tenure | 3 | 3 | 3 | **27** | Schedule | No |
| 19 | F09 | FLSA | Dispatchers may not meet the administrative exemption | 3 | 4 | 2 | **24** | Schedule | Yes |
| 20 | F12 | FLSA | Shift Leads classified as executives without supervisory authority | 4 | 3 | 2 | **24** | Schedule | Yes |
| 21 | F22 | ADA / PWFA | Accommodation requests denied without process or left pending | 4 | 3 | 2 | **24** | Schedule | Yes |
| 22 | F13 | FLSA | Hub 2 leaves differential and bonuses out of the overtime rate | 5 | 2 | 2 | **20** | Schedule | Yes |
| 23 | F14 | FLSA | Overtime paid at straight time or not at all | 5 | 2 | 2 | **20** | Schedule | Yes |
| 24 | F24 | NLRA | Setting-dependent cases (Medium risk) | 2 | 3 | 3 | **18** | Schedule | No |
| 25 | F25 | Data integrity | Conflicting AEDT scores for the same applicant | 2 | 3 | 3 | **18** | Schedule | No |
| 26 | F26 | FLSA | Hourly associate coded Exempt | 4 | 2 | 1 | **8** | Housekeeping | Yes |
| 27 | F27 | Data integrity | Record defects across HR and payroll data | 5 | 1 | 1 | **5** | Housekeeping | No |

## Findings in detail

### 1. F02 · AEDT screens out applicants 40+

**Area:** AEDT / ADEA  
**Scores:** L 5 · S 5 · R 4 → **Priority 100** (Act now; ongoing)

**Evidence.** Advance rate 33.3% for 40+ vs 52.5% for under 40: impact ratio 0.63 (n = 444 / 752, p < 1e-9). Ratios fall by band: 0.71, 0.61, 0.43 (60+). Holding other factors constant, the score is 5-10 points lower for 40+ bands. At the same score, under-40 hires rate 0.36 points lower (p < 1e-4), so the score under-predicts older workers.

**Remediation.** Stop using the cut score of 65 as an automatic screen now. Route every applicant to human review using job-related criteria until the tool is validated. Require the vendor to disclose its features and validation evidence. Run a job-relatedness study. Re-review 40+ applicants the tool rejected within the charge-filing window for openings that are still available.

**Legal basis.** ADEA §4(a), 29 U.S.C. §623(a). Disparate impact: Smith v. City of Jackson, 544 U.S. 228 (2005); RFOA defense, 29 C.F.R. §1625.7. Applicant disparate-impact claims are limited in some circuits (Kleber v. CareFusion, 7th Cir. 2019 (en banc); Villarreal v. R.J. Reynolds, 11th Cir. 2016 (en banc)); disparate treatment is not. An employer is responsible for a vendor tool it uses. Check any state or local AEDT law where hiring occurs.

### 2. F03 · Applicants who asked for an assessment accommodation were screened out

**Area:** AEDT / ADA  
**Scores:** L 5 · S 5 · R 4 → **Priority 100** (Act now; ongoing)

**Evidence.** Advance impact ratio 0.30 (n = 44 vs 1,193, p < 1e-4); hire ratio 0.40. 19 of the 44 were never scored, and none of the 19 was hired. 17 recruiter notes record rejection because the accommodation left them unscored.

**Remediation.** Set up an accommodation path for the assessment now (alternative format or extended time scored on equal terms, or individualized review). Re-contact all 44 requesters and reconsider them for open roles. Add accommodation duties to the vendor contract. Train recruiters.

**Legal basis.** ADA Title I, 42 U.S.C. §12112(b)(5)(A) (accommodating applicants), (b)(6) (screen-out criteria), (b)(7) (tests must measure skills, not impairment); 29 C.F.R. §§1630.10, 1630.11.

### 3. F01 · Discipline imposed for Section 7 activity

**Area:** NLRA  
**Scores:** L 4 · S 5 · R 4 → **Priority 80** (Act now)

**Evidence.** 33 events coded High risk: 7 terminations, 18 final warnings, 8 written warnings, no verbal warnings. Every High-risk first offense started above a verbal warning, against 25% of other first offenses (21 vs 136 events, Fisher p ≈ 1e-11). Themes include pay discussions, petitions and letters about heat, a group refusal over an unsafe dock plate, union cards, recording a bonus meeting, and discussing an investigation.

**Remediation.** Place a litigation hold on all discipline records. Have counsel review each of the 33 events. Rescind discipline where protected activity was the basis. For the 7 terminations, decide on reinstatement and back-pay offers person by person. Stop enforcing the cited rules until F05 is resolved.

**Legal basis.** NLRA §7 and §8(a)(1), 29 U.S.C. §§157, 158(a)(1). §8(a)(3) for union-related events. Remedies under §10(c), 29 U.S.C. §160(c). Safety refusals also implicate NLRA §502 (29 U.S.C. §143) and OSH Act §11(c) (29 U.S.C. §660(c)).

### 4. F06 · Discipline for saying coworkers would complain to the DOL

**Area:** FLSA retaliation  
**Scores:** L 4 · S 5 · R 4 → **Priority 80** (Act now)

**Evidence.** 5 events, a subset of F01, discipline employees for telling a supervisor that coworkers would contact the Department of Labor about unpaid pre-shift time (1 termination). The underlying complaint matches the off-the-clock pattern in F08.

**Remediation.** Rescind the discipline and route these cases to counsel with F01. Investigate the pre-shift time claim on its merits as part of F08. Remind managers that complaints to agencies, including oral complaints, are protected.

**Legal basis.** FLSA §15(a)(3), 29 U.S.C. §215(a)(3); oral complaints are protected (Kasten v. Saint-Gobain, 563 U.S. 1 (2011)). Also NLRA §7, because the complaint was concerted.

### 5. F07 · Discipline for the limitation an accommodation was meant to address

**Area:** ADA / PWFA  
**Scores:** L 4 · S 5 · R 4 → **Priority 80** (Act now)

**Evidence.** 12 events in the 10-57 days after an accommodation request discipline the limitation itself (2 terminations: DE-5175, DE-5031). Discipline in the 90 days after a request runs 5.2× the baseline (15 events in 2,093 person-days, exact p = 6.6e-7).

**Remediation.** Review each of the 12 events individually. Rescind discipline that penalizes the limitation. Decide on reinstatement offers for CL-107471 and CL-101211. Restart the interactive process for every affected employee.

**Legal basis.** ADA 42 U.S.C. §12112(b)(5)(A) (failure to accommodate) and §12203(a)-(b) (retaliation, interference); PWFA 42 U.S.C. §2000gg-1 and 29 C.F.R. Part 1636.

### 6. F16 · Age-coded recruiter notes and post-AEDT age gap

**Area:** ADEA  
**Scores:** L 4 · S 4 · R 4 → **Priority 64** (Act now; ongoing)

**Evidence.** 28 notes use age-coded language ('overqualified', 'more energy', 'close to retiring', 'digital native'). Among applicants the tool advanced, 62.8% of 40+ were hired vs 74.8% of under 40 (n = 137 / 373, p = 0.011).

**Remediation.** Review the decisions behind the 28 notes and reconsider affected applicants. Require a structured, job-related rejection reason in the ATS. Train recruiters.

**Legal basis.** ADEA 29 U.S.C. §623(a)(1) (disparate treatment); the notes are direct evidence of motive.

### 7. F15 · AEDT race disparity through commute distance

**Area:** AEDT / Title VII  
**Scores:** L 3 · S 5 · R 4 → **Priority 60** (Act now; ongoing)

**Evidence.** Race proxy impact ratios: Black 0.80, Hispanic 0.78 among scored applicants (Holm p = 0.030 and 0.015). The score falls 0.48 points per commute mile; mean commute is 16.4 mi for the Black proxy group and 15.5 for Hispanic, against 11.2 for White. Commute does not predict performance (at the same score, a positive coefficient).

**Remediation.** Remove commute and ZIP-derived features from scoring now. Collect voluntary self-identified race and ethnicity data and re-test. If impact remains, look for a less discriminatory alternative.

**Legal basis.** Title VII §703(k), 42 U.S.C. §2000e-2(k); Griggs v. Duke Power Co., 401 U.S. 424 (1971); Connecticut v. Teal, 457 U.S. 440 (1982) (a balanced bottom line does not cure impact at a step); 29 C.F.R. §§1607.3(B), 1607.4(D).

### 8. F04 · Attendance points assessed for approved FMLA absences

**Area:** FMLA  
**Scores:** L 5 · S 4 · R 3 → **Priority 60** (Act now; ongoing)

**Evidence.** All 9 attendance write-ups that cite a family or medical reason count absences inside approved FMLA leave; 8 are final warnings. Discipline in the 60 days after approved leave runs 17.7× the baseline (13 events in 530 person-days, exact p = 2e-12).

**Remediation.** Rescind the 9 write-ups and the points. Trace any later discipline or termination that relied on them; CL-103029 was later terminated. Configure the attendance system so FMLA-designated absences never generate points. Train supervisors.

**Legal basis.** FMLA §105(a)(1), 29 U.S.C. §2615(a)(1); 29 C.F.R. §825.220(c) (FMLA leave cannot count under no-fault attendance policies). Damages, including liquidated damages, under 29 U.S.C. §2617.

### 9. F21 · 'PCA flag' tracks protected activity and predicts termination

**Area:** NLRA  
**Scores:** L 4 · S 4 · R 3 → **Priority 48** (Act this quarter; ongoing)

**Evidence.** Employee Relations keeps a flag for protected concerted activity. Flagged employees are involuntarily terminated at 17.0% vs 4.9% (n = 47 / 371, p = 0.005), and disciplined at 59.6% vs 34.8% (p = 0.001). 5 employees with clear Section 7 discipline are unflagged.

**Remediation.** Have counsel review the flag's purpose and who can see it. Remove it from any decision workflow. Preserve it (do not delete it; it is evidence). Audit who used it and for what.

**Legal basis.** NLRA §8(a)(1) (surveillance or the impression of it) and §8(a)(3); employer knowledge under Wright Line, 251 NLRB 1083 (1980).

### 10. F18 · Accent cited in CSR rejections

**Area:** Title VII  
**Scores:** L 3 · S 4 · R 4 → **Priority 48** (Act this quarter)

**Evidence.** 6 rejection notes for Customer Service applicants cite an accent ('may confuse customers').

**Remediation.** Review each rejection for a documented, job-related communication assessment. Reconsider applicants where none exists.

**Legal basis.** Title VII §703(a), 42 U.S.C. §2000e-2(a). Under EEOC national-origin guidance, accent is a lawful basis only when it materially interferes with job performance.

### 11. F08 · Off-the-clock work at Hub 3

**Area:** FLSA  
**Scores:** L 4 · S 5 · R 2 → **Priority 40** (Act this quarter; ongoing)

**Evidence.** 30 employees (all Hub 3 Fleet Techs and Forklift Operators, plus 2 van drivers) have paid time capped at 40 h/week and no OT. Their badge time exceeds paid time by a median of 9.5 h/week, against a tight 2.75 h/week meal-only baseline elsewhere (Hub 3 vs other hubs: p ≈ 9e-18). About 2,578 unpaid hours, worth $70.8k-$106.2k in Q2 alone.

**Remediation.** Remove the 40-hour cap now and pay all verified time. Reconstruct hours from badge data back through the limitations period and pay what is owed. Retrain supervisors on recording hours.

**Legal basis.** FLSA §7(a), 29 U.S.C. §207(a); hours worked, 29 C.F.R. §§785.11-.13; records, 29 U.S.C. §211(c) and 29 C.F.R. §516.2; limitations, 29 U.S.C. §255 (3 years if willful); liquidated damages, §216(b).

### 12. F19 · Résumé-gap penalty and caregiver-coded notes

**Area:** Title VII / ADA  
**Scores:** L 3 · S 3 · R 4 → **Priority 36** (Act this quarter; ongoing)

**Evidence.** The score falls 0.29 points per gap month (p < 1e-4). Gaps run longer for applicants inferred female (5.0 vs 2.9 months). Gap does not predict performance. 4 notes ask about childcare or kids.

**Remediation.** Remove the gap feature. Review the 4 decisions with caregiver notes.

**Legal basis.** Title VII sex-plus (Phillips v. Martin Marietta Corp., 400 U.S. 542 (1971)); EEOC enforcement guidance on caregiver discrimination (2007); ADA screen-out where gaps reflect disability, 42 U.S.C. §12112(b)(6).

### 13. F05 · Work rules that restrict Section 7 activity

**Area:** NLRA  
**Scores:** L 4 · S 4 · R 2 → **Priority 32** (Act this quarter; ongoing)

**Evidence.** Discipline cites rules on pay confidentiality, no recording, social-media 'disparagement', blanket investigation confidentiality, no union talk or solicitation on premises, company-only insignia, and 'chain of command' or 'negative attitude'.

**Remediation.** Rewrite each rule narrowly with Section 7 savings language. Tell employees which rules are rescinded or changed. Train supervisors on the revised rules.

**Legal basis.** NLRA §8(a)(1). Work-rule standard: Stericycle, Inc., 372 NLRB No. 113 (2023) (confirm current Board law). Solicitation and insignia: Republic Aviation Corp. v. NLRB, 324 U.S. 793 (1945). Discussing pay is core §7 activity.

### 14. F20 · Possible sex impact in physical roles (inconclusive)

**Area:** AEDT / Title VII  
**Scores:** L 2 · S 4 · R 4 → **Priority 32** (Act this quarter; ongoing)

**Evidence.** Women (name proxy) in Forklift, Driver and Fleet Tech roles advance at 0.80× the male rate (n = 50, p = 0.28). The name proxy misclassifies some applicants, which hides effects.

**Remediation.** Collect voluntary self-identified sex data and re-test with an adequate sample. No remedial action on current evidence.

**Legal basis.** Title VII §703(k), 42 U.S.C. §2000e-2(k).

### 15. F10 · Logistics Coordinators paid below the exempt salary floor

**Area:** FLSA  
**Scores:** L 5 · S 3 · R 2 → **Priority 30** (Act this quarter; ongoing)

**Evidence.** 18 exempt coordinators earn $33,200-$35,500, below $35,568 ($684/week). Q2 exposure $8.9k-$31.2k.

**Remediation.** Raise pay to at least $684/week or reclassify as non-exempt now. Pay back overtime.

**Legal basis.** 29 C.F.R. §541.600; §541.200(a)(1). The 2024 threshold increase was vacated (Texas v. U.S. Dep't of Labor, E.D. Tex. Nov. 15, 2024).

### 16. F11 · Van drivers wrongly treated as Motor Carrier Act exempt

**Area:** FLSA  
**Scores:** L 5 · S 3 · R 2 → **Priority 30** (Act this quarter; ongoing)

**Evidence.** 9 Final-Mile Van Drivers in vehicles of 8,550-9,990 lbs GVWR are classified MCA-exempt and receive no OT. Q2 exposure about $24.9k.

**Remediation.** Reclassify as non-exempt and pay OT going forward and back. Check vehicle-assignment logs for any weeks spent in heavier vehicles.

**Legal basis.** 29 U.S.C. §213(b)(1); small-vehicle exception, SAFETEA-LU Technical Corrections Act of 2008, Pub. L. 110-244, §306.

### 17. F17 · Referral overrides favor White applicants

**Area:** Title VII  
**Scores:** L 3 · S 3 · R 3 → **Priority 27** (Schedule; ongoing)

**Evidence.** Among 'Do Not Advance' applicants, 41.9% of those with a referral were hired vs 2.6% without (n = 93 / 534, p < 1e-24). Referrals make up 17.7% of White applicants vs 11.0% (Black) and 12.0% (Hispanic).

**Remediation.** Require a documented, job-related reason for every override. Monitor the overrides' adverse impact. Widen recruiting sources.

**Legal basis.** Title VII §703(k), 42 U.S.C. §2000e-2(k); 29 C.F.R. §1607.4 (impact of each selection procedure).

### 18. F23 · FMLA leave denied as '<12 months' with 541 days' tenure

**Area:** FMLA  
**Scores:** L 3 · S 3 · R 3 → **Priority 27** (Schedule)

**Evidence.** CL-105915's bonding leave was denied for under 12 months of service, but tenure at the leave start was 541 days. The 1,250-hour test cannot be checked from the data.

**Remediation.** Verify hours in the prior 12 months. If eligible, designate the leave retroactively and restore anything lost.

**Legal basis.** 29 U.S.C. §§2611(2)(A), 2615(a)(1); 29 C.F.R. §§825.110, 825.301(d).

### 19. F09 · Dispatchers may not meet the administrative exemption

**Area:** FLSA  
**Scores:** L 3 · S 4 · R 2 → **Priority 24** (Schedule; ongoing)

**Evidence.** 29 Dispatchers are classified Administrative-exempt. The duties summary ('assigns loads using TMS routing recommendations… answers check-in calls') reads as following set procedures. Average 49 h/week. Q2 exposure $23.6k-$88.2k if misclassified.

**Remediation.** Investigate before acting: interview and observe to establish actual duties and discretion. If the test fails, reclassify as non-exempt and pay back overtime.

**Legal basis.** 29 C.F.R. §§541.200-.202 (primary duty requiring discretion and independent judgment on matters of significance).

### 20. F12 · Shift Leads classified as executives without supervisory authority

**Area:** FLSA  
**Scores:** L 4 · S 3 · R 2 → **Priority 24** (Schedule; ongoing)

**Evidence.** 4 Shift Leads with 0-1 direct reports, about 70% floor work and no hire/fire input are classified Executive. Q2 exposure $6.1k-$24.9k.

**Remediation.** Confirm duties, reclassify as non-exempt and pay back overtime.

**Legal basis.** 29 C.F.R. §541.100(a) (directs 2+ FTEs; hire/fire authority or weight); §541.104.

### 21. F22 · Accommodation requests denied without process or left pending

**Area:** ADA / PWFA  
**Scores:** L 4 · S 3 · R 2 → **Priority 24** (Schedule; ongoing)

**Evidence.** 4 denials have no documented interactive process (CL-100105, CL-101497, CL-107471, CL-107512). 3 requests are pending over 60 days, the oldest for 352 days (CL-100247).

**Remediation.** Complete the interactive process for all 7 within a set deadline and document it. Provide interim measures while it runs.

**Legal basis.** 29 C.F.R. §§1630.2(o)(3), 1630.9; PWFA regulations, 29 C.F.R. Part 1636 (interactive process; unnecessary delay).

### 22. F13 · Hub 2 leaves differential and bonuses out of the overtime rate

**Area:** FLSA  
**Scores:** L 5 · S 2 · R 2 → **Priority 20** (Schedule; ongoing)

**Evidence.** 51 of 54 Hub 2 employees with OT and some differential or bonus are paid OT on base rate only, against 0 of 69 at other hubs (p ≈ 2e-31). Q2 shortfall about $3.3k.

**Remediation.** Fix the Hub 2 payroll configuration. Recalculate and pay the shortfall for the limitations period.

**Legal basis.** 29 U.S.C. §207(e); 29 C.F.R. §§778.207(b), 778.208-.211.

### 23. F14 · Overtime paid at straight time or not at all

**Area:** FLSA  
**Scores:** L 5 · S 2 · R 2 → **Priority 20** (Schedule; ongoing)

**Evidence.** 7 employees were paid 1.0× for OT and 2 were paid nothing for recorded OT hours. Q2 shortfall about $5.3k.

**Remediation.** Correct the pay for the 9 employees and find the root cause (manual override or pay-code error).

**Legal basis.** 29 U.S.C. §207(a)(1).

### 24. F24 · Setting-dependent cases (Medium risk)

**Area:** NLRA  
**Scores:** L 2 · S 3 · R 3 → **Priority 18** (Schedule)

**Evidence.** 6 events: 5 profane outbursts in group meetings about schedule changes where others shared the concern, and 1 TikTok about staffing that showed customer labels.

**Remediation.** Counsel review using the setting-specific analysis. No blanket action.

**Legal basis.** NLRA §7; Lion Elastomers LLC, 372 NLRB No. 83 (2023) (confirm current Board law).

### 25. F25 · Conflicting AEDT scores for the same applicant

**Area:** Data integrity  
**Scores:** L 2 · S 3 · R 3 → **Priority 18** (Schedule)

**Evidence.** CL-104284 has two rows, scored 64.0 and 68.1. Both say 'Do Not Advance', so if 68.1 is the true score, the applicant was wrongly screened out. 2 other IDs have conflicting scores below 65.

**Remediation.** Get the authoritative score from the vendor. If it is 68.1, reconsider the applicant.

**Legal basis.** 29 C.F.R. §1607.15 (selection-procedure records); 29 C.F.R. §1602.14 (record retention).

### 26. F26 · Hourly associate coded Exempt

**Area:** FLSA  
**Scores:** L 4 · S 2 · R 1 → **Priority 8** (Housekeeping; ongoing)

**Evidence.** CL-105650 is a Warehouse Associate coded Exempt with no exemption basis. No Q2 payroll exists to measure the effect.

**Remediation.** Correct the classification and check pay history for unpaid OT.

**Legal basis.** 29 U.S.C. §207(a); 29 C.F.R. §541.600.

### 27. F27 · Record defects across HR and payroll data

**Area:** Data integrity  
**Scores:** L 5 · S 1 · R 1 → **Priority 5** (Housekeeping)

**Evidence.** 6 exact duplicate rows; 9 spellings of the exempt label; 8 age bands that contradict graduation year; 2 rejected applicants with employee records; 4 payroll defects (impossible hours, negative OT, components that don't sum, missing badge data); 2 discipline events dated before hire; 5 discipline counts that don't match the event file.

**Remediation.** Deduplicate, standardize codes, reconcile the HRIS discipline count with the event log, and add validation rules at entry.

**Legal basis.** Record-keeping: 29 C.F.R. Part 516 (FLSA), §825.500 (FMLA), §1602.14 (Title VII/ADA), §1607.15 (UGESP).

## What this audit does not show

- **No legal conclusions.** This is a screen. It identifies patterns and leads; it does not find that any law was violated, establish intent, or predict how an agency or court would rule.
- **No causation.** Timing tests show that discipline clusters after accommodation requests and leave. They do not prove the requests caused the discipline. That needs decision-maker interviews, comparator analysis and the documents behind each decision.
- **No true protected-class data.** Race comes from BISG, sex from first names, age from a self-reported band, and disability from an accommodation request. Proxy error usually hides disparities, so the absence of a finding (e.g., sex) is not evidence there is no problem.
- **Not tested.** Disparate discipline or termination by race, sex or age among employees; pay equity (EPA, Title VII); promotion; age in terminations; the vendor model's internals; state and local law (state wage-hour, AEDT bias-audit laws, state leave laws).
- **No full validation study.** The performance check uses 90-day supervisor ratings for hires only (range-restricted, possibly biased). It is a warning sign, not a UGESP-compliant validation.
- **Limited financial exposure.** Dollar figures cover Q2 2026 only. They exclude the 2-3 year lookback, liquidated damages, interest, fees and state penalties. Off-the-clock estimates assume badge time equals time worked and that meal periods were taken.
- **Facts not in the data.** Actual job duties (only HR summaries); whether employees met the FMLA 1,250-hour test; dates of the protected activity behind the PCA flag; the handbook text itself; union status; whether NLRA 'supervisors' have real §2(11) authority.
- **Narrative coding limits.** NLRA risk was coded by keyword rules, then read by hand. Ratings are screening judgments. Board standards (Stericycle, Lion Elastomers) can change and should be confirmed before relying on them.
- **Not a blind review.** The analyst also generated this synthetic dataset, so knew what had been planted. Rules were fixed in code and applied to every record to limit bias, but an independent reviewer should repeat the analysis.
- **Synthetic data.** All records are synthetic. The findings demonstrate the method; they say nothing about any real company.

## Corrections log

Every correction made to the analysis, in order.

| # | Stage | By | What was wrong | What changed | Effect on findings |
|---|---|---|---|---|---|
| 1 | Analysis run 1 | Claude | The age-band consistency check crashed on blank graduation years. | Added a type check before comparing bands. | None. It failed before producing any results. |
| 2 | Analysis run 2 | Claude | pandas deprecation of positional sum(1). | Changed to sum(axis=1). | None. |
| 3 | Console review | Claude | A display filter (grep -v Warning) hid every row containing 'Written Warning' or 'Final Written Warning', so tables looked incomplete. | Re-read the console with a narrower filter before writing the report. | None on numbers. It was caught before reporting. |
| 4 | Draft report | Claude | The accommodation keyword pattern 'schedule change' also matched 'schedule changes' in six group-meeting outbursts. The draft claimed 6 possible missed-notice cases. The same error tagged those outbursts 'ADA/PWFA' in nlra_narrative_screen.csv. | Pattern changed to 'schedule change(?!s)' and '\bsit'. Re-ran. The report now says all 12 matching narratives belong to employees with requests on file. | Removed a false finding before the report was committed. |
| 5 | Draft report | Claude | The DOL-complaint theme was counted as 6 events. | Corrected to 5 after listing every High-risk event by theme (themes now sum to 33). | Fixed before the report was committed. |
| 6 | Committed report | Claude | Key-findings row 3 quoted race ratios (0.80, 0.81; Holm p 0.037, 0.044) from the 'all applicants' population without saying so, while the detail table used scored applicants (0.80, 0.78; p 0.030, 0.015). | Row 3 now gives both populations, labeled. | No change to the conclusion. It was a labeling error in a pushed version. |
| 7 | Committed report | Claude | It said Hub 3 'shows almost no paid OT (29 of 48 have none)'. 60% is not 'almost none'. | Reworded to 29 of 48 (60%) at Hub 3 vs 3 of 132 (2%) at Hubs 1-2. | The wording overstated the pattern. The off-the-clock finding is unchanged. |
| 8 | Audit summary prep | Claude | Re-checked the statement that almost all FMLA denials cite '<12 months'. | Verified: 54 of 55. The other one cites certification not returned. | No change. |

**Corrections by you (the requester):** none recorded. You have not made any corrections to the analysis in this conversation. If you made or want changes recorded from outside this session, add them here with the same columns.

**Pre-analysis (dataset generation).** Before the analysis, during dataset generation, Claude tuned and regenerated the synthetic data several times and corrected figures in the answer key after checking them against the data (for example, a race disparity first described as 2.3 SD was corrected to z ≈ −2.6). Those were corrections to the answer key, which the analysis never read. They are recorded for completeness.
