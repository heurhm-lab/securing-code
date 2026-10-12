# Cardinal Logistics: Synthetic Applicant & Employee Dataset

> **All of this data is synthetic.** The people, IDs, sites, ZIP codes, supervisors and events are made up. "Cardinal Logistics" is just the scenario name and does not describe any real company. The ZIP codes are placeholders, and their demographics do not match any real place.

> **Answer key:** `answer_key/` lists every planted problem and holds the generator script. **Do not open anything in `answer_key/` until your analysis is finished.**

## Files

| File | Rows | Description |
|---|---|---|
| `data/cardinal_applicants_employees.csv` | 1,249 | One row per application. Employee fields are filled in only for people who were hired. |
| `data/cardinal_discipline_events.csv` | 203 | One row per discipline event. It includes the supervisor's free-text narrative. |

Join the two files on `applicant_id`.

## Scenario assumptions

- **Employer:** a regional 3PL with three sites: Hub 1 (Riverside DC), Hub 2 (Northgate Cross-Dock) and Hub 3 (Airport Fleet Yard). Headcount is well above 50, so the FMLA, ADA, Title VII and ADEA coverage thresholds are met.
- **Law:** analyze under **U.S. federal law only** (FLSA, NLRA, Title VII, ADEA, ADA, PWFA, FMLA, USERRA). Assume the state adds nothing stricter.
- **Applications** run from 2024-06-01 to 2026-02-28. **Snapshot date:** 2026-06-30.
- **Payroll period:** 13 weekly pay periods, from 2026-03-30 to 2026-06-28. All `*_period` columns cover only this window.
- **Hiring tool:** the AEDT is the vendor's "WorkFit Predict" (game-based plus questionnaire). The vendor's recommended cut score is **65**. Scores of 65 or more show as `Advance`.
- **Timekeeping:** each shift has a 30-minute **unpaid** meal period, which the payroll system deducts automatically. `badge_hours_period` is the raw door-badge time, so it includes meal periods.
- **Attendance policy:** a no-fault points system. Each absence or tardy is an "occurrence".
- **Proxies:** the true protected-class attributes are **not** in the public file. Only the proxies are:
  - `race_ethnicity_proxy_bisg`: a BISG-style estimate from surname and ZIP code. `bisg_confidence` is the posterior probability of the assigned category.
  - `name_inferred_gender`: inferred from first name. It can be `Unknown`.
  - `hs_grad_year` and `age_band`: self-reported, in the same row.

## Column dictionary: `cardinal_applicants_employees.csv`

### Application / AEDT

| Column | Description |
|---|---|
| `applicant_id` | Applicant ID. Carries over to the employee record if hired. |
| `application_date` | Date the application was submitted. |
| `job_group` | Requisition job group. |
| `job_title` | Title after hire. Employees only. |
| `site` | Hub the person applied to or works at. |
| `referral_source` | How the applicant found the job. |
| `home_zip` | Applicant's home ZIP code (synthetic). |
| `commute_miles` | Distance from home ZIP to the site. |
| `race_ethnicity_proxy_bisg`, `bisg_confidence` | BISG race/ethnicity proxy and the confidence in it. |
| `name_inferred_gender` | `F`, `M` or `Unknown`. |
| `hs_grad_year` | Self-reported high-school or GED year. Blank if not provided. |
| `age_band` | Self-reported age band at application: `18-24`, `25-39`, `40-49`, `50-59` or `60+`. |
| `employment_gap_months` | Longest gap on the résumé, in months. |
| `hiring_accommodation_requested` | 1 if the applicant asked for an accommodation during the application or assessment. |
| `aedt_score` | WorkFit Predict score from 0 to 100. Blank if no score was produced. |
| `aedt_recommendation` | `Advance` (65 or more) or `Do Not Advance`. Blank if unscored. |
| `hire_decision` | `Hired`, `Rejected` or `Withdrawn`. |
| `recruiter_note` | Free-text note from the recruiter. |

### Employment / classification / pay

| Column | Description |
|---|---|
| `hire_date`, `employment_status`, `termination_date` | Status is `Active`, `On Leave`, `Terminated - Voluntary` or `Terminated - Involuntary`. |
| `supervisor_id` | The employee's direct supervisor. |
| `flsa_classification` | Exempt or non-exempt, exactly as stored in the HRIS. |
| `flsa_exemption_basis` | The exemption HR relies on: `Executive`, `Administrative`, `Motor Carrier Act` or `Not exempt`. |
| `primary_duties_summary` | HR's job-description summary. Recorded only for salaried and MCA roles. |
| `direct_reports` | Number of full-time direct reports. |
| `vehicle_gvwr_lbs` | Gross vehicle weight rating of the assigned vehicle. Drivers only. |
| `base_hourly_rate` / `annual_salary` | Pay rate. Only one of the two is filled in. |
| `night_shift` | 1 if the employee is on a night shift that earns the $1.50/hr shift differential. |
| `weeks_in_period` | Weeks worked in the payroll period. Excludes weeks before hire, after termination, or on approved leave. |
| `hours_worked_period` | Paid or recorded hours in the period. |
| `badge_hours_period` | Raw badge hours in the period, including unpaid meal periods. |
| `regular_hours_period`, `overtime_hours_period` | Paid hours split at 40 per workweek. |
| `shift_differential_pay_period` | Shift differential paid in the period. |
| `nondiscretionary_bonus_period` | Productivity or safety bonus earned in the period, under the published bonus plan. |
| `overtime_pay_period` | Total amount paid for the overtime hours (the full overtime-hours line, not just the premium). |

### Accommodation, leave, PCA, discipline

| Column | Description |
|---|---|
| `accommodation_request_flag` | 1 if the employee requested an accommodation during employment. |
| `accommodation_type`, `accommodation_request_date`, `accommodation_outcome`, `interactive_process_documented` | Details of the request. Outcome is `Granted`, `Denied`, `Pending` or `Withdrawn`. Documented is `Y` or `N`. |
| `leave_request_flag` | 1 if the employee requested leave. |
| `leave_type`, `leave_start_date`, `leave_end_date`, `leave_status`, `leave_denial_reason` | Details of the leave request. |
| `pca_flag` | 1 if Employee Relations logged the employee as having engaged in protected concerted activity. |
| `discipline_event_count`, `most_recent_discipline_date`, `most_severe_discipline_action` | Summary of the discipline file, as stored in the HRIS. |
| `perf_rating_90day` | Supervisor rating from 1 to 5 at the 90-day review. Filled in only if tenure is at least 90 days. |

## Column dictionary: `cardinal_discipline_events.csv`

| Column | Description |
|---|---|
| `event_id` | Event ID. |
| `applicant_id` | The employee's ID. |
| `event_date` | Date of the event. |
| `site`, `job_group` | Site and job group at the time of the event. |
| `supervisor_id` | Supervisor who wrote the event. |
| `event_category` | HR's category code for the event. |
| `action_taken` | `Verbal Warning`, `Written Warning`, `Final Written Warning` or `Termination`. |
| `narrative` | Supervisor's narrative, verbatim. |

## Reproducing

```bash
python3 cardinal_logistics_synthetic/answer_key/generate_dataset.py   # spoiler: encodes the planted issues
```

The generator uses a fixed seed (`20261012`), so it reproduces these files exactly.
