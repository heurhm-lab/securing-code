#!/usr/bin/env python3
"""Recomputes the headline numbers quoted in ANSWER_KEY.md (spoiler: uses ground truth)."""
from pathlib import Path
import numpy as np
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
ROOT = Path(__file__).resolve().parent.parent
d = pd.read_csv(ROOT / "data/cardinal_applicants_employees.csv")
ev = pd.read_csv(ROOT / "data/cardinal_discipline_events.csv")
g = pd.read_csv(ROOT / "answer_key/ground_truth_people.csv")
eg = pd.read_csv(ROOT / "answer_key/ground_truth_discipline.csv")

m = d.drop_duplicates("applicant_id").merge(g, on="applicant_id")
m["adv"] = m.aedt_recommendation.eq("Advance")
m["hired"] = m.hire_decision.eq("Hired")
m["band40"] = np.where(m.age_band.isin(["40-49", "50-59", "60+"]), "40+", "<40")


def ir(col, ref, df=m, out="adv"):
    t = df.groupby(col)[out].agg(["mean", "size"])
    t["impact_ratio"] = t["mean"] / t.loc[ref, "mean"]
    return t.round(3)


print("== AEDT selection (Advance) ==")
for col, ref in [("band40", "<40"), ("age_band", "25-39"), ("race_ethnicity_proxy_bisg", "White"),
                 ("true_race_ethnicity", "White"), ("hiring_accommodation_requested", 0)]:
    print(ir(col, ref), "\n")
phys = m[m.job_group.isin(["Forklift Operator", "Driver", "Fleet Maintenance Technician"])]
print("physical roles, gender proxy\n", ir("name_inferred_gender", "M", phys))
print("physical roles, true gender\n", ir("true_gender", "M", phys))
print("== Hire ==")
for col, ref in [("band40", "<40"), ("race_ethnicity_proxy_bisg", "White"), ("hiring_accommodation_requested", 0)]:
    print(ir(col, ref, out="hired"), "\n")
print("advance->hire by age\n", m[m.adv].groupby("band40").hired.mean().round(3))
print(pd.crosstab([m.aedt_recommendation, m.referral_source.eq("Employee Referral")], m.hire_decision))
print("referral share by proxy\n", m.groupby("race_ethnicity_proxy_bisg").referral_source.apply(lambda s: s.eq("Employee Referral").mean()).round(3))
print("score corr\n", m[["aedt_score", "commute_miles", "employment_gap_months", "latent_qualification"]].corr().round(2))
h = m[m.perf_rating_90day.notna()]
print("perf vs score/commute/gap\n", h[["perf_rating_90day", "aedt_score", "commute_miles", "employment_gap_months"]].corr().round(2).iloc[0])
print("perf by age\n", h.groupby("band40").perf_rating_90day.mean().round(2))
print("note classes\n", m.recruiter_note_class.value_counts())

print("\n== FLSA / payroll ==")
iss = g.set_index("applicant_id").issues.fillna("")
e = m[m.hired].copy()
e["issues"] = e.applicant_id.map(iss)
pay = e[e.hours_worked_period.notna()].copy()
pay["ot_due"] = pay.ot_pay_due_at_1_5x_regular_rate
pay["shortfall"] = (pay.ot_due - pay.overtime_pay_period).clip(lower=0)
codes = ["salary_below_threshold", "dispatcher_admin_exemption_doubtful", "exec_exemption_fails_duties",
         "mca_small_vehicle_misapplied", "hourly_coded_exempt", "ot_paid_straight_time", "ot_unpaid",
         "regular_rate_excludes_diff_bonus", "off_the_clock_capped_40"]
rows = []
for c in codes:
    s = pay[pay.issues.str.contains(c)]
    allp = e[e.issues.str.contains(c)]
    extra = 0.0
    if c == "off_the_clock_capped_40":
        unpaid = (s.badge_hours_period - s.hours_worked_period - 2.5 * s.weeks_in_period).clip(lower=0)
        extra = (unpaid * 1.5 * s.regular_rate).sum()
    rows.append((c, len(allp), len(s), round(s.shortfall.sum() + extra, 2)))
print(pd.DataFrame(rows, columns=["issue", "employees", "with_Q2_payroll", "est_Q2_shortfall_$"]))
print("FLSA label variants\n", e.flsa_classification.value_counts())

print("\n== Discipline ==")
evm = ev.merge(eg, on=["event_id", "applicant_id"])
print(evm.narrative_class.value_counts())
print(pd.crosstab(evm.narrative_class, evm.event_category))
print(pd.crosstab(evm.narrative_class, evm.action_taken))
emp = e.set_index("applicant_id")
evm["pca_flag"] = evm.applicant_id.map(emp.pca_flag)
print("PCA narratives by employee pca_flag\n", pd.crosstab(evm.narrative_class, evm.pca_flag))
print("pca flag vs latent\n", pd.crosstab(e.pca_flag, e.pca_engaged))
print("term rate by pca_flag\n", e.groupby("pca_flag").employment_status.apply(lambda s: s.eq("Terminated - Involuntary").mean()).round(3))
print("disc rate by pca_flag\n", e.groupby("pca_flag").discipline_event_count.apply(lambda s: (s > 0).mean()).round(3))
leg = evm[evm.narrative_class == "legit"].copy()
leg["race"] = leg.applicant_id.map(m.set_index("applicant_id").race_ethnicity_proxy_bisg)
leg["sev"] = leg.action_taken.map({"Verbal Warning": 0, "Written Warning": 1, "Final Written Warning": 2, "Termination": 3})
print("legit-event severity by proxy race\n", leg.groupby("race").sev.agg(["mean", "size"]).round(2))
print("other_risk\n", evm.other_risk.value_counts())
print("\n== Issue counts ==")
print(g.issues.dropna().str.split(";").explode().value_counts())
