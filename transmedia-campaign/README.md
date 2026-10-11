# Low Battery: a transmedia campaign planner for Tend

A pitch and a working tool for launching **Tend**, a mental wellness app for Millennial and Gen Z audiences. It tells one brand story across six channels and is built for a small team on a limited budget.

- `index.html` is the planning dashboard. It is also published as a Claude artifact, where team sync and Claude drafting are switched on.
- `standalone.html` is the same page wrapped as a full document so you can open it straight from disk. Regenerate it with `./build-standalone.sh`.

## The campaign architecture

**Big idea.** We treat our phones at 2% better than we treat ourselves. When a phone hits low battery, we notice it and plug it in. When *we* hit low battery, we type "lol I'm fine".

**Tend line.** You don't have to be fully charged. Just tend to it.

**Core narrative.** Three roommates share one group chat ("house plants") and one dying houseplant named Gerald. Over six weeks they stop pretending they're fine.

| Character | Low on | Arc |
|---|---|---|
| Jules, 24, grad student + barista | Productivity guilt | Writes "rest" on the to-do list, and means it |
| Dev, 27, remote designer | Social anxiety | Finally sends the message he keeps deleting |
| Sam, 22, new in town | Loneliness, 2am scrolling | Builds one small ritual and one real connection |
| Gerald, a houseplant | Water | One new leaf. Every user grows their own in the app |

**Six beats, one per week**

| Week | Act | Beat | What it does for the audience |
|---|---|---|---|
| 1 | Setup | 2% | Recognition: they see themselves in the characters |
| 2 | Setup | What's draining you | Naming: gives them words for what drains them |
| 3 | Turn | The unsent message | Permission: shows that saying "I'm not okay" is survivable |
| 4 | Turn | Small charges | Possibility: tiny practices, with Tend as a tool rather than a savior |
| 5 | Real life | Low days still count | Realism: progress isn't a straight line |
| 6 | Real life | Tending, not fixed | Invitation: the audience sends their own unsent message |

**Each channel has its own job in the story.** Nothing is reposted from one channel to another.

| Channel | Job | Format |
|---|---|---|
| TikTok | Discovery: the serialized story | 30–45s episode + 2 cutdowns |
| Instagram Stories | Participation: the inner monologue, and the audience votes on what's canon | 5–7 frames with a poll, slider or question box |
| YouTube | Depth: credentialed experts unpack the week's theme | 6–10 min feature + 2 Shorts |
| Email | Intimacy: "the drafts folder", letters built from unsent messages | 250–400 words, one practice |
| In-app | Habit: check-ins and 3-minute sessions that mirror the beat | Prompts, one session, microcopy |
| Creator collabs | Amplification: micro-creators stitch and duet each episode | Creator brief + do/don't sheet |

**Story threads** run between channels, so people who follow more than one channel get rewarded for it: Gerald the plant, Dev's unsent message, Jules's to-do list, Sam's 2am scroll, and the group chat's name. Each thread has a setup, development and a payoff, and the tool warns you if a payoff gets approved before its setup.

## What the tool does

1. **Story map.** A grid of weeks against channels. Each cell is one piece, with a battery that fills by workflow stage, its thread markers, its publish date and its owner. You can filter by thread or by owner, and set the launch date.
2. **Story threads.** Shows how each thread moves across weeks and channels. It flags continuity problems (a payoff approved before its setup) and overdue pieces that would break a thread.
3. **AI + human workflow.** A kanban board running Brief → First draft (AI) → Human edit → Review → Approved → Live. Each piece moves forward through gates:
   - A piece can't be approved without a voice score of 70+, zero critical issues, and clinical sign-off.
   - Editing an approved piece sends it back to Review.
   - A capacity chart compares weekly hours by role with and without AI against the team's capacity. In week 1, that's about 37.5h with AI and about 65h without, against 54h of capacity.
4. **Voice check.** The voice bible (persona, five pillars with say/not examples, words to swap, safety guardrails), voice settings for each channel, and a live checker for any copy. The rule check runs instantly with no AI. It catches:
   - banned words and clinical claims
   - "you should" phrasing
   - streak shame and false urgency
   - crisis topics that don't include the 988 line
   - creator posts missing the #ad disclosure
   - too many emoji, hashtags or exclamation marks
5. **Campaign architecture.** The strategy itself: insight, characters, how the channels connect, who does what between AI and people, and how to produce it on a small budget ("shoot once, cut many").

**Briefs.** Open any piece to get a content brief, built automatically. It covers:
- the objective
- the story so far
- continuity with every connected piece, including where each one is in the workflow
- voice settings and limits for the channel
- mandatories (CTA, 988 line, disclosure)
- what AI drafts and what a person must own
- KPIs and a review checklist

From the brief you can:
- **Draft with Claude** (inside Claude), which streams a first draft and then runs the voice check on it
- **Copy AI prompt** to use the same brief in any AI tool
- **Ask Claude for a voice read**, a second opinion on tone and safety

## Where data lives

- **Published as a Claude artifact:** workflow stage, owner, drafts, notes and sign-offs are stored in the artifact's shared database, so the whole team sees the same plan live. Claude drafting uses each viewer's own Claude account.
- **Opened from disk:** everything saves to that browser only, and AI drafting is replaced by "Copy AI prompt".
