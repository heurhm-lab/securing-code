# Recording guide: walkthrough for Renee Okafor

A running order for the screen recording. Every prompt, error and number below comes
from the actual session and the committed code. Nothing here is a mock-up.

---

## Scene 1: The prompts as typed

Show these verbatim, including the first prompt cut off at a semicolon.
The agent filled in the rest of that first task itself, and said so at the time.

**Prompt 1: the dataset**
> You are a Model Risk Analyst at Halcyon Insurance, a regional auto insurer operating in four states, whose claims-severity triage model routes incoming claims to fast-pay, standard, or investigation queues. Chief Actuary Renee Okafor needs a lightweight monitoring tool the AI governance committee can run themselves each month without pulling an engineer off the pricing roadmap. Have the agent generate your own synthetic claims dataset of at least 5,000 rows spanning six months, with claim amount, ZIP-code proxy, vehicle age, policy tenure, adjuster queue assignment, and final outcome, and with a proxy-bias pathway you deliberately design so there is something real to detect;

**Prompt 2: the analyzer**
> direct the agent to build a monitoring analyzer that computes group-level selection rates, a four-fifths-rule style disparity ratio, false-investigation rates by group, and month-over-month drift against a rolling three-month baseline, saving chart PNGs plus a plain-language one-page flag summary;

**Prompt 3: incident response and this recording**
> write an incident-response trigger table specifying which metric thresholds page whom, within what response clock, and what interim action protects claimants while the flag is investigated. In your recording, show the prompts you actually typed, show at least one place the agent got it wrong (silently dropped a group, mislabeled a denominator, or produced a ratio that cannot be right) and how you caught and corrected it, run the analyzer live, and interpret the output for Renee — including what your numbers do NOT prove.

Git history to show beside them: `git log --oneline`. That gives one commit per prompt, plus
the fix commit for scene 2.

---

## Scene 2: Where the agent got it wrong

These all happened in this session. Lead with **E1** on camera, because it is the one
the brief names ("silently dropped a group") and it reproduces in about 30 seconds.
Mention E2 to E4 in one sentence each.

### E1: Claims silently dropped from the comparison (on camera)

- **What went wrong.** The first `analyzer.py` filtered out every claim whose ZIP3 was
  not in `zip_reference.csv`. It did that with `df[df[group_col].notna()]` and gave no
  warning, so those claims disappeared from every rate, ratio and chart.
  `monitor.py` reported unmapped ZIPs. The analyzer did not.
- **How it was caught.** I stress-tested the extract with a new ZIP3 (486, the kind
  of thing a territory expansion or a USPS re-zoning produces). The flag summary header
  said **857 claims**, but the file holds **1,007** for September.
- **Why it matters.** All 150 dropped claims came from higher-minority areas. That is a
  third of the monitored group (466 claims down to 316), gone without a trace.
  In this demo the dropped claims were a random sample, so the headline ratio barely
  moved (3.07× to 3.34×). The danger is that nothing said the claims were missing.
  If the dropped claims had been the worst-treated ones, the ratios would have looked
  better than reality, and nobody would have known.
- **The fix.** The fix is in commit `3b98e9f`.
  - The console prints `WARNING: only 857 of 1,007 claims could be assigned to a group`.
  - The summary header reads "1,007 claims, **only 857 analysed**".
  - A Data FLAG names the unmapped ZIP3s.
  - At 1% or more unmapped, the month goes to SEV-2 (data) and the summary is held
    (`INCIDENT_RESPONSE.md`, row D1).
  - A regression test covers it: `test_unmapped_zip_claims_are_reported_not_silently_dropped`.

Reproduce it live, before and after:

```bash
cd halcyon-model-monitoring
python3 demo/make_unmapped_extract.py /tmp/claims_unmapped.csv

# BEFORE: the analyzer as first built (commit 37259c6)
git show 37259c6:halcyon-model-monitoring/analyzer.py > /tmp/analyzer_before_fix.py
PYTHONPATH=. python3 /tmp/analyzer_before_fix.py --claims /tmp/claims_unmapped.csv --out-dir /tmp/before
grep -o "[0-9,]* claims  ·" /tmp/before/flag_summary_2026-09.md     # -> "857 claims", no warning

# AFTER: the current analyzer
python3 analyzer.py --claims /tmp/claims_unmapped.csv --out-dir /tmp/after
# -> WARNING: only 857 of 1,007 claims ...   and   [FLAG ] Data: 150 of 1,007 claims (14.9%) ...
```

### E2: Mislabelled denominator

The analyzer had a drift metric labelled **"Legitimate claims investigated"**. Its
denominator was every claim *not confirmed as fraud*. That includes fast-pay claims
nobody ever examined, so undetected fraud is in there too. "Not confirmed as fraud" is
not the same as "legitimate".

- **Caught by:** reading the code against the label.
- **Fixed by:** renaming it to "Investigated, of claims not confirmed as fraud" and
  adding a comment explaining the denominator.

### E3: A ratio carrying the wrong metric's explanation

A fast-pay flag ended with *"the investigation gap is still 3.1×"*. The text described
the investigation ratio, not fast-pay.

- **Caught by:** reading the console output line by line.
- **Fixed by:** giving fast-pay its own risk adjustment. The real number is 0.81 (CI
  0.65–1.01), which is not significant, so the flag is WATCH, not FLAG.

### E4: Two tools, two verdicts on one number

For the same September fast-pay ratio of 0.57, `monitor.py` said RED and `analyzer.py`
said WATCH. The monitor was checking whether the *investigation* gap was explained.

- **Fixed by:** making both tools apply the same rule. Each raw ratio is judged against
  its own risk adjustment.

Also worth a sentence if time allows: the first four-fifths screen raised full FLAGs on
**control data with the bias switched off**. Higher-minority areas legitimately have larger
claims and newer policies. That is why every disparity flag is now risk-adjusted, and
the control run never reaches FLAG (a test enforces this). The first draft of the
incident page also said the incident would have opened in July. When checked, it opens
in **May**, under the old model version.

---

## Scene 3: Run it live

```bash
cd halcyon-model-monitoring
pip install -r requirements.txt
python3 -m unittest discover -s tests      # 14 tests, about 20 seconds
python3 analyzer.py                         # September: tier SEV-1
python3 monitor.py                          # cross-check: RED, proxy = zip_risk_index
python3 analyzer.py --month 2026-07         # the refresh month: drift flags fire
```

Then open, in order:
1. `reports/2026-09/flag_summary_2026-09.md`
2. `reports/2026-09/chart_selection_rates.png`
3. `reports/2026-09/chart_disparity_ratios.png`
4. `reports/2026-07/chart_drift_vs_baseline.png`
5. `INCIDENT_RESPONSE.md`, section 4

---

## Scene 4: What to tell Renee

### What the September run says

> "This is a SEV-1.
>
> In September, claims from higher-minority ZIP areas went to investigation **27.5%** of
> the time, against **7.0%** elsewhere. That is a four-fifths impact ratio of **0.26**;
> the rule's line is 0.80.
>
> It isn't explained by the claims themselves. After matching on claim size, tenure,
> vehicle age and prior claims, they are still investigated **3.1×** as often. The 95%
> confidence interval is 2.5 to 3.8, so it is nowhere near parity.
>
> Those investigations mostly find nothing: **115 of 128**, or 90%, ended without
> confirmed fraud, against 68% elsewhere.
>
> The input driving it is `zip_risk_index`. It separates the two groups of areas
> almost perfectly but doesn't track confirmed fraud within either group.
>
> It didn't start with the July refresh. It was already SEV-1 in **May** under v2.3, and
> the refresh roughly doubled the gap. The drift flags have gone quiet since August only
> because the three-month baseline now includes the new level.
>
> Fast-pay looks bad raw, 20% against 35%. Most of that is explained by claim size,
> though, and what is left isn't significant, so it stays on watch.
>
> Under the incident table, that pages you, the model owner, Compliance and the SIU
> Director. A second look on every referral and a hold on investigation-based denials
> go in within one business day."

### What these numbers do NOT prove

Say these out loud. They are the difference between a monitoring signal and a finding.

1. **This data is synthetic, and the bias was planted on purpose.** The run proves the
   tool finds a pathway we know is there. It says nothing yet about Halcyon's real
   model. That needs a run on the production extract.
2. **ZIP areas are not people.** "Higher-minority" is an area label from census
   estimates. We cannot say any individual claimant was treated differently because of
   their race. The evidence is about areas.
3. **Risk adjustment covers only four factors.** Claim size, tenure, vehicle age and
   prior claims. On real data, a legitimate factor that is not in the extract (loss
   type, injury, attorney involvement) could explain part of the remaining gap. Here we
   know it can't, because we wrote the generator.
4. **The false-investigation comparison is partly a selection effect.** In "other"
   areas only the most extreme claims are investigated, so their hit rate is naturally
   higher; this is the infra-marginality problem. The "other" figure also rests on just
   **38** investigated claims (about ±15 points). The risk-adjusted referral ratio is the
   stronger evidence. The hit rate supports it but does not prove it on its own.
5. **"No confirmed fraud" does not mean "honest".** Investigations miss fraud, and
   fast-pay claims are never examined at all. A withdrawn claim isn't proof the claim
   was valid.
6. **The proxy screen shows association, not cause.** It shows that `zip_risk_index`
   tracks area, not fraud. Proof that it *drives* the gap comes from control (d): set it
   to neutral, re-score and re-run. That has not been done on a real model.
7. **The four-fifths rule is a screening heuristic from US employment law, not a legal
   standard for insurance.** A FLAG is a reason to investigate. It is not a finding of
   unfair discrimination; that is Compliance and Legal's call.
8. **Some flags will be chance.** Each monthly run of both tools makes about 15–20 statistical comparisons at
   p < 0.05, so expect about one spurious WATCH or FLAG a month. That is why WATCH
   only escalates after two months running.
9. **A quiet drift flag does not mean the problem is fixed.** The rolling baseline
   absorbs a lasting shift within about three months.
10. **No dollar figure for harm.** The tool counts delays, withdrawals and
   investigations. The lookback in control (f) is what would put a number on
   claimant harm.
