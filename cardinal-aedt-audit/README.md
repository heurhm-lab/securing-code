# Cardinal Logistics: internal AEDT and workforce audit (synthetic data)

Cardinal Logistics is a fictional 6,000-employee regional trucking and fulfillment company headquartered in Memphis. Every record here is made up. The data supports a practice internal audit of the automated video-interview tool (AEDT), the premium-overtime scheduling algorithm, pay classification, and discipline practices.

## Files

| File | Rows | What it is |
|---|---|---|
| `cardinal_people.csv` | 1,350 | One row per person: 950 applicants from the AEDT era (361 hired, 589 not) and 400 incumbents hired before the AEDT went live on 2024-07-01. |
| `cardinal_discipline_events.csv` | 459 | One row per discipline event in the review window, with the supervisor's narrative. Join to people on `employee_id`. |
| `answer_key_people.csv`, `answer_key_events.csv` | | What the generator built in. **Keep these from the audit team** until findings are written. |
| `generate_dataset.py` | | Rebuilds every file deterministically (seed `20261012`). |

Data is as of **2026-09-30**. Hours and pay cover the **13 weeks** before each person's last day (or the as-of date). Discipline, leave, accommodation and concerted activity cover an **18-month review window** starting 2025-04-01, or from the hire date if later.

## Fields in `cardinal_people.csv`

**Identity and selection**

| Field | Notes |
|---|---|
| `applicant_id`, `employee_id` | `employee_id` is blank for applicants who weren't hired |
| `record_type`, `record_source` | Employee or Applicant; AEDT-era applicant or Pre-AEDT incumbent |
| `application_date`, `role`, `job_group`, `site` | Seven AAP-style job groups (JG1–JG7) across five sites in TN, MS and AR |
| `selection_procedure` | `AEDT video interview` (warehouse roles: JG1, JG2, and inventory clerks in JG4) or `Structured interview` (everyone else) |
| `sex_self_id`, `race_ethnicity_self_id` | Self-identified EEO categories, including "Declined to self-identify" |
| `age_band` | 18-24 … 60+ |
| `non_native_english_speaker` | Proxy for national origin |
| `interview_accommodation_requested` | Accommodation requested for the AEDT interview. Proxy for disability. Blank for incumbents. |
| `interview_device`, `interview_connection_quality` | As reported by the AEDT vendor |
| `skills_assessment_score` | Structured work-sample test, 0–100 |
| `aedt_problem_solving`, `aedt_communication`, `aedt_engagement`, `aedt_score` | Vendor subscores and overall score, 0–100. Only for applicants who went through the AEDT. |
| `hire_decision`, `hire_date` | |

**Employment, pay and hours (employees only)**

| Field | Notes |
|---|---|
| `employment_status`, `termination_date`, `tenure_months` | Active, Terminated - voluntary, or Terminated - involuntary |
| `shift` | 1st, 2nd or 3rd. The 2nd and 3rd shifts carry a per-hour differential. |
| `flsa_classification` | Non-exempt; Non-exempt (Motor Carrier Act overtime exemption); Exempt - Executive; Exempt - Administrative |
| `pay_type`, `base_hourly_rate`, `shift_differential_per_hr`, `annual_salary` | |
| `hours_worked_13wk`, `weekly_hours_avg_13wk` | Total hours worked |
| `overtime_hours_13wk`, `overtime_pay_13wk` | Overtime hours and overtime pay as recorded by payroll |
| `scheduler_reliability_score` | The input the scheduling algorithm uses to rank people for premium overtime shifts |
| `premium_ot_offers_13wk`, `premium_ot_shifts_worked_13wk` | Premium shifts offered by the algorithm, and shifts actually worked |

**Requests, leave, concerted activity and discipline (employees only)**

| Field | Notes |
|---|---|
| `accommodation_request_flag`, `accommodation_request_date`, `accommodation_type` | ADA accommodation request made as an employee, plus any request made at the interview stage |
| `leave_request_flag`, `leave_start_date`, `leave_end_date`, `leave_type`, `leave_pattern` | FMLA or non-FMLA leave; continuous or intermittent |
| `fmla_eligible_at_request` | 12 months of tenure and 1,250 hours at the time of the request. Sites are assumed to meet the 50-employee/75-mile test. |
| `protected_concerted_activity_flag`, `concerted_activity_date`, `concerted_activity_description` | Group activity about working conditions that management knew of. The flag records the activity; it isn't a legal conclusion. |
| `discipline_events_18mo`, `last_discipline_date` | Totals. The events themselves are in the events file. |

## Fields in `cardinal_discipline_events.csv`

`event_id`, `employee_id`, `event_date`, `category` (Attendance, Productivity, Safety, Conduct), `level` (Verbal warning → Written warning → Final warning → Termination), `issued_by`, `narrative`.

## Things to keep in mind when analyzing

- Some race groups are very small among AEDT applicants (a handful of American Indian/Alaska Native and Native Hawaiian/Pacific Islander applicants), as is the accommodation group. Treat ratios on small groups with care.
- Incumbents have no AEDT score, so they belong in workforce analyses but not in AEDT selection-rate analyses.
- Not every employee with overtime hours is owed overtime pay, and not everyone who discusses working conditions is covered by the NLRA.

## Running the audit

```
python3 generate_dataset.py   # step 1: the synthetic data
python3 analyze.py            # step 2: results/*.csv and results/step2_findings.md (doesn't read the answer keys)
python3 build_summary.py      # step 3: results/findings_register.csv and results/audit_summary.md
```

The ranked summary is `results/audit_summary.md`. It scores each finding on likelihood (1–5), severity (1–5) and reversibility (Low, Medium, High), pairs each with a proportionate remediation step, and includes a log of corrections to the analysis.
