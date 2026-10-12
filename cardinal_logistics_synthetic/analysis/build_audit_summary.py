#!/usr/bin/env python3
"""
Builds the ranked audit summary from REPORT.md findings.

One data source -> two renderings:
    analysis/AUDIT_SUMMARY.md   (export)
    analysis/audit_summary.html (shareable page)

Priority = Likelihood x Severity x Reversibility (each 1-5), computed here.
"""
import html
from pathlib import Path

HERE = Path(__file__).resolve().parent

SCALES = {
    "Likelihood": [
        (5, "Near-certain", "The violation shows on the face of the records (e.g., a salary below the legal floor), or a statistically significant pattern is corroborated by documents."),
        (4, "Likely", "Strong statistical or documentary evidence. An innocent explanation is possible but would need specific facts the records do not show."),
        (3, "Possible", "A significant but proxy-dependent or borderline result, or a documentary lead without corroboration."),
        (2, "Uncertain", "Not statistically significant, small samples, or a judgment call that could go either way."),
        (1, "Remote", "Speculative. Included only for completeness."),
    ],
    "Severity": [
        (5, "Critical", "Loss of a job or job opportunity, discipline or termination for protected activity, or a systemic violation across a whole group where willfulness or liquidated damages are likely."),
        (4, "High", "Adverse action against identifiable individuals (discipline, rejection), or pay loss over $50k per quarter."),
        (3, "Moderate", "Pay loss of $5k-$50k per quarter, or process failures with real but limited individual impact."),
        (2, "Low", "Under $5k per quarter, or a technical violation."),
        (1, "Minimal", "Record-keeping or data integrity with no direct harm to individuals."),
    ],
    "Reversibility": [
        (5, "Irreversible", "The harm is complete and the people affected cannot realistically be found or made whole."),
        (4, "Hard to reverse", "Needs reinstatement offers, re-contacting rejected applicants, or individual back-pay work, and part of the harm (a lost job, chilled activity) cannot be fully undone."),
        (3, "Partly reversible", "Records and discipline can be rescinded, but later decisions built on them have to be traced and corrected."),
        (2, "Reversible at a cost", "Fixed by paying current employees what they are owed. The limitations clock keeps running until it is fixed."),
        (1, "Easily reversed", "A data, configuration or policy fix going forward."),
    ],
}

# (id, area, title, evidence, L, S, R, ongoing, remediation, legal basis)
F = [
    ("F01", "NLRA", "Discipline imposed for Section 7 activity",
     "33 events coded High risk: 7 terminations, 18 final warnings, 8 written warnings, no verbal warnings. Every High-risk first offense started above a verbal warning, against 25% of other first offenses (21 vs 136 events, Fisher p ≈ 1e-11). Themes include pay discussions, petitions and letters about heat, a group refusal over an unsafe dock plate, union cards, recording a bonus meeting, and discussing an investigation.",
     4, 5, 4, False,
     "Place a litigation hold on all discipline records. Have counsel review each of the 33 events. Rescind discipline where protected activity was the basis. For the 7 terminations, decide on reinstatement and back-pay offers person by person. Stop enforcing the cited rules until F05 is resolved.",
     "NLRA §7 and §8(a)(1), 29 U.S.C. §§157, 158(a)(1). §8(a)(3) for union-related events. Remedies under §10(c), 29 U.S.C. §160(c). Safety refusals also implicate NLRA §502 (29 U.S.C. §143) and OSH Act §11(c) (29 U.S.C. §660(c))."),
    ("F02", "AEDT / ADEA", "AEDT screens out applicants 40+",
     "Advance rate 33.3% for 40+ vs 52.5% for under 40: impact ratio 0.63 (n = 444 / 752, p < 1e-9). Ratios fall by band: 0.71, 0.61, 0.43 (60+). Holding other factors constant, the score is 5-10 points lower for 40+ bands. At the same score, under-40 hires rate 0.36 points lower (p < 1e-4), so the score under-predicts older workers.",
     5, 5, 4, True,
     "Stop using the cut score of 65 as an automatic screen now. Route every applicant to human review using job-related criteria until the tool is validated. Require the vendor to disclose its features and validation evidence. Run a job-relatedness study. Re-review 40+ applicants the tool rejected within the charge-filing window for openings that are still available.",
     "ADEA §4(a), 29 U.S.C. §623(a). Disparate impact: Smith v. City of Jackson, 544 U.S. 228 (2005); RFOA defense, 29 C.F.R. §1625.7. Applicant disparate-impact claims are limited in some circuits (Kleber v. CareFusion, 7th Cir. 2019 (en banc); Villarreal v. R.J. Reynolds, 11th Cir. 2016 (en banc)); disparate treatment is not. An employer is responsible for a vendor tool it uses. Check any state or local AEDT law where hiring occurs."),
    ("F03", "AEDT / ADA", "Applicants who asked for an assessment accommodation were screened out",
     "Advance impact ratio 0.30 (n = 44 vs 1,193, p < 1e-4); hire ratio 0.40. 19 of the 44 were never scored, and none of the 19 was hired. 17 recruiter notes record rejection because the accommodation left them unscored.",
     5, 5, 4, True,
     "Set up an accommodation path for the assessment now (alternative format or extended time scored on equal terms, or individualized review). Re-contact all 44 requesters and reconsider them for open roles. Add accommodation duties to the vendor contract. Train recruiters.",
     "ADA Title I, 42 U.S.C. §12112(b)(5)(A) (accommodating applicants), (b)(6) (screen-out criteria), (b)(7) (tests must measure skills, not impairment); 29 C.F.R. §§1630.10, 1630.11."),
    ("F04", "FMLA", "Attendance points assessed for approved FMLA absences",
     "All 9 attendance write-ups that cite a family or medical reason count absences inside approved FMLA leave; 8 are final warnings. Discipline in the 60 days after approved leave runs 17.7× the baseline (13 events in 530 person-days, exact p = 2e-12).",
     5, 4, 3, True,
     "Rescind the 9 write-ups and the points. Trace any later discipline or termination that relied on them; CL-103029 was later terminated. Configure the attendance system so FMLA-designated absences never generate points. Train supervisors.",
     "FMLA §105(a)(1), 29 U.S.C. §2615(a)(1); 29 C.F.R. §825.220(c) (FMLA leave cannot count under no-fault attendance policies). Damages, including liquidated damages, under 29 U.S.C. §2617."),
    ("F05", "NLRA", "Work rules that restrict Section 7 activity",
     "Discipline cites rules on pay confidentiality, no recording, social-media 'disparagement', blanket investigation confidentiality, no union talk or solicitation on premises, company-only insignia, and 'chain of command' or 'negative attitude'.",
     4, 4, 2, True,
     "Rewrite each rule narrowly with Section 7 savings language. Tell employees which rules are rescinded or changed. Train supervisors on the revised rules.",
     "NLRA §8(a)(1). Work-rule standard: Stericycle, Inc., 372 NLRB No. 113 (2023) (confirm current Board law). Solicitation and insignia: Republic Aviation Corp. v. NLRB, 324 U.S. 793 (1945). Discussing pay is core §7 activity."),
    ("F06", "FLSA retaliation", "Discipline for saying coworkers would complain to the DOL",
     "5 events, a subset of F01, discipline employees for telling a supervisor that coworkers would contact the Department of Labor about unpaid pre-shift time (1 termination). The underlying complaint matches the off-the-clock pattern in F08.",
     4, 5, 4, False,
     "Rescind the discipline and route these cases to counsel with F01. Investigate the pre-shift time claim on its merits as part of F08. Remind managers that complaints to agencies, including oral complaints, are protected.",
     "FLSA §15(a)(3), 29 U.S.C. §215(a)(3); oral complaints are protected (Kasten v. Saint-Gobain, 563 U.S. 1 (2011)). Also NLRA §7, because the complaint was concerted."),
    ("F07", "ADA / PWFA", "Discipline for the limitation an accommodation was meant to address",
     "12 events in the 10-57 days after an accommodation request discipline the limitation itself (2 terminations: DE-5175, DE-5031). Discipline in the 90 days after a request runs 5.2× the baseline (15 events in 2,093 person-days, exact p = 6.6e-7).",
     4, 5, 4, False,
     "Review each of the 12 events individually. Rescind discipline that penalizes the limitation. Decide on reinstatement offers for CL-107471 and CL-101211. Restart the interactive process for every affected employee.",
     "ADA 42 U.S.C. §12112(b)(5)(A) (failure to accommodate) and §12203(a)-(b) (retaliation, interference); PWFA 42 U.S.C. §2000gg-1 and 29 C.F.R. Part 1636."),
    ("F08", "FLSA", "Off-the-clock work at Hub 3",
     "30 employees (all Hub 3 Fleet Techs and Forklift Operators, plus 2 van drivers) have paid time capped at 40 h/week and no OT. Their badge time exceeds paid time by a median of 9.5 h/week, against a tight 2.75 h/week meal-only baseline elsewhere (Hub 3 vs other hubs: p ≈ 9e-18). About 2,578 unpaid hours, worth $70.8k-$106.2k in Q2 alone.",
     4, 5, 2, True,
     "Remove the 40-hour cap now and pay all verified time. Reconstruct hours from badge data back through the limitations period and pay what is owed. Retrain supervisors on recording hours.",
     "FLSA §7(a), 29 U.S.C. §207(a); hours worked, 29 C.F.R. §§785.11-.13; records, 29 U.S.C. §211(c) and 29 C.F.R. §516.2; limitations, 29 U.S.C. §255 (3 years if willful); liquidated damages, §216(b)."),
    ("F09", "FLSA", "Dispatchers may not meet the administrative exemption",
     "29 Dispatchers are classified Administrative-exempt. The duties summary ('assigns loads using TMS routing recommendations… answers check-in calls') reads as following set procedures. Average 49 h/week. Q2 exposure $23.6k-$88.2k if misclassified.",
     3, 4, 2, True,
     "Investigate before acting: interview and observe to establish actual duties and discretion. If the test fails, reclassify as non-exempt and pay back overtime.",
     "29 C.F.R. §§541.200-.202 (primary duty requiring discretion and independent judgment on matters of significance)."),
    ("F10", "FLSA", "Logistics Coordinators paid below the exempt salary floor",
     "18 exempt coordinators earn $33,200-$35,500, below $35,568 ($684/week). Q2 exposure $8.9k-$31.2k.",
     5, 3, 2, True,
     "Raise pay to at least $684/week or reclassify as non-exempt now. Pay back overtime.",
     "29 C.F.R. §541.600; §541.200(a)(1). The 2024 threshold increase was vacated (Texas v. U.S. Dep't of Labor, E.D. Tex. Nov. 15, 2024)."),
    ("F11", "FLSA", "Van drivers wrongly treated as Motor Carrier Act exempt",
     "9 Final-Mile Van Drivers in vehicles of 8,550-9,990 lbs GVWR are classified MCA-exempt and receive no OT. Q2 exposure about $24.9k.",
     5, 3, 2, True,
     "Reclassify as non-exempt and pay OT going forward and back. Check vehicle-assignment logs for any weeks spent in heavier vehicles.",
     "29 U.S.C. §213(b)(1); small-vehicle exception, SAFETEA-LU Technical Corrections Act of 2008, Pub. L. 110-244, §306."),
    ("F12", "FLSA", "Shift Leads classified as executives without supervisory authority",
     "4 Shift Leads with 0-1 direct reports, about 70% floor work and no hire/fire input are classified Executive. Q2 exposure $6.1k-$24.9k.",
     4, 3, 2, True,
     "Confirm duties, reclassify as non-exempt and pay back overtime.",
     "29 C.F.R. §541.100(a) (directs 2+ FTEs; hire/fire authority or weight); §541.104."),
    ("F13", "FLSA", "Hub 2 leaves differential and bonuses out of the overtime rate",
     "51 of 54 Hub 2 employees with OT and some differential or bonus are paid OT on base rate only, against 0 of 69 at other hubs (p ≈ 2e-31). Q2 shortfall about $3.3k.",
     5, 2, 2, True,
     "Fix the Hub 2 payroll configuration. Recalculate and pay the shortfall for the limitations period.",
     "29 U.S.C. §207(e); 29 C.F.R. §§778.207(b), 778.208-.211."),
    ("F14", "FLSA", "Overtime paid at straight time or not at all",
     "7 employees were paid 1.0× for OT and 2 were paid nothing for recorded OT hours. Q2 shortfall about $5.3k.",
     5, 2, 2, True,
     "Correct the pay for the 9 employees and find the root cause (manual override or pay-code error).",
     "29 U.S.C. §207(a)(1)."),
    ("F15", "AEDT / Title VII", "AEDT race disparity through commute distance",
     "Race proxy impact ratios: Black 0.80, Hispanic 0.78 among scored applicants (Holm p = 0.030 and 0.015). The score falls 0.48 points per commute mile; mean commute is 16.4 mi for the Black proxy group and 15.5 for Hispanic, against 11.2 for White. Commute does not predict performance (at the same score, a positive coefficient).",
     3, 5, 4, True,
     "Remove commute and ZIP-derived features from scoring now. Collect voluntary self-identified race and ethnicity data and re-test. If impact remains, look for a less discriminatory alternative.",
     "Title VII §703(k), 42 U.S.C. §2000e-2(k); Griggs v. Duke Power Co., 401 U.S. 424 (1971); Connecticut v. Teal, 457 U.S. 440 (1982) (a balanced bottom line does not cure impact at a step); 29 C.F.R. §§1607.3(B), 1607.4(D)."),
    ("F16", "ADEA", "Age-coded recruiter notes and post-AEDT age gap",
     "28 notes use age-coded language ('overqualified', 'more energy', 'close to retiring', 'digital native'). Among applicants the tool advanced, 62.8% of 40+ were hired vs 74.8% of under 40 (n = 137 / 373, p = 0.011).",
     4, 4, 4, True,
     "Review the decisions behind the 28 notes and reconsider affected applicants. Require a structured, job-related rejection reason in the ATS. Train recruiters.",
     "ADEA 29 U.S.C. §623(a)(1) (disparate treatment); the notes are direct evidence of motive."),
    ("F17", "Title VII", "Referral overrides favor White applicants",
     "Among 'Do Not Advance' applicants, 41.9% of those with a referral were hired vs 2.6% without (n = 93 / 534, p < 1e-24). Referrals make up 17.7% of White applicants vs 11.0% (Black) and 12.0% (Hispanic).",
     3, 3, 3, True,
     "Require a documented, job-related reason for every override. Monitor the overrides' adverse impact. Widen recruiting sources.",
     "Title VII §703(k), 42 U.S.C. §2000e-2(k); 29 C.F.R. §1607.4 (impact of each selection procedure)."),
    ("F18", "Title VII", "Accent cited in CSR rejections",
     "6 rejection notes for Customer Service applicants cite an accent ('may confuse customers').",
     3, 4, 4, False,
     "Review each rejection for a documented, job-related communication assessment. Reconsider applicants where none exists.",
     "Title VII §703(a), 42 U.S.C. §2000e-2(a). Under EEOC national-origin guidance, accent is a lawful basis only when it materially interferes with job performance."),
    ("F19", "Title VII / ADA", "Résumé-gap penalty and caregiver-coded notes",
     "The score falls 0.29 points per gap month (p < 1e-4). Gaps run longer for applicants inferred female (5.0 vs 2.9 months). Gap does not predict performance. 4 notes ask about childcare or kids.",
     3, 3, 4, True,
     "Remove the gap feature. Review the 4 decisions with caregiver notes.",
     "Title VII sex-plus (Phillips v. Martin Marietta Corp., 400 U.S. 542 (1971)); EEOC enforcement guidance on caregiver discrimination (2007); ADA screen-out where gaps reflect disability, 42 U.S.C. §12112(b)(6)."),
    ("F20", "AEDT / Title VII", "Possible sex impact in physical roles (inconclusive)",
     "Women (name proxy) in Forklift, Driver and Fleet Tech roles advance at 0.80× the male rate (n = 50, p = 0.28). The name proxy misclassifies some applicants, which hides effects.",
     2, 4, 4, True,
     "Collect voluntary self-identified sex data and re-test with an adequate sample. No remedial action on current evidence.",
     "Title VII §703(k), 42 U.S.C. §2000e-2(k)."),
    ("F21", "NLRA", "'PCA flag' tracks protected activity and predicts termination",
     "Employee Relations keeps a flag for protected concerted activity. Flagged employees are involuntarily terminated at 17.0% vs 4.9% (n = 47 / 371, p = 0.005), and disciplined at 59.6% vs 34.8% (p = 0.001). 5 employees with clear Section 7 discipline are unflagged.",
     4, 4, 3, True,
     "Have counsel review the flag's purpose and who can see it. Remove it from any decision workflow. Preserve it (do not delete it; it is evidence). Audit who used it and for what.",
     "NLRA §8(a)(1) (surveillance or the impression of it) and §8(a)(3); employer knowledge under Wright Line, 251 NLRB 1083 (1980)."),
    ("F22", "ADA / PWFA", "Accommodation requests denied without process or left pending",
     "4 denials have no documented interactive process (CL-100105, CL-101497, CL-107471, CL-107512). 3 requests are pending over 60 days, the oldest for 352 days (CL-100247).",
     4, 3, 2, True,
     "Complete the interactive process for all 7 within a set deadline and document it. Provide interim measures while it runs.",
     "29 C.F.R. §§1630.2(o)(3), 1630.9; PWFA regulations, 29 C.F.R. Part 1636 (interactive process; unnecessary delay)."),
    ("F23", "FMLA", "FMLA leave denied as '<12 months' with 541 days' tenure",
     "CL-105915's bonding leave was denied for under 12 months of service, but tenure at the leave start was 541 days. The 1,250-hour test cannot be checked from the data.",
     3, 3, 3, False,
     "Verify hours in the prior 12 months. If eligible, designate the leave retroactively and restore anything lost.",
     "29 U.S.C. §§2611(2)(A), 2615(a)(1); 29 C.F.R. §§825.110, 825.301(d)."),
    ("F24", "NLRA", "Setting-dependent cases (Medium risk)",
     "6 events: 5 profane outbursts in group meetings about schedule changes where others shared the concern, and 1 TikTok about staffing that showed customer labels.",
     2, 3, 3, False,
     "Counsel review using the setting-specific analysis. No blanket action.",
     "NLRA §7; Lion Elastomers LLC, 372 NLRB No. 83 (2023) (confirm current Board law)."),
    ("F25", "Data integrity", "Conflicting AEDT scores for the same applicant",
     "CL-104284 has two rows, scored 64.0 and 68.1. Both say 'Do Not Advance', so if 68.1 is the true score, the applicant was wrongly screened out. 2 other IDs have conflicting scores below 65.",
     2, 3, 3, False,
     "Get the authoritative score from the vendor. If it is 68.1, reconsider the applicant.",
     "29 C.F.R. §1607.15 (selection-procedure records); 29 C.F.R. §1602.14 (record retention)."),
    ("F26", "FLSA", "Hourly associate coded Exempt",
     "CL-105650 is a Warehouse Associate coded Exempt with no exemption basis. No Q2 payroll exists to measure the effect.",
     4, 2, 1, True,
     "Correct the classification and check pay history for unpaid OT.",
     "29 U.S.C. §207(a); 29 C.F.R. §541.600."),
    ("F27", "Data integrity", "Record defects across HR and payroll data",
     "6 exact duplicate rows; 9 spellings of the exempt label; 8 age bands that contradict graduation year; 2 rejected applicants with employee records; 4 payroll defects (impossible hours, negative OT, components that don't sum, missing badge data); 2 discipline events dated before hire; 5 discipline counts that don't match the event file.",
     5, 1, 1, False,
     "Deduplicate, standardize codes, reconcile the HRIS discipline count with the event log, and add validation rules at entry.",
     "Record-keeping: 29 C.F.R. Part 516 (FLSA), §825.500 (FMLA), §1602.14 (Title VII/ADA), §1607.15 (UGESP)."),
]

NOT_SHOWN = [
    ("No legal conclusions", "This is a screen. It identifies patterns and leads; it does not find that any law was violated, establish intent, or predict how an agency or court would rule."),
    ("No causation", "Timing tests show that discipline clusters after accommodation requests and leave. They do not prove the requests caused the discipline. That needs decision-maker interviews, comparator analysis and the documents behind each decision."),
    ("No true protected-class data", "Race comes from BISG, sex from first names, age from a self-reported band, and disability from an accommodation request. Proxy error usually hides disparities, so the absence of a finding (e.g., sex) is not evidence there is no problem."),
    ("Not tested", "Disparate discipline or termination by race, sex or age among employees; pay equity (EPA, Title VII); promotion; age in terminations; the vendor model's internals; state and local law (state wage-hour, AEDT bias-audit laws, state leave laws)."),
    ("No full validation study", "The performance check uses 90-day supervisor ratings for hires only (range-restricted, possibly biased). It is a warning sign, not a UGESP-compliant validation."),
    ("Limited financial exposure", "Dollar figures cover Q2 2026 only. They exclude the 2-3 year lookback, liquidated damages, interest, fees and state penalties. Off-the-clock estimates assume badge time equals time worked and that meal periods were taken."),
    ("Facts not in the data", "Actual job duties (only HR summaries); whether employees met the FMLA 1,250-hour test; dates of the protected activity behind the PCA flag; the handbook text itself; union status; whether NLRA 'supervisors' have real §2(11) authority."),
    ("Narrative coding limits", "NLRA risk was coded by keyword rules, then read by hand. Ratings are screening judgments. Board standards (Stericycle, Lion Elastomers) can change and should be confirmed before relying on them."),
    ("Not a blind review", "The analyst also generated this synthetic dataset, so knew what had been planted. Rules were fixed in code and applied to every record to limit bias, but an independent reviewer should repeat the analysis."),
    ("Synthetic data", "All records are synthetic. The findings demonstrate the method; they say nothing about any real company."),
]

# (when, who, what was wrong, what changed, effect on findings)
CORRECTIONS = [
    ("Analysis run 1", "Claude", "The age-band consistency check crashed on blank graduation years.",
     "Added a type check before comparing bands.", "None. It failed before producing any results."),
    ("Analysis run 2", "Claude", "pandas deprecation of positional sum(1).",
     "Changed to sum(axis=1).", "None."),
    ("Console review", "Claude", "A display filter (grep -v Warning) hid every row containing 'Written Warning' or 'Final Written Warning', so tables looked incomplete.",
     "Re-read the console with a narrower filter before writing the report.", "None on numbers. It was caught before reporting."),
    ("Draft report", "Claude", "The accommodation keyword pattern 'schedule change' also matched 'schedule changes' in six group-meeting outbursts. The draft claimed 6 possible missed-notice cases. The same error tagged those outbursts 'ADA/PWFA' in nlra_narrative_screen.csv.",
     "Pattern changed to 'schedule change(?!s)' and '\\bsit'. Re-ran. The report now says all 12 matching narratives belong to employees with requests on file.", "Removed a false finding before the report was committed."),
    ("Draft report", "Claude", "The DOL-complaint theme was counted as 6 events.",
     "Corrected to 5 after listing every High-risk event by theme (themes now sum to 33).", "Fixed before the report was committed."),
    ("Committed report", "Claude", "Key-findings row 3 quoted race ratios (0.80, 0.81; Holm p 0.037, 0.044) from the 'all applicants' population without saying so, while the detail table used scored applicants (0.80, 0.78; p 0.030, 0.015).",
     "Row 3 now gives both populations, labeled.", "No change to the conclusion. It was a labeling error in a pushed version."),
    ("Committed report", "Claude", "It said Hub 3 'shows almost no paid OT (29 of 48 have none)'. 60% is not 'almost none'.",
     "Reworded to 29 of 48 (60%) at Hub 3 vs 3 of 132 (2%) at Hubs 1-2.", "The wording overstated the pattern. The off-the-clock finding is unchanged."),
    ("Audit summary prep", "Claude", "Re-checked the statement that almost all FMLA denials cite '<12 months'.",
     "Verified: 54 of 55. The other one cites certification not returned.", "No change."),
]

USER_CORRECTIONS_NOTE = ("You have not made any corrections to the analysis in this conversation. If you made or "
                         "want changes recorded from outside this session, add them here with the same columns.")

PRE_ANALYSIS_NOTE = ("Before the analysis, during dataset generation, Claude tuned and regenerated the synthetic data several "
                     "times and corrected figures in the answer key after checking them against the data (for example, "
                     "a race disparity first described as 2.3 SD was corrected to z ≈ −2.6). Those were corrections to "
                     "the answer key, which the analysis never read. They are recorded for completeness.")


def rows():
    out = []
    for f in F:
        fid, area, title, ev, L, S, R, ong, rem, law = f
        out.append(dict(id=fid, area=area, title=title, evidence=ev, L=L, S=S, R=R, P=L * S * R,
                        ongoing=ong, remediation=rem, law=law))
    out.sort(key=lambda r: (-r["P"], -r["S"], -r["L"], r["id"]))
    for i, r in enumerate(out, 1):
        r["rank"] = i
    return out


def tcls(p):
    return {"Act now": "now", "Act this quarter": "qtr", "Schedule": "sched", "Housekeeping": "house"}[tier(p)]


def tier(p):
    return "Act now" if p >= 60 else "Act this quarter" if p >= 30 else "Schedule" if p >= 15 else "Housekeeping"


# ------------------------------------------------------------------ markdown
def md(rs):
    L = []
    a = L.append
    a("# Cardinal Logistics: Ranked Audit Summary\n")
    a("Synthetic dataset · Analysis of `data/` only (the answer key was not read) · Source report: `analysis/REPORT.md` · Snapshot 2026-06-30\n")
    a("This is a compliance screen, not legal advice. Each item is a lead for counsel to verify.\n")
    a("## How findings are scored\n")
    a("Each finding is scored 1-5 on three scales. **Priority = Likelihood × Severity × Reversibility** (range 1-125). "
      "Multiplying means a finding has to score on all three to rise, and one low factor pulls it down. "
      "Ties are broken by severity, then likelihood. The scores are ordinal judgments, not probabilities or dollar values.\n")
    for name, scale in SCALES.items():
        hdr = {"Reversibility": "Reversibility (5 = hardest to reverse)"}.get(name, name)
        a(f"**{hdr}**\n")
        a("| Score | Label | Meaning |\n|---|---|---|")
        for s, lab, m in scale:
            a(f"| {s} | {lab} | {m} |")
        a("")
    a("**Action tiers** (proportionate response): Act now = priority 60 or more; Act this quarter = 30-59; Schedule = 15-29; Housekeeping = under 15. "
      "Separately, an item marked **Ongoing** keeps causing harm every pay period or every applicant until it is stopped. "
      "Whatever its rank, an ongoing item should get its containment step (stopping the practice) right away; the full remediation can then follow at its tier's pace.\n")
    a("Remediation is scaled to the evidence:\n")
    a("- Likelihood 4-5: correct and make people whole.")
    a("- Likelihood 3: investigate first, contain if cheap.")
    a("- Likelihood 2 or less: collect better data before acting.\n")
    a("## Ranked findings\n")
    a("| Rank | ID | Area | Finding | L | S | R | Priority | Tier | Ongoing |")
    a("|---|---|---|---|---|---|---|---|---|---|")
    for r in rs:
        a(f"| {r['rank']} | {r['id']} | {r['area']} | {r['title']} | {r['L']} | {r['S']} | {r['R']} | **{r['P']}** | {tier(r['P'])} | {'Yes' if r['ongoing'] else 'No'} |")
    a("\n## Findings in detail\n")
    for r in rs:
        a(f"### {r['rank']}. {r['id']} · {r['title']}\n")
        a(f"**Area:** {r['area']}  ")
        a(f"**Scores:** L {r['L']} · S {r['S']} · R {r['R']} → **Priority {r['P']}** ({tier(r['P'])}{'; ongoing' if r['ongoing'] else ''})\n")
        a(f"**Evidence.** {r['evidence']}\n")
        a(f"**Remediation.** {r['remediation']}\n")
        a(f"**Legal basis.** {r['law']}\n")
    a("## What this audit does not show\n")
    for h, t in NOT_SHOWN:
        a(f"- **{h}.** {t}")
    a("\n## Corrections log\n")
    a("Every correction made to the analysis, in order.\n")
    a("| # | Stage | By | What was wrong | What changed | Effect on findings |\n|---|---|---|---|---|---|")
    for i, (w, who, wrong, chg, eff) in enumerate(CORRECTIONS, 1):
        a(f"| {i} | {w} | {who} | {wrong} | {chg} | {eff} |")
    a("\n**Corrections by you (the requester):** none recorded. " + USER_CORRECTIONS_NOTE + "\n")
    a("**Pre-analysis (dataset generation).** " + PRE_ANALYSIS_NOTE + "\n")
    return "\n".join(L)


# ------------------------------------------------------------------ html
def h(s):
    return html.escape(str(s))


def pips(n):
    return "".join(f'<i class="pip{" on" if k < n else ""}"></i>' for k in range(5))


def page(rs):
    tiers = {}
    for r in rs:
        tiers.setdefault(tier(r["P"]), []).append(r)
    counts = " · ".join(f"{len(tiers.get(t, []))} {t.lower()}" for t in ["Act now", "Act this quarter", "Schedule", "Housekeeping"])
    rows_html = "\n".join(
        f'<tr class="t-{tcls(r["P"])}"><td class="num">{r["rank"]}</td><td class="mono">{r["id"]}</td>'
        f'<td><a href="#{r["id"]}">{h(r["title"])}</a><div class="area">{h(r["area"])}</div></td>'
        f'<td class="num">{r["L"]}</td><td class="num">{r["S"]}</td><td class="num">{r["R"]}</td>'
        f'<td class="num prio">{r["P"]}</td><td><span class="tier">{tier(r["P"])}</span></td>'
        f'<td>{"<span class=ong>Ongoing</span>" if r["ongoing"] else ""}</td></tr>' for r in rs)
    cards = "\n".join(f'''
<article class="finding t-{tcls(r["P"])}" id="{r["id"]}">
  <header>
    <div class="rank">{r["rank"]}</div>
    <div class="ttl"><div class="meta"><span class="mono">{r["id"]}</span> · {h(r["area"])} · <span class="tier">{tier(r["P"])}</span>{' · <span class="ong">Ongoing</span>' if r["ongoing"] else ''}</div>
    <h3>{h(r["title"])}</h3></div>
    <div class="score"><div class="prio-big">{r["P"]}</div><div class="axes">
      <span>L</span>{pips(r["L"])}<span>S</span>{pips(r["S"])}<span>R</span>{pips(r["R"])}</div></div>
  </header>
  <dl>
    <dt>Evidence</dt><dd>{h(r["evidence"])}</dd>
    <dt>Remediation</dt><dd>{h(r["remediation"])}</dd>
    <dt>Legal basis</dt><dd class="law">{h(r["law"])}</dd>
  </dl>
</article>''' for r in rs)
    scales = "\n".join(f'''<div class="scale"><h4>{h({"Reversibility": "Reversibility · 5 = hardest to reverse"}.get(n, n))}</h4><ol reversed>
{"".join(f"<li><b>{s} {h(lab)}</b> {h(m)}</li>" for s, lab, m in sc)}</ol></div>''' for n, sc in SCALES.items())
    notshown = "\n".join(f"<li><b>{h(a)}.</b> {h(b)}</li>" for a, b in NOT_SHOWN)
    corr = "\n".join(f"<tr><td class=num>{i}</td><td>{h(w)}</td><td>{h(who)}</td><td>{h(x)}</td><td>{h(c)}</td><td>{h(e)}</td></tr>"
                     for i, (w, who, x, c, e) in enumerate(CORRECTIONS, 1))
    return f'''<title>Cardinal Logistics Audit Summary</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,650&family=Public+Sans:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>
/* Layout: one reading column; ranked register up top, finding dossiers below, method and limits last. */
:root {{
  --paper:#f6f7f9; --sheet:#ffffff; --ink:#18212e; --muted:#5a6575; --rule:#d9dee6; --accent:#1f4e8c;
  --now:#b42318; --qtr:#b54708; --sched:#3b6e3b; --house:#667085; --chip:#eef1f5;
  --display:"Newsreader", Georgia, serif; --body:"Public Sans", system-ui, sans-serif; --mono:"IBM Plex Mono", ui-monospace, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --paper:#11161d; --sheet:#171e27; --ink:#e6eaf0; --muted:#9aa6b6; --rule:#2c3644; --accent:#8db4ea;
  --now:#f97066; --qtr:#fdb022; --sched:#8bc28b; --house:#98a2b3; --chip:#222b37; color-scheme:dark }} }}
:root[data-theme="dark"] {{ --paper:#11161d; --sheet:#171e27; --ink:#e6eaf0; --muted:#9aa6b6; --rule:#2c3644; --accent:#8db4ea;
  --now:#f97066; --qtr:#fdb022; --sched:#8bc28b; --house:#98a2b3; --chip:#222b37; color-scheme:dark }}
body {{ background:var(--paper); color:var(--ink); font:15px/1.6 var(--body); }}
.wrap {{ max-width:1040px; margin:0 auto; padding-inline:20px; padding-block:40px 80px; display:grid; gap:44px; }}
h1,h2,h3 {{ font-family:var(--display); font-weight:650; text-wrap:balance; margin:0; line-height:1.2 }}
h1 {{ font-size:clamp(28px,4.5vw,40px) }} h2 {{ font-size:24px; margin-bottom:14px }} h3 {{ font-size:19px }}
h4 {{ font:600 12px/1.3 var(--body); letter-spacing:.08em; text-transform:uppercase; color:var(--muted); margin:0 0 8px }}
p {{ margin:0; max-width:68ch }} a {{ color:var(--accent) }}
.lede {{ display:grid; gap:12px }} .kicker {{ font:600 12px var(--body); letter-spacing:.1em; text-transform:uppercase; color:var(--muted) }}
.note {{ color:var(--muted); font-size:14px }}
.mono, .num {{ font-family:var(--mono); font-variant-numeric:tabular-nums }}
.tbl {{ overflow-x:auto; border:1px solid var(--rule); border-radius:6px; background:var(--sheet) }}
table {{ border-collapse:collapse; width:100%; min-width:720px; font-size:14px }}
th,td {{ text-align:left; padding:9px 10px; border-bottom:1px solid var(--rule); vertical-align:top }}
th {{ font:600 11px var(--body); letter-spacing:.08em; text-transform:uppercase; color:var(--muted); background:var(--chip) }}
tr:last-child td {{ border-bottom:0 }} td.num {{ text-align:right }} td a {{ color:var(--ink); text-decoration:none; font-weight:600 }} td a:hover {{ text-decoration:underline }}
.area {{ color:var(--muted); font-size:12px }}
.prio {{ font-weight:600 }}
.tier {{ display:inline-block; font:600 11px var(--body); letter-spacing:.04em; padding:2px 8px; border-radius:99px; background:var(--chip); color:var(--tc,var(--muted)); white-space:nowrap }}
.ong {{ display:inline-block; font:600 11px var(--body); padding:2px 8px; border-radius:99px; border:1px solid var(--rule); color:var(--muted); white-space:nowrap }}
.t-now {{ --tc:var(--now) }} .t-qtr {{ --tc:var(--qtr) }} .t-sched {{ --tc:var(--sched) }} .t-house {{ --tc:var(--house) }}
tr td:first-child {{ box-shadow: inset 3px 0 0 var(--tc) }}
.findings {{ display:grid; gap:14px }}
.finding {{ background:var(--sheet); border:1px solid var(--rule); border-left:4px solid var(--tc,var(--house)); border-radius:6px; padding:18px 20px; display:grid; gap:12px; min-width:0 }}
.finding header {{ display:grid; grid-template-columns:auto 1fr auto; gap:16px; align-items:start }}
.rank {{ font:600 26px/1 var(--mono); color:var(--muted) }}
.meta {{ font-size:12px; color:var(--muted); margin-bottom:4px }}
.score {{ display:grid; justify-items:end; gap:6px }}
.prio-big {{ font:600 24px/1 var(--mono); color:var(--tc,var(--ink)) }}
.axes {{ display:grid; grid-template-columns:auto repeat(5,8px); gap:3px 3px; align-items:center; font:600 10px var(--mono); color:var(--muted) }}
.axes span {{ padding-right:4px }}
.pip {{ width:8px; height:8px; border-radius:2px; background:var(--chip); border:1px solid var(--rule) }} .pip.on {{ background:var(--tc,var(--ink)); border-color:transparent }}
dl {{ margin:0; display:grid; grid-template-columns:120px 1fr; gap:8px 16px }}
dt {{ font:600 11px/1.9 var(--body); letter-spacing:.08em; text-transform:uppercase; color:var(--muted) }}
dd {{ margin:0; min-width:0 }} dd.law {{ font-size:14px }}
.scales {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:16px }}
.scale {{ background:var(--sheet); border:1px solid var(--rule); border-radius:6px; padding:16px }}
.scale ol {{ margin:0; padding:0; list-style:none; display:grid; gap:8px; font-size:14px }} .scale b {{ display:block; font-family:var(--mono); font-weight:600 }}
.formula {{ font:600 15px var(--mono); background:var(--chip); padding:10px 14px; border-radius:6px; display:inline-block }}
ul.limits {{ margin:0; padding-left:18px; display:grid; gap:8px; max-width:80ch }}
section {{ display:grid; gap:14px; min-width:0 }}
.tiers {{ display:flex; flex-wrap:wrap; gap:8px }}
.tiers span {{ font-size:13px }}
@media (max-width:640px) {{ .finding header {{ grid-template-columns:auto 1fr }} .score {{ grid-column:1/-1; justify-items:start; grid-auto-flow:column; align-items:center }} dl {{ grid-template-columns:1fr }} dt {{ margin-top:4px }} }}
@media (prefers-reduced-motion: reduce) {{ * {{ scroll-behavior:auto }} }}
:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px }}
</style>
<div class="wrap">
  <section class="lede">
    <div class="kicker">Compliance screen · Synthetic dataset · Snapshot 2026-06-30</div>
    <h1>Cardinal Logistics Audit Summary</h1>
    <p>{len(rs)} findings across AEDT hiring, FLSA, ADA/PWFA, FMLA and the NLRA, ranked by likelihood, severity and reversibility. Each one comes with a proportionate remediation step and its legal basis. Only the files in <span class="mono">data/</span> were analyzed; the answer key was not read.</p>
    <p class="note">{counts}. This is a screen, not legal advice. Every item is a lead for counsel to verify.</p>
  </section>

  <section>
    <h2>Ranked findings</h2>
    <div class="tbl"><table>
      <thead><tr><th>#</th><th>ID</th><th>Finding</th><th title="Likelihood">L</th><th title="Severity">S</th><th title="Reversibility (5 = hardest)">R</th><th>Priority</th><th>Tier</th><th></th></tr></thead>
      <tbody>{rows_html}</tbody></table></div>
  </section>

  <section>
    <h2>How findings are scored</h2>
    <p><span class="formula">Priority = L × S × R</span></p>
    <p>Each finding is scored 1 to 5 on three scales, giving a priority from 1 to 125. Multiplying means a finding has to score on all three to rise, and one low factor pulls it down. Ties go to severity, then likelihood. The scores are ordinal judgments, not probabilities or dollar values.</p>
    <div class="scales">{scales}</div>
    <p><b>Action tiers.</b> Act now: 60 or more. Act this quarter: 30-59. Schedule: 15-29. Housekeeping: under 15. An item marked <span class="ong">Ongoing</span> keeps causing harm every pay period or every applicant until stopped. Whatever its rank, it gets its containment step right away; the full fix then follows at its tier's pace.</p>
    <p><b>Proportionality.</b> Remediation is scaled to the evidence. At likelihood 4-5: correct and make people whole. At likelihood 3: investigate first, and contain if that is cheap. At likelihood 2 or less: collect better data before acting.</p>
  </section>

  <section>
    <h2>Findings in detail</h2>
    <div class="findings">{cards}</div>
  </section>

  <section>
    <h2>What this audit does not show</h2>
    <ul class="limits">{notshown}</ul>
  </section>

  <section>
    <h2>Corrections log</h2>
    <p>Every correction made to the analysis, in order.</p>
    <div class="tbl"><table>
      <thead><tr><th>#</th><th>Stage</th><th>By</th><th>What was wrong</th><th>What changed</th><th>Effect on findings</th></tr></thead>
      <tbody>{corr}</tbody></table></div>
    <p><b>Corrections by you (the requester):</b> none recorded. {h(USER_CORRECTIONS_NOTE)}</p>
    <p class="note"><b>Pre-analysis (dataset generation).</b> {h(PRE_ANALYSIS_NOTE)}</p>
  </section>
</div>
'''


if __name__ == "__main__":
    rs = rows()
    (HERE / "AUDIT_SUMMARY.md").write_text(md(rs))
    (HERE / "audit_summary.html").write_text(page(rs))
    for r in rs:
        print(f"{r['rank']:>2} {r['id']} P={r['P']:>3} L{r['L']} S{r['S']} R{r['R']} {tier(r['P']):<16} {r['title']}")
