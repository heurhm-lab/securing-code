#!/usr/bin/env python3
"""
Halcyon claims-triage fairness monitor -- monthly run for the AI Governance Committee.

    python3 monitor.py                    # latest month in data/claims.csv
    python3 monitor.py --month 2026-08    # a specific month

Reads the claims extract and the ZIP3 reference table, compares claims from
higher-minority ZIP3s with all other ZIP3s, and writes:

    reports/fairness_report_<month>.html   plain-English report with RAG status
    reports/fairness_metrics_<month>.csv   every number in the report, for the minutes

Only needs Python 3.9+ with pandas and numpy. Thresholds live in thresholds.json.
"""
import argparse
import html
import json
import math
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REQUIRED = ["claim_id", "month", "zip3", "claim_amount", "vehicle_age_years", "policy_tenure_years",
            "prior_claims_3yr", "model_score", "queue_assignment", "final_outcome", "days_to_close"]
QUEUES = {"fast_pay", "standard", "investigation"}
OUTCOMES = {"paid_in_full", "paid_adjusted", "denied_fraud_confirmed", "withdrawn_by_claimant"}
STATUS_ORDER = {"green": 0, "grey": 1, "amber": 2, "red": 3}


# --------------------------------------------------------------------------- data

def load(claims_path, zip_path):
    claims = pd.read_csv(claims_path, dtype={"zip3": str, "month": str})
    zref = pd.read_csv(zip_path, dtype={"zip3": str})
    missing = [c for c in REQUIRED if c not in claims.columns]
    if missing:
        sys.exit(f"ERROR: claims file is missing required columns: {', '.join(missing)}")
    claims["zip3"] = claims["zip3"].str.zfill(3)
    zref["zip3"] = zref["zip3"].str.zfill(3)
    df = claims.merge(zref[["zip3", "community_group"]], on="zip3", how="left")
    df["is_inv"] = df["queue_assignment"] == "investigation"
    df["is_fast"] = df["queue_assignment"] == "fast_pay"
    df["is_confirmed"] = df["final_outcome"] == "denied_fraud_confirmed"
    df["is_withdrawn"] = df["final_outcome"] == "withdrawn_by_claimant"
    return df


def data_quality(m):
    issues = []
    nulls = m[REQUIRED].isna().sum()
    for col, n in nulls[nulls > 0].items():
        issues.append(f"{n} claims have a blank '{col}'")
    if (n := m["community_group"].isna().sum()):
        issues.append(f"{n} claims have a ZIP3 not in the reference table (excluded from comparisons)")
    if (n := (~m["queue_assignment"].isin(QUEUES)).sum()):
        issues.append(f"{n} claims have an unrecognised queue value")
    if (n := (~m["final_outcome"].isin(OUTCOMES)).sum()):
        issues.append(f"{n} claims have an unrecognised outcome value")
    if (n := ((m["model_score"] < 0) | (m["model_score"] > 1)).sum()):
        issues.append(f"{n} claims have a model score outside 0-1")
    if (n := m["claim_id"].duplicated().sum()):
        issues.append(f"{n} duplicate claim IDs")
    return issues


# --------------------------------------------------------------------------- statistics

def ratio(a, b):
    return a / b if b else float("nan")


def two_prop_p(x1, n1, x2, n2):
    """Two-sided p-value for a difference in two proportions (normal approximation)."""
    if min(n1, n2) == 0:
        return float("nan")
    p = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return 1.0
    z = abs(x1 / n1 - x2 / n2) / se
    return math.erfc(z / math.sqrt(2))


def add_strata(m):
    """Bands for the legitimate risk factors the model is allowed to use."""
    s = m.copy()
    s["amt_band"] = pd.qcut(s["claim_amount"], 4, labels=False, duplicates="drop")
    s["tenure_band"] = pd.cut(s["policy_tenure_years"], [-1, 1, 3, 1e9], labels=False)
    s["veh_band"] = pd.cut(s["vehicle_age_years"], [-1, 4, 10, 1e9], labels=False)
    s["prior_band"] = (s["prior_claims_3yr"] > 0).astype(int)
    return s


def risk_adjusted_ratio(m, target, ref):
    """
    Indirect standardisation: how many monitored-group claims WOULD have gone to
    investigation if each were treated like a reference-group claim with the same
    claim size, tenure, vehicle age and prior-claims band? Ratio = observed / expected.
    """
    s = add_strata(m)
    keys = ["amt_band", "tenure_band", "veh_band", "prior_band"]
    ref_rates = s[s["community_group"] == ref].groupby(keys)["is_inv"].agg(["mean", "size"])
    ref_rates = ref_rates[ref_rates["size"] >= 5]["mean"].rename("ref_rate")
    t = s[s["community_group"] == target].join(ref_rates, on=keys)
    covered = t["ref_rate"].notna()
    observed = int(t.loc[covered, "is_inv"].sum())
    expected = float(t.loc[covered, "ref_rate"].sum())
    r = ratio(observed, expected)
    if observed > 0 and expected > 0:
        half = 1.96 / math.sqrt(observed)
        lo, hi = r * math.exp(-half), r * math.exp(half)
    else:
        lo = hi = float("nan")
    return {"observed": observed, "expected": expected, "ratio": r, "ci_low": lo, "ci_high": hi,
            "coverage": float(covered.mean()) if len(t) else float("nan")}


def psi(base, cur, bins=10):
    edges = np.unique(np.quantile(base, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    b = np.histogram(base, edges)[0] / len(base)
    c = np.histogram(cur, edges)[0] / len(cur)
    b, c = np.clip(b, 1e-4, None), np.clip(c, 1e-4, None)
    return float(np.sum((c - b) * np.log(c / b)))


def group_stats(m, group):
    g = m[m["community_group"] == group]
    inv = g[g["is_inv"]]
    return {
        "claims": len(g),
        "investigated": int(g["is_inv"].sum()),
        "investigation_rate": g["is_inv"].mean() if len(g) else float("nan"),
        "fast_pay_rate": g["is_fast"].mean() if len(g) else float("nan"),
        "confirmed_in_investigation": int(inv["is_confirmed"].sum()),
        "investigation_hit_rate": inv["is_confirmed"].mean() if len(inv) else float("nan"),
        "withdrawn": int(g["is_withdrawn"].sum()),
        "withdrawal_rate": g["is_withdrawn"].mean() if len(g) else float("nan"),
        "median_days_to_close": float(g["days_to_close"].median()) if len(g) else float("nan"),
        "mean_model_score": g["model_score"].mean() if len(g) else float("nan"),
        "confirmed_fraud_rate_all_claims": g["is_confirmed"].mean() if len(g) else float("nan"),
    }


def proxy_screen(m, features, target, ref, cfg):
    rows = []
    for f in features:
        if f not in m.columns:
            continue
        a = m.loc[m["community_group"] == target, f]
        b = m.loc[m["community_group"] == ref, f]
        pooled = math.sqrt((a.var() + b.var()) / 2) or float("nan")
        smd = (a.mean() - b.mean()) / pooled
        # Association with confirmed fraud measured WITHIN each group, so that a
        # feature cannot look "predictive" merely because it separates the groups.
        cors = []
        for grp in (target, ref):
            g = m[m["community_group"] == grp]
            if g[f].std() > 0 and g["is_confirmed"].std() > 0:
                cors.append((g[f].corr(g["is_confirmed"].astype(float)), len(g)))
        within = sum(c * n for c, n in cors) / sum(n for _, n in cors) if cors else float("nan")
        likely_proxy = abs(smd) >= cfg["group_separation_smd"] and abs(within) < cfg["max_within_group_fraud_correlation"]
        rows.append({"feature": f, "group_separation_smd": smd, "within_group_fraud_corr": within,
                     "likely_proxy": bool(likely_proxy)})
    return rows


def rag(value, rule, enough_data=True):
    if not enough_data or value is None or (isinstance(value, float) and math.isnan(value)):
        return "grey"
    if rule["direction"] == "high":
        return "red" if value >= rule["red"] else "amber" if value >= rule["amber"] else "green"
    return "red" if value <= rule["red"] else "amber" if value <= rule["amber"] else "green"


# --------------------------------------------------------------------------- monthly metrics

def month_metrics(df, month, cfg, baseline_month):
    target, ref = cfg["monitored_group"], cfg["reference_group"]
    m = df[df["month"] == month]
    comp = m[m["community_group"].notna()]
    t, r = group_stats(comp, target), group_stats(comp, ref)
    enough = min(t["claims"], r["claims"]) >= cfg["min_group_claims"]
    enough_inv = enough and min(t["investigated"], r["investigated"]) >= 20
    adj = risk_adjusted_ratio(comp, target, ref)
    base = df.loc[df["month"] == baseline_month, "model_score"]
    # The proxy screen looks at a trailing window: one month is too few confirmed
    # frauds to tell a weak-but-real signal from none at all.
    months = sorted(df["month"].dropna().unique())
    recent = [mo for mo in months if mo <= month][-cfg["proxy_screen"].get("window_months", 6):]
    window = df[df["month"].isin(recent) & df["community_group"].notna()]

    values = {
        "investigation_rate_ratio": ratio(t["investigation_rate"], r["investigation_rate"]),
        "risk_adjusted_investigation_ratio": adj["ratio"],
        "fast_pay_rate_ratio": ratio(t["fast_pay_rate"], r["fast_pay_rate"]),
        "investigation_hit_rate_ratio": ratio(t["investigation_hit_rate"], r["investigation_hit_rate"]),
        "withdrawal_rate_ratio": ratio(t["withdrawal_rate"], r["withdrawal_rate"]),
        "score_psi_vs_baseline": psi(base.to_numpy(), m["model_score"].to_numpy()) if len(base) and len(m) else float("nan"),
    }
    pvals = {
        "investigation_rate_ratio": two_prop_p(t["investigated"], t["claims"], r["investigated"], r["claims"]),
        "fast_pay_rate_ratio": two_prop_p(round(t["fast_pay_rate"] * t["claims"]), t["claims"],
                                          round(r["fast_pay_rate"] * r["claims"]), r["claims"]),
        "investigation_hit_rate_ratio": two_prop_p(t["confirmed_in_investigation"], t["investigated"],
                                                   r["confirmed_in_investigation"], r["investigated"]),
        "withdrawal_rate_ratio": two_prop_p(t["withdrawn"], t["claims"], r["withdrawn"], r["claims"]),
    }
    status = {}
    for k, v in values.items():
        data_ok = enough_inv if k == "investigation_hit_rate_ratio" else (True if k == "score_psi_vs_baseline" else enough)
        s = rag(v, cfg["checks"][k], data_ok)
        # A group-comparison alert must also be distinguishable from month-to-month noise:
        # red needs p < 0.05; amber needs p < 0.10, otherwise the check stays green.
        if k in pvals:
            if s == "red" and not pvals[k] < 0.05:
                s = "amber"
            if s == "amber" and not pvals[k] < 0.10:
                s = "green"
        if s == "red" and k == "risk_adjusted_investigation_ratio" and not (adj["ci_low"] > 1):
            s = "amber"
        status[k] = s
    # Raw rate gaps that disappear once legitimate risk factors are accounted for are
    # worth watching but are not, on their own, evidence the model treats areas unfairly.
    explained = status["risk_adjusted_investigation_ratio"] == "green"
    for k in ("investigation_rate_ratio", "fast_pay_rate_ratio"):
        if explained and status[k] == "red":
            status[k] = "amber"
    return {"month": month, "claims": len(m), "dq": data_quality(m), "target": t, "ref": r,
            "adj": adj, "values": values, "pvals": pvals, "status": status,
            "proxy": proxy_screen(window, cfg["model_inputs"], target, ref, cfg["proxy_screen"]),
            "proxy_window": (window["month"].min(), window["month"].max(), len(window)),
            "model_versions": sorted(m["model_version"].dropna().unique()) if "model_version" in m else []}


# --------------------------------------------------------------------------- report

CHECK_TEXT = {
    "investigation_rate_ratio": ("Investigation referral ratio",
        "How many times more often claims from higher-minority ZIPs are sent to the investigation queue."),
    "risk_adjusted_investigation_ratio": ("Risk-adjusted referral ratio",
        "The same comparison after accounting for claim size, policy tenure, vehicle age and prior claims. "
        "Above 1.0 means a gap remains that those legitimate factors do not explain."),
    "fast_pay_rate_ratio": ("Fast-pay access ratio",
        "Fast-pay rate for higher-minority ZIPs divided by the rate elsewhere (four-fifths rule: below 0.80 is adverse)."),
    "investigation_hit_rate_ratio": ("Investigation hit-rate ratio",
        "Share of investigations that confirm fraud, higher-minority ZIPs vs elsewhere. Well below 1.0 means "
        "those claimants are investigated on weaker grounds."),
    "withdrawal_rate_ratio": ("Claimant withdrawal ratio",
        "How many times more often claimants from higher-minority ZIPs abandon their claim."),
    "score_psi_vs_baseline": ("Score stability (PSI)",
        "Population stability index of model scores against the baseline month. Above 0.25 means the score "
        "distribution has shifted materially."),
}


def fmt(v, kind="ratio"):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "n/a"
    if kind == "pct":
        return f"{v * 100:.1f}%"
    if kind == "p":
        return "<0.001" if v < 0.001 else f"{v:.3f}"
    return f"{v:.2f}"


def headline(res):
    t, r, v, adj = res["target"], res["ref"], res["values"], res["adj"]
    lines = []
    if res["status"]["investigation_rate_ratio"] in ("amber", "red"):
        lines.append(f"Claims from higher-minority ZIP areas were sent to investigation {fmt(v['investigation_rate_ratio'])}&times; as often "
                     f"({fmt(t['investigation_rate'], 'pct')} vs {fmt(r['investigation_rate'], 'pct')}).")
    if res["status"]["risk_adjusted_investigation_ratio"] in ("amber", "red"):
        lines.append(f"After adjusting for claim size, tenure, vehicle age and prior claims, a {fmt(adj['ratio'])}&times; gap remains "
                     f"({adj['observed']} referrals vs {adj['expected']:.0f} expected).")
    elif res["status"]["investigation_rate_ratio"] in ("amber", "red"):
        lines.append("Once legitimate risk factors are accounted for, the gap largely disappears &mdash; it is explained by the claims "
                     "themselves rather than by where the claimant lives.")
    if res["status"]["investigation_hit_rate_ratio"] in ("amber", "red"):
        lines.append(f"Investigations in those areas confirmed fraud only {fmt(t['investigation_hit_rate'], 'pct')} of the time, "
                     f"against {fmt(r['investigation_hit_rate'], 'pct')} elsewhere.")
    proxies = [p["feature"] for p in res["proxy"] if p["likely_proxy"]]
    if proxies:
        lines.append(f"Likely proxy input{'s' if len(proxies) > 1 else ''}: <code>{'</code>, <code>'.join(proxies)}</code> &mdash; "
                     "it separates the two groups of ZIPs but does not track confirmed fraud.")
    if not lines:
        lines.append("No material difference in how the model treats claims from higher-minority ZIP areas this month.")
    return lines


def line_chart(series, months, title, y_fmt, thresholds=(), band=None, y_floor=0.0):
    """Small inline-SVG line chart. series: list of (label, css_var, values)."""
    W, H, L, R, T, B = 680, 240, 52, 160, 16, 30
    vals = [x for _, _, ys in series for x in ys if not math.isnan(x)]
    vals += [th for th, _, _ in thresholds]
    if band:
        vals += [x for x in band[1] if not math.isnan(x)]
    ymin = min(y_floor, min(vals)) if vals else 0
    raw_step = ((max(vals) if vals else 1) - ymin) / 4 or 1
    mag = 10 ** math.floor(math.log10(raw_step))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw_step)
    ymax = ymin + step * 4
    sx = lambda i: L + (W - L - R) * (i / max(1, len(months) - 1))
    sy = lambda y: T + (H - T - B) * (1 - (y - ymin) / ((ymax - ymin) or 1))
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{html.escape(title)}" class="chart">']
    for k in range(5):
        y = ymin + step * k
        out.append(f'<line x1="{L}" x2="{W - R}" y1="{sy(y):.1f}" y2="{sy(y):.1f}" class="grid"/>'
                   f'<text x="{L - 8}" y="{sy(y) + 4:.1f}" class="tick" text-anchor="end">{y_fmt(y)}</text>')
    for i, mo in enumerate(months):
        out.append(f'<text x="{sx(i):.1f}" y="{H - 8}" class="tick" text-anchor="middle">{mo}</text>')
    last_label_y = None
    for th, cls, lab in sorted(thresholds, reverse=True):
        out.append(f'<line x1="{L}" x2="{W - R}" y1="{sy(th):.1f}" y2="{sy(th):.1f}" class="thresh {cls}"/>')
        y = sy(th) + 4 if last_label_y is None else max(sy(th) + 4, last_label_y + 13)
        out.append(f'<text x="{W - R + 6}" y="{y:.1f}" class="tick">{lab} {th:g}</text>')
        last_label_y = y
    if band:
        lo, hi = band
        pts = [(sx(i), sy(h)) for i, h in enumerate(hi)] + [(sx(i), sy(l)) for i, l in reversed(list(enumerate(lo)))]
        out.append('<polygon class="band" points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + '"/>')
    for label, var, ys in series:
        d = " ".join(f"{'M' if i == 0 else 'L'}{sx(i):.1f},{sy(y):.1f}" for i, y in enumerate(ys))
        out.append(f'<path d="{d}" fill="none" stroke="var({var})" stroke-width="2" stroke-linejoin="round"/>')
        for i, y in enumerate(ys):
            tip = html.escape(f"{label} · {months[i]}: {y_fmt(y)}")
            out.append(f'<circle cx="{sx(i):.1f}" cy="{sy(y):.1f}" r="4" fill="var({var})" stroke="var(--surface)" stroke-width="2"/>'
                       f'<circle cx="{sx(i):.1f}" cy="{sy(y):.1f}" r="14" class="hit" data-tip="{tip}"/>')
        if len(series) > 1:
            out.append(f'<text x="{sx(len(ys) - 1) + 10:.1f}" y="{sy(ys[-1]) + 4:.1f}" class="dlabel">{html.escape(label)}</text>')
    out.append("</svg>")
    return "".join(out)


def render(res, trend, cfg, baseline_month):
    overall = max(res["status"].values(), key=lambda s: STATUS_ORDER[s])
    if res["dq"] and overall == "green":
        overall = "amber"
    icon = {"green": "&#10003;", "amber": "!", "red": "&#10005;", "grey": "&ndash;"}
    word = {"green": "Within tolerance", "amber": "Watch", "red": "Escalate", "grey": "Insufficient data"}
    t, r = res["target"], res["ref"]

    rows = []
    for k, (name, desc) in CHECK_TEXT.items():
        s = res["status"][k]
        rule = cfg["checks"][k]
        op = "&ge;" if rule["direction"] == "high" else "&le;"
        p = res["pvals"].get(k)
        extra = ""
        if k == "risk_adjusted_investigation_ratio":
            extra = f"<div class='muted'>95% CI {fmt(res['adj']['ci_low'])}&ndash;{fmt(res['adj']['ci_high'])}</div>"
        elif p is not None:
            extra = f"<div class='muted'>p = {fmt(p, 'p')}</div>"
        rows.append(f"<tr><td><span class='pill {s}'><span aria-hidden='true'>{icon[s]}</span> {word[s]}</span></td>"
                    f"<td><strong>{name}</strong><div class='muted'>{desc}</div></td>"
                    f"<td class='num'>{fmt(res['values'][k])}{extra}</td>"
                    f"<td class='num muted'>amber {op} {rule['amber']}<br>red {op} {rule['red']}</td></tr>")

    def grow(label, key, kind):
        return f"<tr><td>{label}</td><td class='num'>{fmt(t[key], kind) if kind else f'{t[key]:,.0f}'}</td><td class='num'>{fmt(r[key], kind) if kind else f'{r[key]:,.0f}'}</td></tr>"

    group_rows = "".join([
        grow("Claims", "claims", None), grow("Sent to investigation", "investigation_rate", "pct"),
        grow("Sent to fast-pay", "fast_pay_rate", "pct"), grow("Investigations confirming fraud", "investigation_hit_rate", "pct"),
        grow("Confirmed fraud, all claims", "confirmed_fraud_rate_all_claims", "pct"),
        grow("Claimant withdrew", "withdrawal_rate", "pct"), grow("Median days to close", "median_days_to_close", None),
        f"<tr><td>Mean model score</td><td class='num'>{t['mean_model_score']:.3f}</td><td class='num'>{r['mean_model_score']:.3f}</td></tr>",
    ])

    proxy_rows = "".join(
        f"<tr><td><code>{p['feature']}</code></td><td class='num'>{p['group_separation_smd']:+.2f}</td>"
        f"<td class='num'>{p['within_group_fraud_corr']:+.3f}</td>"
        f"<td>{'<span class=\"pill red\"><span aria-hidden=\"true\">&#10005;</span> Likely proxy</span>' if p['likely_proxy'] else '<span class=\"muted\">&mdash;</span>'}</td></tr>"
        for p in res["proxy"])

    months = list(trend["month"])
    chk = cfg["checks"]
    chart1 = line_chart([("Higher-minority ZIPs", "--s1", list(trend["target_investigation_rate"])),
                         ("Other ZIPs", "--s2", list(trend["ref_investigation_rate"]))],
                        months, "Investigation referral rate by month", lambda y: f"{y * 100:.0f}%")
    chart2 = line_chart([("Risk-adjusted ratio", "--s1", list(trend["risk_adjusted_investigation_ratio"]))],
                        months, "Risk-adjusted referral ratio by month", lambda y: f"{y:.2f}",
                        thresholds=[(1.0, "parity", "parity"),
                                    (chk["risk_adjusted_investigation_ratio"]["amber"], "amber", "amber"),
                                    (chk["risk_adjusted_investigation_ratio"]["red"], "red", "red")],
                        band=(list(trend["risk_adjusted_ci_low"]), list(trend["risk_adjusted_ci_high"])))

    trend_rows = "".join(
        f"<tr><td>{row.month}</td><td>{html.escape(row.model_versions)}</td><td class='num'>{row.claims:,}</td>"
        f"<td class='num'>{row.target_investigation_rate * 100:.1f}%</td><td class='num'>{row.ref_investigation_rate * 100:.1f}%</td>"
        f"<td class='num'>{fmt(row.investigation_rate_ratio)}</td><td class='num'>{fmt(row.risk_adjusted_investigation_ratio)}</td>"
        f"<td class='num'>{fmt(row.investigation_hit_rate_ratio)}</td><td class='num'>{fmt(row.fast_pay_rate_ratio)}</td>"
        f"<td><span class='pill {row.overall}'><span aria-hidden='true'>{icon[row.overall]}</span> {word[row.overall]}</span></td></tr>"
        for row in trend.itertuples())

    dq = ("<ul>" + "".join(f"<li>{html.escape(i)}</li>" for i in res["dq"]) + "</ul>") if res["dq"] else "<p class='muted'>No data-quality issues found.</p>"
    actions = {
        "red": "Escalate to the model owner and Chief Actuary this week. Ask for (1) a review of every input flagged as a likely proxy, "
               "(2) a manual second look at investigation referrals from the affected ZIP areas, and (3) a remediation date for the next meeting.",
        "amber": "Record in the minutes and ask the model owner for an explanation before next month's run.",
        "green": "No action needed. File the report with the committee minutes.",
        "grey": "Not enough claims to judge; re-run when more data is available.",
    }[overall]

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Triage Fairness Report</title>
<style>
:root{{--surface:#fcfcfb;--panel:#f3f2ef;--ink:#0b0b0b;--ink2:#52514e;--rule:#dedcd6;--s1:#2a78d6;--s2:#eb6834;
--good:#0ca30c;--warn:#fab219;--crit:#d03b3b;--grey:#8a8984;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--surface:#1a1a19;--panel:#242422;--ink:#f0efec;--ink2:#c3c2b7;--rule:#3a3a37;--s1:#3987e5;--s2:#d95926;color-scheme:dark}}}}
:root[data-theme="dark"]{{--surface:#1a1a19;--panel:#242422;--ink:#f0efec;--ink2:#c3c2b7;--rule:#3a3a37;--s1:#3987e5;--s2:#d95926;color-scheme:dark}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--surface);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:960px;margin:0 auto;padding:32px 16px 64px}}h1{{font-size:26px;margin:0 0 4px}}h2{{font-size:18px;margin:36px 0 10px}}
.muted{{color:var(--ink2);font-size:13px}}code{{font-size:13px}}
.banner{{border:1px solid var(--rule);border-left:6px solid var(--grey);background:var(--panel);border-radius:8px;padding:16px 20px;margin:20px 0}}
.banner.red{{border-left-color:var(--crit)}}.banner.amber{{border-left-color:var(--warn)}}.banner.green{{border-left-color:var(--good)}}
.banner ul{{margin:8px 0 0;padding-left:20px}}.banner li{{margin:4px 0}}
.pill{{display:inline-flex;gap:6px;align-items:center;white-space:nowrap;font-size:13px;font-weight:600;padding:2px 10px;border-radius:999px;border:1.5px solid var(--grey)}}
.pill.red{{border-color:var(--crit)}}.pill.amber{{border-color:var(--warn)}}.pill.green{{border-color:var(--good)}}
.pill.red span{{color:var(--crit)}}.pill.amber span{{color:var(--warn)}}.pill.green span{{color:var(--good)}}
.scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%}}th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid var(--rule);vertical-align:top}}
.trend td:first-child,.trend td:nth-child(2){{white-space:nowrap}}th{{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--ink2);font-weight:600}}.num{{text-align:right;font-variant-numeric:tabular-nums}}
.chart{{width:100%;height:auto;display:block}}.grid{{stroke:var(--rule);stroke-width:1}}.tick,.dlabel{{fill:var(--ink2);font-size:11px}}.dlabel{{fill:var(--ink);font-size:12px}}
.thresh{{stroke-width:1;stroke-dasharray:4 4;stroke:var(--ink2)}}.thresh.amber{{stroke:var(--warn)}}.thresh.red{{stroke:var(--crit)}}
.band{{fill:var(--s1);opacity:.14}}.hit{{fill:transparent;cursor:default}}
.legend{{display:flex;gap:18px;font-size:13px;color:var(--ink2);margin:4px 0 8px}}.legend i{{display:inline-block;width:14px;height:3px;border-radius:2px;vertical-align:middle;margin-right:6px}}
#tip{{position:fixed;pointer-events:none;background:var(--ink);color:var(--surface);font-size:12px;padding:4px 8px;border-radius:4px;display:none}}
.card{{background:var(--panel);border:1px solid var(--rule);border-radius:8px;padding:16px;margin:12px 0}}
</style></head><body><main>
<p class="muted">Halcyon Insurance &middot; AI Governance Committee &middot; Claims-severity triage model</p>
<h1>Triage fairness report &mdash; {res['month']}</h1>
<p class="muted">{res['claims']:,} claims &middot; model {', '.join(res['model_versions']) or 'n/a'} &middot; score baseline {baseline_month} &middot;
comparing ZIP3 areas labelled <em>{cfg['monitored_group']}</em> with all <em>{cfg['reference_group']}</em> ZIP3 areas</p>

<div class="banner {overall}"><span class="pill {overall}"><span aria-hidden="true">{icon[overall]}</span> Overall: {word[overall]}</span>
<ul>{''.join(f'<li>{l}</li>' for l in headline(res))}</ul>
<p style="margin:10px 0 0"><strong>Recommended action:</strong> {actions}</p></div>

<h2>Checks this month</h2><div class="scroll"><table><thead><tr><th>Status</th><th>Check</th><th class="num">Value</th><th class="num">Thresholds</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>

<h2>Six-month trend</h2>
<div class="card"><strong>Investigation referral rate by month</strong>
<div class="legend"><span><i style="background:var(--s1)"></i>Higher-minority ZIPs</span><span><i style="background:var(--s2)"></i>Other ZIPs</span></div>{chart1}</div>
<div class="card"><strong>Risk-adjusted referral ratio by month</strong><div class="muted">Shaded band is the 95% confidence interval; 1.0 is parity.</div>{chart2}</div>
<div class="scroll"><table class="trend"><thead><tr><th>Month</th><th>Model</th><th class="num">Claims</th><th class="num">Inv. rate (HM)</th><th class="num">Inv. rate (other)</th>
<th class="num">Referral ratio</th><th class="num">Risk-adj. ratio</th><th class="num">Hit-rate ratio</th><th class="num">Fast-pay ratio</th><th>Status</th></tr></thead><tbody>{trend_rows}</tbody></table></div>

<h2>Group detail &mdash; {res['month']}</h2>
<div class="scroll"><table><thead><tr><th>Measure</th><th class="num">Higher-minority ZIPs</th><th class="num">Other ZIPs</th></tr></thead><tbody>{group_rows}</tbody></table></div>

<h2>Proxy screen &mdash; model inputs</h2>
<p class="muted">Based on {res['proxy_window'][2]:,} claims from {res['proxy_window'][0]} to {res['proxy_window'][1]}. An input is flagged as a likely proxy when it separates the two groups of ZIP areas strongly (standardised mean difference &ge; {cfg['proxy_screen']['group_separation_smd']})
but, within each group, barely tracks confirmed fraud (|correlation| &lt; {cfg['proxy_screen']['max_within_group_fraud_correlation']}). Such an input steers decisions by location without adding real fraud signal.</p>
<div class="scroll"><table><thead><tr><th>Input</th><th class="num">Group separation (SMD)</th><th class="num">Within-group fraud correlation</th><th>Flag</th></tr></thead><tbody>{proxy_rows}</tbody></table></div>

<h2>Data quality</h2>{dq}

<h2>How to read this report</h2>
<p class="muted">The model never sees race or ethnicity. ZIP3 areas are labelled using census-based population estimates in <code>zip_reference.csv</code>
so the committee can test whether location-based inputs reproduce a protected-class disparity. A red status requires both the threshold breach and statistical
significance (p &lt; 0.05, or a confidence interval that excludes parity). The raw referral and fast-pay ratios are capped at amber when the
risk-adjusted ratio is green, because that gap is explained by the claims themselves; otherwise it is shown as amber. An amber needs p &lt; 0.10, so ordinary month-to-month noise stays green. Thresholds are set in <code>thresholds.json</code>.</p>
</main><div id="tip" role="status"></div>
<script>const tip=document.getElementById('tip');document.querySelectorAll('.hit').forEach(c=>{{c.addEventListener('mousemove',e=>{{tip.textContent=c.dataset.tip;tip.style.display='block';tip.style.left=(e.clientX+12)+'px';tip.style.top=(e.clientY+12)+'px'}});c.addEventListener('mouseleave',()=>tip.style.display='none')}});</script>
</body></html>"""


# --------------------------------------------------------------------------- main

def run(claims_path, zip_path, config_path, month=None, baseline=None, out_dir=None):
    with open(config_path) as fh:
        cfg = json.load(fh)
    df = load(claims_path, zip_path)
    months = sorted(df["month"].dropna().unique())
    month = month or months[-1]
    if month not in months:
        sys.exit(f"ERROR: month {month} not found. Available: {', '.join(months)}")
    baseline = baseline or months[0]

    results = [month_metrics(df, mo, cfg, baseline) for mo in months if mo <= month]
    res = results[-1]
    trend = pd.DataFrame([{
        "month": x["month"], "claims": x["claims"], "model_versions": ", ".join(x["model_versions"]),
        "target_investigation_rate": x["target"]["investigation_rate"], "ref_investigation_rate": x["ref"]["investigation_rate"],
        **x["values"], "risk_adjusted_ci_low": x["adj"]["ci_low"], "risk_adjusted_ci_high": x["adj"]["ci_high"],
        "overall": max(x["status"].values(), key=lambda s: STATUS_ORDER[s]),
    } for x in results])

    out_dir = out_dir or os.path.join(HERE, "reports")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, f"fairness_report_{month}.html")
    with open(report_path, "w") as fh:
        fh.write(render(res, trend, cfg, baseline))

    metrics = [{"month": month, "metric": k, "value": res["values"][k], "p_value": res["pvals"].get(k), "status": res["status"][k]}
               for k in res["values"]]
    metrics += [{"month": month, "metric": f"{grp}.{k}", "value": v} for grp, d in (("higher_minority", res["target"]), ("other", res["ref"])) for k, v in d.items()]
    metrics += [{"month": month, "metric": f"proxy.{p['feature']}.smd", "value": p["group_separation_smd"], "status": "red" if p["likely_proxy"] else "green"} for p in res["proxy"]]
    metrics_path = os.path.join(out_dir, f"fairness_metrics_{month}.csv")
    pd.DataFrame(metrics).to_csv(metrics_path, index=False)
    return res, trend, report_path, metrics_path


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--month", help="YYYY-MM to report on (default: latest in the file)")
    p.add_argument("--baseline", help="YYYY-MM baseline for score stability (default: earliest month)")
    p.add_argument("--claims", default=os.path.join(HERE, "data", "claims.csv"))
    p.add_argument("--zip-ref", default=os.path.join(HERE, "data", "zip_reference.csv"))
    p.add_argument("--config", default=os.path.join(HERE, "thresholds.json"))
    p.add_argument("--out-dir", default=None)
    args = p.parse_args()

    res, trend, report, metrics = run(args.claims, args.zip_ref, args.config, args.month, args.baseline, args.out_dir)
    overall = max(res["status"].values(), key=lambda s: STATUS_ORDER[s])
    print(f"\nHalcyon triage fairness monitor -- {res['month']}  ({res['claims']:,} claims)")
    print(f"Overall status: {overall.upper()}\n")
    for k, (name, _) in CHECK_TEXT.items():
        print(f"  [{res['status'][k].upper():5}] {name:32} {fmt(res['values'][k])}")
    flagged = [x["feature"] for x in res["proxy"] if x["likely_proxy"]]
    print(f"\n  Likely proxy inputs: {', '.join(flagged) or 'none'}")
    if res["dq"]:
        print("  Data-quality issues: " + "; ".join(res["dq"]))
    print(f"\nReport:  {report}\nMetrics: {metrics}\n")


if __name__ == "__main__":
    main()
