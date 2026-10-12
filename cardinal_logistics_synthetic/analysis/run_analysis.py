#!/usr/bin/env python3
"""
Compliance screen of the Cardinal Logistics synthetic dataset.

Reads ONLY data/*.csv (never answer_key/). Every decision rule is defined
up front as a constant or function; results go to analysis/outputs/.

    python3 cardinal_logistics_synthetic/analysis/run_analysis.py
"""
import re
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.multitest import multipletests

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "outputs"
OUT.mkdir(exist_ok=True)
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_colwidth", 160)

# ---------------------------------------------------------------- assumptions
SNAPSHOT = pd.Timestamp("2026-06-30")
SALARY_FLOOR = 35568            # 29 CFR 541.600, $684/wk (2024 increase vacated)
MCA_SMALL_VEHICLE_LBS = 10000   # SAFETEA-LU TCA small-vehicle exception
MEAL_HRS_PER_WEEK = 2.5         # 5 shifts x 30-min unpaid meal (README)
OTC_FLAG_HRS_PER_WEEK = 4.0     # badge - paid gap above this => possible off-the-clock
MIN_GROUP_N = 30                # groups smaller than this are not used as comparator
MONEY_TOL = 0.50
ACCOM_WINDOW = 90               # days after accommodation request
LEAVE_WINDOW = 60               # days after leave end
PENDING_STALE = 60
PHYSICAL = ["Forklift Operator", "Driver", "Fleet Maintenance Technician"]
SEV = {"Verbal Warning": 0, "Written Warning": 1, "Final Written Warning": 2, "Termination": 3}

log = []


def section(t):
    print("\n" + "=" * 100 + f"\n{t}\n" + "=" * 100)


# ---------------------------------------------------------------- load + clean
raw = pd.read_csv(ROOT / "data/cardinal_applicants_employees.csv",
                  parse_dates=["application_date", "hire_date", "termination_date", "accommodation_request_date",
                               "leave_start_date", "leave_end_date", "most_recent_discipline_date"])
ev = pd.read_csv(ROOT / "data/cardinal_discipline_events.csv", parse_dates=["event_date"])

section("0. DATA QUALITY")
n_raw = len(raw)
exact_dups = raw[raw.duplicated(keep=False)].applicant_id.unique()
d = raw.drop_duplicates()
conflict_ids = d[d.applicant_id.duplicated(keep=False)].applicant_id.unique()
print(f"raw rows {n_raw}; exact-duplicate rows removed {n_raw - len(raw.drop_duplicates())} "
      f"(IDs {list(exact_dups)}); IDs with conflicting rows {list(conflict_ids)}")
print(d[d.applicant_id.isin(conflict_ids)][["applicant_id", "aedt_score", "aedt_recommendation", "hire_decision"]]
      .sort_values("applicant_id"))
# Assumption: conflicting rows cannot be resolved -> exclude those IDs from the AEDT analysis.
d = d[~d.applicant_id.isin(conflict_ids)].copy()
print(f"unique applicants analysed: {len(d)} (+{len(conflict_ids)} conflicting IDs excluded)")

# recommendation vs score consistency
d["rec_check"] = np.where(d.aedt_score >= 65, "Advance", np.where(d.aedt_score.notna(), "Do Not Advance", None))
bad_rec = d[d.aedt_score.notna() & (d.rec_check != d.aedt_recommendation)]
print(f"rows where recommendation != (score>=65): {len(bad_rec)}")

# FLSA label normalisation
def norm_flsa(x):
    if pd.isna(x):
        return None
    k = re.sub(r"[^a-z]", "", str(x).lower())
    return {"exempt": "Exempt", "e": "Exempt", "nonexempt": "Non-Exempt", "ne": "Non-Exempt"}.get(k, "UNKNOWN")


print("FLSA label variants:", d.flsa_classification.value_counts().to_dict())
d["flsa"] = d.flsa_classification.map(norm_flsa)

# age band vs graduation year
BANDS = ["18-24", "25-39", "40-49", "50-59", "60+"]


def band_of(age):
    return BANDS[0] if age < 25 else BANDS[1] if age < 40 else BANDS[2] if age < 50 else BANDS[3] if age < 60 else BANDS[4]


d["implied_age"] = d.application_date.dt.year - d.hs_grad_year + 18
d["implied_band"] = d.implied_age.map(lambda a: band_of(a) if pd.notna(a) else None)
d["band_gap"] = [abs(BANDS.index(a) - BANDS.index(b)) if isinstance(b, str) else np.nan for a, b in zip(d.age_band, d.implied_band)]
age_incons = d[d.band_gap >= 2]
print(f"age_band inconsistent with hs_grad_year by >=2 bands: {len(age_incons)} -> {list(age_incons.applicant_id)}")

# employee-record anomalies
rej_emp = d[(d.hire_decision != "Hired") & d.hire_date.notna()]
print(f"non-hired rows carrying employee data: {list(rej_emp.applicant_id)}")
emp = d[d.hire_decision == "Hired"].copy()
pay = emp[emp.hours_worked_period.notna() & (emp.weeks_in_period > 0)].copy()
pay["hrs_wk"] = pay.hours_worked_period / pay.weeks_in_period
dq_pay = pd.concat([
    pay[pay.hrs_wk > 100].assign(dq="hours/week > 100"),
    pay[(pay.regular_hours_period + pay.overtime_hours_period - pay.hours_worked_period).abs() > 0.01].assign(dq="regular+OT != hours"),
    pay[pay.overtime_pay_period < 0].assign(dq="negative OT pay"),
    pay[pay.badge_hours_period.isna()].assign(dq="badge hours missing"),
])
print(dq_pay[["applicant_id", "dq", "hours_worked_period", "regular_hours_period", "overtime_hours_period", "overtime_pay_period"]])
dq_pay_ids = set(dq_pay.applicant_id)

ev = ev.merge(emp[["applicant_id", "hire_date", "job_title", "direct_reports", "pca_flag"]], on="applicant_id", how="left")
ev_before_hire = ev[ev.event_date < ev.hire_date]
print(f"discipline events dated before hire: {ev_before_hire[['event_id', 'applicant_id', 'event_date', 'hire_date']].values.tolist()}")
cnt = ev.groupby("applicant_id").size()
emp["ev_count_actual"] = emp.applicant_id.map(cnt).fillna(0).astype(int)
mism = emp[emp.discipline_event_count.fillna(0) != emp.ev_count_actual]
print(f"discipline_event_count != events file: {mism[['applicant_id', 'discipline_event_count', 'ev_count_actual']].values.tolist()}")
dq_rows = []
for i in exact_dups: dq_rows.append((i, "exact duplicate row"))
for i in conflict_ids: dq_rows.append((i, "conflicting duplicate (AEDT score differs) - excluded from AEDT stats"))
for i in age_incons.applicant_id: dq_rows.append((i, "age_band vs hs_grad_year mismatch"))
for i in rej_emp.applicant_id: dq_rows.append((i, "rejected applicant with employee record"))
for _, r in dq_pay.iterrows(): dq_rows.append((r.applicant_id, r.dq))
for _, r in ev_before_hire.iterrows(): dq_rows.append((r.applicant_id, f"{r.event_id} dated before hire"))
for i in mism.applicant_id: dq_rows.append((i, "discipline_event_count mismatch"))
pd.DataFrame(dq_rows, columns=["applicant_id", "issue"]).to_csv(OUT / "data_quality_flags.csv", index=False)

# ---------------------------------------------------------------- 1. AEDT
section("1. AEDT FOUR-FIFTHS ANALYSIS")
d["age40"] = np.where(d.age_band.isin(["40-49", "50-59", "60+"]), "40+", "<40")
d["accom"] = d.hiring_accommodation_requested.map({0: "No request", 1: "Requested accommodation"})
d["sel_scored"] = d.aedt_recommendation.eq("Advance")


def four_fifths(df, col, sel, label, ref=None):
    g = df.groupby(col)[sel].agg(selected="sum", n="size")
    g["rate"] = g.selected / g.n
    eligible = g[g.n >= MIN_GROUP_N]
    comp = ref if ref is not None else eligible.rate.idxmax()
    cr, cn, cs = g.loc[comp, "rate"], g.loc[comp, "n"], g.loc[comp, "selected"]
    rows = []
    for k, r in g.iterrows():
        if k == comp:
            rows.append(dict(attribute=label, group=k, n=r.n, selected=r.selected, rate=r.rate, comparator=comp,
                             impact_ratio=1.0, z=np.nan, p_fisher=np.nan, shortfall=0.0, small_n=r.n < MIN_GROUP_N))
            continue
        tbl = [[r.selected, r.n - r.selected], [cs, cn - cs]]
        p_f = stats.fisher_exact(tbl)[1]
        pp = (r.selected + cs) / (r.n + cn)
        z = (r.rate - cr) / np.sqrt(pp * (1 - pp) * (1 / r.n + 1 / cn)) if 0 < pp < 1 else np.nan
        rows.append(dict(attribute=label, group=k, n=r.n, selected=r.selected, rate=r.rate, comparator=comp,
                         impact_ratio=r.rate / cr, z=z, p_fisher=p_f, shortfall=r.n * cr - r.selected,
                         small_n=r.n < MIN_GROUP_N))
    t = pd.DataFrame(rows)
    m = t.p_fisher.notna()
    t.loc[m, "p_holm"] = multipletests(t.loc[m, "p_fisher"], method="holm")[1]
    t["flag_4_5ths"] = t.impact_ratio < 0.8
    t["flag_sig"] = t.p_holm < 0.05
    return t


scored = d[d.aedt_score.notna()]
print(f"population A (scored): n={len(scored)}; population B (all, unscored = not selected): n={len(d)}; "
      f"unscored n={d.aedt_score.isna().sum()}")
specs = [("age40", "Age 40+ (self-reported band)", "<40"), ("age_band", "Age band", None),
         ("race_ethnicity_proxy_bisg", "Race/ethnicity (BISG proxy)", None),
         ("name_inferred_gender", "Sex (name-inferred proxy)", None), ("accom", "Disability proxy: hiring accommodation", "No request")]
res = []
for col, lab, ref in specs:
    res.append(four_fifths(scored, col, "sel_scored", lab, ref).assign(population="A: scored, AEDT Advance"))
    res.append(four_fifths(d, col, "sel_scored", lab, ref).assign(population="B: all, unscored=not selected"))
phys = scored[scored.job_group.isin(PHYSICAL)]
res.append(four_fifths(phys, "name_inferred_gender", "sel_scored", "Sex proxy - physical roles only", None)
           .assign(population="A: scored, AEDT Advance"))
# hire stage (withdrawn excluded)
h = d[d.hire_decision != "Withdrawn"].copy()
h["hired"] = h.hire_decision.eq("Hired")
for col, lab, ref in specs:
    res.append(four_fifths(h, col, "hired", lab, ref).assign(population="C: final hire (withdrawn excluded)"))
aedt = pd.concat(res, ignore_index=True)
aedt.to_csv(OUT / "aedt_four_fifths.csv", index=False)
show = ["population", "attribute", "group", "n", "selected", "rate", "comparator", "impact_ratio", "z", "p_fisher", "p_holm", "shortfall", "small_n"]
print(aedt[show].round(4).to_string())

# sensitivity: drop age-inconsistent rows
s2 = scored[~scored.applicant_id.isin(age_incons.applicant_id)]
print("\nsensitivity, age40 excluding inconsistent age rows:")
print(four_fifths(s2, "age40", "sel_scored", "age40", "<40")[["group", "n", "rate", "impact_ratio", "p_fisher"]].round(4))

# by job group: age 40+ ratio
print("\nAge 40+ impact ratio within job group (population A):")
jr = []
for jg, sub in scored.groupby("job_group"):
    t = four_fifths(sub, "age40", "sel_scored", jg, "<40")
    o = t[t.group == "40+"]
    if len(o):
        jr.append(dict(job_group=jg, n_40plus=int(o.n.iloc[0]), n_under40=int(sub[sub.age40 == "<40"].shape[0]),
                       ir=o.impact_ratio.iloc[0], p=o.p_fisher.iloc[0]))
print(pd.DataFrame(jr).round(3).to_string())

# mechanism: what drives the score?
section("1b. AEDT SCORE DRIVERS AND JOB-RELATEDNESS")
mod = smf.ols("aedt_score ~ C(age_band, Treatment('25-39')) + C(race_ethnicity_proxy_bisg, Treatment('White')) "
              "+ C(name_inferred_gender, Treatment('M')) + commute_miles + employment_gap_months + hiring_accommodation_requested",
              data=scored).fit()
print(mod.summary().tables[1])
print("\ncommute by race proxy:\n", d.groupby("race_ethnicity_proxy_bisg").commute_miles.agg(["mean", "median", "size"]).round(1))
print("\ngap months by gender proxy:\n", d.groupby("name_inferred_gender").employment_gap_months.agg(["mean", "size"]).round(1))
pr = emp[emp.perf_rating_90day.notna()]
print(f"\nhires with 90-day rating: n={len(pr)}")
mp = smf.ols("perf_rating_90day ~ aedt_score + commute_miles + employment_gap_months + C(age40)",
             data=pr.assign(age40=np.where(pr.age_band.isin(['40-49', '50-59', '60+']), '40+', '<40'))).fit()
print(mp.summary().tables[1])
print("mean 90-day rating by age group:", pr.assign(a=np.where(pr.age_band.isin(['40-49', '50-59', '60+']), '40+', '<40'))
      .groupby("a").perf_rating_90day.agg(["mean", "size"]).round(2).to_dict())
r_ = stats.pearsonr(pr.aedt_score, pr.perf_rating_90day)
print(f"r(score, rating)={r_[0]:.2f} p={r_[1]:.2g}")
# advance -> hire by age
adv = h[h.aedt_recommendation == "Advance"]
t = pd.crosstab(adv.age40, adv.hired)
print("\nAmong AEDT 'Advance' applicants, hire rate by age:\n", (t[True] / t.sum(axis=1)).round(3).to_dict(), "n:", t.sum(axis=1).to_dict(),
      "Fisher p=%.3g" % stats.fisher_exact(t.values)[1])
dna = h[h.aedt_recommendation == "Do Not Advance"]
t = pd.crosstab(dna.referral_source.eq("Employee Referral"), dna.hired)
print("Among 'Do Not Advance', hire rate referral vs not:", (t[True] / t.sum(axis=1)).round(3).to_dict(), "n:", t.sum(axis=1).to_dict(),
      "Fisher p=%.3g" % stats.fisher_exact(t.values)[1])
print("referral share by race proxy:", d.groupby("race_ethnicity_proxy_bisg").referral_source.apply(lambda s: s.eq("Employee Referral").mean()).round(3).to_dict())
notes = d[d.recruiter_note.notna()]
AGE_WORDS = r"overqualified|energy|retir|long-term fit|keeping pace|younger|digital native|recent grad|young"
print("\nrecruiter notes matching age-coded terms:", notes.recruiter_note.str.contains(AGE_WORDS, case=False).sum(),
      "| accent:", notes.recruiter_note.str.contains("accent", case=False).sum(),
      "| childcare/kids:", notes.recruiter_note.str.contains("childcare|kids", case=False).sum(),
      "| unscored accommodation:", notes.recruiter_note.str.contains("extra time|alt format|accommodation", case=False).sum())
notes[notes.recruiter_note.str.contains(AGE_WORDS + "|accent|childcare|kids|extra time|alt format|accommodation|override",
                                        case=False)][["applicant_id", "age_band", "job_group", "aedt_recommendation", "hire_decision", "recruiter_note"]] \
    .to_csv(OUT / "recruiter_notes_flagged.csv", index=False)

# ---------------------------------------------------------------- 2. FLSA
section("2. FLSA CLASSIFICATION AND OVERTIME")
emp = emp[~emp.applicant_id.isin(rej_emp.applicant_id)]
emp["flsa"] = emp.flsa_classification.map(norm_flsa)
print("employees:", len(emp), "| by normalised class:", emp.flsa.value_counts().to_dict())
print(pd.crosstab([emp.job_title], [emp.flsa, emp.flsa_exemption_basis.fillna("(blank)")]))

ADMIN_DUTIES_DOUBT = r"using TMS routing recommendations|answers driver check-in calls"
flags = []
ex = emp[emp.flsa == "Exempt"]
for _, r in ex.iterrows():
    f = []
    if r.flsa_exemption_basis in ("Executive", "Administrative") or pd.isna(r.flsa_exemption_basis):
        if pd.notna(r.annual_salary) and r.annual_salary < SALARY_FLOOR:
            f.append("F1 salary below $35,568 floor")
        if pd.isna(r.annual_salary):
            f.append("F2 paid hourly / no salary basis")
    if pd.isna(r.flsa_exemption_basis) or r.flsa_exemption_basis == "Not exempt":
        f.append("F3 exempt with no exemption basis")
    if r.flsa_exemption_basis == "Executive" and (pd.isna(r.direct_reports) or r.direct_reports < 2):
        f.append("F4 executive w/ <2 direct reports")
    if r.flsa_exemption_basis == "Motor Carrier Act" and pd.notna(r.vehicle_gvwr_lbs) and r.vehicle_gvwr_lbs <= MCA_SMALL_VEHICLE_LBS:
        f.append("F5 MCA claimed but vehicle <=10,000 lbs")
    if r.flsa_exemption_basis == "Administrative" and isinstance(r.primary_duties_summary, str) and re.search(ADMIN_DUTIES_DOUBT, r.primary_duties_summary):
        f.append("F6 admin duties look clerical/rule-following (review)")
    for x in f:
        flags.append((r.applicant_id, r.job_title, r.site, r.flsa_exemption_basis, r.annual_salary, r.direct_reports, r.vehicle_gvwr_lbs, x))
cls = pd.DataFrame(flags, columns=["applicant_id", "job_title", "site", "basis", "annual_salary", "direct_reports", "gvwr", "flag"])
print("\nexempt-classification flags (employees):")
print(cls.groupby(["flag", "job_title"]).size().to_string())
print("\nnot flagged, by title (exempt):", ex[~ex.applicant_id.isin(cls.applicant_id)].job_title.value_counts().to_dict())
print("Logistics Coordinator salary distribution:", emp[emp.job_title == "Logistics Coordinator"].annual_salary.describe().round(0).to_dict())

# exposure for misclassified exempt (Q2 payroll window)
pay = emp[emp.hours_worked_period.notna() & (emp.weeks_in_period > 0) & ~emp.applicant_id.isin(dq_pay_ids)].copy()
pay["hrs_wk"] = pay.hours_worked_period / pay.weeks_in_period
mis = pay[pay.applicant_id.isin(cls.applicant_id)].merge(cls.groupby("applicant_id").flag.agg("; ".join), on="applicant_id")


def exposure(r):
    ot = r.overtime_hours_period
    if pd.notna(r.base_hourly_rate):  # hourly MCA drivers: regular rate known
        rr = (r.base_hourly_rate * r.hours_worked_period + r.shift_differential_pay_period + r.nondiscretionary_bonus_period) / r.hours_worked_period
        return pd.Series({"low": 1.5 * rr * ot, "high": 1.5 * rr * ot})
    wk = r.annual_salary / 52
    return pd.Series({"low": 0.5 * (wk / r.hrs_wk) * ot,       # fluctuating-workweek half-time
                      "high": 1.5 * (wk / 40) * ot})            # salary covers 40 h only


mis[["exp_low", "exp_high"]] = mis.apply(exposure, axis=1)
mis["primary"] = mis.flag.str.split("; ").str[0]
print("\nQ2 OT exposure, flagged exempt employees with payroll (low=FWW half-time, high=1.5x salary/40):")
print(mis.groupby("primary").agg(n=("applicant_id", "size"), avg_hrs_wk=("hrs_wk", "mean"), ot_hrs=("overtime_hours_period", "sum"),
                                 exp_low=("exp_low", "sum"), exp_high=("exp_high", "sum")).round(0).to_string())

# non-exempt OT pay pattern
ne = pay[(pay.flsa == "Non-Exempt") & pay.base_hourly_rate.notna()].copy()
ne["rr"] = (ne.base_hourly_rate * ne.hours_worked_period + ne.shift_differential_pay_period + ne.nondiscretionary_bonus_period) / ne.hours_worked_period
ne["due"] = 1.5 * ne.rr * ne.overtime_hours_period


def pattern(r):
    if r.overtime_hours_period == 0:
        return "no OT hours"
    p = r.overtime_pay_period
    if abs(p - r.due) <= MONEY_TOL:
        return "correct (1.5x regular rate)"
    if p == 0:
        return "OT unpaid"
    if abs(p - 1.5 * r.base_hourly_rate * r.overtime_hours_period) <= MONEY_TOL:
        return "1.5x base rate (diff/bonus excluded)"
    if abs(p - r.base_hourly_rate * r.overtime_hours_period) <= MONEY_TOL:
        return "straight time (1.0x)"
    return "other mismatch"


ne["ot_pattern"] = ne.apply(pattern, axis=1)
ne["shortfall"] = (ne.due - ne.overtime_pay_period).clip(lower=0).where(ne.overtime_hours_period > 0, 0)
print(f"\nnon-exempt hourly with clean Q2 payroll: n={len(ne)}")
print(pd.crosstab(ne.ot_pattern, ne.site, margins=True))
print(ne.groupby("ot_pattern").shortfall.agg(["size", "sum"]).round(2))
t = ne[(ne.overtime_hours_period > 0) & ((ne.shift_differential_pay_period + ne.nondiscretionary_bonus_period) > 0)]
t = pd.crosstab(t.site.str.startswith("Hub 2"), t.ot_pattern.eq("1.5x base rate (diff/bonus excluded)"))
print("regular-rate exclusion, Hub 2 vs other hubs (employees with OT and diff/bonus):\n", t, "\nFisher p=%.3g" % stats.fisher_exact(t.values)[1])

# off-the-clock
allp = pay[pay.badge_hours_period.notna()].copy()
allp["gap_wk"] = (allp.badge_hours_period - allp.hours_worked_period) / allp.weeks_in_period
print("\nbadge-minus-paid hours per week, all employees with payroll: ",
      allp.gap_wk.describe().round(2).to_dict())
allp["otc"] = allp.gap_wk > OTC_FLAG_HRS_PER_WEEK
print(pd.crosstab([allp.site, allp.job_title], allp.otc).to_string())
otc = allp[allp.otc].copy()
otc["unpaid_hrs"] = (otc.gap_wk - MEAL_HRS_PER_WEEK) * otc.weeks_in_period
otc["rr"] = np.where(otc.base_hourly_rate.notna(),
                     (otc.base_hourly_rate * otc.hours_worked_period + otc.shift_differential_pay_period.fillna(0)
                      + otc.nondiscretionary_bonus_period.fillna(0)) / otc.hours_worked_period,
                     otc.annual_salary / 2080)
otc["exp_low"] = otc.unpaid_hrs * otc.rr
otc["exp_high"] = otc.unpaid_hrs * otc.rr * 1.5
print(f"\nflagged off-the-clock: n={len(otc)}; paid hrs/wk among flagged: {otc.hrs_wk.describe().round(2).to_dict()}; "
      f"OT hours paid among flagged: {otc.overtime_hours_period.sum()}")
print("flagged gap/wk:", otc.gap_wk.describe().round(2).to_dict())
print("non-flagged gap/wk:", allp[~allp.otc].gap_wk.describe().round(2).to_dict())
print(f"est. unpaid hours {otc.unpaid_hrs.sum():.0f}; exposure ${otc.exp_low.sum():,.0f} (straight) to ${otc.exp_high.sum():,.0f} (all at 1.5x)")
tt = pd.crosstab(allp.site.str.startswith("Hub 3"), allp.otc)
print("Hub 3 vs others Fisher p=%.3g" % stats.fisher_exact(tt.values)[1])

ne[ne.ot_pattern.isin(["OT unpaid", "1.5x base rate (diff/bonus excluded)", "straight time (1.0x)", "other mismatch"])][
    ["applicant_id", "site", "job_title", "base_hourly_rate", "overtime_hours_period", "shift_differential_pay_period",
     "nondiscretionary_bonus_period", "overtime_pay_period", "due", "shortfall", "ot_pattern"]].round(2).to_csv(OUT / "flsa_ot_pay_flags.csv", index=False)
mis[["applicant_id", "job_title", "site", "annual_salary", "base_hourly_rate", "hrs_wk", "overtime_hours_period", "flag", "exp_low", "exp_high"]] \
    .round(2).to_csv(OUT / "flsa_classification_flags_with_payroll.csv", index=False)
cls.to_csv(OUT / "flsa_classification_flags_all.csv", index=False)
otc[["applicant_id", "site", "job_title", "weeks_in_period", "hours_worked_period", "badge_hours_period", "gap_wk", "unpaid_hrs", "exp_low", "exp_high"]] \
    .round(2).to_csv(OUT / "flsa_off_the_clock_flags.csv", index=False)

# ---------------------------------------------------------------- 3. ADA / FMLA sequences
section("3. ACCOMMODATION / LEAVE -> DISCIPLINE SEQUENCES")
emp["start"] = emp.hire_date
emp["end"] = emp.termination_date.fillna(SNAPSHOT).clip(upper=SNAPSHOT)
ev2 = ev[ev.event_date >= ev.hire_date].merge(
    emp[["applicant_id", "accommodation_request_flag", "accommodation_type", "accommodation_request_date", "accommodation_outcome",
         "interactive_process_documented", "leave_request_flag", "leave_type", "leave_start_date", "leave_end_date", "leave_status",
         "leave_denial_reason"]], on="applicant_id", how="inner")


def window_rate_test(win_start, days, label):
    """Exact conditional test: events inside per-employee windows vs. all other employee-time."""
    in_ev = 0
    in_t = 0.0
    ids = []
    for _, r in emp[win_start.notna()].iterrows():
        s = win_start[r.name]
        e = min(s + pd.Timedelta(days=days), r.end)
        if e <= s:
            continue
        in_t += (e - s).days
        k = ev2[(ev2.applicant_id == r.applicant_id) & (ev2.event_date > s) & (ev2.event_date <= e)]
        in_ev += len(k)
        ids.append(r.applicant_id)
    tot_t = (emp.end - emp.start).dt.days.clip(lower=0).sum()
    tot_ev = len(ev2)
    out_t, out_ev = tot_t - in_t, tot_ev - in_ev
    p = stats.binomtest(in_ev, in_ev + out_ev, in_t / (in_t + out_t), alternative="greater").pvalue
    rate_in, rate_out = in_ev / in_t * 365, out_ev / out_t * 365
    print(f"{label}: windows n={len(ids)}, {in_t:.0f} person-days, {in_ev} events -> {rate_in:.2f}/person-yr; "
          f"rest of workforce {out_ev} events / {out_t:.0f} person-days -> {rate_out:.2f}/person-yr; "
          f"rate ratio {rate_in / rate_out:.1f}; one-sided exact p={p:.2g}")
    return rate_in / rate_out, p


acc = emp[emp.accommodation_request_flag == 1]
print(f"employees with accommodation requests: n={len(acc)}; outcomes {acc.accommodation_outcome.value_counts().to_dict()}")
print(pd.crosstab(acc.accommodation_outcome, acc.interactive_process_documented))
window_rate_test(emp.accommodation_request_date, ACCOM_WINDOW, f"Discipline within {ACCOM_WINDOW}d after accommodation request")
acc_seq = ev2[(ev2.accommodation_request_flag == 1) & (ev2.event_date > ev2.accommodation_request_date)].copy()
acc_seq["days_after_request"] = (acc_seq.event_date - acc_seq.accommodation_request_date).dt.days
ACC_WORDS = r"restriction|\bsit|pregnan|medical|schedule change(?!s)|modified duty|lighter tasks"
acc_seq["narrative_mentions_condition"] = acc_seq.narrative.str.contains(ACC_WORDS, case=False)
print("\nevents after an accommodation request:")
print(acc_seq[["event_id", "applicant_id", "accommodation_type", "accommodation_outcome", "days_after_request", "event_category",
               "action_taken", "narrative_mentions_condition"]].sort_values("days_after_request").to_string())
acc_flags = acc[((acc.accommodation_outcome == "Denied") & (acc.interactive_process_documented == "N"))
                | ((acc.accommodation_outcome == "Pending") & ((SNAPSHOT - acc.accommodation_request_date).dt.days > PENDING_STALE))]
print("\ndenied w/o documented interactive process, or pending >60 days:")
print(acc_flags[["applicant_id", "accommodation_type", "accommodation_request_date", "accommodation_outcome", "interactive_process_documented"]].to_string())
cond_any = ev2[ev2.narrative.str.contains(ACC_WORDS, case=False)]
print(f"\nevents whose narrative references a restriction/medical/pregnancy (any employee): {len(cond_any)}; "
      f"of these, employee has accommodation flag: {int(cond_any.accommodation_request_flag.sum())}")

lv = emp[emp.leave_request_flag == 1]
print(f"\nemployees with leave requests: n={len(lv)}")
print(pd.crosstab(lv.leave_type, lv.leave_status))
fm = emp.leave_type.fillna("").str.startswith("FMLA") & emp.leave_status.eq("Approved")
window_rate_test(emp.leave_end_date.where(fm), LEAVE_WINDOW, f"Discipline within {LEAVE_WINDOW}d after approved FMLA leave ends")

# parse dates written inside narratives and test overlap with leave
MON = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def narrative_dates(text, ref):
    out = []
    for m in re.finditer(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b", text):
        y = int(m.group(3)); y = y + 2000 if y < 100 else y
        try: out.append(pd.Timestamp(dt.date(y, int(m.group(1)), int(m.group(2)))))
        except ValueError: pass
    for m in re.finditer(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2})\b", text):
        c = pd.Timestamp(dt.date(ref.year, MON[m.group(1)], int(m.group(2))))
        out.append(c if c <= ref + pd.Timedelta(days=31) else c - pd.DateOffset(years=1))
    return out


ev2["nd"] = [narrative_dates(t, r) for t, r in zip(ev2.narrative, ev2.event_date)]
FMLA_WORDS = r"caring for parent|newborn|flare-up|doctor's note|surgery|medical"
fmla_seq = ev2[(ev2.leave_request_flag == 1) & ev2.leave_type.fillna("").str.startswith("FMLA")].copy()
fmla_seq["absence_in_leave_window"] = [any(ls <= x <= le for x in nd) if pd.notna(ls) else False
                                       for nd, ls, le in zip(fmla_seq.nd, fmla_seq.leave_start_date, fmla_seq.leave_end_date)]
fmla_seq["days_after_leave_end"] = (fmla_seq.event_date - fmla_seq.leave_end_date).dt.days
fmla_seq = fmla_seq[(fmla_seq.event_date >= fmla_seq.leave_start_date)]
print("\nevents on/after an FMLA leave start (FMLA requesters):")
print(fmla_seq[["event_id", "applicant_id", "leave_type", "leave_status", "days_after_leave_end", "event_category", "action_taken",
                "absence_in_leave_window"]].sort_values("days_after_leave_end").to_string())
kw = ev2[ev2.narrative.str.contains(FMLA_WORDS, case=False) & (ev2.event_category == "Attendance")]
print(f"\nattendance events citing a family/medical reason: {len(kw)}; employee had approved FMLA covering those dates: "
      f"{int(kw.event_id.isin(fmla_seq[fmla_seq.absence_in_leave_window].event_id).sum())}; "
      f"no FMLA request on file: {int((kw.leave_request_flag != 1).sum())}")
print(kw[kw.leave_request_flag != 1][["event_id", "applicant_id", "event_date", "action_taken", "narrative"]].to_string())

lv_d = lv[lv.leave_denial_reason.fillna("").str.contains("12 months")].copy()
lv_d["tenure_days_at_leave"] = (lv_d.leave_start_date - lv_d.hire_date).dt.days
print("\nFMLA denied for '<12 months' but tenure >=365 days at leave start:")
print(lv_d[lv_d.tenure_days_at_leave >= 365][["applicant_id", "leave_type", "hire_date", "leave_start_date", "tenure_days_at_leave"]].to_string())
print("non-FMLA leave denials:", lv[(lv.leave_status == "Denied") & ~lv.leave_type.str.startswith("FMLA")][["applicant_id", "leave_type", "leave_denial_reason"]].values.tolist())

seq_out = pd.concat([
    acc_seq.assign(sequence="accommodation -> discipline")[["sequence", "event_id", "applicant_id", "event_date", "days_after_request", "event_category", "action_taken", "narrative"]],
    fmla_seq.assign(sequence="FMLA leave -> discipline")[["sequence", "event_id", "applicant_id", "event_date", "days_after_leave_end", "event_category", "action_taken", "absence_in_leave_window", "narrative"]],
    kw[kw.leave_request_flag != 1].assign(sequence="medical/family absence, no FMLA on file")[["sequence", "event_id", "applicant_id", "event_date", "event_category", "action_taken", "narrative"]],
])
seq_out.to_csv(OUT / "ada_fmla_sequences.csv", index=False)

# ---------------------------------------------------------------- 4. NLRA
section("4. NLRA SECTION 7 SCREEN OF DISCIPLINE NARRATIVES")
SUBJECT = {
    "wages/pay": r"pay rates|paystub|what they make|compare rates|compare schedules and pay|compensation is confidential|wage|bonus structure|unpaid",
    "hours/OT/schedule": r"overtime|OT schedule|forced overtime|attendance points|schedule changes|staffing",
    "safety/heat": r"dock plate|guard|water breaks|heat|fans|cooling|fall off|cut our breaks|AC\b",
    "union": r"\bunion\b|authorization cards|Fair Pay|picket",
    "agency complaint": r"Dept of Labor|\bDOL\b|OSHA|NLRB",
    "investigation discussion": r"discussed the ongoing investigation",
}
CONCERTED = (r"coworkers|other (associates|operators|drivers|dispatchers|coordinators|leads|techs|reps|staff)|others|group|"
             r"on behalf|whole shift|signatures|signed letter|several of the|who's with me|none of us|we're|petition|stood with|"
             r"\d+ (associates|operators|drivers|dispatchers|coordinators|leads|techs|reps)|stirring up|got others|authorization cards|union")
INDIVIDUAL = r"No other employees involved|No coworker engagement|personal dispute|own schedule|Only EE refused"
AGGRAVATING = r"f\*\*\*|threw|Customer names visible|customer's product labels|yelled insults"
RULES = {
    "pay confidentiality": r"compensation is confidential|pay information is confidential|Wage confidentiality",
    "social media / disparagement": r"social media policy|Disparaging the company|negative comments about the company",
    "no-solicitation / union talk ban": r"no-solicitation|union discussions are not allowed",
    "insignia / dress code": r"company-issued insignia|Told to change",
    "no-recording": r"no-recording",
    "investigation confidentiality": r"Blanket confidentiality",
    "chain of command / attitude": r"chain of command|Negative attitude|Attitude issue|not consistent with our values|undermining of mgmt|unofficial work communications",
}


def nlra(text):
    subj = [k for k, p in SUBJECT.items() if re.search(p, text, re.I)]
    conc = bool(re.search(CONCERTED, text, re.I))
    indiv = bool(re.search(INDIVIDUAL, text, re.I))
    aggr = bool(re.search(AGGRAVATING, text, re.I))
    rules = [k for k, p in RULES.items() if re.search(p, text, re.I)]
    gripe_sm = bool(re.search(r"idiot|hate this place", text, re.I))
    if indiv or gripe_sm:
        risk = "Low" if (subj or gripe_sm or "refuse" in text) else "None"
        if re.search(r"Only EE refused", text) and subj:
            risk = "Medium"
    elif subj and (conc or "union" in subj or "wages/pay" in subj or "investigation discussion" in subj):
        risk = "Medium" if aggr else "High"
    elif subj:
        risk = "Medium"
    elif aggr and conc:
        risk = "Medium"
    else:
        risk = "None"
    return pd.Series(dict(s7_subjects=", ".join(subj), concerted_indicator=conc, individual_indicator=indiv,
                          aggravating_conduct=aggr, rule_invoked=", ".join(rules), nlra_risk=risk))


nl = pd.concat([ev, ev.narrative.apply(nlra)], axis=1)
nl["likely_statutory_supervisor"] = nl.job_title.isin(["Warehouse Supervisor", "Operations Manager"]) & (nl.direct_reports >= 2)
nl["nlra_risk_adj"] = np.where(nl.likely_statutory_supervisor & nl.nlra_risk.isin(["High", "Medium"]), "Low (supervisor, s.2(11))", nl.nlra_risk)
nl["other_statute"] = np.select(
    [nl.narrative.str.contains(r"caring for parent|newborn|flare-up|doctor's note", case=False),
     nl.narrative.str.contains(ACC_WORDS, case=False)],
    ["FMLA (protected absence counted?)", "ADA/PWFA (accommodation-related)"], "")
print("events:", len(nl))
print(nl.nlra_risk_adj.value_counts().to_string())
print(pd.crosstab(nl.nlra_risk_adj, nl.action_taken))
print(pd.crosstab(nl.event_category, nl.nlra_risk_adj))
print("\nrules invoked in High/Medium events:", nl[nl.nlra_risk.isin(["High", "Medium"])].rule_invoked.str.split(", ").explode().value_counts().to_dict())
print("subjects in High/Medium events:", nl[nl.nlra_risk.isin(["High", "Medium"])].s7_subjects.str.split(", ").explode().value_counts().to_dict())
print("\nMedium / Low / supervisor events (all printed for manual review):")
print(nl[nl.nlra_risk_adj.isin(["Medium", "Low"]) | nl.likely_statutory_supervisor & nl.nlra_risk.ne("None")][
    ["event_id", "job_group", "action_taken", "nlra_risk_adj", "narrative"]].to_string())
print("\nNone-rated events mentioning coworkers/group (manual check):")
print(nl[(nl.nlra_risk == "None") & nl.concerted_indicator][["event_id", "event_category", "narrative"]].to_string())

# severity / progressive discipline
nl = nl.sort_values(["applicant_id", "event_date"])
nl["prior_events"] = nl.groupby("applicant_id").cumcount()
first = nl[nl.prior_events == 0]
first = first.assign(hi=first.nlra_risk_adj.eq("High"), beyond_verbal=first.action_taken.ne("Verbal Warning"))
t = pd.crosstab(first.hi, first.beyond_verbal)
print("\nFIRST-offense events: share above Verbal Warning, High-risk vs other:", (t[True] / t.sum(axis=1)).round(3).to_dict(),
      "n:", t.sum(axis=1).to_dict(), "Fisher p=%.3g" % stats.fisher_exact(t.values)[1])
print("High-risk events by action:", nl[nl.nlra_risk_adj == "High"].action_taken.value_counts().to_dict())

# pca_flag cross-check
em = emp.copy()
hi_ids = set(nl[nl.nlra_risk_adj.isin(["High", "Medium"])].applicant_id)
em["s7_narrative"] = em.applicant_id.isin(hi_ids)
print("\npca_flag vs having a High/Medium Section 7 narrative:\n", pd.crosstab(em.pca_flag, em.s7_narrative, margins=True))
print("unflagged employees with High/Medium narrative:", sorted(em[em.s7_narrative & (em.pca_flag == 0)].applicant_id))
em["invol"] = em.employment_status.eq("Terminated - Involuntary")
em["disc"] = em.ev_count_actual > 0
for c in ["disc", "invol"]:
    t = pd.crosstab(em.pca_flag, em[c])
    print(f"{c} rate by pca_flag:", (t[True] / t.sum(axis=1)).round(3).to_dict(), "n:", t.sum(axis=1).to_dict(),
          "Fisher p=%.3g" % stats.fisher_exact(t.values)[1])
nl[["event_id", "applicant_id", "event_date", "site", "job_group", "event_category", "action_taken", "pca_flag", "s7_subjects",
    "concerted_indicator", "aggravating_conduct", "rule_invoked", "likely_statutory_supervisor", "nlra_risk_adj", "other_statute", "narrative"]] \
    .to_csv(OUT / "nlra_narrative_screen.csv", index=False)
print("\noutputs written to", OUT)
