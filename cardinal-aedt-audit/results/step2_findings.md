# Step 2 findings: Cardinal Logistics internal audit (synthetic data)

Data as of 2026-09-30. Sources: `cardinal_people.csv` (1350 rows) and `cardinal_discipline_events.csv` (459 events). Answer keys not used.

## Method choices to review

- **Four-fifths population.** AEDT applicants only (661), from the AEDT go-live onward. Pre-AEDT incumbents have no AEDT decision and are left out. Structured-interview applicants (289) are a comparison group.
- **Reference group.** The group with the highest selection rate among groups with enough data. "Declined to self-identify" is never the reference.
- **Sample-size rule.** A group needs at least 30 applicants and at least 5 expected hires before its ratio is interpreted. Smaller groups are reported as counts only.
- **Significance.** Fisher's exact test of each group against the reference, two-sided, alpha 0.05. Every group is tested, including ones that pass four-fifths.
- **Leave and accommodation sequences.** Requesters are compared with non-requesters observed over a similar-length window starting on a random date. Timing alone is a lead for review, not a finding of retaliation.
- **Section 7.** Transparent rules on the narrative text, then a tier. Every High and Medium item needs a person to read the full file.

## A. Selection rates (four-fifths rule)

### AEDT applicants (all AEDT job groups)

| Dimension | Group | Applicants | Hires | Rate | Impact ratio | Fisher p | Shortfall | Assessment |
|---|---|---|---|---|---|---|---|---|
| Race/ethnicity | American Indian or Alaska Native | 2 | 1 | 50.0% | 1.29 | 1.000 | -0.2 | Insufficient sample: report count only, do not interpret ratio |
| Race/ethnicity | Asian | 19 | 7 | 36.8% | 0.95 | 1.000 | 0.4 | Insufficient sample: report count only, do not interpret ratio |
| Race/ethnicity | Black or African American | 293 | 114 | 38.9% | 1.00 |  | 0.0 | Reference group |
| Race/ethnicity | Declined to self-identify | 29 | 11 | 37.9% | 0.97 | 1.000 | 0.3 | Not interpretable (no group identity) |
| Race/ethnicity | Hispanic or Latino | 88 | 27 | 30.7% | 0.79 | 0.169 | 7.2 | Fails 4/5, not statistically significant: monitor, aggregate more data |
| Race/ethnicity | Native Hawaiian or Pacific Islander | 3 | 1 | 33.3% | 0.86 | 1.000 | 0.2 | Insufficient sample: report count only, do not interpret ratio |
| Race/ethnicity | Two or More Races | 22 | 13 | 59.1% | 1.52 | 0.073 | -4.4 | Insufficient sample: report count only, do not interpret ratio |
| Race/ethnicity | White | 205 | 77 | 37.6% | 0.97 | 0.779 | 2.8 | Passes 4/5, no significant difference (not proof of compliance) |
| Sex | Declined to self-identify | 15 | 4 | 26.7% | 0.67 | 0.418 | 1.9 | Not interpretable (no group identity) |
| Sex | Female | 240 | 95 | 39.6% | 1.00 |  | 0.0 | Reference group |
| Sex | Male | 406 | 152 | 37.4% | 0.95 | 0.616 | 8.7 | Passes 4/5, no significant difference (not proof of compliance) |
| Age (ADEA 40+) | 40 and over | 193 | 63 | 32.6% | 0.81 | 0.078 | 14.5 | Passes 4/5, no significant difference (not proof of compliance) |
| Age (ADEA 40+) | Under 40 | 468 | 188 | 40.2% | 1.00 |  | 0.0 | Reference group |
| Age band vs under 40 | Under 40 (pooled) | 468 | 188 | 40.2% | 1.00 |  | 0.0 | Reference group |
| Age band vs under 40 | 40-49 | 82 | 30 | 36.6% | 0.91 | 0.625 | 2.9 | Passes 4/5, no significant difference (not proof of compliance) |
| Age band vs under 40 | 50-59 | 83 | 27 | 32.5% | 0.81 | 0.222 | 6.3 | Passes 4/5, no significant difference (not proof of compliance) |
| Age band vs under 40 | 60+ | 28 | 6 | 21.4% | 0.53 | 0.071 | 5.2 | Insufficient sample: report count only, do not interpret ratio |
| Disability proxy: interview accommodation | No request | 621 | 245 | 39.5% | 1.00 |  | 0.0 | Reference group |
| Disability proxy: interview accommodation | Requested accommodation | 40 | 6 | 15.0% | 0.38 | 0.002 | 9.8 | Fails 4/5 and statistically significant |
| National-origin proxy: English fluency | Native English | 598 | 230 | 38.5% | 1.00 |  | 0.0 | Reference group |
| National-origin proxy: English fluency | Non-native English | 63 | 21 | 33.3% | 0.87 | 0.496 | 3.2 | Passes 4/5, no significant difference (not proof of compliance) |
| Connection quality (non-protected) | Fair | 167 | 55 | 32.9% | 0.81 | 0.090 | 13.0 | Passes 4/5, no significant difference (not proof of compliance) |
| Connection quality (non-protected) | Good | 415 | 169 | 40.7% | 1.00 |  | 0.0 | Reference group |
| Connection quality (non-protected) | Poor | 79 | 27 | 34.2% | 0.84 | 0.316 | 5.2 | Passes 4/5, no significant difference (not proof of compliance) |

### Structured-interview applicants (comparison)

| Dimension | Group | Applicants | Hires | Rate | Impact ratio | Fisher p | Shortfall | Assessment |
|---|---|---|---|---|---|---|---|---|
| Race/ethnicity | Asian | 5 | 3 | 60.0% | 1.46 | 0.638 | -0.9 | Insufficient sample: report count only, do not interpret ratio |
| Race/ethnicity | Black or African American | 129 | 47 | 36.4% | 0.89 | 0.706 | 5.9 | Passes 4/5, no significant difference (not proof of compliance) |
| Race/ethnicity | Declined to self-identify | 13 | 6 | 46.2% | 1.12 | 0.757 | -0.7 | Not interpretable (no group identity) |
| Race/ethnicity | Hispanic or Latino | 39 | 16 | 41.0% | 1.00 |  | 0.0 | Reference group |
| Race/ethnicity | Native Hawaiian or Pacific Islander | 1 | 1 | 100.0% | 2.44 | 0.425 | -0.6 | Insufficient sample: report count only, do not interpret ratio |
| Race/ethnicity | Two or More Races | 6 | 1 | 16.7% | 0.41 | 0.385 | 1.5 | Insufficient sample: report count only, do not interpret ratio |
| Race/ethnicity | White | 96 | 36 | 37.5% | 0.91 | 0.702 | 3.4 | Passes 4/5, no significant difference (not proof of compliance) |
| Sex | Declined to self-identify | 8 | 3 | 37.5% | 0.97 | 1.000 | 0.1 | Not interpretable (no group identity) |
| Sex | Female | 103 | 38 | 36.9% | 0.95 | 0.799 | 1.9 | Passes 4/5, no significant difference (not proof of compliance) |
| Sex | Male | 178 | 69 | 38.8% | 1.00 |  | 0.0 | Reference group |
| Age (ADEA 40+) | 40 and over | 156 | 54 | 34.6% | 0.82 | 0.224 | 11.7 | Passes 4/5, no significant difference (not proof of compliance) |
| Age (ADEA 40+) | Under 40 | 133 | 56 | 42.1% | 1.00 |  | 0.0 | Reference group |
| Age band vs under 40 | Under 40 (pooled) | 133 | 56 | 42.1% | 1.00 |  | 0.0 | Reference group |
| Age band vs under 40 | 40-49 | 76 | 27 | 35.5% | 0.84 | 0.380 | 5.0 | Passes 4/5, no significant difference (not proof of compliance) |
| Age band vs under 40 | 50-59 | 49 | 17 | 34.7% | 0.82 | 0.398 | 3.6 | Passes 4/5, no significant difference (not proof of compliance) |
| Age band vs under 40 | 60+ | 31 | 10 | 32.3% | 0.77 | 0.416 | 3.1 | Fails 4/5, not statistically significant: monitor, aggregate more data |

### AEDT applicants, JG1 Material Handlers only

| Dimension | Group | Applicants | Hires | Rate | Impact ratio | Fisher p | Shortfall | Assessment |
|---|---|---|---|---|---|---|---|---|
| Race/ethnicity | American Indian or Alaska Native | 2 | 1 | 50.0% | 1.25 | 1.000 | -0.2 | Insufficient sample: report count only, do not interpret ratio |
| Race/ethnicity | Asian | 17 | 6 | 35.3% | 0.88 | 0.801 | 0.8 | Insufficient sample: report count only, do not interpret ratio |
| Race/ethnicity | Black or African American | 208 | 83 | 39.9% | 1.00 |  | 0.0 | Reference group |
| Race/ethnicity | Declined to self-identify | 23 | 8 | 34.8% | 0.87 | 0.823 | 1.2 | Not interpretable (no group identity) |
| Race/ethnicity | Hispanic or Latino | 63 | 22 | 34.9% | 0.88 | 0.555 | 3.1 | Passes 4/5, no significant difference (not proof of compliance) |
| Race/ethnicity | Native Hawaiian or Pacific Islander | 2 | 1 | 50.0% | 1.25 | 1.000 | -0.2 | Insufficient sample: report count only, do not interpret ratio |
| Race/ethnicity | Two or More Races | 15 | 7 | 46.7% | 1.17 | 0.599 | -1.0 | Insufficient sample: report count only, do not interpret ratio |
| Race/ethnicity | White | 158 | 57 | 36.1% | 0.90 | 0.515 | 6.0 | Passes 4/5, no significant difference (not proof of compliance) |
| Sex | Declined to self-identify | 13 | 4 | 30.8% | 0.80 | 0.772 | 1.0 | Not interpretable (no group identity) |
| Sex | Female | 175 | 65 | 37.1% | 0.96 | 0.769 | 2.7 | Passes 4/5, no significant difference (not proof of compliance) |
| Sex | Male | 300 | 116 | 38.7% | 1.00 |  | 0.0 | Reference group |
| Age (ADEA 40+) | 40 and over | 138 | 43 | 31.2% | 0.77 | 0.062 | 13.0 | Fails 4/5, not statistically significant: monitor, aggregate more data |
| Age (ADEA 40+) | Under 40 | 350 | 142 | 40.6% | 1.00 |  | 0.0 | Reference group |
| Disability proxy: interview accommodation | No request | 456 | 180 | 39.5% | 1.00 |  | 0.0 | Reference group |
| Disability proxy: interview accommodation | Requested accommodation | 32 | 5 | 15.6% | 0.40 | 0.008 | 7.6 | Fails 4/5 and statistically significant |
| National-origin proxy: English fluency | Native English | 442 | 166 | 37.6% | 0.91 | 0.634 | 16.6 | Passes 4/5, no significant difference (not proof of compliance) |
| National-origin proxy: English fluency | Non-native English | 46 | 19 | 41.3% | 1.00 |  | 0.0 | Reference group |
| Age band vs under 40 | Under 40 (pooled) | 350 | 142 | 40.6% | 1.00 |  | 0.0 | Reference group |
| Age band vs under 40 | 40-49 | 58 | 20 | 34.5% | 0.85 | 0.469 | 3.5 | Passes 4/5, no significant difference (not proof of compliance) |
| Age band vs under 40 | 50-59 | 61 | 21 | 34.4% | 0.85 | 0.397 | 3.7 | Passes 4/5, no significant difference (not proof of compliance) |
| Age band vs under 40 | 60+ | 19 | 2 | 10.5% | 0.26 | 0.008 | 5.7 | Small sample, but exact test is significant: treat as a finding, ratio is unstable |

### Where the gap enters: AEDT score vs skills test (standard deviations from the reference group)

| Dimension | Group | n | AEDT score | Skills test | Communication | Engagement | Problem solving |
|---|---|---|---|---|---|---|---|
| Race/ethnicity | Black or African American | 293 | -0.01 | +0.06 | +0.04 | -0.20 | +0.06 |
| Race/ethnicity | Hispanic or Latino | 88 | -0.18 | +0.05 | -0.31 | -0.15 | -0.00 |
| Sex | Male | 406 | -0.00 | +0.08 | +0.06 | +0.01 | -0.05 |
| Age (ADEA 40+) | 40 and over | 193 | -0.39 | -0.06 | -0.42 | -0.67 | +0.00 |
| Disability proxy: interview accommodation | Requested accommodation | 40 | -0.88 | +0.05 | -1.10 | -1.33 | +0.02 |
| National-origin proxy: English fluency | Non-native English | 63 | -0.30 | +0.10 | -0.77 | +0.03 | +0.04 |
| Age band | 40-49 | 82 | -0.35 | -0.07 | -0.33 | -0.31 | -0.20 |
| Age band | 50-59 | 83 | -0.54 | -0.15 | -0.54 | -0.95 | -0.01 |

**Subscore gaps with no matching skills-test gap** (a good overall selection rate does not excuse a biased component; *Connecticut v. Teal*):

- Race/ethnicity: Black or African American (n=293): engagement -0.20 SD vs skills test +0.06 SD.
- Race/ethnicity: Hispanic or Latino (n=88): communication -0.31 SD vs skills test +0.05 SD.
- Age (ADEA 40+): 40 and over (n=193): engagement -0.67 SD vs skills test -0.06 SD.
- Disability proxy: interview accommodation: Requested accommodation (n=40): engagement -1.33 SD vs skills test +0.05 SD.
- National-origin proxy: English fluency: Non-native English (n=63): communication -0.77 SD vs skills test +0.10 SD.
- Age band: 40-49 (n=82): communication -0.33 SD vs skills test -0.07 SD.

**Age note:** the ADEA protects workers 40 and over only, so younger bands are not tested against older ones. The four-fifths rule comes from the Uniform Guidelines, which do not govern ADEA claims; for age it is a screening signal, and the defense is a reasonable factor other than age.

## B. FLSA classification and overtime

- **Classification needs duties review:** 9 employees; 13-week exposure $7,986 to $30,016.
- **Misclassification (data-confirmed):** 7 employees; 13-week exposure $7,581 to $31,171.
- **Overtime underpayment (data-confirmed):** 79 employees; 13-week exposure $5,501 to $5,501.
  - Underpayments by site and shift: Southaven, MS 2nd shift: 33; Southaven, MS 3rd shift: 21; West Memphis, AR 2nd shift: 16; West Memphis, AR 3rd shift: 9.
- **Not flagged: 128 CDL-A drivers** averaging 53.0 hours/week with no overtime pay. That is consistent with the Motor Carrier Act exemption *if* they drive vehicles over 10,000 lbs in interstate commerce. Confirm both, and check state overtime law.

### Premium-overtime scheduling algorithm (active hourly employees it schedules)

| Group | n | Mean offers (group) | Mean offers (others) | Ratio | Reliability score (group / others) | Permutation p |
|---|---|---|---|---|---|---|
| Leave started in last 26 weeks | 20 | 3.4 | 7.44 | 0.46 | 61.8 / 83.6 | 0.0002 |
| Accommodation request on file | 17 | 4.06 | 7.33 | 0.55 | 71.9 / 82.5 | 0.0004 |
| Age 40+ | 54 | 6.7 | 7.2 | 0.93 | 82.1 / 81.6 | 0.3253 |
| Female | 84 | 7.58 | 6.79 | 1.12 | 80.3 / 82.5 | 0.0622 |
| Black or African American | 99 | 7.52 | 6.75 | 1.11 | 82.0 / 81.5 | 0.0724 |
| Hispanic or Latino | 27 | 6.74 | 7.13 | 0.95 | 79.6 / 82.0 | 0.5601 |

## C. Leave and accommodation sequences followed by discipline

| Request | Requesters | Disciplined in window | Comparison | Disciplined | Rate ratio | Fisher p |
|---|---|---|---|---|---|---|
| Leave (start through end + 90 days) | 82 | 57 (69.5%) | 371 | 75 (20.2%) | 3.44 | 0.0000 |
| Accommodation (120 days after request) | 40 | 23 (57.5%) | 413 | 101 (24.5%) | 2.35 | 0.0000 |
| Concerted activity (60 days after) | 27 | 23 (85.2%) | 426 | 65 (15.3%) | 5.58 | 0.0000 |

- **Discipline within 120 days of accommodation request: timing warrants review:** 7 employees.
- **Discipline within 90 days of leave: timing warrants review, not itself a violation:** 7 employees.
- **FMLA interference: attendance points assessed for FMLA-protected absences:** 17 employees.
- **Performance discipline that cites the accommodation itself: standard not adjusted (ADA failure to accommodate / retaliation risk):** 16 employees.
- **Points assessed during non-FMLA medical leave: review as possible ADA leave-as-accommodation or state-law issue:** 33 employees.

## D. NLRA Section 7 risk in discipline narratives

- **Excluded if a statutory supervisor: verify actual authority (title alone does not decide):** 1 events (1 with a concerted-activity flag on file).
- **High: likely protected concerted activity:** 20 events (20 with a concerted-activity flag on file).
- **Low: conduct likely unprotected:** 14 events (0 with a concerted-activity flag on file).
- **Low: individual gripe (protected only if it seeks group action):** 15 events (0 with a concerted-activity flag on file).
- **Work-rule risk:** 3 discipline narratives enforce a "pay confidentiality policy." A rule that bars employees from discussing pay is itself a Section 7 risk, separate from any one discipline decision.
