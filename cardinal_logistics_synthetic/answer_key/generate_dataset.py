#!/usr/bin/env python3
"""
Generator for the Cardinal Logistics synthetic applicant/employee dataset.

SPOILER WARNING: this script encodes every planted problem. It lives in
answer_key/ for that reason. Do not read it before completing the analysis.

All people, sites, ZIP codes and events are fictitious. "Cardinal Logistics"
is used only as the scenario name requested for the exercise and does not
describe any real company.

Usage (from repo root):
    python3 cardinal_logistics_synthetic/answer_key/generate_dataset.py
"""
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20261012
rng = np.random.default_rng(SEED)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
KEY = ROOT / "answer_key"

N = 1240
SNAPSHOT = dt.date(2026, 6, 30)
PERIOD_START = dt.date(2026, 3, 30)   # Monday; 13 payroll weeks
PERIOD_WEEKS = 13
PERIOD_END = PERIOD_START + dt.timedelta(weeks=PERIOD_WEEKS) - dt.timedelta(days=1)
APP_START = dt.date(2024, 6, 1)
APP_END = dt.date(2026, 2, 28)
SALARY_THRESHOLD_ANNUAL = 35568  # federal $684/week (2019 rule; 2024 rule vacated)

SITES = ["Hub 1 - Riverside DC", "Hub 2 - Northgate Cross-Dock", "Hub 3 - Airport Fleet Yard"]

JOB_GROUPS = {
    # name: (applicant weight, share female, site weights)
    "Warehouse Associate": (0.35, 0.38, [0.45, 0.45, 0.10]),
    "Forklift Operator": (0.12, 0.15, [0.40, 0.40, 0.20]),
    "Driver": (0.14, 0.08, [0.15, 0.25, 0.60]),
    "Dispatcher": (0.06, 0.45, [0.30, 0.30, 0.40]),
    "Logistics Coordinator": (0.07, 0.55, [0.40, 0.40, 0.20]),
    "Warehouse Supervisor": (0.05, 0.25, [0.45, 0.45, 0.10]),
    "Fleet Maintenance Technician": (0.05, 0.05, [0.10, 0.10, 0.80]),
    "Customer Service Representative": (0.10, 0.65, [0.60, 0.30, 0.10]),
    "HR Generalist": (0.02, 0.75, [0.70, 0.20, 0.10]),
    "Operations Manager": (0.04, 0.30, [0.40, 0.35, 0.25]),
}

RACES = ["White", "Black", "Hispanic", "Asian", "Other/Multiracial"]
RACE_P = [0.50, 0.22, 0.20, 0.06, 0.02]

ZIP_GROUPS = {
    "A": ["70011", "70012", "70013", "70014", "70015", "70016"],  # near hubs, mostly White
    "B": ["70021", "70022", "70023", "70024", "70025"],           # mostly Black
    "C": ["70031", "70032", "70033", "70034"],                    # mostly Hispanic
    "D": ["70041", "70042", "70043", "70044", "70045"],           # mixed
}
ZIP_BY_RACE = {
    "White": [0.62, 0.05, 0.05, 0.28],
    "Black": [0.08, 0.65, 0.07, 0.20],
    "Hispanic": [0.10, 0.10, 0.60, 0.20],
    "Asian": [0.35, 0.05, 0.10, 0.50],
    "Other/Multiracial": [0.20, 0.15, 0.15, 0.50],
}
COMMUTE = {"A": (8, 3), "B": (20, 4), "C": (18, 4), "D": (13, 4)}


def rand_date(a, b):
    return a + dt.timedelta(days=int(rng.integers(0, (b - a).days + 1)))


def fmt_date(d):
    """HR notes use inconsistent date formats."""
    r = rng.random()
    if r < 0.45:
        return f"{d.month}/{d.day}/{d.year % 100:02d}"
    if r < 0.8:
        return d.strftime("%m/%d/%Y")
    return d.strftime("%b %d")


def pick(seq):
    return seq[int(rng.integers(0, len(seq)))]


def age_band(age):
    if age < 25:
        return "18-24"
    if age < 40:
        return "25-39"
    if age < 50:
        return "40-49"
    if age < 60:
        return "50-59"
    return "60+"


# ---------------------------------------------------------------------------
# 1. Applicants
# ---------------------------------------------------------------------------
jg_names = list(JOB_GROUPS)
jg_w = np.array([JOB_GROUPS[j][0] for j in jg_names])
jg_w = jg_w / jg_w.sum()

people = []
for i in range(N):
    jg = jg_names[rng.choice(len(jg_names), p=jg_w)]
    _, pf, site_w = JOB_GROUPS[jg]
    site = SITES[rng.choice(3, p=site_w)]
    gender = "F" if rng.random() < pf else "M"
    race = RACES[rng.choice(5, p=RACE_P)]
    zgrp = "ABCD"[rng.choice(4, p=ZIP_BY_RACE[race])]
    zipc = pick(ZIP_GROUPS[zgrp])
    mu, sd = COMMUTE[zgrp]
    commute = round(float(np.clip(rng.normal(mu, sd), 1.0, 45.0)), 1)

    band_draw = rng.choice(5, p=[0.21, 0.42, 0.18, 0.13, 0.06])
    lo, hi = [(18, 24), (25, 39), (40, 49), (50, 59), (60, 68)][band_draw]
    if jg in ("Operations Manager", "Warehouse Supervisor", "HR Generalist") and rng.random() < 0.6:
        lo = max(lo, 27)
        hi = max(hi, lo)
    age = int(rng.integers(lo, hi + 1))

    disability = rng.random() < (0.05 + 0.0025 * (age - 18))
    q = float(rng.normal())  # latent job-relevant qualification

    gap = rng.exponential(2.0)
    if gender == "F" and rng.random() < 0.35:
        gap += rng.exponential(7.0)
    if disability and rng.random() < 0.5:
        gap += rng.exponential(8.0)
    if age >= 55 and rng.random() < 0.4:
        gap += rng.exponential(5.0)
    gap = int(min(round(gap), 60))

    app_date = rand_date(APP_START, APP_END)
    grad = app_date.year - age + 18 + int(rng.integers(-1, 2))
    if rng.random() < 0.06:
        grad = None

    hiring_accom = (disability and rng.random() < 0.33) or rng.random() < 0.008

    referral_p = {"A": 0.22, "B": 0.07, "C": 0.08, "D": 0.12}[zgrp]
    if rng.random() < referral_p:
        source = "Employee Referral"
    else:
        source = ["Indeed", "Company Careers Site", "Staffing Agency", "Job Fair", "LinkedIn"][
            rng.choice(5, p=[0.40, 0.25, 0.15, 0.10, 0.10])]

    # --- AEDT score (vendor "WorkFit Predict") --------------------------------
    raw = (71 + 11 * q
           - 5.5 * (age >= 40) - 3.0 * (age >= 55)
           - 0.30 * min(gap, 36)
           - 0.60 * max(commute - 8, 0)
           - 7.0 * (gender == "F" and jg in ("Forklift Operator", "Driver", "Fleet Maintenance Technician"))
           - 8.0 * hiring_accom
           + rng.normal(0, 3))
    score = round(float(np.clip(raw, 5, 99)), 1)
    score_missing_reason = None
    if hiring_accom and rng.random() < 0.40:
        score = None
        score_missing_reason = "accommodation_unscored"
    elif rng.random() < 0.015:
        score = None
        score_missing_reason = "incomplete_assessment"

    rec = None if score is None else ("Advance" if score >= 65 else "Do Not Advance")

    # --- decision ------------------------------------------------------------
    note = None
    note_flag = None
    failed_screen = rng.random() < 0.05
    if rng.random() < 0.06:
        decision = "Withdrawn"
    elif score is None:
        decision = "Rejected"
        if score_missing_reason == "accommodation_unscored":
            note = pick(["Requested extra time on assessment - could not be scored, moved on",
                         "Asked for alt format of WorkFit test. No score = no advance",
                         "Did not complete standard assessment (accommodation request)"])
            note_flag = "accommodation_unscored_rejected"
        else:
            note = "Assessment incomplete after 2 reminders"
    elif rec == "Advance":
        p_hire = 0.80
        if age >= 50:
            p_hire = 0.50
        if failed_screen:
            decision = "Rejected"
            note = pick(["Failed pre-employment drug screen", "Background check - disqualifying conviction (role-related)",
                         "Failed DOT physical", "Did not pass forklift practical eval"])
            note_flag = "legit_rejection"
        else:
            decision = "Hired" if rng.random() < p_hire else "Rejected"
            if decision == "Rejected" and age >= 50 and rng.random() < 0.55:
                note = pick(["Overqualified - likely to leave once something better comes along",
                             "Not a long-term fit for the team", "Concerned about keeping pace on the floor",
                             "Looking for someone with more energy", "Probably close to retiring",
                             "Would not take direction well from younger supervisors"])
                note_flag = "age_coded_note"
    else:
        p_hire = 0.04
        if source == "Employee Referral":
            p_hire = 0.38
        decision = "Hired" if rng.random() < p_hire else "Rejected"
        if decision == "Hired" and source == "Employee Referral" and rng.random() < 0.6:
            note = pick(["Referred by site lead - override score", "Good word from referral, override",
                         "Manager override - known to team"])
            note_flag = "referral_override"

    if note is None and rng.random() < 0.10:
        if decision == "Hired" and age < 30:
            note = pick(["High energy, digital native", "Recent grad, great growth potential",
                         "Young and hungry - great culture add"])
            note_flag = "age_coded_note"
        elif gap >= 12 and gender == "F":
            note = pick(["Large gap in employment - ask about childcare situation", "Gap in work history (kids?)"])
            note_flag = "caregiver_coded_note"
        else:
            note = pick(["Strong references", "Forklift cert verified", "Available all shifts",
                         "Prior 3PL experience", "Bilingual Eng/Span - plus", "Clean MVR"])
            note_flag = "neutral_note"
    if (jg == "Customer Service Representative" and race in ("Hispanic", "Asian")
            and decision == "Rejected" and note is None and rng.random() < 0.25):
        note = pick(["Heavy accent - concern for phone queue", "Communication - accent may confuse customers"])
        note_flag = "national_origin_note"

    # --- proxies -------------------------------------------------------------
    if rng.random() < 0.74:
        bisg = race
    else:
        bisg = RACES[rng.choice(5, p=RACE_P)]
    bisg_conf = round(float(np.clip(rng.normal(0.72 if bisg == race else 0.52, 0.12), 0.30, 0.98)), 2)
    r = rng.random()
    name_gender = "Unknown" if r < 0.06 else (gender if r < 0.94 else ("M" if gender == "F" else "F"))

    people.append(dict(
        applicant_id=f"CL-{100000 + i * 7 + int(rng.integers(0, 7))}",
        application_date=app_date, job_group=jg, site=site, referral_source=source,
        home_zip=zipc, commute_miles=commute, race_ethnicity_proxy_bisg=bisg, bisg_confidence=bisg_conf,
        name_inferred_gender=name_gender, hs_grad_year=grad, age_band=age_band(age),
        employment_gap_months=gap, hiring_accommodation_requested=int(hiring_accom),
        aedt_score=score, aedt_recommendation=rec, hire_decision=decision, recruiter_note=note,
        # latent truth
        _race=race, _gender=gender, _age=age, _zgrp=zgrp, _disability=int(disability), _q=round(q, 3),
        _note_flag=note_flag, _score_missing_reason=score_missing_reason, _issues=[],
    ))

for p in people:
    if p["_note_flag"] in ("age_coded_note", "caregiver_coded_note", "national_origin_note",
                           "accommodation_unscored_rejected", "referral_override"):
        p["_issues"].append(p["_note_flag"])

# ---------------------------------------------------------------------------
# 2. Employees: comp, classification, payroll
# ---------------------------------------------------------------------------
PAY = {
    "Warehouse Associate": ("hourly", (17.50, 20.50), (37, 47)),
    "Forklift Operator": ("hourly", (19.50, 23.00), (39, 49)),
    "Driver": ("hourly", (23.00, 30.00), (44, 56)),
    "Dispatcher": ("salary", (40000, 47000), (45, 55)),
    "Logistics Coordinator": ("salary", (33200, 39000), (42, 51)),
    "Warehouse Supervisor": ("salary", (46000, 58000), (47, 57)),
    "Fleet Maintenance Technician": ("hourly", (25.00, 32.00), (40, 48)),
    "Customer Service Representative": ("hourly", (17.00, 19.50), (37, 43)),
    "HR Generalist": ("salary", (58000, 68000), (42, 48)),
    "Operations Manager": ("salary", (85000, 115000), (48, 58)),
}
EXEMPT_BASIS = {
    "Dispatcher": "Administrative", "Logistics Coordinator": "Administrative",
    "Warehouse Supervisor": "Executive", "HR Generalist": "Administrative",
    "Operations Manager": "Executive",
}
DUTIES = {  # only recorded for salaried / exempt-coded roles
    "Dispatcher": "Assigns loads to drivers using TMS routing recommendations; updates load status; answers driver check-in calls; escalates exceptions to Ops Manager",
    "Logistics Coordinator": "Selects carriers and negotiates spot rates within approved budget; resolves shipment exceptions with customers; recommends lane/carrier changes",
    "Warehouse Supervisor": "Manages a shift of associates: schedules, assigns work, evaluates performance, recommends hires/terminations; occasionally covers floor tasks",
    "Shift Lead": "Works picking/loading on the floor ~70% of shift; relays assignments from supervisor to temp associates; no hire/fire input",
    "HR Generalist": "Advises managers on policy, conducts workplace investigations, administers leave and benefits programs",
    "Operations Manager": "Runs site operations and budget; directs supervisors; hires and terminates",
    "CDL-A Linehaul Driver": "Operates tractor-trailer on interstate linehaul routes",
    "Final-Mile Van Driver": "Delivers parcels from Hub 3 to local addresses in cargo van",
}
FLSA_LABELS_NE = ["Non-Exempt"] * 14 + ["NON-EXEMPT", "Nonexempt", "NE", "non exempt"]
FLSA_LABELS_E = ["Exempt"] * 14 + ["EXEMPT", "exempt", "E"]

disc_events = []   # filled in section 3
event_seq = [0]


def add_event(p, date, category, action, narrative, klass, nlra_risk, other_risk=None):
    if klass in ("pca", "ambiguous") and p.get("job_title") in ("Warehouse Supervisor", "Operations Manager"):
        nlra_risk = "Low - likely statutory supervisor, outside NLRA coverage"
    event_seq[0] += 1
    disc_events.append(dict(
        event_id=f"DE-{5000 + event_seq[0]}", applicant_id=p["applicant_id"], event_date=date,
        site=p["site"], job_group=p["job_group"], supervisor_id=p["supervisor_id"],
        event_category=category, action_taken=action, narrative=narrative,
        _class=klass, _nlra_risk=nlra_risk, _other_risk=other_risk,
    ))


employees = [p for p in people if p["hire_decision"] == "Hired"]
for p in employees:
    p["hire_date"] = p["application_date"] + dt.timedelta(days=int(rng.integers(10, 41)))
    p["supervisor_id"] = f"SUP-{SITES.index(p['site']) + 1}{int(rng.integers(1, 9)):02d}"
    jg = p["job_group"]
    basis, prng, hrs = PAY[jg]
    title = jg
    p["direct_reports"] = 0
    p["vehicle_gvwr_lbs"] = None
    exempt = basis == "salary"
    p["flsa_exemption_basis"] = EXEMPT_BASIS.get(jg, "Not exempt")
    if jg == "Driver":
        if rng.random() < 0.80:
            title = "CDL-A Linehaul Driver"
            p["vehicle_gvwr_lbs"] = 80000
        else:
            title = "Final-Mile Van Driver"
            p["vehicle_gvwr_lbs"] = int(pick([9350, 9990, 9900, 8550]))
            p["_issues"].append("mca_small_vehicle_misapplied")
        exempt = True
        p["flsa_exemption_basis"] = "Motor Carrier Act"
    if jg == "Warehouse Supervisor":
        if rng.random() < 0.28:
            title = "Shift Lead"
            p["direct_reports"] = int(rng.integers(0, 2))
            p["_issues"].append("exec_exemption_fails_duties")
        else:
            p["direct_reports"] = int(rng.integers(6, 21))
    if jg == "Operations Manager":
        p["direct_reports"] = int(rng.integers(15, 61))
    if jg == "HR Generalist":
        p["direct_reports"] = 0
    p["job_title"] = title
    p["primary_duties_summary"] = DUTIES.get(title) or DUTIES.get(jg)
    if basis == "hourly":
        p["base_hourly_rate"] = round(float(rng.uniform(*prng)) * 4) / 4
        p["annual_salary"] = None
    else:
        p["base_hourly_rate"] = None
        sal = int(round(rng.uniform(*prng) / 100) * 100)
        p["annual_salary"] = sal
        if jg == "Logistics Coordinator" and sal < SALARY_THRESHOLD_ANNUAL:
            p["_issues"].append("salary_below_threshold")
        if jg == "Dispatcher":
            p["_issues"].append("dispatcher_admin_exemption_doubtful")
    # data-entry miscoding of a few hourly associates as exempt
    if jg == "Warehouse Associate" and rng.random() < 0.02:
        exempt = True
        p["flsa_exemption_basis"] = None
        p["_issues"].append("hourly_coded_exempt")
    p["_exempt"] = exempt
    p["flsa_classification"] = pick(FLSA_LABELS_E) if exempt else pick(FLSA_LABELS_NE)
    p["_hrs"] = hrs
    p["night_shift"] = int(basis == "hourly" and p["site"] != SITES[0] and rng.random() < 0.40)

# --- latent workplace events (decided before discipline so discipline can react)
for p in employees:
    tenure_end = SNAPSHOT
    # voluntary quit
    monthly_h = 0.028 if p["job_group"] in ("Warehouse Associate", "Forklift Operator", "Customer Service Representative") else 0.012
    d = p["hire_date"]
    quit_date = None
    while d < SNAPSHOT:
        if rng.random() < monthly_h:
            quit_date = d + dt.timedelta(days=int(rng.integers(0, 30)))
            break
        d += dt.timedelta(days=30)
    if quit_date and quit_date > SNAPSHOT:
        quit_date = None
    p["_quit"] = quit_date
    end = quit_date or SNAPSHOT
    p["_end"] = end
    span = (end - p["hire_date"]).days

    # accommodation (employment stage)
    p["accommodation_request_flag"] = 0
    for k in ("accommodation_type", "accommodation_request_date", "accommodation_outcome", "interactive_process_documented"):
        p[k] = None
    pr = 0.55 if p["_disability"] else (0.035 + (0.03 if p["_gender"] == "F" and p["_age"] < 42 else 0))
    if span > 45 and rng.random() < pr:
        p["accommodation_request_flag"] = 1
        if not p["_disability"] and p["_gender"] == "F" and rng.random() < 0.6:
            p["accommodation_type"] = "Pregnancy-related (PWFA)"
        else:
            p["accommodation_type"] = pick(["Lifting restriction", "Schedule modification", "Ergonomic equipment",
                                            "Modified duty", "Leave as accommodation", "Reserved parking",
                                            "Lifting restriction", "Modified duty"])
        p["accommodation_request_date"] = p["hire_date"] + dt.timedelta(days=int(rng.integers(30, span)))
        o = rng.choice(4, p=[0.52, 0.22, 0.16, 0.10])
        p["accommodation_outcome"] = ["Granted", "Denied", "Pending", "Withdrawn"][o]
        if p["accommodation_outcome"] == "Granted":
            p["interactive_process_documented"] = "Y" if rng.random() < 0.9 else "N"
        elif p["accommodation_outcome"] == "Denied":
            p["interactive_process_documented"] = "N" if rng.random() < 0.6 else "Y"
            if p["interactive_process_documented"] == "N":
                p["_issues"].append("accommodation_denied_no_interactive_process")
        else:
            p["interactive_process_documented"] = "N" if rng.random() < 0.5 else "Y"
        if p["accommodation_outcome"] == "Pending" and (SNAPSHOT - p["accommodation_request_date"]).days > 60:
            p["_issues"].append("accommodation_stale_pending")

    # leave
    p["leave_request_flag"] = 0
    for k in ("leave_type", "leave_start_date", "leave_end_date", "leave_status", "leave_denial_reason"):
        p[k] = None
    if span > 60 and rng.random() < 0.20 + 0.10 * p["_disability"]:
        p["leave_request_flag"] = 1
        lt = rng.choice(6, p=[0.30, 0.25, 0.15, 0.15, 0.05, 0.10])
        p["leave_type"] = ["FMLA - Own serious health condition", "FMLA - Family care", "FMLA - Bonding",
                           "Personal (unpaid)", "Military (USERRA)", "Workers' comp"][lt]
        start = p["hire_date"] + dt.timedelta(days=int(rng.integers(max(45, span // 2), span)))
        length = int(rng.integers(3, 12)) if lt in (0, 1) and rng.random() < 0.5 else int(rng.integers(5, 60))
        p["leave_start_date"] = start
        p["leave_end_date"] = min(start + dt.timedelta(days=length), SNAPSHOT)
        tenure_days = (start - p["hire_date"]).days
        if p["leave_type"].startswith("FMLA"):
            if tenure_days < 365:
                p["leave_status"] = "Denied"
                p["leave_denial_reason"] = "Not FMLA eligible (<12 months)"
            elif rng.random() < 0.10:
                p["leave_status"] = "Denied"
                p["leave_denial_reason"] = "Not FMLA eligible (<12 months)"
                p["_issues"].append("fmla_denied_wrong_reason")
            elif rng.random() < 0.08:
                p["leave_status"] = "Denied"
                p["leave_denial_reason"] = "Certification not returned"
            else:
                p["leave_status"] = "Approved"
        else:
            p["leave_status"] = "Approved" if rng.random() < 0.85 else "Denied"
            if p["leave_status"] == "Denied":
                p["leave_denial_reason"] = pick(["Business needs", "Insufficient notice"])
                if p["leave_type"] == "Military (USERRA)":
                    p["_issues"].append("userra_leave_denied")

    # protected concerted activity (latent) and HR flag
    p["_pca"] = int(span > 30 and rng.random() < 0.12)
    p["_pca_date"] = p["hire_date"] + dt.timedelta(days=int(rng.integers(20, max(span, 21)))) if p["_pca"] else None
    if p["_pca"]:
        p["pca_flag"] = int(rng.random() < 0.70)
    else:
        p["pca_flag"] = int(rng.random() < 0.015)
        if p["pca_flag"]:
            p["_issues"].append("pca_flag_false_positive")
    if p["_pca"] and not p["pca_flag"]:
        p["_issues"].append("pca_unflagged")

# ---------------------------------------------------------------------------
# 3. Discipline events + narratives
# ---------------------------------------------------------------------------
AISLES = list(range(3, 41))
LEGIT = {
    "Attendance": [
        "No call/no show for scheduled {shift} shift on {d}. Did not contact supervisor or the call-out line. Per attendance policy section 3.1 this is occurrence #{n} in rolling 12 months.",
        "EE clocked in late {n} times between {d} and {d2} (range 9-38 min). Previously coached verbally. Tardiness affects outbound wave start.",
        "Left shift early on {d} without notifying lead; 3.5 hrs of scheduled shift not worked. EE stated 'had somewhere to be.'",
        "Called out {n} times in 30 days without available PTO. Points total now at threshold under attendance policy.",
        "NCNS {d} and {d2}. Reached EE by phone on 2nd day, stated phone was broken. Policy: 2 consecutive NCNS = voluntary resignation; mgmt elected to issue final instead.",
    ],
    "Safety": [
        "Observed operating PIT in aisle {a} without seatbelt fastened on {d}. 2nd documented seatbelt violation in 90 days. Retrained on PIT policy 4.2.",
        "EE drove forklift with raised forks (approx 6 ft) while traveling in pedestrian walkway on {d}. Near-miss with picker. Camera footage reviewed by safety mgr.",
        "Failed to chock trailer wheels at door {a} before entering trailer w/ pallet jack on {d}. Trailer creep observed. Violates dock safety SOP.",
        "Speeding in yard (est. 22 mph in 10 mph zone) captured on telematics {d}. Prior coaching on file.",
        "Hard-braking + following-distance alerts (6 events) on route {d}. Dash cam reviewed: phone in hand while vehicle in motion.",
        "Bypassed lockout/tagout on conveyor section {a} to clear jam on {d}. Serious violation per LOTO program.",
    ],
    "Performance": [
        "Mis-scanned {n} outbound pallets to wrong trailer on {d}, resulting in customer chargeback. Accuracy 96.1% vs 99.5% standard over 4 wks.",
        "Pick rate averaged 118 UPH over 3 weeks vs 160 UPH standard after full training period. Coaching plan issued {d}.",
        "Dispatch board not updated for {n} loads on {d}; two drivers sent to wrong consignee. Second documented occurrence.",
        "Failed to complete DVIR before pre-trip on {d} and {d2}. Audit found pencil-whipped inspections.",
        "Call QA scores below 70% for 4 consecutive weeks (standard 85%); {n} customer escalations for incorrect delivery ETAs given on {d}.",
        "Signed off brake inspection on unit #{a}07 on {d} without completing torque check; unit failed roadside inspection 2 days later.",
    ],
    "Conduct": [
        "Verbal altercation with coworker in breakroom on {d}; EE threatened to 'meet him in the parking lot.' Witnessed by 2 associates. Sent home pending investigation.",
        "EE found with company fuel card used for personal vehicle on {d} (receipt + GPS mismatch). Admitted in investigation meeting.",
        "Sleeping in forklift during active shift {d}, observed by supervisor for approx 20 minutes.",
        "Removed 2 cases of customer product from facility without authorization on {d} (badge + camera). Loss prevention involved.",
        "Used racial slur directed at coworker on {d}. Two witnesses confirm. Violates EEO/anti-harassment policy.",
    ],
}
PCA = [  # (category, [narrative variants], nlra_risk) - one theme per tuple
    ("Policy Violation - Confidentiality", [
        "EE was overheard on {d} discussing pay rates w/ other {crew} and told them they were 'getting shorted compared to Hub 1.' Reminded that compensation is confidential and that discussing wages is a violation of company policy.",
        "On {d} EE showed paystub to several {crew} in breakroom and encouraged them to compare rates. Per handbook 6.4, pay information is confidential. EE told to stop.",
        "EE asked coworkers what they make and posted the numbers on whiteboard in breakroom ({d}). Whiteboard erased. Wage confidentiality policy reviewed with EE.",
    ], "High"),
    ("Insubordination", [
        "On {d} EE circulated a petition among 2nd shift {crew} requesting extra water breaks during heat advisory. Collected approx {n} signatures during shift change. Supervisor considers this disruptive and undermining of mgmt.",
        "EE brought a signed letter from {n} {crew} to GM on {d} asking for fans/cooling in the trailer bays. Was told to go through chain of command. Documented for going around supervisor.",
    ], "High"),
    ("Policy Violation - Social Media", [
        "EE posted on Facebook {d} that management 'doesn't care if we fall off the trailers' about the broken dock plates. Several coworkers commented agreeing. Violates social media policy prohibiting negative comments about the company.",
        "Instagram story {d}: photo of break room w/ caption 'they cut our breaks again, who's with me'. {n} coworkers replied. Disparaging the company on social media - policy 9.2.",
        "EE started a private group chat used by {crew} to compare schedules and pay and to plan a meeting about staffing. Supervisor was shown screenshots on {d}. Violates policy on unofficial work communications.",
    ], "High"),
    ("Insubordination", [
        "EE and {n} coworkers refused to load trailer at door {a} on {d} until damaged dock plate was replaced. EE acted as spokesperson for the group. Written up for refusing a direct instruction.",
        "On {d} EE told lead that 'none of us' would run the Line 3 conveyor until the guard was fixed; {n} {crew} stood with EE. Work stopped ~25 min. Guard was in fact missing (maintenance ticket opened same day).",
    ], "High"),
    ("Solicitation", [
        "EE was handing out union authorization cards in the employee parking lot before start of shift on {d}. Reminded of no-solicitation policy and told this activity is not permitted on company property.",
        "Security reported EE talking to {crew} about 'the union' at the picnic tables during lunch on {d}. EE told that union discussions are not allowed on premises.",
    ], "High"),
    ("Dress Code", [
        "EE wore a 'Drivers Deserve Fair Pay' button on uniform on {d}. Instructed to remove it; EE refused. Dress code allows only company-issued insignia.",
        "EE wore a union t-shirt under hi-vis vest on {d}. Told to change. EE said other {crew} would wear them too next week.",
    ], "High"),
    ("Conduct", [
        "Negative attitude in team huddle {d}: EE questioned the new mandatory Saturday OT schedule 'on behalf of the whole shift' and said others felt the same. Behavior is not consistent with our values.",
        "EE organized a group of {n} {crew} to go to the GM's office on {d} to complain about forced overtime w/out notice. Left work area without permission for ~15 min.",
        "EE is a 'ringleader' - has been stirring up {crew} about the new attendance points system and got others to complain at the {d} all-hands. Attitude issue.",
    ], "High"),
    ("Policy Violation - Confidentiality", [
        "EE discussed the ongoing investigation into Supervisor {sup} with other {crew} after being told to keep it confidential. Blanket confidentiality instruction given at start of investigation per HR template.",
    ], "High"),
    ("Policy Violation - Recording", [
        "EE recorded the {d} shift meeting on phone where mgmt announced changes to bonus structure; shared the audio in a group text with coworkers. Violates no-recording policy.",
    ], "High"),
    ("Insubordination", [
        "On {d} EE told supervisor that several of the {crew} were going to contact the Dept of Labor about unpaid pre-shift time and that 'we're done being quiet.' Supervisor documented as threatening and insubordinate.",
    ], "High"),
]
AMBIGUOUS = [
    ("Conduct",
     "During group meeting about schedule changes on {d}, EE swore at supervisor ('this is f***ing ridiculous') and threw clipboard on table. Others in meeting had raised the same concerns.",
     "Medium"),
    ("Conduct",
     "EE posted on TikTok {d} a video from inside the warehouse showing a customer's product labels and complaining about short staffing. Customer names visible.",
     "Medium"),
    ("Insubordination",
     "EE refused overtime assignment on {d} stating 'none of us are doing it until they fix the AC.' Only EE refused; others worked.",
     "Medium"),
    ("Conduct",
     "On picket line during the {d} protest outside Hub 2 gate (off-duty), EE yelled insults at replacement drivers entering. No threats or physical contact reported.",
     "Medium"),
]
GRIPE = [
    ("Insubordination",
     "EE complained repeatedly about own schedule being moved to 2nd shift and refused to work the assigned shift on {d}. No other employees involved.",
     "Low"),
    ("Conduct",
     "EE argued w/ lead on {d} about not being picked for the open dispatcher job; personal dispute, raised voice in front of customers.",
     "Low"),
    ("Policy Violation - Social Media",
     "EE posted on Facebook {d} that their supervisor is 'an idiot' and 'I hate this place.' No coworker engagement, no reference to working conditions.",
     "Low"),
]
FMLA_ATT = [
    "Absent {d} through {d2} ({n} consecutive shifts). EE stated was caring for parent after surgery. Absences counted as occurrences under attendance policy; EE now at {pts} points.",
    "Excessive absenteeism: {n} absences in the last 60 days incl {d}-{d2}. EE provided doctor's note but occurrences still assessed per policy (notes do not excuse absences).",
    "Called out {d} and {d2} citing 'flare-up' of condition. Points assessed. EE reminded that attendance is an essential function.",
    "Attendance - EE out from {d} to {d2} with newborn; did not return for scheduled shifts. Points assessed; final warning issued.",
]
ACCOM_PERF = [
    "Since returning w/ lifting restriction on {d} EE has not met pick rate standard (avg {n} UPH vs 160). Modified duty not available on this shift. Performance plan issued.",
    "EE requested to sit periodically; observed sitting on {d} and {d2} during active wave. Coached that all associates must be standing and productive.",
    "EE has been late {n} times since asking for schedule change for medical appointments. Schedule change still under review.",
    "Productivity below standard since disclosure of pregnancy; EE requesting lighter tasks and more breaks. Performance warning issued per standard.",
]

WAREHOUSE_KW = ("PIT", "forklift", "aisle", "pick rate", "conveyor", "trailer wheels", "pallets", "Sleeping in forklift", "customer product")
DRIVER_KW = ("telematics", "Dash cam", "DVIR", "Speeding in yard", "fuel card")
KW_GROUPS = [
    (WAREHOUSE_KW, ("Warehouse Associate", "Forklift Operator", "Warehouse Supervisor")),
    (DRIVER_KW, ("Driver",)),
    (("Dispatch board",), ("Dispatcher", "Logistics Coordinator")),
    (("Call QA",), ("Customer Service Representative",)),
    (("brake inspection",), ("Fleet Maintenance Technician",)),
]


def legit_template(cat, jg):
    ok = []
    for t in LEGIT[cat]:
        allowed = None
        for kws, groups in KW_GROUPS:
            if any(k in t for k in kws):
                allowed = groups
        if allowed is None or jg in allowed:
            ok.append(t)
    return pick(ok) if ok else None


CREW = {
    "Warehouse Associate": "associates", "Forklift Operator": "operators", "Driver": "drivers",
    "Dispatcher": "dispatchers", "Logistics Coordinator": "coordinators", "Warehouse Supervisor": "leads",
    "Fleet Maintenance Technician": "techs", "Customer Service Representative": "reps",
    "HR Generalist": "HR staff", "Operations Manager": "managers",
}
TAILS = ["", "", "", " EE refused to sign.", " Reviewed w/ HR.", " EE signed.", " Witness: lead on shift.", " -documented by sup"]

ACTIONS = ["Verbal Warning", "Written Warning", "Final Written Warning", "Termination"]


def fill(t, d, extra=None):
    d2 = d + dt.timedelta(days=int(rng.integers(1, 9)))
    return t.format(d=fmt_date(d), d2=fmt_date(d2), n=int(rng.integers(3, 11)), a=pick(AISLES),
                    shift=pick(["1st", "2nd", "3rd"]), pts=pick([7, 8, 9, 10]),
                    sup=f"SUP-{int(rng.integers(101, 399))}", **(extra or {}))


for p in employees:
    cands = []  # (date, kind, payload)
    start, end = p["hire_date"], p["_end"]
    span = (end - start).days
    lam = 0.35 * span / 365 + 0.12 * (p["_race"] == "Black")
    for _ in range(int(rng.poisson(lam))):
        cat = pick(list(LEGIT)) if p["job_group"] not in ("Driver",) else pick(["Safety", "Safety", "Attendance", "Performance", "Conduct"])
        cands.append((start + dt.timedelta(days=int(rng.integers(5, max(span, 6)))), "legit", cat))
    if p["_pca"] and rng.random() < 0.70:
        for _ in range(1 + int(rng.random() < 0.3)):
            cands.append((p["_pca_date"] + dt.timedelta(days=int(rng.integers(3, 45))), "pca", None))
    if not p["_pca"] and rng.random() < 0.03:
        cands.append((start + dt.timedelta(days=int(rng.integers(5, max(span, 6)))), "ambiguous", None))
    if not p["_pca"] and rng.random() < 0.025:
        cands.append((start + dt.timedelta(days=int(rng.integers(5, max(span, 6)))), "gripe", None))
    if p["accommodation_request_flag"] and rng.random() < 0.55:
        cands.append((p["accommodation_request_date"] + dt.timedelta(days=int(rng.integers(10, 60))), "accom", None))
    if (p["leave_request_flag"] and p["leave_type"].startswith("FMLA") and p["leave_status"] == "Approved"
            and rng.random() < 0.85):
        cands.append((p["leave_end_date"] + dt.timedelta(days=int(rng.integers(1, 15))), "fmla", None))
    cands = sorted([c for c in cands if c[0] <= end and c[0] > start])

    step = 0
    p["_terminated_invol"] = None
    for date, kind, payload in cands:
        lvl = step
        if p["_race"] == "Black" and rng.random() < 0.45:
            lvl += 1
        if kind == "legit":
            cat = payload
            t = legit_template(cat, p["job_group"])
            if t is None:
                cat = "Attendance"
                t = legit_template(cat, p["job_group"])
            text = fill(t, date)
            if "slur" in text or "Removed 2 cases" in text or "LOTO" in text or "fuel card" in text:
                lvl = max(lvl, 3)
            add_args = (cat, text, "legit", "None", None)
        elif kind == "pca":
            cat, variants, risk = pick(PCA)
            lvl += int(rng.integers(1, 3))
            add_args = (cat, fill(pick(variants), date, {"crew": CREW[p["job_group"]]}), "pca", risk, None)
        elif kind == "ambiguous":
            cat, t, risk = pick(AMBIGUOUS)
            add_args = (cat, fill(t, date), "ambiguous", risk, None)
        elif kind == "gripe":
            cat, t, risk = pick(GRIPE)
            add_args = (cat, fill(t, date), "individual_gripe", risk, None)
        elif kind == "accom":
            t = pick(ACCOM_PERF)
            if "pregnancy" in t and p["_gender"] != "F":
                t = ACCOM_PERF[0]
            lvl += 1
            add_args = ("Performance", fill(t, date), "accommodation_retaliation", "None", "ADA/PWFA failure to accommodate or retaliation")
        else:  # fmla
            t = pick(FMLA_ATT)
            if "newborn" in t and p["leave_type"] != "FMLA - Bonding":
                t = FMLA_ATT[0]
            lvl = max(lvl, 2)
            ls = p["leave_start_date"]
            text = t.format(d=fmt_date(ls), d2=fmt_date(p["leave_end_date"]), n=int(rng.integers(3, 9)),
                            pts=pick([7, 8, 9, 10]))
            add_args = ("Attendance", text, "fmla_interference", "None", "FMLA interference (protected leave counted as occurrences)")
            date = max(date, p["leave_end_date"] + dt.timedelta(days=1))
            if date > end:
                continue
        action = ACTIONS[min(lvl, 3)]
        cat, text, klass, risk, other = add_args
        text += pick(TAILS)
        if p["_race"] == "Black" and lvl > step and kind == "legit":
            other = "Severity above progressive-discipline step (disparate treatment pattern)"
        if kind == "pca" and lvl > step:
            other = "Skipped progressive-discipline steps"
        add_event(p, date, cat, action, text, klass, risk, other)
        step += 1
        if action == "Termination":
            p["_terminated_invol"] = date
            break

# employment status
for p in employees:
    if p["_terminated_invol"]:
        p["employment_status"] = "Terminated - Involuntary"
        p["termination_date"] = p["_terminated_invol"]
    elif p["_quit"]:
        p["employment_status"] = "Terminated - Voluntary"
        p["termination_date"] = p["_quit"]
    elif p["leave_request_flag"] and p["leave_status"] == "Approved" and p["leave_end_date"] >= SNAPSHOT:
        p["employment_status"] = "On Leave"
        p["termination_date"] = None
    else:
        p["employment_status"] = "Active"
        p["termination_date"] = None
    p["_end"] = p["termination_date"] or SNAPSHOT
    # 90-day performance rating depends only on latent qualification (not age, gap, commute)
    if (min(p["_end"], SNAPSHOT) - p["hire_date"]).days >= 90:
        p["perf_rating_90day"] = int(np.clip(round(3 + 0.8 * p["_q"] + rng.normal(0, 0.6)), 1, 5))
    else:
        p["perf_rating_90day"] = None

# --- payroll for Q2-2026 period ---------------------------------------------
for p in employees:
    for k in ("weeks_in_period", "hours_worked_period", "badge_hours_period", "regular_hours_period",
              "overtime_hours_period", "shift_differential_pay_period", "nondiscretionary_bonus_period",
              "overtime_pay_period"):
        p[k] = None
    ws = max(p["hire_date"], PERIOD_START)
    we = min(p["_end"], PERIOD_END)
    if we < ws:
        continue
    weeks = []
    for w in range(PERIOD_WEEKS):
        wk_start = PERIOD_START + dt.timedelta(weeks=w)
        wk_end = wk_start + dt.timedelta(days=6)
        if wk_end < ws or wk_start > we:
            continue
        if p["leave_request_flag"] and p["leave_status"] == "Approved" and p["leave_start_date"] <= wk_end and p["leave_end_date"] >= wk_start:
            continue
        weeks.append(w)
    if not weeks:
        p["weeks_in_period"] = 0
        continue
    lo, hi = p["_hrs"]
    mean_h = rng.uniform(lo, hi)
    off_clock = (p["site"] == SITES[2] and p["job_group"] in ("Forklift Operator", "Fleet Maintenance Technician")
                 and not p["_exempt"]) or (p["job_title"] == "Final-Mile Van Driver" and p["site"] == SITES[2] and rng.random() < 0.5)
    tot = reg = ot = badge = 0.0
    for _ in weeks:
        h = float(np.clip(rng.normal(mean_h, 2.8), 20, 70))
        if off_clock:
            true_h = h + rng.uniform(1.5, 4.0)
            paid = min(round(h * 4) / 4, 40.0)
            badge += true_h + 2.5
        else:
            paid = round(h * 4) / 4
            badge += paid + 2.5 + rng.uniform(0, 0.5)
        tot += paid
        reg += min(paid, 40)
        ot += max(paid - 40, 0)
    if off_clock:
        p["_issues"].append("off_the_clock_capped_40")
    p["weeks_in_period"] = len(weeks)
    p["hours_worked_period"] = round(tot, 2)
    p["badge_hours_period"] = round(badge, 2)
    p["regular_hours_period"] = round(reg, 2)
    p["overtime_hours_period"] = round(ot, 2)
    if p["base_hourly_rate"] is not None:
        rate = p["base_hourly_rate"]
        diff = round(tot * 1.50, 2) if p["night_shift"] else 0.0
        bonus = float(pick([0, 0, 150, 250, 300, 450, 600])) if p["job_group"] != "Customer Service Representative" else float(pick([0, 100, 200]))
        p["shift_differential_pay_period"] = diff
        p["nondiscretionary_bonus_period"] = bonus
        regular_rate = (rate * tot + diff + bonus) / tot
        p["_regular_rate"] = regular_rate
        due = 1.5 * regular_rate * ot
        if p["_exempt"]:
            paid_ot = 0.0
        else:
            r = rng.random()
            if r < 0.06 and ot > 0:
                paid_ot = rate * ot
                p["_issues"].append("ot_paid_straight_time")
            elif r < 0.10 and ot > 0:
                paid_ot = 0.0
                p["_issues"].append("ot_unpaid")
            elif p["site"] == SITES[1]:
                paid_ot = 1.5 * rate * ot
                if ot > 0 and (diff > 0 or bonus > 0):
                    p["_issues"].append("regular_rate_excludes_diff_bonus")
            else:
                paid_ot = due
        p["overtime_pay_period"] = round(paid_ot, 2)
        p["_ot_due"] = round(due, 2)
    else:
        p["shift_differential_pay_period"] = 0.0
        p["nondiscretionary_bonus_period"] = 0.0
        p["overtime_pay_period"] = 0.0
        p["_regular_rate"] = p["annual_salary"] / 2080
        p["_ot_due"] = round(1.5 * p["_regular_rate"] * ot, 2)

# discipline summary columns
ev_df = pd.DataFrame(disc_events)
for p in people:
    p["discipline_event_count"] = None
    p["most_recent_discipline_date"] = None
    p["most_severe_discipline_action"] = None
for p in employees:
    mine = [e for e in disc_events if e["applicant_id"] == p["applicant_id"]]
    p["discipline_event_count"] = len(mine)
    if mine:
        p["most_recent_discipline_date"] = max(e["event_date"] for e in mine)
        p["most_severe_discipline_action"] = max((e["action_taken"] for e in mine), key=ACTIONS.index)

# ---------------------------------------------------------------------------
# 4. Data-quality defects
# ---------------------------------------------------------------------------
emp_idx = [i for i, p in enumerate(people) if p["hire_decision"] == "Hired"]
non_idx = [i for i, p in enumerate(people) if p["hire_decision"] != "Hired"]

for i in rng.choice(len(people), 10, replace=False):  # age band inconsistent with grad year
    p = people[i]
    if p["hs_grad_year"]:
        bands = ["18-24", "25-39", "40-49", "50-59", "60+"]
        b = bands.index(p["age_band"])
        p["age_band"] = bands[(b + 2) % 5]
        p["_issues"].append("dq_age_band_vs_grad_year")

# impossible / negative payroll values
paid_emps = [i for i in emp_idx if people[i].get("hours_worked_period")]
bad = rng.choice(paid_emps, 4, replace=False)
people[bad[0]]["hours_worked_period"] = 2184.0
people[bad[0]]["_issues"].append("dq_impossible_hours")
people[bad[1]]["overtime_pay_period"] = -abs(people[bad[1]]["overtime_pay_period"] or 312.75)
people[bad[1]]["_issues"].append("dq_negative_ot_pay")
people[bad[2]]["regular_hours_period"] = round(people[bad[2]]["regular_hours_period"] + 40, 2)
people[bad[2]]["_issues"].append("dq_hours_components_dont_sum")
people[bad[3]]["badge_hours_period"] = None
people[bad[3]]["_issues"].append("dq_missing_badge_hours")

# discipline count mismatches
disc_emps = [i for i in emp_idx if people[i]["discipline_event_count"]]
for i in rng.choice(disc_emps, 5, replace=False):
    people[i]["discipline_event_count"] += int(pick([-1, 1, 2]))
    people[i]["_issues"].append("dq_discipline_count_mismatch")

# discipline event before hire date
for j in rng.choice(len(disc_events), 2, replace=False):
    e = disc_events[j]
    hp = next(p for p in people if p["applicant_id"] == e["applicant_id"])
    e["event_date"] = hp["hire_date"] - dt.timedelta(days=int(rng.integers(5, 40)))
    e["_dq"] = "event_before_hire_date"
    hp["_issues"].append("dq_discipline_before_hire")

# rejected applicants carrying employee data (ATS/HRIS merge error)
for i in rng.choice(non_idx, 2, replace=False):
    p = people[i]
    if p["hire_decision"] != "Rejected":
        continue
    p["hire_date"] = p["application_date"] + dt.timedelta(days=21)
    p["employment_status"] = "Active"
    p["flsa_classification"] = "Non-Exempt"
    p["job_title"] = p["job_group"]
    p["_issues"].append("dq_rejected_with_employee_record")

# ---------------------------------------------------------------------------
# 5. Output
# ---------------------------------------------------------------------------
PUBLIC_COLS = [
    "applicant_id", "application_date", "job_group", "job_title", "site", "referral_source",
    "home_zip", "commute_miles", "race_ethnicity_proxy_bisg", "bisg_confidence", "name_inferred_gender",
    "hs_grad_year", "age_band", "employment_gap_months", "hiring_accommodation_requested",
    "aedt_score", "aedt_recommendation", "hire_decision", "recruiter_note",
    "hire_date", "employment_status", "termination_date", "supervisor_id",
    "flsa_classification", "flsa_exemption_basis", "primary_duties_summary", "direct_reports", "vehicle_gvwr_lbs",
    "base_hourly_rate", "annual_salary", "night_shift",
    "weeks_in_period", "hours_worked_period", "badge_hours_period", "regular_hours_period",
    "overtime_hours_period", "shift_differential_pay_period", "nondiscretionary_bonus_period",
    "overtime_pay_period",
    "accommodation_request_flag", "accommodation_type", "accommodation_request_date",
    "accommodation_outcome", "interactive_process_documented",
    "leave_request_flag", "leave_type", "leave_start_date", "leave_end_date", "leave_status", "leave_denial_reason",
    "pca_flag", "discipline_event_count", "most_recent_discipline_date", "most_severe_discipline_action",
    "perf_rating_90day",
]
df = pd.DataFrame(people)
for c in PUBLIC_COLS:
    if c not in df.columns:
        df[c] = None
pub = df[PUBLIC_COLS].copy()

# duplicates: 6 exact, 3 re-scored conflicting
dup_rows = pub.sample(6, random_state=SEED)
conf_src = pub[pub["aedt_score"].notna() & (pub["hire_decision"] == "Rejected")].sample(3, random_state=SEED + 1).copy()
conf_src["aedt_score"] = (conf_src["aedt_score"] + rng.uniform(4, 9, 3)).round(1).clip(upper=99)
pub = pd.concat([pub, dup_rows, conf_src], ignore_index=True)
pub = pub.sample(frac=1, random_state=SEED + 2).reset_index(drop=True)

# integer-looking columns as nullable ints
for c in ["hs_grad_year", "direct_reports", "vehicle_gvwr_lbs", "annual_salary", "weeks_in_period",
          "accommodation_request_flag", "leave_request_flag", "pca_flag", "discipline_event_count",
          "perf_rating_90day", "night_shift"]:
    pub[c] = pd.to_numeric(pub[c], errors="coerce").astype("Int64")
pub.to_csv(DATA / "cardinal_applicants_employees.csv", index=False)

ev_pub = ev_df.copy()
for j, e in enumerate(disc_events):
    ev_pub.loc[j, "event_date"] = e["event_date"]
ev_pub = ev_pub.sort_values(["event_date", "event_id"])
ev_pub[["event_id", "applicant_id", "event_date", "site", "job_group", "supervisor_id",
        "event_category", "action_taken", "narrative"]].to_csv(DATA / "cardinal_discipline_events.csv", index=False)

# ---- ground truth -----------------------------------------------------------
dup_ids = set(dup_rows["applicant_id"]) | set(conf_src["applicant_id"])
for p in people:
    if p["applicant_id"] in set(dup_rows["applicant_id"]):
        p["_issues"].append("dq_exact_duplicate_row")
    if p["applicant_id"] in set(conf_src["applicant_id"]):
        p["_issues"].append("dq_conflicting_duplicate_aedt_score")
gt = pd.DataFrame([dict(
    applicant_id=p["applicant_id"], true_race_ethnicity=p["_race"], true_gender=p["_gender"], true_age=p["_age"],
    zip_cluster=p["_zgrp"], latent_disability=p["_disability"], latent_qualification=p["_q"],
    score_missing_reason=p["_score_missing_reason"], recruiter_note_class=p["_note_flag"],
    pca_engaged=p.get("_pca"), pca_activity_date=p.get("_pca_date"),
    regular_rate=round(p["_regular_rate"], 4) if p.get("_regular_rate") is not None else None,
    ot_pay_due_at_1_5x_regular_rate=p.get("_ot_due"),
    issues=";".join(dict.fromkeys(p["_issues"])),
) for p in people])
gt.to_csv(KEY / "ground_truth_people.csv", index=False)

ev_gt = pd.DataFrame([dict(event_id=e["event_id"], applicant_id=e["applicant_id"], narrative_class=e["_class"],
                           nlra_risk=e["_nlra_risk"], other_risk=e["_other_risk"], dq_issue=e.get("_dq"))
                      for e in disc_events])
ev_gt.to_csv(KEY / "ground_truth_discipline.csv", index=False)

print(f"people rows (with dups): {len(pub)}; unique applicants: {len(people)}; hired: {len(employees)}; "
      f"discipline events: {len(disc_events)}")
