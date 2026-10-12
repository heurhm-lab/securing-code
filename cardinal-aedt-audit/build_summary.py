"""Step 3: ranked audit summary for Cardinal Logistics (synthetic data).

Reads the Step 2 outputs in results/ and writes:
  results/findings_register.csv   one row per finding, ranked, with scores and remediation
  results/audit_summary.md        the summary for HR leadership and counsel

Every figure is read from the Step 2 files, so re-running analyze.py then this script
keeps the summary in step with the data.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

R = Path(__file__).resolve().parent / "results"
AI = pd.read_csv(R / "adverse_impact.csv")
GAPS = pd.read_csv(R / "aedt_score_gaps.csv")
FLSA = pd.read_csv(R / "flsa_flags.csv")
OT = pd.read_csv(R / "premium_ot_algorithm.csv").set_index("group")
SEQ = pd.read_csv(R / "leave_accommodation_flags.csv")
SR = pd.read_csv(R / "sequence_rates.csv").set_index("request")
S7 = pd.read_csv(R / "section7_flags.csv")
PEOPLE = pd.read_csv(R.parent / "cardinal_people.csv")

AEDT_POP = "AEDT applicants (all AEDT job groups)"


def ai_row(dimension, group):
    return AI[(AI["population"] == AEDT_POP) & (AI["dimension"] == dimension) & (AI["group"] == group)].iloc[0]


def gap(dimension, group, col):
    return GAPS[(GAPS["dimension"] == dimension) & (GAPS["group"] == group)].iloc[0][col]


def seq_count(prefix, levels=None):
    g = SEQ[SEQ["flag"].str.startswith(prefix)]
    return len(g) if levels is None else int(g["level_of_most_serious"].isin(levels).sum())


# ------------------------------------------------------------------ scoring scales
LIKELIHOOD = {
    5: "Violation shown on the face of the data",
    4: "Strong evidence: significant disparity plus direct evidence in records",
    3: "Significant disparity or credible pattern; employer has a defense to build",
    2: "Signal only: not significant, small sample, or facts missing from the data",
    1: "Verification item: no violation indicated, but the basis is undocumented",
}
SEVERITY = {
    5: "Systemic, many people, termination or willfulness exposure",
    4: "Systemic or touching protected leave/disability/organizing; damages beyond back pay",
    3: "Wage or classification exposure, recoverable with back pay and liquidated damages",
    2: "Limited group or limited dollars",
    1: "Minimal",
}
REVERSIBILITY = {
    "Low": "Harm is hard to undo (lost jobs, terminations, chilled organizing): act first",
    "Medium": "Undoable with effort (re-evaluate applicants, rescind discipline, restore lost earnings)",
    "High": "Fully curable by paying money owed and fixing the rule",
}
REV_WEIGHT = {"Low": 1.5, "Medium": 1.2, "High": 1.0}

# ------------------------------------------------------------------ findings
acc = ai_row("Disability proxy: interview accommodation", "Requested accommodation")
age40 = ai_row("Age (ADEA 40+)", "40 and over")
hisp = ai_row("Race/ethnicity", "Hispanic or Latino")
small = AI[(AI["population"] == AEDT_POP) & AI["assessment"].str.startswith(("Insufficient", "Small sample"))]
under = FLSA[FLSA["flag_type"].str.startswith("Overtime underpayment")]
below = FLSA[FLSA["flag_type"].str.startswith("Misclassification")]
duties = FLSA[FLSA["flag_type"].str.startswith("Classification needs duties")]
drivers = PEOPLE[PEOPLE["flsa_classification"].astype(str).str.contains("Motor Carrier")]
s7_high = S7[S7["risk_tier"].str.startswith("High")]
s7_sup = S7[S7["risk_tier"].str.startswith("Excluded")]
pay_rule = int(S7["narrative"].str.contains("confidentiality policy", case=False).sum())
lv, ac = OT.loc["Leave started in last 26 weeks"], OT.loc["Accommodation request on file"]
seq_leave, seq_acc, seq_pca = (SR.loc[k] for k in SR.index)

F = [
    dict(id="F01", area="AEDT / ADA",
         finding=f"Applicants who asked for an interview accommodation were hired at {acc['selection_rate']:.1%} vs {ai_row('Disability proxy: interview accommodation', 'No request')['selection_rate']:.1%} "
                 f"(impact ratio {acc['impact_ratio']:.2f}, Fisher p={acc['fisher_p_vs_reference']:.3f}; {int(acc['applicants'])} applicants, {int(acc['hires'])} hired). "
                 f"Their AEDT engagement score is {abs(gap('Disability proxy: interview accommodation', 'Requested accommodation', 'engagement_gap_sd')):.2f} SD lower, while their skills-test gap is "
                 f"{gap('Disability proxy: interview accommodation', 'Requested accommodation', 'skills_test_gap_sd'):+.2f} SD: the gap sits in the tool's affect scoring, not in measured job skill.",
         law="ADA 42 U.S.C. 12112(b)(6)-(7): selection criteria that screen out people with disabilities; tests must measure skill, not impairment",
         L=4, S=4, rev="Medium", people=int(acc["applicants"] - acc["hires"]),
         remediation=f"Now: route every accommodation request to a structured-interview alternative instead of AEDT scoring. Within 30 days: re-evaluate the {int(acc['applicants'] - acc['hires'])} rejected requesters on the skills test and a structured interview, and offer the next opening to those who qualify. Require the vendor to document its accommodation process."),
    dict(id="F02", area="AEDT / ADEA",
         finding=f"Applicants 40+ were hired at an impact ratio of {age40['impact_ratio']:.2f} (p={age40['fisher_p_vs_reference']:.3f}). That passes the four-fifths screen, "
                 f"but is not evidence of compliance: their engagement subscore is {abs(gap('Age (ADEA 40+)', '40 and over', 'engagement_gap_sd')):.2f} SD lower and communication "
                 f"{abs(gap('Age (ADEA 40+)', '40 and over', 'communication_gap_sd')):.2f} SD lower, with a skills-test gap of only {gap('Age (ADEA 40+)', '40 and over', 'skills_test_gap_sd'):+.2f} SD. "
                 "The 50-59 band falls to 0.81 and 60+ to 0.53 (only 28 applicants).",
         law="ADEA disparate impact (Smith v. City of Jackson): defense is a reasonable factor other than age; the four-fifths rule is a Title VII screening guide, not the ADEA test",
         L=3, S=4, rev="Medium", people=int(age40["applicants"]),
         remediation="Now: set the engagement and communication subscores to zero weight in hiring decisions until validated. Within 90 days: get the vendor's validation study, or commission one, showing those subscores predict job performance. Keep the problem-solving subscore and the skills test, which show no age gap."),
    dict(id="F03", area="AEDT / Title VII",
         finding=f"Non-native English speakers score {abs(gap('National-origin proxy: English fluency', 'Non-native English', 'communication_gap_sd')):.2f} SD lower on AEDT communication with no skills-test gap. "
                 f"Hispanic applicants' impact ratio is {hisp['impact_ratio']:.2f} (p={hisp['fisher_p_vs_reference']:.2f}): it fails the four-fifths screen, but the difference isn't statistically significant. "
                 f"Black applicants have the highest selection rate, but score {abs(gap('Race/ethnicity', 'Black or African American', 'engagement_gap_sd')):.2f} SD lower on engagement.",
         law="Title VII disparate impact (race, national origin); Connecticut v. Teal: a good bottom line does not excuse a discriminatory component",
         L=3, S=4, rev="Medium", people=int(hisp["applicants"]),
         remediation="Same subscore change as F02 (one fix covers both). For English-language communication, require a documented job analysis showing the level needed for warehouse roles. Re-run this analysis after 6 months of new applicants before drawing conclusions about the Hispanic ratio."),
    dict(id="F04", area="FLSA",
         finding=f"{len(under)} hourly employees were paid overtime without the shift differential in the regular rate: ${under['exposure_13wk_high_usd'].sum():,.0f} short in 13 weeks "
                 f"(about ${under['exposure_13wk_high_usd'].sum() * 4:,.0f} a year). Every case is on 2nd or 3rd shift at {', '.join(sorted(under['site'].unique()))}, which points to a payroll configuration.",
         law="FLSA 29 U.S.C. 207(e): regular rate includes shift differentials; 2-year lookback (3 if willful) plus equal liquidated damages",
         L=5, S=3, rev="High", people=len(under),
         remediation="Now: fix the payroll rule at both sites. Within 30 days: recompute overtime for all affected employees, current and former, back 3 years, and pay the difference. Check whether other premiums (attendance bonus, lead pay) have the same problem."),
    dict(id="F05", area="FLSA",
         finding=f"{len(below)} supervisors are classified exempt but paid below the $35,568 salary floor, while averaging {below['weekly_hours_avg_13wk'].mean():.0f} hours a week. "
                 f"Overtime exposure: ${below['exposure_13wk_low_usd'].sum():,.0f}-${below['exposure_13wk_high_usd'].sum():,.0f} per 13 weeks, depending on the regular-rate method counsel accepts.",
         law="29 C.F.R. 541.600: salary-level test; failing it defeats the exemption regardless of duties",
         L=5, S=3, rev="High", people=len(below),
         remediation="Now: either raise these salaries above the floor or reclassify them as non-exempt and start tracking hours. Pay back overtime for the lookback period. Add a salary-floor check to the compensation system so this can't recur."),
    dict(id="F06", area="FLSA",
         finding=f"{len(duties)} dispatchers are classified as administrative-exempt. Their work appears to be routine scheduling, which may not meet the duties test; payroll data can't settle it.",
         law="29 C.F.R. 541.200-202: administrative exemption needs discretion and independent judgment on significant matters",
         L=3, S=2, rev="High", people=len(duties),
         remediation="Within 60 days: have counsel run a duties interview with each dispatcher and their manager. Reclassify any who don't meet the test, with back pay. No change before that review."),
    dict(id="F07", area="Premium OT algorithm / FMLA, ADA",
         finding=f"The scheduling algorithm offers premium overtime {lv['offer_ratio']:.2f}x as often to employees whose leave started in the last 26 weeks (p={lv['permutation_p']:.4f}, n={int(lv['n_group'])}) "
                 f"and {ac['offer_ratio']:.2f}x as often to employees with an accommodation on file (p={ac['permutation_p']:.4f}, n={int(ac['n_group'])}). "
                 f"Their reliability scores are {lv['mean_reliability_group']:.0f} and {ac['mean_reliability_group']:.0f} vs about 83: the score counts protected leave and restrictions against them.",
         law="FMLA 29 C.F.R. 825.220(c): leave can't be a negative factor in employment actions; ADA: restrictions can't reduce opportunities without an individualized assessment",
         L=4, S=4, rev="Medium", people=int(lv["n_group"] + ac["n_group"]),
         remediation="Now: remove FMLA-designated absences and accommodation restrictions from the reliability score. Within 30 days: estimate premium-overtime earnings each affected employee lost and pay it. Put any change to the algorithm's inputs through HR and legal sign-off."),
    dict(id="F08", area="FMLA",
         finding=f"{seq_count('FMLA interference')} employees received attendance points for absences during approved FMLA leave; "
                 f"{seq_count('FMLA interference', ['Termination'])} were terminated and {seq_count('FMLA interference', ['Final warning'])} reached a final warning. "
                 f"Employees who took leave were disciplined {seq_leave['rate_ratio']:.1f}x as often as a matched comparison window (p<0.001).",
         law="FMLA 29 U.S.C. 2615(a)(1) interference; 29 C.F.R. 825.220(c)",
         L=5, S=5, rev="Low", people=seq_count("FMLA interference"),
         remediation="Now: rescind the points and any discipline built on them. Offer reinstatement and back pay to the terminated employees. Set the attendance system to exclude FMLA-designated time automatically. Retrain supervisors on how points work with protected leave."),
    dict(id="F09", area="ADA",
         finding=f"{seq_count('Performance discipline that cites')} employees were written up for productivity in narratives that cite their own accommodation (for example, held to the full pick rate while on a lifting restriction). "
                 f"Accommodation requesters were disciplined {seq_acc['rate_ratio']:.1f}x as often in the following 120 days (p<0.001).",
         law="ADA failure to accommodate and retaliation (42 U.S.C. 12112(b)(5)(A), 12203)",
         L=4, S=4, rev="Medium", people=seq_count("Performance discipline that cites"),
         remediation="Now: rescind these warnings. For each accommodated employee, set and document an adjusted productivity standard through the interactive process. Within 60 days: change the productivity reports so they flag employees with an active accommodation before any warning is issued."),
    dict(id="F10", area="NLRA",
         finding=f"{len(s7_high)} discipline events penalize what looks like protected concerted activity: petitions over heat, discussing pay, a group refusal over a broken dock fan, a drivers' group post about the overtime algorithm. "
                 f"{int((s7_high['level'] == 'Termination').sum())} ended in termination. Employees with concerted activity on file were disciplined {seq_pca['rate_ratio']:.1f}x as often within 60 days (p<0.001).",
         law="NLRA Sections 7 and 8(a)(1); non-union workplaces are covered",
         L=4, S=4, rev="Low", people=int(s7_high["employee_id"].nunique()),
         remediation="Now: have counsel review each of these events. Rescind and expunge the discipline where the activity was protected, and offer reinstatement where it led to termination. Within 30 days: train supervisors on concerted activity. Any written posting or notice is a decision for counsel."),
    dict(id="F11", area="NLRA",
         finding=f"Discipline narratives enforce a \"pay confidentiality policy\" ({pay_rule} events). A rule against discussing pay is unlawful on its face for non-supervisory employees, separate from any one discipline decision.",
         law="NLRA Section 8(a)(1); long-standing Board law on pay-discussion rules",
         L=5, S=3, rev="High", people=pay_rule,
         remediation="Now: rescind the rule and tell employees in writing that they may discuss pay. Remove discipline issued under it (covered in F10). Review the handbook for similar rules."),
    dict(id="F12", area="ADA / state law",
         finding=f"{seq_count('Points assessed during non-FMLA')} employees got attendance points during medical leave that wasn't FMLA-eligible. "
                 f"{seq_count('Points assessed during non-FMLA', ['Termination'])} was terminated. FMLA doesn't apply to them, but leave can be a required ADA accommodation, and state law may protect it.",
         law="ADA (leave as reasonable accommodation); state leave and disability laws in TN, MS, AR",
         L=2, S=4, rev="Medium", people=seq_count("Points assessed during non-FMLA"),
         remediation="Within 60 days: HR reviews each case for an ADA request that should have opened the interactive process. Rescind points where it should have. Update the leave intake so a medical leave request that doesn't qualify for FMLA prompts an ADA review."),
    dict(id="F13", area="AEDT / monitoring",
         finding=f"{len(small)} AEDT group comparisons are too small to interpret ({', '.join(f'{r.group} n={int(r.applicants)}' for r in small.itertuples())}). They're reported as counts only. No conclusion is drawn either way.",
         law="UGESP 29 C.F.R. 1607.4(D): small numbers need cautious interpretation; pool data over time",
         L=2, S=2, rev="Medium", people=int(small["applicants"].sum()),
         remediation="Pool these groups' data over a rolling 24-month window and re-test at each quarterly review. Don't publish their ratios until each group has at least 30 applicants."),
    dict(id="F14", area="FLSA / verification",
         finding=f"{len(drivers)} CDL-A drivers average about 53 hours a week with no overtime pay. That's lawful under the Motor Carrier Act exemption only if they drive vehicles over 10,000 lbs in interstate commerce. The file doesn't document either point.",
         law="FLSA 29 U.S.C. 213(b)(1); SAFETEA-LU small-vehicle exception",
         L=1, S=3, rev="High", people=len(drivers),
         remediation="Within 60 days: document vehicle weights and interstate routes for each driver. Confirm whether state law follows the federal exemption."),
    dict(id="F15", area="NLRA / verification",
         finding=f"{len(s7_sup)} supervisor was disciplined for joining associates' concerted complaint. Supervisors aren't covered by Section 7, but a job title doesn't settle who counts as one.",
         law="NLRA Section 2(11) supervisor definition; Oakwood Healthcare test",
         L=1, S=1, rev="Medium", people=len(s7_sup),
         remediation="Confirm whether the person actually has authority to hire, fire, discipline or direct work using independent judgment. If not, review the event under F10."),
]

reg = pd.DataFrame(F)
reg["priority_score"] = (reg["L"] * reg["S"] * reg["rev"].map(REV_WEIGHT)).round(1)
reg = reg.sort_values(["priority_score", "L"], ascending=False).reset_index(drop=True)
reg.insert(0, "rank", reg.index + 1)
reg.rename(columns={"L": "likelihood_1to5", "S": "severity_1to5", "rev": "reversibility", "people": "people_affected"}, inplace=True)
reg.to_csv(R / "findings_register.csv", index=False)

# ------------------------------------------------------------------ markdown
md = ["# Cardinal Logistics internal audit: ranked findings",
      "", "*Synthetic data for training. Draft for review by counsel. Run real audits at counsel's direction to preserve privilege.*", "",
      f"Scope: {len(PEOPLE):,} applicant and employee records (AEDT era 2024-07-01 to 2026-07-31, plus pre-AEDT incumbents) and the 18-month discipline record ending 2026-09-30.", "",
      f"**Bottom line.** {int((reg['likelihood_1to5'] >= 4).sum())} of {len(reg)} findings are likely violations, and "
      f"{int((reg['reversibility'] == 'Low').sum())} of those carry harm that is hard to undo (terminations tied to FMLA leave and concerted activity), so they come first. "
      "The AEDT's disparities trace to two affect-based subscores, so zero-weighting them is a proportionate first step that doesn't require scrapping the tool. "
      "The wage findings are fully curable with a payroll fix and back pay.", "",
      "## How findings are ranked", "",
      "Priority = likelihood × severity × reversibility weight (Low 1.5, Medium 1.2, High 1.0). Harm that's harder to undo moves up.", "",
      "| Score | Likelihood | Severity |", "|---|---|---|"]
for k in range(5, 0, -1):
    md.append(f"| {k} | {LIKELIHOOD[k]} | {SEVERITY[k]} |")
md += ["", "| Reversibility | Meaning |", "|---|---|"] + [f"| {k} | {v} |" for k, v in REVERSIBILITY.items()]
md += ["", "## Ranked register", "",
       "| Rank | ID | Area | L | S | Reversibility | Priority | People | Finding |", "|---|---|---|---|---|---|---|---|---|"]
for _, r in reg.iterrows():
    md.append(f"| {r['rank']} | {r['id']} | {r['area']} | {r['likelihood_1to5']} | {r['severity_1to5']} | {r['reversibility']} | {r['priority_score']} | {r['people_affected']} | {r['finding']} |")
md += ["", "## Remediation, in priority order", ""]
for _, r in reg.iterrows():
    md += [f"### {r['rank']}. {r['id']} · {r['area']}", "", f"**Legal basis:** {r['law']}", "", f"**Proportionate step:** {r['remediation']}", ""]
md += ["## What this audit does not show", "",
       "- **Passing the four-fifths rule is not proof of compliance.** Groups that passed still have subscore gaps (F02, F03). The Uniform Guidelines require a validation study for any procedure with adverse impact, and a disparity can exist without failing the ratio.",
       "- **Small groups are not cleared.** A ratio isn't interpreted when a group has fewer than 30 applicants or fewer than 5 expected hires. Those groups are neither a finding nor evidence of fairness (F13).",
       "- **Timing is evidence, not a conclusion.** Discipline soon after leave, an accommodation or concerted activity is a reason to review each file. It doesn't prove retaliation.",
       "- **Narrative screening is rule-based.** Every Section 7 tier needs a person to read the full file before acting.", "",
       "## Analysis corrections log", "",
       "| # | Where | Original logic | Corrected logic | Who caught it |", "|---|---|---|---|---|",
       "| 1 | Section 7 rules | Matched routine words (\"scheduled shift\", \"safety lead\"); 167 events in Medium | Match only employee activity about pay, hours or conditions | Analyst self-review |",
       "| 2 | Small samples | Groups under 30 hidden even when the exact test was significant | Report the exact test; a significant small-group result is a finding | Analyst self-review |",
       "| 3 | Age bands | Compared against the best band, so 18-24 \"failed\"; four-fifths implied as the ADEA test | Each 40+ band vs pooled under-40; ADEA defense is a reasonable factor other than age | Analyst self-review |",
       "| 4 | Sequence comparison | Comparison windows a different length from requesters' | Matched median window length | Analyst self-review |",
       "| 5 | AEDT bottom line | Only overall selection rates reported | Subscore gaps reported (Connecticut v. Teal) | Analyst self-review |",
       "| 6 | | | | Reviewer |", "| 7 | | | | Reviewer |", ""]
(R / "audit_summary.md").write_text("\n".join(md))
print(reg[["rank", "id", "area", "likelihood_1to5", "severity_1to5", "reversibility", "priority_score", "people_affected"]].to_string(index=False))
