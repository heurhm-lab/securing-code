"""Generate a synthetic applicant + employee dataset for a trucking and fulfillment company.

Every row is fictional. The dataset is built for bias-audit training: an automated
video-interview (VI) score carries injected, correlated bias against older applicants,
applicants who requested an accommodation, non-native English speakers, and applicants
on poor connections, while true job ability is identical across those groups.

Outputs (written next to this script):
  warehouse_workforce_synthetic.csv  - the blind dataset (1,200 rows)
  ground_truth_bias.csv              - what was injected, per person (answer key)
  audit_summary.md                   - checks showing the bias is detectable

Run:  python3 generate.py            (deterministic; seed below)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20261011
N = 1200
AS_OF = pd.Timestamp("2026-09-30")
HIRE_RATE = 0.42                      # share hired within each role
FLSA_SALARY_THRESHOLD = 684 * 52      # federal white-collar exemption floor, $35,568/yr
OUT = Path(__file__).resolve().parent

rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------- reference data
ROLES = {
    # role: (share of applicants, age-band weights 18-24..60+)
    "Warehouse Associate":     (0.25, [0.26, 0.19, 0.24, 0.15, 0.11, 0.05]),
    "Picker/Packer":           (0.18, [0.30, 0.20, 0.22, 0.13, 0.10, 0.05]),
    "Forklift Operator":       (0.12, [0.14, 0.18, 0.28, 0.20, 0.14, 0.06]),
    "Inventory Control Clerk": (0.07, [0.16, 0.18, 0.26, 0.18, 0.14, 0.08]),
    "CDL-A Driver":            (0.14, [0.03, 0.10, 0.24, 0.25, 0.25, 0.13]),
    "Dispatcher":              (0.05, [0.08, 0.16, 0.30, 0.22, 0.16, 0.08]),
    "Maintenance Technician":  (0.06, [0.08, 0.15, 0.28, 0.23, 0.18, 0.08]),
    "Shift Supervisor":        (0.09, [0.04, 0.16, 0.36, 0.24, 0.15, 0.05]),
    "Operations Manager":      (0.04, [0.00, 0.06, 0.38, 0.30, 0.20, 0.06]),
}
AGE_BANDS = ["18-24", "25-29", "30-39", "40-49", "50-59", "60+"]
AGE_RANGE = {"18-24": (18, 24), "25-29": (25, 29), "30-39": (30, 39), "40-49": (40, 49), "50-59": (50, 59), "60+": (60, 68)}
SITES = {  # site: (share, non-native English rate)
    "Memphis, TN": (0.24, 0.10), "Columbus, OH": (0.20, 0.12), "Reno, NV": (0.16, 0.22),
    "Allentown, PA": (0.18, 0.20), "Dallas, TX": (0.22, 0.26),
}
ACCOM_RATE = dict(zip(AGE_BANDS, [0.04, 0.04, 0.05, 0.07, 0.11, 0.15]))   # disability prevalence rises with age
PHONE_RATE = dict(zip(AGE_BANDS, [0.66, 0.56, 0.46, 0.40, 0.37, 0.34]))
FMLA_RATE = dict(zip(AGE_BANDS, [0.08, 0.13, 0.20, 0.19, 0.21, 0.25]))   # own health + caregiving

# Injected VI bias, in subscore points (subscores are 0-100).
BIAS_AGE_COMM = dict(zip(AGE_BANDS, [0, 0, 0, -2.5, -6, -9]))
BIAS_AGE_ENTH = dict(zip(AGE_BANDS, [1, 1, 0, -3.5, -9, -13]))
BIAS_ACCOM = {"comm": -12.0, "enth": -11.0}
BIAS_LANG = {"comm": -10.0, "prob": -1.5}
BIAS_PHONE_ENTH = -3.0
BIAS_CONN = {"Good": (0, 0), "Fair": (-1.5, -1.0), "Poor": (-5.0, -4.0)}   # (comm, enth)
VI_WEIGHTS = {"prob": 0.40, "comm": 0.35, "enth": 0.25}


def pick(options, weights, size=None):
    w = np.asarray(weights, float)
    return rng.choice(options, size=size, p=w / w.sum())


def clip(x, lo=0, hi=100):
    return np.clip(x, lo, hi)


# ---------------------------------------------------------------- applicants
role_names = list(ROLES)
role = pick(role_names, [ROLES[r][0] for r in role_names], N)
age_band = np.array([pick(AGE_BANDS, ROLES[r][1]) for r in role])
age = np.array([rng.integers(*AGE_RANGE[b], endpoint=True) for b in age_band])
site_names = list(SITES)
site = pick(site_names, [SITES[s][0] for s in site_names], N)

accommodation = rng.random(N) < np.vectorize(ACCOM_RATE.get)(age_band)
non_native = rng.random(N) < np.vectorize(lambda s: SITES[s][1])(site)
device = np.where(rng.random(N) < np.vectorize(PHONE_RATE.get)(age_band), "Smartphone", "Laptop/Desktop")
conn_p = {"Smartphone": [0.55, 0.30, 0.15], "Laptop/Desktop": [0.72, 0.21, 0.07]}
connection = np.array([pick(["Good", "Fair", "Poor"], conn_p[d]) for d in device])

# True, job-relevant ability: independent of every protected or proxy attribute.
ability = rng.standard_normal(N)
max_exp = np.maximum(age - 18, 0)
experience = np.round(np.minimum(max_exp, rng.gamma(2.0, 1.2 + 0.18 * max_exp) * (1 + 0.15 * ability).clip(0.5)), 1)

skills_test = np.round(clip(62 + 10 * ability + rng.normal(0, 5, N)), 1)

# Video-interview subscores: shared noise draws so the unbiased version differs only by the bias terms.
e_prob, e_comm, e_enth = (rng.normal(0, s, N) for s in (6, 7, 8))
prob_fair = 60 + 9 * ability + e_prob
comm_fair = 62 + 6 * ability + e_comm
enth_fair = 61 + 3 * ability + e_enth

pen_age_comm = np.vectorize(BIAS_AGE_COMM.get)(age_band)
pen_age_enth = np.vectorize(BIAS_AGE_ENTH.get)(age_band)
pen_acc_comm = np.where(accommodation, BIAS_ACCOM["comm"], 0)
pen_acc_enth = np.where(accommodation, BIAS_ACCOM["enth"], 0)
pen_lang_comm = np.where(non_native, BIAS_LANG["comm"], 0)
pen_lang_prob = np.where(non_native, BIAS_LANG["prob"], 0)
pen_dev_enth = np.where(device == "Smartphone", BIAS_PHONE_ENTH, 0)
pen_conn_comm = np.array([BIAS_CONN[c][0] for c in connection])
pen_conn_enth = np.array([BIAS_CONN[c][1] for c in connection])

vi_prob = np.round(clip(prob_fair + pen_lang_prob), 1)
vi_comm = np.round(clip(comm_fair + pen_age_comm + pen_acc_comm + pen_lang_comm + pen_conn_comm), 1)
vi_enth = np.round(clip(enth_fair + pen_age_enth + pen_acc_enth + pen_dev_enth + pen_conn_enth), 1)
W = VI_WEIGHTS
vi_score = np.round(W["prob"] * vi_prob + W["comm"] * vi_comm + W["enth"] * vi_enth, 1)
vi_fair = np.round(W["prob"] * clip(prob_fair) + W["comm"] * clip(comm_fair) + W["enth"] * clip(enth_fair), 1)

def vi_part(prob=0, comm=0, enth=0):
    return np.round(W["prob"] * prob + W["comm"] * comm + W["enth"] * enth, 2)

gt_pen_age = vi_part(comm=pen_age_comm, enth=pen_age_enth)
gt_pen_acc = vi_part(comm=pen_acc_comm, enth=pen_acc_enth)
gt_pen_lang = vi_part(prob=pen_lang_prob, comm=pen_lang_comm)
gt_pen_tech = vi_part(comm=pen_conn_comm, enth=pen_dev_enth + pen_conn_enth)

# Hiring: the screen weights the VI score heavily; top HIRE_RATE per role (with a little recruiter noise).
decision_noise = rng.normal(0, 2.5, N)
composite = 0.65 * vi_score + 0.35 * skills_test + decision_noise
composite_fair = 0.65 * vi_fair + 0.35 * skills_test + decision_noise

def top_share(score):
    out = np.zeros(N, bool)
    for r in role_names:
        idx = np.flatnonzero(role == r)
        k = int(round(len(idx) * HIRE_RATE))
        out[idx[np.argsort(-score[idx])[:k]]] = True
    return out

hired = top_share(composite)
hired_fair = top_share(composite_fair)

app_start, app_end = pd.Timestamp("2023-01-02"), pd.Timestamp("2026-07-31")
app_date = app_start + pd.to_timedelta(rng.integers(0, (app_end - app_start).days, N), unit="D")
hire_date = pd.Series(pd.NaT, index=range(N), dtype="datetime64[ns]")
hire_date[hired] = app_date[hired] + pd.to_timedelta(rng.integers(10, 36, hired.sum()), unit="D")

# ---------------------------------------------------------------- employees
emp = pd.DataFrame(index=np.flatnonzero(hired))
emp_role = role[emp.index]

flsa, pay_type, base_rate, hours = [], [], [], []
gt_below_threshold = np.zeros(N, bool)
gt_duties_doubtful = np.zeros(N, bool)
HOURLY = {"Warehouse Associate": (17.5, 21), "Picker/Packer": (17, 20), "Forklift Operator": (19, 23.5),
          "Inventory Control Clerk": (18.5, 22.5), "Maintenance Technician": (25, 33), "CDL-A Driver": (27, 34),
          "Dispatcher": (21, 26), "Shift Supervisor": (24, 28)}
for i, r in zip(emp.index, emp_role):
    u = rng.random()
    if r == "Operations Manager":
        f, pt, rate, h = "Exempt - Executive", "Salary", rng.uniform(72000, 98000), rng.normal(52, 4)
    elif r == "Shift Supervisor" and u < 0.85:
        f, pt, h = "Exempt - Executive", "Salary", rng.normal(50, 4)
        if rng.random() < 0.14:          # salaried below the federal floor: cannot be exempt
            rate = rng.uniform(30500, 35400); gt_below_threshold[i] = True
        else:
            rate = rng.uniform(45000, 62000)
    elif r == "Dispatcher" and u < 0.30:  # salaried, but mostly routine scheduling work
        f, pt, rate, h = "Exempt - Administrative", "Salary", rng.uniform(40000, 48000), rng.normal(48, 4)
        gt_duties_doubtful[i] = True
    elif r == "CDL-A Driver":
        f, pt, rate, h = "Non-exempt - Motor Carrier Act OT exemption", "Hourly", rng.uniform(*HOURLY[r]), rng.normal(52, 5)
    else:
        f, pt, rate = "Non-exempt", "Hourly", rng.uniform(*HOURLY[r])
        h = rng.uniform(22, 30) if rng.random() < 0.10 and r in ("Warehouse Associate", "Picker/Packer") else rng.normal(41.5, 4)
    flsa.append(f); pay_type.append(pt); base_rate.append(round(rate, 2) if pt == "Hourly" else round(rate, -2)); hours.append(h)
emp["flsa_classification"] = flsa
emp["pay_type"] = pay_type
emp["base_rate_usd"] = base_rate
emp["weekly_hours_avg_13wk"] = np.round(np.clip(hours, 18, 62), 1)
emp["overtime_hours_avg_13wk"] = np.where(emp["flsa_classification"] == "Non-exempt",
                                          np.round(np.maximum(emp["weekly_hours_avg_13wk"] - 40, 0), 1), 0.0)

# Voluntary attrition, then the 12-month window that discipline and FMLA are measured over.
h_date = hire_date[emp.index]
vol_months = rng.exponential(34, len(emp))
vol_end = h_date + pd.to_timedelta(vol_months * 30.44, unit="D")
end = vol_end.where(vol_end < AS_OF, AS_OF)
status = np.where(vol_end < AS_OF, "Terminated - voluntary", "Active")

def months_between(a, b):
    return (b - a).dt.days / 30.44

tenure = months_between(h_date, end)
exposure = np.clip(np.minimum(tenure, 12) / 12, 0, 1).to_numpy()
ab = age_band[emp.index]
acc = accommodation[emp.index]
abil = ability[emp.index]

# FMLA: eligible after 12 months and 1,250 hours (about 24 h/week); all sites assumed to have 50+ employees.
fmla_eligible = (tenure >= 12).to_numpy() & (emp["weekly_hours_avg_13wk"].to_numpy() * 52 >= 1250)
p_fmla = np.vectorize(FMLA_RATE.get)(ab) + np.where(acc, 0.15, 0)
fmla = fmla_eligible & (rng.random(len(emp)) < p_fmla)
fmla_type = np.where(fmla, pick(["Continuous", "Intermittent"], [0.45, 0.55], len(emp)), "")
fmla_days = np.where(fmla, np.where(fmla_type == "Continuous", rng.integers(10, 61, len(emp)), rng.integers(3, 25, len(emp))), 0)

# Discipline over the 12 months before `end`.
safety_mult = np.where(np.isin(emp_role, ["Forklift Operator", "CDL-A Driver"]), 1.8, 1.0)
d_att = rng.poisson(0.45 * exposure)
d_prod = rng.poisson(0.30 * exposure * np.exp(-0.6 * abil))
d_safe = rng.poisson(0.12 * exposure * safety_mult)
d_cond = rng.poisson(0.08 * exposure)
# Injected: attendance points assessed for FMLA-protected absences.
gt_fmla_points = np.where(fmla & (rng.random(len(emp)) < 0.55), rng.integers(1, 4, len(emp)), 0)
# Injected: productivity write-ups because rate standards were not adjusted for accommodations.
gt_unadjusted = np.where(acc, rng.poisson(0.45 * exposure), 0)
d_att = d_att + gt_fmla_points
d_prod = d_prod + gt_unadjusted
d_total = d_att + d_prod + d_safe + d_cond

# Involuntary terminations follow discipline.
p_invol = 1 / (1 + np.exp(-(-3.4 + 0.75 * d_total)))
invol = (status == "Active") & (rng.random(len(emp)) < p_invol) & (tenure.to_numpy() > 3)
new_end = AS_OF - pd.to_timedelta(rng.integers(5, 150, len(emp)), unit="D")
end = end.where(~invol, np.maximum(new_end, h_date + pd.Timedelta(days=60)))
status = np.where(invol, "Terminated - involuntary", status)
tenure = months_between(h_date, end)

last_type, last_date = [], []
cats = np.array(["Attendance", "Productivity", "Safety", "Conduct"])
for j, i in enumerate(emp.index):
    counts = np.array([d_att[j], d_prod[j], d_safe[j], d_cond[j]])
    if counts.sum() == 0:
        last_type.append(""); last_date.append(pd.NaT); continue
    last_type.append(rng.choice(cats, p=counts / counts.sum()))
    lo = max(h_date[i], end[i] - pd.Timedelta(days=365))
    span = max((end[i] - lo).days, 1)
    last_date.append(end[i] - pd.Timedelta(days=int(rng.integers(0, min(span, 120)))))

perf = np.where(tenure >= 3, np.clip(np.round(3 + 0.8 * abil + rng.normal(0, 0.6, len(emp))), 1, 5), np.nan)

# ---------------------------------------------------------------- assemble
df = pd.DataFrame({
    "person_id": [f"TF-{i + 1:05d}" for i in range(N)],
    "record_type": np.where(hired, "Employee", "Applicant"),
    "application_date": app_date.strftime("%Y-%m-%d"),
    "requisition_role": role,
    "site": site,
    "age_band": age_band,
    "age_40_plus": np.isin(age_band, ["40-49", "50-59", "60+"]),
    "accommodation_request_flag": accommodation,
    "non_native_english_speaker": non_native,
    "interview_device": device,
    "interview_connection_quality": connection,
    "relevant_experience_yrs": experience,
    "skills_assessment_score": skills_test,
    "vi_problem_solving": vi_prob,
    "vi_communication": vi_comm,
    "vi_engagement": vi_enth,
    "vi_overall_score": vi_score,
    "hired": hired,
})
emp_cols = {
    "hire_date": h_date.dt.strftime("%Y-%m-%d"),
    "employment_status": status,
    "termination_date": end.where(status != "Active").dt.strftime("%Y-%m-%d"),
    "tenure_months": np.round(tenure, 1),
    "flsa_classification": emp["flsa_classification"],
    "pay_type": emp["pay_type"],
    "base_rate_usd": emp["base_rate_usd"],
    "weekly_hours_avg_13wk": emp["weekly_hours_avg_13wk"],
    "overtime_hours_avg_13wk": emp["overtime_hours_avg_13wk"],
    "fmla_eligible": fmla_eligible,
    "fmla_leave_flag_12mo": fmla,
    "fmla_leave_type": fmla_type,
    "fmla_leave_days_12mo": fmla_days,
    "discipline_events_12mo": d_total,
    "discipline_attendance_12mo": d_att,
    "discipline_productivity_12mo": d_prod,
    "discipline_safety_12mo": d_safe,
    "discipline_conduct_12mo": d_cond,
    "last_discipline_type": last_type,
    "last_discipline_date": pd.Series(last_date, index=emp.index).dt.strftime("%Y-%m-%d"),
    "performance_rating_latest": perf,
}
for col, vals in emp_cols.items():
    df[col] = pd.Series(np.asarray(vals), index=emp.index)
df["performance_rating_latest"] = df["performance_rating_latest"].astype("Int64")
for c in ["fmla_leave_days_12mo", "discipline_events_12mo", "discipline_attendance_12mo",
          "discipline_productivity_12mo", "discipline_safety_12mo", "discipline_conduct_12mo"]:
    df[c] = df[c].astype("Int64")

gt = pd.DataFrame({
    "person_id": df["person_id"],
    "latent_ability_z": np.round(ability, 3),
    "vi_overall_score_unbiased": vi_fair,
    "vi_penalty_age": gt_pen_age,
    "vi_penalty_accommodation": gt_pen_acc,
    "vi_penalty_language": gt_pen_lang,
    "vi_penalty_device_connection": gt_pen_tech,
    "vi_penalty_total": np.round(gt_pen_age + gt_pen_acc + gt_pen_lang + gt_pen_tech, 2),
    "hired_without_vi_bias": hired_fair,
})
gt["attendance_points_during_fmla"] = pd.Series(gt_fmla_points, index=emp.index).astype("Int64")
gt["productivity_events_unadjusted_standard"] = pd.Series(gt_unadjusted, index=emp.index).astype("Int64")
gt["exempt_salary_below_threshold"] = pd.Series(gt_below_threshold[emp.index], index=emp.index).astype("boolean")
gt["exempt_duties_test_doubtful"] = pd.Series(gt_duties_doubtful[emp.index], index=emp.index).astype("boolean")

df.to_csv(OUT / "warehouse_workforce_synthetic.csv", index=False)
gt.to_csv(OUT / "ground_truth_bias.csv", index=False)

# ---------------------------------------------------------------- audit summary
def rate_table(mask_groups, outcome):
    rows = []
    for name, m in mask_groups:
        rows.append((name, int(m.sum()), outcome[m].mean()))
    best = max(r[2] for r in rows)
    return rows, best

lines = ["# Audit summary (generated)", "",
         f"Seed {SEED} · {N} records · {int(hired.sum())} employees · as of {AS_OF.date()}.",
         "Selection rates use the actual hiring decision. The impact ratio is each group's rate divided by the highest rate in its comparison; under 0.80 fails the four-fifths rule of thumb.", ""]

def section(title, groups):
    rows, best = rate_table(groups, hired)
    fair_rows, _ = rate_table(groups, hired_fair)
    lines.extend([f"## {title}", "", "| Group | Applicants | Hired | Impact ratio | Hired without VI bias | Mean VI score | Mean skills test |", "|---|---|---|---|---|---|---|"])
    for (name, n, r), (_, _, fr), (_, m) in zip(rows, fair_rows, groups):
        lines.append(f"| {name} | {n} | {r:.1%} | {r / best:.2f} | {fr:.1%} | {vi_score[m].mean():.1f} | {skills_test[m].mean():.1f} |")
    lines.append("")

section("By age band", [(b, age_band == b) for b in AGE_BANDS])
over40 = np.isin(age_band, ["40-49", "50-59", "60+"])
section("Age 40+ (ADEA)", [("Under 40", ~over40), ("40 and over", over40)])
section("Accommodation request", [("No request", ~accommodation), ("Requested", accommodation)])
section("Language", [("Native English", ~non_native), ("Non-native English", non_native)])
section("Interview connection", [(c, connection == c) for c in ["Good", "Fair", "Poor"]])

E = df[hired]
lines.extend(["## Is the VI gap job-related?", "",
              "Among employees with a rating, mean performance (1-5) is flat across the groups the VI score penalizes, so the score gap is not predicting job performance.", "",
              "| Group | Employees rated | Mean performance | Mean VI score |", "|---|---|---|---|"])
rated = E["performance_rating_latest"].notna()
for name, m in [("Under 40", ~E["age_40_plus"]), ("40 and over", E["age_40_plus"]),
                ("No accommodation request", ~E["accommodation_request_flag"]), ("Accommodation request", E["accommodation_request_flag"])]:
    mm = m & rated
    lines.append(f"| {name} | {int(mm.sum())} | {E.loc[mm, 'performance_rating_latest'].astype(float).mean():.2f} | {E.loc[mm, 'vi_overall_score'].mean():.1f} |")
lines.append("")

lines.extend(["## Discipline", "", "| Group | Employees | Attendance events / person | Productivity events / person |", "|---|---|---|---|"])
for name, m in [("No FMLA leave", ~E["fmla_leave_flag_12mo"].astype(bool)), ("Took FMLA leave", E["fmla_leave_flag_12mo"].astype(bool)),
                ("No accommodation request", ~E["accommodation_request_flag"]), ("Accommodation request", E["accommodation_request_flag"])]:
    lines.append(f"| {name} | {int(m.sum())} | {E.loc[m, 'discipline_attendance_12mo'].astype(float).mean():.2f} | {E.loc[m, 'discipline_productivity_12mo'].astype(float).mean():.2f} |")
lines.append("")

ex = E["flsa_classification"].str.startswith("Exempt")
lines.extend(["## FLSA classification", "",
              f"- {int(ex.sum())} employees are classified exempt.",
              f"- {int((ex & (E['base_rate_usd'] < FLSA_SALARY_THRESHOLD)).sum())} exempt employees are paid below the ${FLSA_SALARY_THRESHOLD:,}/yr federal salary floor.",
              f"- {int((E['flsa_classification'] == 'Exempt - Administrative').sum())} dispatchers are classified administrative-exempt; the ground truth marks their duties test as doubtful.", ""])
(OUT / "audit_summary.md").write_text("\n".join(lines))
print("\n".join(lines))
