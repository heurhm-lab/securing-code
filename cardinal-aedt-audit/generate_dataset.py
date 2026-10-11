"""Step 1: synthetic applicant-and-employee dataset for Cardinal Logistics (fictional).

Cardinal Logistics is a fictional 6,000-employee regional trucking and fulfillment company
headquartered in Memphis. This script builds an internal-audit sample: every row is made up.

What is modeled
  - An automated employment decision tool (AEDT) that scores warehouse applicants from a
    recorded video interview. Its score carries correlated bias (age, disability-related
    accommodation requests, race, English fluency, connection quality). True ability does not
    differ by group.
  - Non-AEDT hiring (drivers, maintenance, supervisors, managers) by structured interview.
  - Incumbent employees hired before the AEDT went live (2024-07-01), who have no AEDT score.
  - A scheduling algorithm that offers premium overtime shifts using a "reliability" score
    that counts protected leave and work restrictions against people.
  - Pay practice problems: overtime computed without shift differentials at two sites, and
    salaried supervisors and dispatchers classified exempt who may not qualify.
  - Discipline events with free-text narratives. Some follow accommodation or leave requests
    closely; some follow concerted activity; some are ordinary, and some look like Section 7
    issues but are not (individual gripes, threats, supervisors).

Outputs (in this folder)
  cardinal_people.csv             one row per applicant or employee (1,350 rows)
  cardinal_discipline_events.csv  one row per discipline event, with narrative
  answer_key_people.csv           what was injected, per person (keep from the audit team)
  answer_key_events.csv           what was injected, per event (keep from the audit team)

Run: python3 generate_dataset.py   (deterministic; seed below)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20261012
N_APPLICANTS = 950            # AEDT-era applicant pool, 2024-07-01 to 2026-07-31
N_INCUMBENTS = 400            # employees hired before the AEDT went live
AEDT_GO_LIVE = pd.Timestamp("2024-07-01")
AS_OF = pd.Timestamp("2026-09-30")
REVIEW_START = pd.Timestamp("2025-04-01")          # 18-month discipline / leave review window
HIRE_RATE = 0.38
SALARY_FLOOR = 684 * 52                            # federal white-collar floor, $35,568/yr
OUT = Path(__file__).resolve().parent
rng = np.random.default_rng(SEED)

# ------------------------------------------------------------------ reference data
JOBS = {
    # role: (job group, selection procedure, applicant share, incumbent share, age-band weights)
    "Warehouse Associate":     ("JG1 Material Handlers",      "AEDT video interview", 0.32, 0.26, [0.25, 0.19, 0.24, 0.15, 0.11, 0.06]),
    "Picker/Packer":           ("JG1 Material Handlers",      "AEDT video interview", 0.18, 0.14, [0.30, 0.20, 0.22, 0.13, 0.10, 0.05]),
    "Forklift Operator":       ("JG2 Equipment Operators",    "AEDT video interview", 0.14, 0.13, [0.14, 0.18, 0.28, 0.20, 0.14, 0.06]),
    "Inventory Control Clerk": ("JG4 Inventory & Dispatch",   "AEDT video interview", 0.06, 0.05, [0.16, 0.18, 0.26, 0.18, 0.14, 0.08]),
    "Dispatcher":              ("JG4 Inventory & Dispatch",   "Structured interview", 0.03, 0.05, [0.08, 0.16, 0.30, 0.22, 0.16, 0.08]),
    "CDL-A Driver":            ("JG3 Drivers",                "Structured interview", 0.14, 0.18, [0.03, 0.10, 0.24, 0.25, 0.25, 0.13]),
    "Maintenance Technician":  ("JG5 Maintenance",            "Structured interview", 0.06, 0.07, [0.08, 0.15, 0.28, 0.23, 0.18, 0.08]),
    "Shift Supervisor":        ("JG6 First-Line Supervisors", "Structured interview", 0.05, 0.09, [0.03, 0.15, 0.36, 0.25, 0.16, 0.05]),
    "Operations Manager":      ("JG7 Operations Management",  "Structured interview", 0.02, 0.03, [0.00, 0.06, 0.38, 0.30, 0.20, 0.06]),
}
AGE_BANDS = ["18-24", "25-29", "30-39", "40-49", "50-59", "60+"]
AGE_RANGE = {"18-24": (18, 24), "25-29": (25, 29), "30-39": (30, 39), "40-49": (40, 49), "50-59": (50, 59), "60+": (60, 68)}
SITES = {"Memphis, TN (HQ DC)": 0.40, "Southaven, MS": 0.22, "West Memphis, AR": 0.16, "Jackson, TN": 0.12, "Little Rock, AR": 0.10}
RACE = {"Black or African American": 0.45, "White": 0.30, "Hispanic or Latino": 0.135, "Asian": 0.03,
        "Two or More Races": 0.03, "American Indian or Alaska Native": 0.008, "Native Hawaiian or Pacific Islander": 0.004,
        "Declined to self-identify": 0.043}
SEX = {"Male": 0.62, "Female": 0.36, "Declined to self-identify": 0.02}
NON_NATIVE = {"Hispanic or Latino": 0.45, "Asian": 0.35}
ACCOM_P = dict(zip(AGE_BANDS, [0.03, 0.04, 0.05, 0.07, 0.10, 0.13]))
LEAVE_P = dict(zip(AGE_BANDS, [0.10, 0.14, 0.20, 0.19, 0.21, 0.24]))
PHONE_P = dict(zip(AGE_BANDS, [0.66, 0.56, 0.46, 0.40, 0.37, 0.34]))

# Injected AEDT bias (points on 0-100 subscores).
B_AGE_COMM = dict(zip(AGE_BANDS, [0, 0, 0, -2.0, -5.0, -8.0]))
B_AGE_ENG = dict(zip(AGE_BANDS, [1, 1, 0, -3.0, -8.0, -12.0]))
B_ACCOM = (-12.0, -11.0)                   # (communication, engagement)
B_LANG_COMM = -9.0
B_RACE = {"Black or African American": (-2.0, -2.5)}   # affect/dialect model trained on unrepresentative data
B_CONN = {"Good": (0, 0), "Fair": (-1.5, -1.0), "Poor": (-5.0, -4.0)}
B_PHONE_ENG = -3.0
W = {"prob": 0.40, "comm": 0.35, "eng": 0.25}

HOURLY = {"Warehouse Associate": (17.5, 21), "Picker/Packer": (17, 20), "Forklift Operator": (19, 23.5),
          "Inventory Control Clerk": (18.5, 22.5), "Maintenance Technician": (25, 33), "CDL-A Driver": (27, 34),
          "Dispatcher": (21, 26), "Shift Supervisor": (24, 28)}
SHIFT_DIFF = {"1st": 0.0, "2nd": 1.00, "3rd": 1.50}
OT_BUG_SITES = {"Southaven, MS", "West Memphis, AR"}   # payroll config leaves differentials out of the regular rate


def pick(options, weights, size=None):
    w = np.asarray(list(weights), float)
    return rng.choice(list(options), size=size, p=w / w.sum())


def draw_people(n, share_idx):
    roles = list(JOBS)
    role = pick(roles, [JOBS[r][share_idx] for r in roles], n)
    age_band = np.array([pick(AGE_BANDS, JOBS[r][4]) for r in role])
    return pd.DataFrame({
        "role": role,
        "job_group": [JOBS[r][0] for r in role],
        "selection_procedure": [JOBS[r][1] for r in role],
        "site": pick(SITES, SITES.values(), n),
        "sex": pick(SEX, SEX.values(), n),
        "race_ethnicity": pick(RACE, RACE.values(), n),
        "age_band": age_band,
        "age": [int(rng.integers(*AGE_RANGE[b], endpoint=True)) for b in age_band],
        "ability": rng.standard_normal(n),
    })


# ------------------------------------------------------------------ applicants (AEDT era)
A = draw_people(N_APPLICANTS, 2)
n = len(A)
A["non_native_english"] = rng.random(n) < A["race_ethnicity"].map(NON_NATIVE).fillna(0.03)
A["interview_accommodation"] = rng.random(n) < A["age_band"].map(ACCOM_P)
A["device"] = np.where(rng.random(n) < A["age_band"].map(PHONE_P), "Smartphone", "Laptop/Desktop")
A["connection"] = [pick(["Good", "Fair", "Poor"], [0.55, 0.30, 0.15] if d == "Smartphone" else [0.72, 0.21, 0.07]) for d in A["device"]]
A["application_date"] = AEDT_GO_LIVE + pd.to_timedelta(rng.integers(0, (pd.Timestamp("2026-07-31") - AEDT_GO_LIVE).days, n), unit="D")
A["skills_test"] = np.round(np.clip(62 + 10 * A["ability"] + rng.normal(0, 5, n), 0, 100), 1)

e = {k: rng.normal(0, s, n) for k, s in (("prob", 6), ("comm", 7), ("eng", 8))}
fair = {"prob": 60 + 9 * A["ability"] + e["prob"], "comm": 62 + 6 * A["ability"] + e["comm"], "eng": 61 + 3 * A["ability"] + e["eng"]}
pen = {
    "age": (A["age_band"].map(B_AGE_COMM), A["age_band"].map(B_AGE_ENG)),
    "accommodation": (np.where(A["interview_accommodation"], B_ACCOM[0], 0), np.where(A["interview_accommodation"], B_ACCOM[1], 0)),
    "language": (np.where(A["non_native_english"], B_LANG_COMM, 0), np.zeros(n)),
    "race": (A["race_ethnicity"].map(lambda r: B_RACE.get(r, (0, 0))[0]), A["race_ethnicity"].map(lambda r: B_RACE.get(r, (0, 0))[1])),
    "technology": (A["connection"].map(lambda c: B_CONN[c][0]), A["connection"].map(lambda c: B_CONN[c][1]) + np.where(A["device"] == "Smartphone", B_PHONE_ENG, 0)),
}
comm = fair["comm"] + sum(p[0] for p in pen.values())
eng = fair["eng"] + sum(p[1] for p in pen.values())
clip = lambda x: np.clip(x, 0, 100)
is_aedt = A["selection_procedure"].eq("AEDT video interview")
A["aedt_problem_solving"] = np.where(is_aedt, np.round(clip(fair["prob"]), 1), np.nan)
A["aedt_communication"] = np.where(is_aedt, np.round(clip(comm), 1), np.nan)
A["aedt_engagement"] = np.where(is_aedt, np.round(clip(eng), 1), np.nan)
A["aedt_score"] = np.where(is_aedt, np.round(W["prob"] * clip(fair["prob"]) + W["comm"] * clip(comm) + W["eng"] * clip(eng), 1), np.nan)
aedt_fair = W["prob"] * clip(fair["prob"]) + W["comm"] * clip(fair["comm"]) + W["eng"] * clip(fair["eng"])
for k, (pc, pe) in pen.items():
    A[f"_pen_{k}"] = np.where(is_aedt, np.round(W["comm"] * np.asarray(pc, float) + W["eng"] * np.asarray(pe, float), 2), 0.0)

noise = rng.normal(0, 2.5, n)
interview = 60 + 10 * A["ability"] + rng.normal(0, 6, n)
score = np.where(is_aedt, 0.65 * A["aedt_score"].fillna(0) + 0.35 * A["skills_test"], interview) + noise
score_fair = np.where(is_aedt, 0.65 * aedt_fair + 0.35 * A["skills_test"], interview) + noise


def select(s):
    hired = np.zeros(n, bool)
    for jg, idx in A.groupby("role").groups.items():
        idx = np.asarray(idx)
        k = int(round(len(idx) * HIRE_RATE))
        hired[idx[np.argsort(-s[idx])[:k]]] = True
    return hired


A["hired"] = select(score)
A["_hired_without_aedt_bias"] = select(score_fair)
A["hire_date"] = pd.NaT
A.loc[A["hired"], "hire_date"] = A.loc[A["hired"], "application_date"] + pd.to_timedelta(rng.integers(10, 36, A["hired"].sum()), unit="D")
A["_aedt_score_unbiased"] = np.where(is_aedt, np.round(aedt_fair, 1), np.nan)

# ------------------------------------------------------------------ incumbents (pre-AEDT)
I = draw_people(N_INCUMBENTS, 3)
I["non_native_english"] = rng.random(len(I)) < I["race_ethnicity"].map(NON_NATIVE).fillna(0.03)
I["interview_accommodation"] = False
I["hired"] = True
I["hire_date"] = pd.Timestamp("2017-01-02") + pd.to_timedelta(rng.integers(0, (AEDT_GO_LIVE - pd.Timestamp("2017-01-02")).days, len(I)), unit="D")
I["application_date"] = I["hire_date"] - pd.to_timedelta(rng.integers(10, 36, len(I)), unit="D")

P = pd.concat([A.assign(record_source="AEDT-era applicant"), I.assign(record_source="Pre-AEDT incumbent")], ignore_index=True)
P["applicant_id"] = [f"CL-A{i + 1:05d}" for i in range(len(P))]
P["employee_id"] = ""
emp_idx = P.index[P["hired"]]
P.loc[emp_idx, "employee_id"] = [f"CL-E{i + 1:05d}" for i in range(len(emp_idx))]

# ------------------------------------------------------------------ employment, pay and hours
E = P.loc[emp_idx].copy()
m = len(E)
vol_end = E["hire_date"] + pd.to_timedelta(rng.exponential(40, m) * 30.44, unit="D")
E["end"] = vol_end.where(vol_end < AS_OF, AS_OF)
E["status"] = np.where(vol_end < AS_OF, "Terminated - voluntary", "Active")
E["shift"] = pick(["1st", "2nd", "3rd"], [0.45, 0.33, 0.22], m)

flsa, pay_type, rate, salary, wk_hours, diff = [], [], [], [], [], []
E["_exempt_issue"] = ""
for i, r in zip(E.index, E["role"]):
    u = rng.random()
    d = SHIFT_DIFF[E.at[i, "shift"]]
    if r == "Operations Manager":
        f, pt, sal, h, d = "Exempt - Executive", "Salary", rng.uniform(72000, 98000), rng.normal(52, 4), 0
    elif r == "Shift Supervisor" and u < 0.85:
        f, pt, h, d = "Exempt - Executive", "Salary", rng.normal(51, 4), 0
        if rng.random() < 0.16:
            sal = rng.uniform(30500, 35400); E.at[i, "_exempt_issue"] = "Salary below federal floor"
        else:
            sal = rng.uniform(45000, 62000)
    elif r == "Dispatcher" and u < 0.40:
        f, pt, sal, h, d = "Exempt - Administrative", "Salary", rng.uniform(40000, 48000), rng.normal(48, 4), 0
        E.at[i, "_exempt_issue"] = "Duties test doubtful (routine scheduling, no independent judgment)"
    elif r == "CDL-A Driver":
        f, pt, sal, h = "Non-exempt (Motor Carrier Act overtime exemption)", "Hourly", np.nan, rng.normal(53, 5)
    else:
        f, pt, sal = "Non-exempt", "Hourly", np.nan
        h = rng.uniform(22, 30) if (rng.random() < 0.08 and r in ("Warehouse Associate", "Picker/Packer")) else rng.normal(40.5, 1.5)
    flsa.append(f); pay_type.append(pt); salary.append(np.nan if np.isnan(sal) else round(sal, -2)); wk_hours.append(h)
    rate.append(round(rng.uniform(*HOURLY[r]), 2) if pt == "Hourly" else np.nan); diff.append(d if pt == "Hourly" else 0.0)
E["flsa_classification"] = flsa
E["pay_type"] = pay_type
E["base_hourly_rate"] = rate
E["annual_salary"] = salary
E["shift_differential_per_hr"] = diff
E["_sched_hours"] = np.clip(wk_hours, 18, 66)

# ------------------------------------------------------------------ requests, leave, concerted activity
def rand_date(lo, hi):
    lo, hi = pd.Timestamp(lo), pd.Timestamp(hi)
    return lo + pd.Timedelta(days=int(rng.integers(0, max((hi - lo).days, 1))))

E["win_start"] = E["hire_date"].where(E["hire_date"] > REVIEW_START, REVIEW_START)
covered_window = E["end"] > E["win_start"] + pd.Timedelta(days=30)

E["accommodation_request_flag"] = covered_window & (E["interview_accommodation"] | (rng.random(m) < E["age_band"].map(ACCOM_P)))
E["accommodation_request_date"] = [rand_date(s, en - pd.Timedelta(days=20)) if f else pd.NaT for s, en, f in zip(E["win_start"], E["end"], E["accommodation_request_flag"])]
E["accommodation_type"] = [pick(["Lifting restriction", "Modified schedule", "Seated work station", "Intermittent breaks", "Hearing/captioning support"], [0.32, 0.22, 0.18, 0.18, 0.10]) if f else "" for f in E["accommodation_request_flag"]]

E["leave_request_flag"] = covered_window & (rng.random(m) < E["age_band"].map(LEAVE_P) + np.where(E["accommodation_request_flag"], 0.12, 0))
E["leave_start"] = [rand_date(s, en - pd.Timedelta(days=15)) if f else pd.NaT for s, en, f in zip(E["win_start"], E["end"], E["leave_request_flag"])]
tenure_at_leave = (E["leave_start"] - E["hire_date"]).dt.days / 30.44
E["fmla_eligible_at_request"] = E["leave_request_flag"] & (tenure_at_leave >= 12) & (E["_sched_hours"] * 52 >= 1250)
E["leave_type"] = np.where(~E["leave_request_flag"], "", np.where(E["fmla_eligible_at_request"],
                    pick(["FMLA - own serious health condition", "FMLA - family care", "FMLA - bonding"], [0.5, 0.35, 0.15], m),
                    "Non-FMLA medical/personal"))
E["leave_pattern"] = np.where(E["leave_request_flag"], pick(["Continuous", "Intermittent"], [0.45, 0.55], m), "")
E["leave_days"] = np.where(E["leave_request_flag"], np.where(E["leave_pattern"] == "Continuous", rng.integers(7, 61, m), rng.integers(3, 21, m)), 0)
E["leave_end"] = [s + pd.Timedelta(days=int(d)) if f else pd.NaT for s, d, f in zip(E["leave_start"], E["leave_days"], E["leave_request_flag"])]

is_sup = E["job_group"].isin(["JG6 First-Line Supervisors", "JG7 Operations Management"])
E["concerted_activity_flag"] = covered_window & (rng.random(m) < np.where(is_sup, 0.05, 0.065))
E["concerted_activity_date"] = [rand_date(s, en - pd.Timedelta(days=20)) if f else pd.NaT for s, en, f in zip(E["win_start"], E["end"], E["concerted_activity_flag"])]
ACTS = ["Circulated petition about trailer heat on second shift", "Discussed pay rates with coworkers",
        "Group complaint to HR about mandatory overtime", "Posted in drivers' Facebook group criticizing the overtime algorithm",
        "Joined coworkers in refusing to load trailer until dock fan repaired", "Organized break-room meeting about attendance policy"]
E["concerted_activity_description"] = [pick(ACTS, [1] * len(ACTS)) if f else "" for f in E["concerted_activity_flag"]]

# ------------------------------------------------------------------ premium overtime algorithm (last 13 weeks)
# The algorithm schedules hourly warehouse and maintenance staff; drivers, dispatchers and salaried staff are outside it.
hourly_ot_eligible = E["pay_type"].eq("Hourly") & E["role"].isin(["Warehouse Associate", "Picker/Packer", "Forklift Operator", "Inventory Control Clerk", "Maintenance Technician"])
recent_leave = E["leave_request_flag"] & (E["leave_start"] > AS_OF - pd.Timedelta(days=182))
active_restriction = E["accommodation_request_flag"]
E["scheduler_reliability_score"] = np.round(np.clip(80 + 6 * E["ability"] - 18 * recent_leave - 12 * active_restriction + rng.normal(0, 6, m), 20, 100), 0)
lam = 7 * np.exp(-0.9 * recent_leave - 0.6 * active_restriction + 0.08 * E["ability"])
E["premium_ot_offers_13wk"] = np.where(hourly_ot_eligible & E["status"].eq("Active"), rng.poisson(lam), 0)
E["premium_ot_shifts_worked_13wk"] = rng.binomial(E["premium_ot_offers_13wk"], 0.78)

weeks = 13
E["hours_worked_13wk"] = np.round(weeks * E["_sched_hours"] + 8 * E["premium_ot_shifts_worked_13wk"] + rng.normal(0, 6, m), 1)
E["weekly_hours_avg_13wk"] = np.round(E["hours_worked_13wk"] / weeks, 1)
ot_paid_class = E["flsa_classification"].eq("Non-exempt")
weekly_over = np.maximum(E["_sched_hours"] - 40, 0)
E["overtime_hours_13wk"] = np.where(ot_paid_class, np.round(weeks * weekly_over + 8 * E["premium_ot_shifts_worked_13wk"] + np.abs(rng.normal(0, 2, m)) * (weekly_over > 0), 1), 0.0)
reg_rate = E["base_hourly_rate"].fillna(0) + E["shift_differential_per_hr"]
ot_bug = ot_paid_class & E["site"].isin(OT_BUG_SITES) & (E["shift_differential_per_hr"] > 0)
paid_rate = np.where(ot_bug, E["base_hourly_rate"].fillna(0), reg_rate)
E["overtime_pay_13wk"] = np.round(1.5 * paid_rate * E["overtime_hours_13wk"], 2)
E["_ot_underpayment_13wk"] = np.round(np.where(ot_bug, 1.5 * (reg_rate - paid_rate) * E["overtime_hours_13wk"], 0), 2)

# ------------------------------------------------------------------ discipline events with narratives
NARR = {
    "Attendance": ["No-call/no-show for scheduled shift on {d}. Third occurrence in a rolling 90 days.",
                   "Clocked in 22 minutes late on {d}; 1 attendance point assessed.",
                   "Left shift 2 hours early on {d} without supervisor approval.",
                   "Accumulated 8 attendance points as of {d}; final warning under attendance policy."],
    "Productivity": ["Pick rate 71% of standard (120 UPH) for two consecutive weeks ending {d}. Coaching documented.",
                     "Missed cycle-count deadline twice in the week of {d}.",
                     "Load build errors on 3 outbound trailers on {d}."],
    "Safety": ["Operated forklift without seatbelt fastened on {d}; observed by safety lead.",
               "Failed to complete pre-trip inspection log on {d}.",
               "Walked through marked forklift lane on {d} after verbal warning."],
    "Conduct": ["Used profanity toward a coworker during shift change on {d}.",
                "Told supervisor on {d} that he would 'take care of' him after the meeting; security notified.",
                "Posted photo of a coworker's medical paperwork in a group chat on {d}.",
                "Complained loudly on {d} that his own schedule change was 'a joke'; refused to discuss it further."],
}
LEAVE_NARR = ["Absent {d1} through {d2}; {p} attendance points assessed under the no-fault attendance policy.",
              "Did not report for scheduled shifts {d1} through {d2}. Points assessed: {p}. Medical note not accepted as excuse under policy."]
ACCOM_NARR = ["Pick rate 64% of standard for the two weeks ending {d} while working under {a}. Standard rate applied; written warning.",
              "Unable to complete full load-out assignment on {d} due to {a}; documented as failure to meet job expectations."]
PCA_NARR = {
    "Circulated petition about trailer heat on second shift": "On {d} employee circulated a petition among second-shift associates about trailer heat and was told to stop soliciting on the dock. Written warning for disrupting operations.",
    "Discussed pay rates with coworkers": "On {d} employee discussed hourly pay rates with coworkers in the break room, violating the pay confidentiality policy. Written warning.",
    "Group complaint to HR about mandatory overtime": "On {d} employee encouraged coworkers to bring complaints about mandatory overtime to HR as a group. Supervisor notes 'negative attitude, stirring things up.' Final warning.",
    "Posted in drivers' Facebook group criticizing the overtime algorithm": "On {d} employee posted in a Facebook group with other drivers that the overtime algorithm is 'rigged against anyone who's been out sick.' Final warning for disloyalty and damaging company reputation.",
    "Joined coworkers in refusing to load trailer until dock fan repaired": "On {d} employee and four coworkers refused to load trailer #4 until the dock fan was repaired. Written warning for insubordination.",
    "Organized break-room meeting about attendance policy": "On {d} employee organized an unscheduled meeting of associates in the break room to discuss the attendance policy. Written warning for unauthorized meeting on company time.",
}
SUP_NARR = "On {d} shift supervisor joined associates' complaint about {x} and told the crew to stop work until it was resolved. Written warning for failing to carry out management directives."
fmt = lambda t: t.strftime("%b %-d, %Y")

events = []
for i, row in E.iterrows():
    lo, hi = row["win_start"], row["end"]
    if hi <= lo + pd.Timedelta(days=30):
        continue
    expo = (hi - lo).days / 365
    rates = {"Attendance": 0.45, "Productivity": 0.25 * np.exp(-0.6 * row["ability"]) if row["job_group"] in ("JG1 Material Handlers", "JG2 Equipment Operators", "JG4 Inventory & Dispatch") else 0.05,
             "Safety": 0.12 * (1.8 if row["job_group"] in ("JG2 Equipment Operators", "JG3 Drivers") else 1), "Conduct": 0.07}
    for cat, r in rates.items():
        for _ in range(rng.poisson(r * expo)):
            d = rand_date(lo, hi)
            events.append((i, d, cat, pick(NARR[cat], [1] * len(NARR[cat])).format(d=fmt(d)), "Baseline", "Not Section 7"))
    if row["leave_request_flag"] and rng.random() < 0.55:
        d1, d2 = row["leave_start"], min(row["leave_end"], hi)
        protected = row["fmla_eligible_at_request"]
        events.append((i, d2, "Attendance", pick(LEAVE_NARR, [1, 1]).format(d1=fmt(d1), d2=fmt(d2), p=int(rng.integers(2, 5))),
                       "Points for protected leave" if protected else "Points during non-FMLA leave (check ADA/state law)", "Not Section 7"))
    if row["accommodation_request_flag"] and rng.random() < 0.45:
        d = min(row["accommodation_request_date"] + pd.Timedelta(days=int(rng.integers(20, 110))), hi)
        events.append((i, d, "Productivity", pick(ACCOM_NARR, [1, 1]).format(d=fmt(d), a=row["accommodation_type"].lower()),
                       "Standard not adjusted for accommodation", "Not Section 7"))
    if row["concerted_activity_flag"] and rng.random() < 0.65:
        d = min(row["concerted_activity_date"] + pd.Timedelta(days=int(rng.integers(3, 45))), hi)
        act = row["concerted_activity_description"]
        if row["job_group"] in ("JG6 First-Line Supervisors", "JG7 Operations Management"):
            x = "trailer heat" if "heat" in act else "mandatory overtime"
            events.append((i, d, "Conduct", SUP_NARR.format(d=fmt(d), x=x), "Discipline after concerted activity (supervisor)", "Not covered: supervisor excluded under NLRA Sec. 2(3)"))
        else:
            events.append((i, d, "Conduct", PCA_NARR[act].format(d=fmt(d)), "Discipline after protected concerted activity", "Likely protected"))

ev = pd.DataFrame(events, columns=["_i", "event_date", "category", "narrative", "_injected", "_section7_truth"])
for j in ev.index[ev["narrative"].str.contains("'a joke'|take care of|medical paperwork")]:
    ev.at[j, "_section7_truth"] = "Not protected (individual gripe, threat, or privacy violation)"
ev = ev.sort_values(["_i", "event_date"]).reset_index(drop=True)
LEVELS = ["Verbal warning", "Written warning", "Final warning", "Termination"]
ev["seq"] = ev.groupby("_i").cumcount()
ev = ev[ev["seq"] <= 3].copy()
ev["level"] = ev["seq"].map(lambda k: LEVELS[k])
for j in ev.index[ev["level"].eq("Termination")]:
    i = ev.at[j, "_i"]
    if ev.at[j, "event_date"] < E.at[i, "end"] or E.at[i, "status"] == "Active":
        E.at[i, "end"] = ev.at[j, "event_date"]; E.at[i, "status"] = "Terminated - involuntary"
ev["event_id"] = [f"DE-{k + 1:05d}" for k in range(len(ev))]
ev["employee_id"] = ev["_i"].map(E["employee_id"])
ev["issued_by"] = ev["_i"].map(lambda i: "Operations Manager" if E.at[i, "role"] == "Shift Supervisor" else "Shift Supervisor")

counts = ev.groupby("_i").size()
E["discipline_events_18mo"] = counts.reindex(E.index).fillna(0).astype(int)
E["last_discipline_date"] = ev.groupby("_i")["event_date"].max().reindex(E.index)
E["tenure_months"] = np.round((E["end"] - E["hire_date"]).dt.days / 30.44, 1)

# ------------------------------------------------------------------ assemble outputs
for c in E.columns:
    P.loc[E.index, c] = E[c]
P["employment_status"] = P["status"].where(P["hired"], "")
P["termination_date"] = P["end"].where(P["status"].astype(str).str.startswith("Terminated"))
P["record_type"] = np.where(P["hired"], "Employee", "Applicant")
d = lambda s: pd.to_datetime(s).dt.strftime("%Y-%m-%d")

people = pd.DataFrame({
    "applicant_id": P["applicant_id"], "employee_id": P["employee_id"], "record_type": P["record_type"], "record_source": P["record_source"],
    "application_date": d(P["application_date"]), "role": P["role"], "job_group": P["job_group"], "site": P["site"],
    "selection_procedure": P["selection_procedure"],
    "sex_self_id": P["sex"], "race_ethnicity_self_id": P["race_ethnicity"], "age_band": P["age_band"],
    "non_native_english_speaker": P["non_native_english"], "interview_accommodation_requested": P["interview_accommodation"],
    "interview_device": P.get("device"), "interview_connection_quality": P.get("connection"),
    "skills_assessment_score": P.get("skills_test"),
    "aedt_problem_solving": P.get("aedt_problem_solving"), "aedt_communication": P.get("aedt_communication"),
    "aedt_engagement": P.get("aedt_engagement"), "aedt_score": P.get("aedt_score"),
    "hire_decision": np.where(P["hired"], "Hired", "Not hired"), "hire_date": d(P["hire_date"]),
    "employment_status": P["employment_status"], "termination_date": d(P["termination_date"]), "tenure_months": P.get("tenure_months"),
    "shift": P.get("shift"), "flsa_classification": P.get("flsa_classification"), "pay_type": P.get("pay_type"),
    "base_hourly_rate": P.get("base_hourly_rate"), "shift_differential_per_hr": P.get("shift_differential_per_hr"), "annual_salary": P.get("annual_salary"),
    "hours_worked_13wk": P.get("hours_worked_13wk"), "weekly_hours_avg_13wk": P.get("weekly_hours_avg_13wk"),
    "overtime_hours_13wk": P.get("overtime_hours_13wk"), "overtime_pay_13wk": P.get("overtime_pay_13wk"),
    "scheduler_reliability_score": P.get("scheduler_reliability_score"),
    "premium_ot_offers_13wk": P.get("premium_ot_offers_13wk"), "premium_ot_shifts_worked_13wk": P.get("premium_ot_shifts_worked_13wk"),
    "accommodation_request_flag": P.get("accommodation_request_flag"), "accommodation_request_date": d(P.get("accommodation_request_date")),
    "accommodation_type": P.get("accommodation_type"),
    "leave_request_flag": P.get("leave_request_flag"), "leave_start_date": d(P.get("leave_start")), "leave_end_date": d(P.get("leave_end")),
    "leave_type": P.get("leave_type"), "leave_pattern": P.get("leave_pattern"), "fmla_eligible_at_request": P.get("fmla_eligible_at_request"),
    "protected_concerted_activity_flag": P.get("concerted_activity_flag"), "concerted_activity_date": d(P.get("concerted_activity_date")),
    "concerted_activity_description": P.get("concerted_activity_description"),
    "discipline_events_18mo": P.get("discipline_events_18mo"), "last_discipline_date": d(P.get("last_discipline_date")),
})
for c in ["premium_ot_offers_13wk", "premium_ot_shifts_worked_13wk", "discipline_events_18mo", "scheduler_reliability_score"]:
    people[c] = pd.to_numeric(people[c]).astype("Int64")
for c in ["accommodation_request_flag", "leave_request_flag", "fmla_eligible_at_request", "protected_concerted_activity_flag"]:
    people[c] = people[c].astype("boolean")
people.loc[people["record_type"].eq("Applicant"), "accommodation_request_flag"] = pd.NA
people["interview_accommodation_requested"] = people["interview_accommodation_requested"].astype("boolean")
people.loc[people["record_source"].eq("Pre-AEDT incumbent"), "interview_accommodation_requested"] = pd.NA
people.to_csv(OUT / "cardinal_people.csv", index=False)

events_out = pd.DataFrame({"event_id": ev["event_id"], "employee_id": ev["employee_id"], "event_date": d(ev["event_date"]),
                           "category": ev["category"], "level": ev["level"], "issued_by": ev["issued_by"], "narrative": ev["narrative"]})
events_out.to_csv(OUT / "cardinal_discipline_events.csv", index=False)

key_people = pd.DataFrame({
    "applicant_id": P["applicant_id"], "employee_id": P["employee_id"],
    "latent_ability_z": np.round(P["ability"], 3), "aedt_score_unbiased": P.get("_aedt_score_unbiased"),
    **{f"aedt_penalty_{k}": P.get(f"_pen_{k}") for k in pen},
    "hired_without_aedt_bias": P.get("_hired_without_aedt_bias"),
    "exempt_classification_issue": P.get("_exempt_issue"), "overtime_underpayment_13wk": P.get("_ot_underpayment_13wk"),
})
key_people.to_csv(OUT / "answer_key_people.csv", index=False)
pd.DataFrame({"event_id": ev["event_id"], "employee_id": ev["employee_id"], "injected_pattern": ev["_injected"],
              "section7_truth": ev["_section7_truth"]}).to_csv(OUT / "answer_key_events.csv", index=False)

print(f"people: {len(people)} rows ({(people.record_type == 'Employee').sum()} employees, {(people.record_type == 'Applicant').sum()} not hired)")
print(f"discipline events: {len(events_out)}")
