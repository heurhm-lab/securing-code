# Synthetic warehouse workforce dataset with injected bias

1,200 fictional applicants and employees at a trucking and fulfillment company. All rows are made up. The data is for bias-audit training, testing fairness tools, and HR-analytics coursework. It is not real people and not real outcomes.

The dataset has a problem planted in it on purpose. An automated **video-interview (VI) score** penalizes older applicants, applicants who asked for an accommodation, non-native English speakers, and applicants with poor connections. In this data, true job ability is the same across all of those groups. The penalty is correlated in realistic ways: accommodation requests rise with age, and device type varies by age. The bias then carries into hiring decisions, and two further problems show up among employees.

| File | What it is |
|---|---|
| `warehouse_workforce_synthetic.csv` | The dataset auditors work from (1,200 rows, 39 columns). |
| `ground_truth_bias.csv` | The answer key: hidden ability, unbiased VI score, each injected penalty, and per-employee flags. Keep it away from auditors until they've done their analysis. |
| `audit_summary.md` | Selection rates, impact ratios and outcome checks computed from the data. |
| `generate.py` | Deterministic generator (seed `20261011`). Change the constants at the top to adjust bias strength, rates or size. |

Regenerate with `python3 generate.py` (needs numpy and pandas).

## What's planted, and what an audit should find

| Issue | How it's built | What shows up in the data |
|---|---|---|
| Age bias in the VI score | The communication and engagement subscores are docked from age 40 up, most at 60+ | Age 40+ impact ratio **0.77**; 60+ is **0.56**. Skills test and performance are flat by age. |
| Disability-related bias | The same subscores are docked when an accommodation was requested | Impact ratio **0.56** with equal skills-test means and equal or better performance |
| Language bias | Communication docked for non-native English speakers | Impact ratio **0.60** |
| Technology bias | Engagement docked on smartphones; both subscores docked on poor connections | Poor-connection impact ratio **0.75** |
| FMLA interference | 55% of employees who took FMLA leave got 1–3 attendance points for protected absences | About 4x the attendance discipline rate (1.23 vs 0.32 per person) |
| Accommodation not applied to productivity standards | Extra productivity write-ups for employees who requested accommodations | Higher productivity discipline (0.28 vs 0.15 per person) |
| FLSA misclassification | 8 exempt supervisors are paid below the $35,568 federal salary floor. 8 dispatchers are salaried as administrative-exempt while doing routine scheduling. | Visible from `flsa_classification` × `base_rate_usd` and role |

The hidden ability score drives the skills test and the performance ratings, and nothing else. So the VI score's group gaps are not job-related, and any check of how well it predicts performance will show it under-predicting for the groups it penalizes. The groups are small (74 accommodation requests, 18 hired), as they would be in real data, so expect wide confidence intervals and use exact tests for them.

## Columns

**Everyone (applicants and employees)**

| Column | Values |
|---|---|
| `person_id` | `TF-00001` … `TF-01200` |
| `record_type` | `Applicant` (not hired) or `Employee` |
| `application_date` | 2023-01-02 to 2026-07-31 |
| `requisition_role` | Warehouse Associate, Picker/Packer, Forklift Operator, Inventory Control Clerk, CDL-A Driver, Dispatcher, Maintenance Technician, Shift Supervisor, Operations Manager |
| `site` | Memphis TN, Columbus OH, Reno NV, Allentown PA, Dallas TX |
| `age_band` | 18-24, 25-29, 30-39, 40-49, 50-59, 60+ |
| `age_40_plus` | True for the ADEA-protected bands |
| `accommodation_request_flag` | Asked for an interview accommodation (extended time, captions, assistive tech) |
| `non_native_english_speaker` | Self-reported |
| `interview_device` | Smartphone or Laptop/Desktop |
| `interview_connection_quality` | Good, Fair, Poor (vendor-reported) |
| `relevant_experience_yrs` | Years of relevant experience |
| `skills_assessment_score` | Structured work-sample test, 0–100. Valid and unbiased by design. |
| `vi_problem_solving`, `vi_communication`, `vi_engagement` | Vendor VI subscores, 0–100 |
| `vi_overall_score` | 0.40 problem-solving + 0.35 communication + 0.25 engagement |
| `hired` | The top 42% per role on 0.65 × VI + 0.35 × skills test, plus a small amount of recruiter noise |

**Employees only (blank for applicants)**

| Column | Values |
|---|---|
| `hire_date`, `employment_status`, `termination_date`, `tenure_months` | Status is Active, Terminated - voluntary, or Terminated - involuntary. Data is as of 2026-09-30. |
| `flsa_classification` | Non-exempt; Non-exempt - Motor Carrier Act OT exemption (CDL drivers); Exempt - Executive; Exempt - Administrative |
| `pay_type`, `base_rate_usd` | Hourly rate, or annual salary for salaried employees |
| `weekly_hours_avg_13wk` | Average weekly hours over the last 13 weeks |
| `overtime_hours_avg_13wk` | Hours over 40 for non-exempt employees (0 for exempt and Motor Carrier Act drivers) |
| `fmla_eligible` | 12+ months of tenure and 1,250+ hours a year. All sites are assumed to have 50+ employees. |
| `fmla_leave_flag_12mo`, `fmla_leave_type`, `fmla_leave_days_12mo` | Leave taken in the last 12 months: Continuous or Intermittent, and how many days |
| `discipline_events_12mo` | Total, and split by `discipline_attendance_12mo`, `_productivity_`, `_safety_` and `_conduct_` |
| `last_discipline_type`, `last_discipline_date` | Most recent event |
| `performance_rating_latest` | 1–5. Only for employees with 3+ months of tenure. |

## Using it responsibly

- These are synthetic records meant for practice and tool testing. Don't present them as real company data or treat the effect sizes as real-world estimates.
- An impact ratio under 0.80 is a screening rule of thumb, not a legal finding. A real audit pairs it with statistical significance, a job-relatedness review, and advice from employment counsel.
- The regulatory reference points (four-fifths rule, ADEA age 40+, the FMLA 12-month/1,250-hour test, the $684/week federal salary floor, the Motor Carrier Act overtime exemption) reflect federal rules as generally understood. State law can be stricter.
