"""Step 2: internal audit analysis for Cardinal Logistics (synthetic data).

Reads only cardinal_people.csv and cardinal_discipline_events.csv. The answer keys are
not used, so the findings stand on the data alone.

Writes to results/:
  adverse_impact.csv            selection rates, impact ratios, exact tests, sample-size checks
  aedt_score_gaps.csv           standardized score gaps (AEDT vs skills test) by group
  flsa_flags.csv                per-employee classification and overtime-pay flags
  premium_ot_algorithm.csv      premium-overtime offers by group
  leave_accommodation_flags.csv per-employee leave/accommodation → discipline sequences
  sequence_rates.csv            discipline after a request vs a comparison window
  section7_flags.csv            per-event NLRA Section 7 risk tier with reasons
  step2_findings.md             readable summary
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(7)

AS_OF = pd.Timestamp("2026-09-30")
REVIEW_START = pd.Timestamp("2025-04-01")
SALARY_FLOOR = 35568            # $684/week, federal white-collar salary level
MIN_N = 30                      # below this, a selection rate is too unstable to compare
MIN_EXPECTED_HIRES = 5          # below this, a ratio is noise
ALPHA = 0.05

P = pd.read_csv(HERE / "cardinal_people.csv", parse_dates=[
    "application_date", "hire_date", "termination_date", "accommodation_request_date",
    "leave_start_date", "leave_end_date", "concerted_activity_date", "last_discipline_date"])
EV = pd.read_csv(HERE / "cardinal_discipline_events.csv", parse_dates=["event_date"])
EMP = P[P["record_type"].eq("Employee")].copy()
EMP["window_start"] = EMP["hire_date"].where(EMP["hire_date"] > REVIEW_START, REVIEW_START)
EMP["window_end"] = EMP["termination_date"].fillna(AS_OF)


# ------------------------------------------------------------------ statistics helpers
def _log_comb(n, k):
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def fisher_two_sided(a, b, c, d):
    """Fisher's exact test on [[a, b], [c, d]], two-sided (sum of tables no more likely than observed)."""
    r1, r2, c1 = a + b, c + d, a + c
    n = r1 + r2
    lo, hi = max(0, c1 - r2), min(r1, c1)
    logp = lambda x: _log_comb(r1, x) + _log_comb(r2, c1 - x) - _log_comb(n, c1)
    p_obs = logp(a)
    total = sum(math.exp(logp(x)) for x in range(lo, hi + 1) if logp(x) <= p_obs + 1e-9)
    return min(1.0, total)


def perm_test_mean(x, y, n_perm=5000):
    """Two-sided permutation test for a difference in means."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    obs = abs(x.mean() - y.mean())
    pooled = np.concatenate([x, y])
    hits = 0
    for _ in range(n_perm):
        rng.shuffle(pooled)
        hits += abs(pooled[: len(x)].mean() - pooled[len(x):].mean()) >= obs - 1e-12
    return (hits + 1) / (n_perm + 1)


# ------------------------------------------------------------------ A. four-fifths rule
def selection_table(df, col, label, population, exclude_from_reference=("Declined to self-identify",)):
    g = df.groupby(col)["hired"].agg(applicants="size", hires="sum").reset_index().rename(columns={col: "group"})
    g["group"] = g["group"].astype(str)
    pool_rate = df["hired"].mean()
    g["selection_rate"] = g["hires"] / g["applicants"]
    g["expected_hires_at_pool_rate"] = g["applicants"] * pool_rate
    g["adequate_sample"] = (g["applicants"] >= MIN_N) & (g["expected_hires_at_pool_rate"] >= MIN_EXPECTED_HIRES)
    eligible = g[g["adequate_sample"] & ~g["group"].isin(exclude_from_reference)]
    ref = eligible.loc[eligible["selection_rate"].idxmax()]
    g["reference_group"] = ref["group"]
    g["impact_ratio"] = g["selection_rate"] / ref["selection_rate"]
    pvals, shortfall = [], []
    for _, r in g.iterrows():
        if r["group"] == ref["group"]:
            pvals.append(np.nan); shortfall.append(0.0); continue
        pvals.append(fisher_two_sided(int(r["hires"]), int(r["applicants"] - r["hires"]),
                                      int(ref["hires"]), int(ref["applicants"] - ref["hires"])))
        shortfall.append(r["applicants"] * ref["selection_rate"] - r["hires"])
    g["fisher_p_vs_reference"] = pvals
    g["hire_shortfall_vs_reference"] = np.round(shortfall, 1)

    def verdict(r):
        if r["group"] == ref["group"]:
            return "Reference group"
        if r["group"] in exclude_from_reference:
            return "Not interpretable (no group identity)"
        if not r["adequate_sample"]:
            if r["fisher_p_vs_reference"] < ALPHA:
                return "Small sample, but exact test is significant: treat as a finding, ratio is unstable"
            return "Insufficient sample: report count only, do not interpret ratio"
        fails, sig = r["impact_ratio"] < 0.8, r["fisher_p_vs_reference"] < ALPHA
        if fails and sig:
            return "Fails 4/5 and statistically significant"
        if fails:
            return "Fails 4/5, not statistically significant: monitor, aggregate more data"
        if sig:
            return "Passes 4/5 but statistically significant: still a disparity"
        return "Passes 4/5, no significant difference (not proof of compliance)"
    g["assessment"] = g.apply(verdict, axis=1)
    g.insert(0, "dimension", label)
    g.insert(0, "population", population)
    return g


aedt = P[P["record_source"].eq("AEDT-era applicant") & P["selection_procedure"].eq("AEDT video interview")].copy()
structured = P[P["record_source"].eq("AEDT-era applicant") & P["selection_procedure"].eq("Structured interview")].copy()
for df in (aedt, structured):
    df["hired"] = df["hire_decision"].eq("Hired")
    df["age_group"] = np.where(df["age_band"].isin(["40-49", "50-59", "60+"]), "40 and over", "Under 40")
    df["accommodation"] = np.where(df["interview_accommodation_requested"].astype(str).eq("True"), "Requested accommodation", "No request")
    df["language"] = np.where(df["non_native_english_speaker"].astype(bool), "Non-native English", "Native English")

DIMS = [("race_ethnicity_self_id", "Race/ethnicity"), ("sex_self_id", "Sex"), ("age_group", "Age (ADEA 40+)"),
        ("age_band", "Age band"), ("accommodation", "Disability proxy: interview accommodation"),
        ("language", "National-origin proxy: English fluency"), ("interview_connection_quality", "Connection quality (non-protected)")]
def age_band_table(df, population):
    """Each 40+ band against the pooled under-40 rate. Under-40 bands are not ADEA-protected, so they are not tested."""
    young = df[~df["age_band"].isin(["40-49", "50-59", "60+"])]
    ref_rate, rows = young["hired"].mean(), []
    rows.append({"population": population, "dimension": "Age band vs under 40", "group": "Under 40 (pooled)", "applicants": len(young),
                 "hires": int(young["hired"].sum()), "selection_rate": ref_rate, "expected_hires_at_pool_rate": np.nan, "adequate_sample": True,
                 "reference_group": "Under 40 (pooled)", "impact_ratio": 1.0, "fisher_p_vs_reference": np.nan, "hire_shortfall_vs_reference": 0.0,
                 "assessment": "Reference group"})
    for band in ["40-49", "50-59", "60+"]:
        g = df[df["age_band"].eq(band)]
        n, h = len(g), int(g["hired"].sum())
        p = fisher_two_sided(h, n - h, int(young["hired"].sum()), len(young) - int(young["hired"].sum()))
        ratio, adequate = (h / n) / ref_rate, n >= MIN_N and n * df["hired"].mean() >= MIN_EXPECTED_HIRES
        if not adequate:
            a = "Small sample, but exact test is significant: treat as a finding, ratio is unstable" if p < ALPHA else "Insufficient sample: report count only, do not interpret ratio"
        elif ratio < 0.8:
            a = "Fails 4/5 and statistically significant" if p < ALPHA else "Fails 4/5, not statistically significant: monitor, aggregate more data"
        else:
            a = "Passes 4/5 but statistically significant: still a disparity" if p < ALPHA else "Passes 4/5, no significant difference (not proof of compliance)"
        rows.append({"population": population, "dimension": "Age band vs under 40", "group": band, "applicants": n, "hires": h,
                     "selection_rate": h / n, "expected_hires_at_pool_rate": n * df["hired"].mean(), "adequate_sample": adequate,
                     "reference_group": "Under 40 (pooled)", "impact_ratio": ratio, "fisher_p_vs_reference": p,
                     "hire_shortfall_vs_reference": round(n * ref_rate - h, 1), "assessment": a})
    return pd.DataFrame(rows)


DIMS = [d for d in DIMS if d[0] != "age_band"]
ai_tables = [selection_table(aedt, c, l, "AEDT applicants (all AEDT job groups)") for c, l in DIMS]
ai_tables.insert(3, age_band_table(aedt, "AEDT applicants (all AEDT job groups)"))
ai_tables += [selection_table(structured, c, l, "Structured-interview applicants (comparison)") for c, l in DIMS[:3]]
ai_tables.append(age_band_table(structured, "Structured-interview applicants (comparison)"))
# Within the largest job group, to check the pooled result isn't an artifact of job-group mix.
jg1 = aedt[aedt["job_group"].eq("JG1 Material Handlers")]
ai_tables += [selection_table(jg1, c, l, "AEDT applicants, JG1 Material Handlers only") for c, l in DIMS[:5]]
ai_tables.append(age_band_table(jg1, "AEDT applicants, JG1 Material Handlers only"))
AI = pd.concat(ai_tables, ignore_index=True)
AI.round(4).to_csv(OUT / "adverse_impact.csv", index=False)

# Where does the gap enter? Standardized gaps on the AEDT score vs the skills test, same applicants.
gap_rows = []
for col, label in DIMS[:5] + [("age_band", "Age band")]:
    groups = aedt.groupby(col)
    sd_a, sd_s = aedt["aedt_score"].std(), aedt["skills_assessment_score"].std()
    sizes = groups.size()
    ref = aedt.groupby(col)["aedt_score"].mean()[sizes >= MIN_N].idxmax()
    for gname, gdf in groups:
        if gname == ref:
            continue
        rdf = aedt[aedt[col] == ref]
        gap_rows.append({"dimension": label, "group": gname, "reference": ref, "n": len(gdf),
                         "aedt_gap_sd": round((gdf["aedt_score"].mean() - rdf["aedt_score"].mean()) / sd_a, 2),
                         "skills_test_gap_sd": round((gdf["skills_assessment_score"].mean() - rdf["skills_assessment_score"].mean()) / sd_s, 2),
                         "communication_gap_sd": round((gdf["aedt_communication"].mean() - rdf["aedt_communication"].mean()) / aedt["aedt_communication"].std(), 2),
                         "engagement_gap_sd": round((gdf["aedt_engagement"].mean() - rdf["aedt_engagement"].mean()) / aedt["aedt_engagement"].std(), 2),
                         "problem_solving_gap_sd": round((gdf["aedt_problem_solving"].mean() - rdf["aedt_problem_solving"].mean()) / aedt["aedt_problem_solving"].std(), 2),
                         "adequate_sample": len(gdf) >= MIN_N})
GAPS = pd.DataFrame(gap_rows)
GAPS = GAPS[~(GAPS["dimension"].eq("Age band") & GAPS["group"].isin(["18-24", "25-29", "30-39"]))]   # ADEA: 40+ only
GAPS.to_csv(OUT / "aedt_score_gaps.csv", index=False)

# ------------------------------------------------------------------ B. FLSA classification and overtime
F = EMP.copy()
F["is_exempt"] = F["flsa_classification"].str.startswith("Exempt")
F["weekly_ot_hours_est"] = np.maximum(F["weekly_hours_avg_13wk"] - 40, 0)
flags = []
for i, r in F.iterrows():
    out = []
    if r["is_exempt"] and r["annual_salary"] < SALARY_FLOOR:
        reg = r["annual_salary"] / 52 / max(r["weekly_hours_avg_13wk"], 40)
        out.append(("Exempt but salary below $35,568 floor: fails salary-level test", "Misclassification (data-confirmed)",
                    round(0.5 * reg * r["weekly_ot_hours_est"] * 13, 2), round(1.5 * (r["annual_salary"] / 2080) * r["weekly_ot_hours_est"] * 13, 2)))
    elif r["flsa_classification"] == "Exempt - Administrative":
        out.append(("Administrative exemption on a dispatcher role: duties test cannot be confirmed from payroll data",
                    "Classification needs duties review", round(0.5 * (r["annual_salary"] / 52 / max(r["weekly_hours_avg_13wk"], 40)) * r["weekly_ot_hours_est"] * 13, 2),
                    round(1.5 * (r["annual_salary"] / 2080) * r["weekly_ot_hours_est"] * 13, 2)))
    if r["flsa_classification"] == "Non-exempt" and r["pay_type"] == "Hourly" and r["overtime_hours_13wk"] > 0:
        regular = r["base_hourly_rate"] + r["shift_differential_per_hr"]
        expected = 1.5 * regular * r["overtime_hours_13wk"]
        short = expected - r["overtime_pay_13wk"]
        if short > 0.5:
            out.append(("Overtime paid below 1.5x regular rate (shift differential left out of regular rate)",
                        "Overtime underpayment (data-confirmed)", round(short, 2), round(short, 2)))
    for desc, kind, lo, hi in out:
        flags.append({"employee_id": r["employee_id"], "role": r["role"], "site": r["site"], "shift": r["shift"],
                      "flsa_classification": r["flsa_classification"], "annual_salary": r["annual_salary"],
                      "base_hourly_rate": r["base_hourly_rate"], "shift_differential_per_hr": r["shift_differential_per_hr"],
                      "weekly_hours_avg_13wk": r["weekly_hours_avg_13wk"], "overtime_hours_13wk": r["overtime_hours_13wk"],
                      "overtime_pay_13wk": r["overtime_pay_13wk"], "flag_type": kind, "finding": desc,
                      "exposure_13wk_low_usd": lo, "exposure_13wk_high_usd": hi})
FLSA = pd.DataFrame(flags)
FLSA.to_csv(OUT / "flsa_flags.csv", index=False)
mca = F[F["flsa_classification"].str.contains("Motor Carrier", na=False)]

# Premium-overtime algorithm: offers among the employees it schedules, active at the as-of date.
S = F[F["pay_type"].eq("Hourly") & F["role"].isin(["Warehouse Associate", "Picker/Packer", "Forklift Operator", "Inventory Control Clerk", "Maintenance Technician"])
      & F["employment_status"].eq("Active")].copy()
S["recent_leave"] = S["leave_request_flag"].astype(str).eq("True") & (S["leave_start_date"] > AS_OF - pd.Timedelta(days=182))
S["accommodation"] = S["accommodation_request_flag"].astype(str).eq("True")
S["age_40_plus"] = S["age_band"].isin(["40-49", "50-59", "60+"])
ot_rows = []
for label, mask in [("Leave started in last 26 weeks", S["recent_leave"]), ("Accommodation request on file", S["accommodation"]),
                    ("Age 40+", S["age_40_plus"]), ("Female", S["sex_self_id"].eq("Female")),
                    ("Black or African American", S["race_ethnicity_self_id"].eq("Black or African American")),
                    ("Hispanic or Latino", S["race_ethnicity_self_id"].eq("Hispanic or Latino"))]:
    a, b = S.loc[mask, "premium_ot_offers_13wk"].astype(float), S.loc[~mask, "premium_ot_offers_13wk"].astype(float)
    ot_rows.append({"group": label, "n_group": len(a), "n_others": len(b), "mean_offers_group": round(a.mean(), 2),
                    "mean_offers_others": round(b.mean(), 2), "offer_ratio": round(a.mean() / b.mean(), 2) if b.mean() else np.nan,
                    "mean_reliability_group": round(S.loc[mask, "scheduler_reliability_score"].astype(float).mean(), 1),
                    "mean_reliability_others": round(S.loc[~mask, "scheduler_reliability_score"].astype(float).mean(), 1),
                    "permutation_p": round(perm_test_mean(a, b), 4) if len(a) >= 5 else np.nan, "adequate_sample": len(a) >= MIN_N})
OTALG = pd.DataFrame(ot_rows)
OTALG.to_csv(OUT / "premium_ot_algorithm.csv", index=False)

# ------------------------------------------------------------------ C. leave / accommodation → discipline
DATE_RANGE = re.compile(r"(\w{3} \d{1,2}, \d{4}) through (\w{3} \d{1,2}, \d{4})")
RESTRICTION = re.compile(r"while working under|due to (?:lifting restriction|modified schedule|seated work station|intermittent breaks|hearing)", re.I)
ev_by_emp = {k: v for k, v in EV.groupby("employee_id")}

seq_rows = []
for _, r in EMP.iterrows():
    evs = ev_by_emp.get(r["employee_id"], EV.iloc[0:0])
    if str(r["leave_request_flag"]) == "True":
        lo, hi = r["leave_start_date"], r["leave_end_date"] + pd.Timedelta(days=90)
        after = evs[(evs["event_date"] >= lo) & (evs["event_date"] <= hi)]
        overlap = []
        for _, e in evs[evs["category"].eq("Attendance")].iterrows():
            m = DATE_RANGE.search(e["narrative"])
            if m:
                a0, a1 = pd.to_datetime(m.group(1)), pd.to_datetime(m.group(2))
                if a0 <= r["leave_end_date"] and a1 >= r["leave_start_date"]:
                    overlap.append(e["event_id"])
        fmla = str(r["fmla_eligible_at_request"]) == "True"
        if overlap:
            kind = ("FMLA interference: attendance points assessed for FMLA-protected absences" if fmla else
                    "Points assessed during non-FMLA medical leave: review as possible ADA leave-as-accommodation or state-law issue")
        elif len(after):
            kind = "Discipline within 90 days of leave: timing warrants review, not itself a violation"
        else:
            kind = ""
        if kind:
            seq_rows.append({"employee_id": r["employee_id"], "request": "Leave", "request_type": r["leave_type"],
                             "request_date": r["leave_start_date"].date(), "fmla_eligible": fmla,
                             "events_in_window": ";".join(after["event_id"]), "events_overlapping_leave": ";".join(overlap),
                             "days_to_first_event": (after["event_date"].min() - lo).days if len(after) else np.nan,
                             "flag": kind, "level_of_most_serious": after["level"].iloc[-1] if len(after) else ""})
    if str(r["accommodation_request_flag"]) == "True":
        lo, hi = r["accommodation_request_date"], r["accommodation_request_date"] + pd.Timedelta(days=120)
        after = evs[(evs["event_date"] >= lo) & (evs["event_date"] <= hi)]
        restr = after[after["narrative"].str.contains(RESTRICTION)]
        if len(restr):
            kind = "Performance discipline that cites the accommodation itself: standard not adjusted (ADA failure to accommodate / retaliation risk)"
        elif len(after):
            kind = "Discipline within 120 days of accommodation request: timing warrants review"
        else:
            kind = ""
        if kind:
            seq_rows.append({"employee_id": r["employee_id"], "request": "Accommodation", "request_type": r["accommodation_type"],
                             "request_date": r["accommodation_request_date"].date(), "fmla_eligible": np.nan,
                             "events_in_window": ";".join(after["event_id"]), "events_overlapping_leave": "",
                             "days_to_first_event": (after["event_date"].min() - lo).days, "flag": kind,
                             "level_of_most_serious": after["level"].iloc[-1]})
SEQ = pd.DataFrame(seq_rows)
SEQ.to_csv(OUT / "leave_accommodation_flags.csv", index=False)


# Comparison: share disciplined in a same-length window after the request vs after a random date for non-requesters.
def window_rate(flag_col, date_col, days, end_col=None):
    """Requesters: request date through (end date or request date) + days. Comparison: non-requesters over a window
    of the same median length, starting on a random date inside their own review window."""
    req, base = [], []
    reqs = EMP[EMP[flag_col].astype(str).eq("True")]
    span_days = int(((reqs[end_col] if end_col else reqs[date_col]) - reqs[date_col]).dt.days.median()) + days
    for _, r in EMP.iterrows():
        if r["window_end"] <= r["window_start"] + pd.Timedelta(days=30):
            continue
        evs = ev_by_emp.get(r["employee_id"], EV.iloc[0:0])
        if str(r[flag_col]) == "True":
            lo = r[date_col]
            hi = (r[end_col] if end_col else lo) + pd.Timedelta(days=days)
            req.append(((evs["event_date"] >= lo) & (evs["event_date"] <= hi)).any())
        else:
            span = (r["window_end"] - r["window_start"]).days
            lo = r["window_start"] + pd.Timedelta(days=int(rng.integers(0, max(span - 30, 1))))
            hi = lo + pd.Timedelta(days=span_days)
            base.append(((evs["event_date"] >= lo) & (evs["event_date"] <= hi)).any())
    a, c = sum(req), sum(base)
    return {"window_days_comparison": span_days, "n_requesters": len(req), "requesters_disciplined": a, "rate_requesters": a / len(req),
            "n_comparison": len(base), "comparison_disciplined": c, "rate_comparison": c / len(base),
            "rate_ratio": (a / len(req)) / (c / len(base)), "fisher_p": fisher_two_sided(a, len(req) - a, c, len(base) - c)}

SR = pd.DataFrame([
    {"request": "Leave (start through end + 90 days)", **window_rate("leave_request_flag", "leave_start_date", 90, "leave_end_date")},
    {"request": "Accommodation (120 days after request)", **window_rate("accommodation_request_flag", "accommodation_request_date", 120)},
    {"request": "Concerted activity (60 days after)", **window_rate("protected_concerted_activity_flag", "concerted_activity_date", 60)},
])
SR.round(4).to_csv(OUT / "sequence_rates.csv", index=False)

# ------------------------------------------------------------------ D. NLRA Section 7 risk in narratives
CONCERTED = re.compile(r"coworkers|associates|petition|as a group|other drivers|meeting of|four coworkers|the crew", re.I)
TERMS = re.compile(r"\bpay\b|pay rates|wages?|overtime|trailer heat|dock fan|discuss the attendance policy|algorithm", re.I)
EMPLOYER_FRAMING = re.compile(r"confidentiality policy|disloyalty|reputation|negative attitude|stirring things up|unauthorized meeting|soliciting|insubordination|disrupting", re.I)
LOSES_PROTECTION = re.compile(r"take care of|medical paperwork|profanity", re.I)
INDIVIDUAL = re.compile(r"his own|her own|their own", re.I)
SUPERVISORY = {"Shift Supervisor", "Operations Manager"}
role_of = EMP.set_index("employee_id")["role"]
pca = EMP.set_index("employee_id")[["protected_concerted_activity_flag", "concerted_activity_date", "concerted_activity_description"]]

s7 = []
for _, e in EV.iterrows():
    t = e["narrative"]
    c, s, f, lp, ind = (bool(rx.search(t)) for rx in (CONCERTED, TERMS, EMPLOYER_FRAMING, LOSES_PROTECTION, INDIVIDUAL))
    if not (c or s or f or lp or ind):
        continue
    role = role_of.get(e["employee_id"], "")
    reasons = []
    if c: reasons.append("group activity")
    if s: reasons.append("subject is pay/hours/safety/working conditions")
    if f: reasons.append("discipline framed around the activity itself")
    if lp: reasons.append("conduct that can lose protection (threat, privacy breach, abuse)")
    if ind: reasons.append("individual complaint about own situation")
    if role in SUPERVISORY and not (c or s or f):
        continue
    if role in SUPERVISORY:
        tier = "Excluded if a statutory supervisor: verify actual authority (title alone does not decide)"
    elif lp:
        tier = "Low: conduct likely unprotected"
    elif c and s:
        tier = "High: likely protected concerted activity"
    elif s and f:
        tier = "Medium: protected subject, concertedness unclear"
    elif ind and not c:
        tier = "Low: individual gripe (protected only if it seeks group action)"
    else:
        tier = "Medium: review"
    pc = pca.loc[e["employee_id"]] if e["employee_id"] in pca.index else None
    days_after = (e["event_date"] - pc["concerted_activity_date"]).days if pc is not None and pd.notna(pc["concerted_activity_date"]) else np.nan
    s7.append({"event_id": e["event_id"], "employee_id": e["employee_id"], "role": role, "event_date": e["event_date"].date(),
               "level": e["level"], "risk_tier": tier, "reasons": "; ".join(reasons),
               "pca_flag_on_file": bool(pc is not None and str(pc["protected_concerted_activity_flag"]) == "True"),
               "days_after_concerted_activity": days_after, "narrative": t})
S7 = pd.DataFrame(s7).sort_values("risk_tier")
S7.to_csv(OUT / "section7_flags.csv", index=False)
policy_hits = EV["narrative"].str.contains("confidentiality policy", case=False).sum()

# ------------------------------------------------------------------ summary
def pct(x):
    return f"{x:.1%}"

L = ["# Step 2 findings: Cardinal Logistics internal audit (synthetic data)", "",
     f"Data as of {AS_OF.date()}. Sources: `cardinal_people.csv` ({len(P)} rows) and `cardinal_discipline_events.csv` ({len(EV)} events). Answer keys not used.", "",
     "## Method choices to review", "",
     f"- **Four-fifths population.** AEDT applicants only ({len(aedt)}), from the AEDT go-live onward. Pre-AEDT incumbents have no AEDT decision and are left out. Structured-interview applicants ({len(structured)}) are a comparison group.",
     "- **Reference group.** The group with the highest selection rate among groups with enough data. \"Declined to self-identify\" is never the reference.",
     f"- **Sample-size rule.** A group needs at least {MIN_N} applicants and at least {MIN_EXPECTED_HIRES} expected hires before its ratio is interpreted. Smaller groups are reported as counts only.",
     "- **Significance.** Fisher's exact test of each group against the reference, two-sided, alpha 0.05. Every group is tested, including ones that pass four-fifths.",
     "- **Leave and accommodation sequences.** Requesters are compared with non-requesters observed over a similar-length window starting on a random date. Timing alone is a lead for review, not a finding of retaliation.",
     "- **Section 7.** Transparent rules on the narrative text, then a tier. Every High and Medium item needs a person to read the full file.", ""]

L += ["## A. Selection rates (four-fifths rule)", ""]
for pop in AI["population"].unique():
    L += [f"### {pop}", "", "| Dimension | Group | Applicants | Hires | Rate | Impact ratio | Fisher p | Shortfall | Assessment |", "|---|---|---|---|---|---|---|---|---|"]
    for _, r in AI[AI["population"] == pop].iterrows():
        p = "" if pd.isna(r["fisher_p_vs_reference"]) else f"{r['fisher_p_vs_reference']:.3f}"
        L.append(f"| {r['dimension']} | {r['group']} | {r['applicants']} | {r['hires']} | {pct(r['selection_rate'])} | {r['impact_ratio']:.2f} | {p} | {r['hire_shortfall_vs_reference']:.1f} | {r['assessment']} |")
    L.append("")
L += ["### Where the gap enters: AEDT score vs skills test (standard deviations from the reference group)", "",
      "| Dimension | Group | n | AEDT score | Skills test | Communication | Engagement | Problem solving |", "|---|---|---|---|---|---|---|---|"]
for _, r in GAPS[GAPS["adequate_sample"]].iterrows():
    L.append(f"| {r['dimension']} | {r['group']} | {r['n']} | {r['aedt_gap_sd']:+.2f} | {r['skills_test_gap_sd']:+.2f} | {r['communication_gap_sd']:+.2f} | {r['engagement_gap_sd']:+.2f} | {r['problem_solving_gap_sd']:+.2f} |")
L.append("")
hidden = GAPS[GAPS["adequate_sample"] & (GAPS["skills_test_gap_sd"] > -0.10)
              & (GAPS[["communication_gap_sd", "engagement_gap_sd", "problem_solving_gap_sd"]].min(axis=1) <= -0.20)]
if len(hidden):
    L += ["**Subscore gaps with no matching skills-test gap** (a good overall selection rate does not excuse a biased component; *Connecticut v. Teal*):", ""]
    for _, r in hidden.iterrows():
        worst = min(("communication", r["communication_gap_sd"]), ("engagement", r["engagement_gap_sd"]), ("problem solving", r["problem_solving_gap_sd"]), key=lambda x: x[1])
        L.append(f"- {r['dimension']}: {r['group']} (n={r['n']}): {worst[0]} {worst[1]:+.2f} SD vs skills test {r['skills_test_gap_sd']:+.2f} SD.")
    L.append("")
L += ["**Age note:** the ADEA protects workers 40 and over only, so younger bands are not tested against older ones. The four-fifths rule comes from the Uniform Guidelines, which do not govern ADEA claims; for age it is a screening signal, and the defense is a reasonable factor other than age.", ""]

L += ["## B. FLSA classification and overtime", ""]
for kind, g in FLSA.groupby("flag_type"):
    L.append(f"- **{kind}:** {len(g)} employees; 13-week exposure ${g['exposure_13wk_low_usd'].sum():,.0f} to ${g['exposure_13wk_high_usd'].sum():,.0f}.")
under = FLSA[FLSA["flag_type"].str.startswith("Overtime underpayment")]
if len(under):
    L.append("  - Underpayments by site and shift: " + "; ".join(f"{s} {sh} shift: {n}" for (s, sh), n in under.groupby(["site", "shift"]).size().items()) + ".")
L += [f"- **Not flagged: {len(mca)} CDL-A drivers** averaging {mca['weekly_hours_avg_13wk'].mean():.1f} hours/week with no overtime pay. That is consistent with the Motor Carrier Act exemption *if* they drive vehicles over 10,000 lbs in interstate commerce. Confirm both, and check state overtime law.", ""]
L += ["### Premium-overtime scheduling algorithm (active hourly employees it schedules)", "",
      "| Group | n | Mean offers (group) | Mean offers (others) | Ratio | Reliability score (group / others) | Permutation p |", "|---|---|---|---|---|---|---|"]
for _, r in OTALG.iterrows():
    L.append(f"| {r['group']} | {r['n_group']} | {r['mean_offers_group']} | {r['mean_offers_others']} | {r['offer_ratio']} | {r['mean_reliability_group']} / {r['mean_reliability_others']} | {r['permutation_p']} |")
L.append("")

L += ["## C. Leave and accommodation sequences followed by discipline", "",
      "| Request | Requesters | Disciplined in window | Comparison | Disciplined | Rate ratio | Fisher p |", "|---|---|---|---|---|---|---|"]
for _, r in SR.iterrows():
    L.append(f"| {r['request']} | {r['n_requesters']} | {r['requesters_disciplined']} ({pct(r['rate_requesters'])}) | {r['n_comparison']} | {r['comparison_disciplined']} ({pct(r['rate_comparison'])}) | {r['rate_ratio']:.2f} | {r['fisher_p']:.4f} |")
L.append("")
for kind, g in SEQ.groupby("flag"):
    L.append(f"- **{kind}:** {len(g)} employees.")
L.append("")

L += ["## D. NLRA Section 7 risk in discipline narratives", ""]
for tier, g in S7.groupby("risk_tier"):
    L.append(f"- **{tier}:** {len(g)} events ({int(g['pca_flag_on_file'].sum())} with a concerted-activity flag on file).")
L += [f"- **Work-rule risk:** {policy_hits} discipline narratives enforce a \"pay confidentiality policy.\" A rule that bars employees from discussing pay is itself a Section 7 risk, separate from any one discipline decision.", ""]
(OUT / "step2_findings.md").write_text("\n".join(L))
print("\n".join(L))
