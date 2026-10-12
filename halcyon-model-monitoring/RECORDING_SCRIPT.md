# Recording script: claims-triage fairness monitor

**Length:** about 12 minutes · **Audience:** Renee Okafor, Chief Actuary, and the AI
Governance Committee · **Presenter:** Model Risk Analyst

**How to use this script**

- **SCREEN** is what to show.
- **SAY** is what to say. It is written to be read aloud, but put it in your own words.
- **POINT** marks the one idea each scene must land.
- Every number here comes from the committed data, and the live run will reproduce it.

**Before you hit record**

```bash
cd halcyon-model-monitoring
pip install -r requirements.txt
DEMO_NOPAUSE=1 bash demo/run_demo.sh > /dev/null   # rehearsal: warms caches, checks it runs (~30 s)
```

Open these in tabs, in this order:

1. this conversation, scrolled to your first prompt
2. a terminal in `halcyon-model-monitoring/`
3. `reports/2026-09/flag_summary_2026-09.md`
4. `reports/2026-09/chart_disparity_ratios.png`
5. `reports/2026-07/chart_drift_vs_baseline.png`
6. `INCIDENT_RESPONSE.md`

Then run `bash demo/run_demo.sh` in the terminal. It pauses before each step; press
Enter when the script below says **[Enter]**.

---

## Scene 0: Opening (0:00–0:40)

**SCREEN:** `README.md`, top of the page.

**SAY:**
> "Renee, this is the monthly fairness check for the claims-triage model, built so the
> governance committee can run it without an engineer. In the next ten minutes I'll show
> you four things:
>
> - exactly what I asked the AI agent to build;
> - a real mistake it made, and how I caught it;
> - a live run on six months of data;
> - what the results mean, and what they don't.
>
> One thing up front: the claims data is synthetic. I designed a bias into it on purpose,
> so we can see whether the tool finds it."

**POINT:** The data is synthetic and the bias was planted. Say it in the first minute.

---

## Scene 1: The prompts I actually typed (0:40–2:10)

**SCREEN:** this conversation. Scroll slowly through the three prompts, then switch to the
terminal. **[Enter]** runs `git log`.

**SAY:**
> "These are my prompts, unedited.
>
> The first asked for a synthetic claims dataset: at least 5,000 rows over six months,
> with a proxy-bias pathway I designed. You'll see it stops mid-sentence, at a semicolon.
> I'm leaving it that way rather than tidying it up after the fact. The agent noticed it
> was cut off, said so, and built the monitoring tool as the natural next step.
>
> The second asked for an analyzer covering five things:
>
> - selection rates by group;
> - a four-fifths-rule disparity ratio;
> - false-investigation rates;
> - drift against a rolling three-month baseline;
> - charts and a one-page summary.
>
> The third asked for an incident-response table and for this walkthrough.
>
> In git, each prompt became a commit. There's one fix commit for the bug I'm about to
> show you, and one small edit after that."

**SAY**, while `git log` is on screen:
> "The planted bias works like this. The model uses an input called `zip_risk_index`. It
> measures how often each ZIP area was referred to the investigations unit in the past.
> In higher-minority areas that number is inflated by old referral habits, not by more
> fraud. In the data I generated, actual fraud does not depend on ZIP at all.
>
> On July 1 a model refresh increased the weight on that input. I also built in a
> legitimate difference: those areas have somewhat older cars, newer policies and larger
> claims. That's so the tool has to tell a real gap from an explained one."

**POINT:** The prompts are unedited, and the bias pathway is known, so we can check
whether the tool finds it.

---

## Scene 2: Where the agent got it wrong (2:10–4:40)

**SCREEN:** terminal. **[Enter]** builds the test extract.

**SAY:**
> "Now the most important part, because you shouldn't trust a tool you haven't seen fail.
>
> I gave the analyzer a stress test: a claims file where 150 September claims carry a
> ZIP3, 486, that isn't in our reference table. That happens in real life after a
> territory expansion or a postal re-zoning."

**[Enter]** runs the BEFORE version.

**SAY:**
> "This is the analyzer as the agent first built it. Look at the summary header: 857
> claims. The file has 1,007. A hundred and fifty claims are gone. No warning, no error.
>
> And all 150 came from higher-minority areas, so a third of the group we're monitoring
> vanished. In this test the headline ratio barely moved, but that was luck. If those
> had been the worst-treated claims, the report would have looked better than reality,
> and nothing on the page would have told us."

**SAY** (how it was caught):
> "I caught it by checking the claim count in the summary against the source file. That
> one check is now built into the tool."

**[Enter]** runs the AFTER version.

**SAY:**
> "Here's the fixed version on the same file.
>
> - A warning: only 857 of 1,007 claims could be assigned to a group.
> - A Data flag that names the missing ZIP3.
> - If 1% or more of a month's claims can't be assigned, the incident table holds that
>   month's summary until the data is fixed."

**[Enter]** runs the regression test.

**SAY:**
> "And a test, so this can't come back quietly.
>
> It wasn't the only mistake. The agent labelled one measure 'legitimate claims
> investigated' when the denominator was really 'claims not confirmed as fraud'. That
> includes fast-pay claims nobody ever looked at. It also attached the investigation
> ratio's explanation to a fast-pay flag. And for a while the two tools gave different
> verdicts on the same number. Each of those was caught by reading the output line by
> line against the definitions, and each is fixed."

**POINT:** Check the counts and read the labels against their definitions. A clean-looking
report can still be wrong.

---

## Scene 3: Live run (4:40–7:30)

**SCREEN:** terminal. **[Enter]** runs the full test suite.

**SAY:**
> "Fourteen tests, about twenty seconds. They check three things:
>
> - the tool finds the bias I planted;
> - it catches the July refresh;
> - it does not raise a flag on control data where the bias is switched off. That last
>   one matters as much as the first."

**[Enter]** runs the September analyzer.

**SAY:**
> "This is the September run, live. Incident tier: SEV-1, the top tier. Two flags.
>
> First: claims from higher-minority areas are sent to investigation 27.5% of the time,
> against 7.0% elsewhere. That's 3.9 times as often. The four-fifths ratio is 0.26, and
> anything under 0.80 fails.
>
> And this is the line I care about. After adjusting for claim size, tenure, vehicle age
> and prior claims, the gap is still 3.1 times, with a confidence interval of 2.5 to 3.8.
> The claims themselves don't explain it.
>
> Second: 115 of the 128 investigations in those areas, 90%, found no fraud. Elsewhere
> it's 68%.
>
> Fast-pay looks bad raw, 20% against 35%. After adjustment, though, what's left isn't
> statistically significant, so it's on watch, not flagged."

**[Enter]** runs the monitor cross-check.

**SAY:**
> "The second tool agrees: RED on the risk-adjusted referral ratio and on the hit rate.
> The proxy screen names one input, `zip_risk_index`. It separates the two groups of
> areas almost completely, but it doesn't track confirmed fraud. That's the signature of
> a proxy."

**[Enter]** runs July.

**SAY:**
> "July is the refresh month. Against the April-to-June baseline, the investigation rate
> in those areas jumps from 14.2% to 27.8%, and the four-fifths ratio falls from 0.40 to
> 0.22. The drift flags caught the refresh in its first month."

**SCREEN:** open `chart_disparity_ratios.png`, then `chart_drift_vs_baseline.png`.

**SAY:**
> "On this chart, the dashed red line is the four-fifths threshold. The blue line is
> higher-minority areas, and it was below the line in April, before the refresh. The
> refresh made it worse; it didn't start it.
>
> And a warning about drift. By September the drift flags have gone quiet, because the
> three-month baseline now contains the higher level. Quiet drift does not mean fixed.
> That's why the disparity checks run every month regardless."

**POINT:** It's SEV-1, and it predates the refresh. Quiet drift doesn't mean fixed.

---

## Scene 4: What it means for you, Renee (7:30–9:00)

**SCREEN:** `flag_summary_2026-09.md`, then `INCIDENT_RESPONSE.md`, section 2, the SEV-1 row.

**SAY:**
> "Renee, here's the summary the committee would get. It's one page, written in plain
> language, with the action at the top.
>
> Under the incident table, SEV-1 pages you, the model owner, the Chief Compliance
> Officer and the SIU Director. We have four business hours to acknowledge.
>
> Within one business day, three protections for claimants:
>
> - a senior adjuster takes a second look at every investigation referral, in every
>   area, so the safeguard doesn't itself treat people differently by location;
> - no denial based on an investigation without the SIU Director's sign-off;
> - anyone waiting more than 30 days gets a call, and any undisputed amount is paid.
>
> Within five days, the proxy input is neutralised under emergency change control.
>
> Rolling back to the July model isn't a fix. The older version was already SEV-1 in
> May. Run against these rules, the incident would have opened in May, two months
> before the refresh."

**POINT:** There's a named action, an owner and a clock. Rollback is not the fix.

---

## Scene 5: What these numbers do NOT prove (9:00–11:20)

**SCREEN:** `RECORDING_GUIDE.md`, the section "What these numbers do NOT prove".

**SAY:**
> "Now the limits, which matter as much as the findings.
>
> **One.** This is synthetic data with a bias I planted. Today proves the tool can find
> a pathway we know exists. It says nothing yet about our production model. That needs a
> run on the real extract.
>
> **Two.** 'Higher-minority' is a label for a ZIP area, based on census estimates. We
> cannot say any individual claimant was treated differently because of their race.
>
> **Three.** The risk adjustment covers four factors. On real data, something missing
> from the extract, like loss type, injury or attorney involvement, could explain part
> of a gap.
>
> **Four.** The false-investigation comparison is partly a selection effect. Elsewhere,
> only the most extreme claims get investigated, so of course more of them turn out to
> be fraud. That comparison also rests on just 38 investigations, plus or minus about
> 15 points. The risk-adjusted referral ratio is the stronger evidence.
>
> **Five.** 'No fraud found' does not mean 'honest'. Investigations miss fraud, and
> fast-pay claims are never examined.
>
> **Six.** The proxy screen shows association, not cause. The proof that
> `zip_risk_index` drives the gap is to neutralise it, re-score and re-run. On a real
> model, that hasn't been done yet.
>
> **Seven.** The four-fifths rule is a screening heuristic from employment law. It is
> not the legal standard for insurance. A flag is a reason to investigate, not a finding
> of unfair discrimination. That's for Compliance and Legal.
>
> **Eight.** Each monthly run makes 15 to 20 statistical comparisons, so expect about
> one false flag a month by chance. That's why a WATCH only escalates if it repeats.
>
> **Nine.** No dollar figure for harm. The remediation lookback is what would put a
> number on that."

**POINT:** This validates the tool, not a finding about our real model. It's an
area-level signal, not proof about any individual, and a screen, not a legal
determination.

---

## Scene 6: Close and the ask (11:20–12:00)

**SCREEN:** `README.md`, the section "Monthly routine".

**SAY:**
> "To run it each month: drop in the extract, run two commands, and read one page. No
> engineer required.
>
> Three asks:
>
> 1. Approve the incident table as written, or tell me what to change.
> 2. Approve a first run on the real September extract, with the ZIP reference table
>    rebuilt from actual census data.
> 3. Authorise the neutralise-and-re-run test on the production model. That's the test
>    that turns 'likely proxy' into evidence.
>
> Thank you."

---

## If Renee asks…

| Question | Answer |
|---|---|
| "Is our real model biased?" | "We don't know yet. Today shows the tool works on data where we know the answer. The production run is ask number two." |
| "Why not just remove `zip_risk_index`?" | "That's control (d) in the incident table. But in a real incident we'd re-score and re-run first, to confirm it's the cause and that removing it doesn't make fraud detection worse." |
| "Why does the tool say fast-pay is only WATCH when 20% vs 35% fails four-fifths?" | "Most of that gap is explained by claim size: in this model, fast-pay is only open to claims of $3,500 or less. What's left after adjustment, a ratio of 0.81, isn't statistically significant this month. If it stays on WATCH next month, it escalates." |
| "Could this flag be a fluke?" | "Not this one. The adjusted ratio's confidence interval is 2.5 to 3.8, and the investigation gap has been flagged every month since April. Individual WATCH items can be chance, which is why they need to repeat." |
| "Who maintains it?" | "Thresholds live in one settings file, `thresholds.json`, that the committee can edit. The tests run in about 20 seconds and fail if the tool stops finding the planted bias or starts flagging the control data." |
| "What if the data feed is incomplete?" | "That's the bug from scene 2. The tool now refuses to stay quiet about it: a Data flag, and the month's summary is held until the extract is fixed." |
