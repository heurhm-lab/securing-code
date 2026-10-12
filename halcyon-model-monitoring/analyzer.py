#!/usr/bin/env python3
"""
Halcyon claims-triage monitoring analyzer.

    python3 analyzer.py                          # latest month, groups = ZIP community group
    python3 analyzer.py --month 2026-07
    python3 analyzer.py --group-col state        # compare the four states instead

For the chosen month it computes:

  1. Selection rates     share of each group's claims routed to fast-pay, standard
                         and investigation
  2. Disparity ratios    four-fifths-rule style: each group's fast-pay rate divided by
                         the best group's rate; and for investigation (an adverse
                         outcome) the least-investigated group's rate divided by each
                         group's rate. Below 0.80 fails the four-fifths rule.
  3. False-investigation rates
                         of the claims each group had investigated, the share that did
                         NOT end in confirmed fraud; and the share of each group's
                         claims NOT confirmed as fraud that were sent to investigation
  4. Drift               every metric above, plus the model-score distribution, compared
                         with a rolling baseline of the previous three months pooled

and writes to reports/<month>/
(or reports/<month>/by_<column>/ when --group-col is used):

  flag_summary_<month>.md        plain-language one-page flag summary
  analyzer_metrics_<month>.csv   every number behind the summary
  chart_selection_rates.png      chart_disparity_ratios.png
  chart_false_investigation.png  chart_drift_vs_baseline.png
"""
import argparse
import json
import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from monitor import HERE, load, psi, risk_adjusted_ratio, two_prop_p  # noqa: E402

QUEUES = ["fast_pay", "standard", "investigation"]
QUEUE_LABEL = {"fast_pay": "Fast-pay", "standard": "Standard", "investigation": "Investigation"}

# Chart styling: categorical slots in fixed order, recessive ink and grid.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, GRID, SURFACE, CRITICAL = "#0b0b0b", "#52514e", "#dedcd6", "#fcfcfb", "#d03b3b"


# --------------------------------------------------------------------------- metrics

def group_metrics(m, group_col):
    """Per-group counts and rates for one slice of claims."""
    rows = []
    for g, d in m.groupby(group_col):
        inv = d[d["is_inv"]]
        # Denominator is every claim NOT confirmed as fraud. That is not the same as
        # "legitimate": fast-pay claims are never examined, so undetected fraud sits here too.
        unconfirmed = d[~d["is_confirmed"]]
        rows.append({
            "group": g,
            "claims": len(d),
            **{f"sel_{q}": (d["queue_assignment"] == q).mean() for q in QUEUES},
            **{f"n_{q}": int((d["queue_assignment"] == q).sum()) for q in QUEUES},
            "investigated": len(inv),
            "false_investigations": int((~inv["is_confirmed"]).sum()),
            "false_investigation_rate": (~inv["is_confirmed"]).mean() if len(inv) else float("nan"),
            "unconfirmed_claims": len(unconfirmed),
            "unconfirmed_investigated": int(unconfirmed["is_inv"].sum()),
            "unconfirmed_investigation_rate": unconfirmed["is_inv"].mean() if len(unconfirmed) else float("nan"),
        })
    return pd.DataFrame(rows).set_index("group")


def disparity(gm, min_claims):
    """Four-fifths-style impact ratios against the most favourably treated group."""
    ok = gm[gm["claims"] >= min_claims]
    out = pd.DataFrame(index=gm.index)
    best_fast = ok["sel_fast_pay"].idxmax()
    least_inv = ok["sel_investigation"].idxmin()
    out["fast_pay_ratio"] = gm["sel_fast_pay"] / gm.loc[best_fast, "sel_fast_pay"]
    out["investigation_ratio"] = gm.loc[least_inv, "sel_investigation"] / gm["sel_investigation"]
    out["fast_pay_p"] = [two_prop_p(gm.loc[g, "n_fast_pay"], gm.loc[g, "claims"],
                                    gm.loc[best_fast, "n_fast_pay"], gm.loc[best_fast, "claims"]) for g in gm.index]
    out["investigation_p"] = [two_prop_p(gm.loc[g, "n_investigation"], gm.loc[g, "claims"],
                                         gm.loc[least_inv, "n_investigation"], gm.loc[least_inv, "claims"]) for g in gm.index]
    best_fir = ok["false_investigation_rate"].idxmin()
    out["false_inv_gap"] = gm["false_investigation_rate"] - gm.loc[best_fir, "false_investigation_rate"]
    out["false_inv_p"] = [two_prop_p(gm.loc[g, "false_investigations"], gm.loc[g, "investigated"],
                                     gm.loc[best_fir, "false_investigations"], gm.loc[best_fir, "investigated"]) for g in gm.index]
    out.attrs.update(best_fast=best_fast, least_inv=least_inv, best_fir=best_fir)
    return out


def analyse_slice(m, group_col, min_claims):
    gm = group_metrics(m, group_col)
    return gm, disparity(gm, min_claims)


def adjusted_ratios(m, group_col, dp):
    """
    Risk-adjusted ratios (same method as monitor.py): is each raw gap still there
    once claim size, tenure, vehicle age and prior claims are taken into account?
    Investigation is compared with the least-investigated group, fast-pay with the
    group that gets fast-pay most often. 1.0 means the gap is fully explained.
    """
    mm = m.assign(community_group=m[group_col])
    out = {}
    for kind, outcome, ref in [("Investigation", "is_inv", dp.attrs["least_inv"]),
                               ("Fast-pay", "is_fast", dp.attrs["best_fast"])]:
        out[kind] = {g: (risk_adjusted_ratio(mm, g, ref, outcome) if g != ref else None) for g in dp.index}
    return out


# --------------------------------------------------------------------------- flags

def flag_level(level_list):
    return "FLAG" if "FLAG" in level_list else "WATCH" if "WATCH" in level_list else "OK"


def build_flags(month, gm, dp, adj, drift, score_psi, cfg, min_claims, baseline_months):
    a = cfg["analyzer"]
    p_sig = a["significance_p"]
    flags = []

    def add(level, area, text, group=None):
        flags.append({"level": level, "area": area, "text": text, "group": group})

    for g in gm.index:
        if gm.loc[g, "claims"] < min_claims:
            add("WATCH", "Data", f"{g}: only {gm.loc[g, 'claims']} claims this month, too few to judge.")
            continue
        for kind, ratio_col, p_col in [("Fast-pay", "fast_pay_ratio", "fast_pay_p"),
                                       ("Investigation", "investigation_ratio", "investigation_p")]:
            r, p = dp.loc[g, ratio_col], dp.loc[g, p_col]
            if r < a["four_fifths_threshold"]:
                lvl = "FLAG" if p < p_sig else "WATCH"
                if kind == "Fast-pay":
                    text = (f"**{g}** claims reach fast-pay at {r:.2f}× the rate of the best-treated group "
                            f"({gm.loc[g, 'sel_fast_pay']:.1%} vs {gm.loc[dp.attrs['best_fast'], 'sel_fast_pay']:.1%}). "
                            f"Fails the four-fifths rule")
                else:
                    times = 1 / r
                    text = (f"**{g}** claims are sent to investigation {times:.1f}× as often as the least-investigated group "
                            f"({gm.loc[g, 'sel_investigation']:.1%} vs {gm.loc[dp.attrs['least_inv'], 'sel_investigation']:.1%}); "
                            f"impact ratio {r:.2f}. Fails the four-fifths rule")
                text += "." if lvl == "FLAG" else ", but the difference is not statistically significant this month."
                a_g = adj[kind].get(g)
                if lvl == "FLAG" and a_g is not None:
                    lo, hi, ar = a_g["ci_low"], a_g["ci_high"], a_g["ratio"]
                    persists = lo > 1 if kind == "Investigation" else hi < 1
                    shown = ar if kind == "Investigation" else 1 / ar
                    if persists:
                        text += (f" After adjusting for claim size, tenure, vehicle age and prior claims, the gap is still "
                                 f"{shown:.1f}× (risk-adjusted ratio {ar:.2f}, 95% CI {lo:.2f}–{hi:.2f}): "
                                 "the claims themselves do not explain it.")
                    else:
                        lvl = "WATCH"
                        text += f" However, after adjusting for claim size, tenure, vehicle age and prior claims the ratio is {ar:.2f} (95% CI {lo:.2f}–{hi:.2f})"
                        text += (", so the gap is largely explained by legitimate risk factors." if 0.9 <= ar <= 1.1 else
                                 ": a smaller gap may remain, but it is not statistically significant this month.")
                add(lvl, f"Disparity — {kind.lower()}", text, g)
            elif r < a["four_fifths_watch"] and p < p_sig:
                add("WATCH", f"Disparity — {kind.lower()}",
                    f"**{g}** {kind.lower()} impact ratio is {r:.2f}: passes the four-fifths rule but is close to it.")
        gap, p = dp.loc[g, "false_inv_gap"], dp.loc[g, "false_inv_p"]
        if gap >= a["false_investigation_gap_flag"]:
            lvl = "FLAG" if p < p_sig else "WATCH"
            best = dp.attrs["best_fir"]
            add(lvl, "False investigations", group=g, text=(
                f"**{g}**: {gm.loc[g, 'false_investigation_rate']:.0%} of investigations found no fraud, "
                f"against {gm.loc[best, 'false_investigation_rate']:.0%} for {best} "
                f"({gm.loc[g, 'false_investigations']} of {gm.loc[g, 'investigated']} investigated claims). "
                + ("Honest claimants in this group are investigated far more often." if lvl == "FLAG"
                   else "Not statistically significant this month.")))

    if drift is not None:
        for _, d in drift.iterrows():
            if d["metric_kind"] == "rate" and abs(d["change"]) >= a["drift_rate_change_flag"]:
                lvl = "FLAG" if d["p_value"] < p_sig else "WATCH"
                add(lvl, "Drift",
                    f"**{d['group']}** {d['label'].lower()} moved from {d['baseline']:.1%} (rolling {baseline_months}-month baseline) "
                    f"to {d['current']:.1%} this month ({d['change'] * 100:+.1f} points)"
                    + ("." if lvl == "FLAG" else "; not statistically significant."))
            elif d["metric_kind"] == "ratio" and abs(d["change"]) >= a["drift_ratio_change_flag"]:
                worse = d["change"] < 0
                add("FLAG" if worse else "WATCH", "Drift",
                    f"**{d['group']}** {d['label'].lower()} {'fell' if worse else 'rose'} from {d['baseline']:.2f} to {d['current']:.2f} "
                    f"against the rolling baseline.")
        if score_psi >= a["drift_psi_flag"]:
            add("FLAG", "Drift", f"Model score distribution shifted materially from the baseline (PSI {score_psi:.2f}).")
        elif score_psi >= a["drift_psi_watch"]:
            add("WATCH", "Drift", f"Model score distribution shifted moderately from the baseline (PSI {score_psi:.2f}).")
    order = {"FLAG": 0, "WATCH": 1}
    flags.sort(key=lambda f: (order[f["level"]], f["area"] != "Data"))
    return flags


def unmapped_flag(month_all, group_col, cfg):
    """Claims with no group label are excluded from every comparison: say so loudly."""
    miss = month_all[month_all[group_col].isna()]
    if miss.empty:
        return None
    share = len(miss) / len(month_all)
    zips = ", ".join(sorted(miss["zip3"].astype(str).unique())[:8])
    level = "FLAG" if share >= cfg["analyzer"].get("unmapped_flag_share", 0.01) else "WATCH"
    return {"level": level, "area": "Data", "group": None,
            "text": f"{len(miss):,} of {len(month_all):,} claims ({share:.1%}) have no `{group_col}` "
                    f"(ZIP3 not in the reference table: {zips}) and are left out of every comparison below. "
                    "Add them to `zip_reference.csv` and re-run before relying on this summary."}


def incident_tier(flags):
    """Map flags to the severity tiers in INCIDENT_RESPONSE.md."""
    flagged = [f for f in flags if f["level"] == "FLAG"]
    inv = {f["group"] for f in flagged if f["area"] == "Disparity — investigation"}
    fir = {f["group"] for f in flagged if f["area"] == "False investigations"}
    if inv & fir:
        return "SEV-1"
    if flagged:
        return "SEV-2"
    return "SEV-3" if flags else "None"


# --------------------------------------------------------------------------- drift

DRIFT_METRICS = [
    ("sel_investigation", "Investigation rate", "rate", "n_investigation", "claims"),
    ("sel_fast_pay", "Fast-pay rate", "rate", "n_fast_pay", "claims"),
    ("false_investigation_rate", "False-investigation rate", "rate", "false_investigations", "investigated"),
    ("unconfirmed_investigation_rate", "Investigation rate among claims not confirmed as fraud", "rate", "unconfirmed_investigated", "unconfirmed_claims"),
    ("fast_pay_ratio", "Fast-pay impact ratio", "ratio", None, None),
    ("investigation_ratio", "Investigation impact ratio", "ratio", None, None),
]


def drift_table(cur_gm, cur_dp, base_gm, base_dp):
    rows = []
    for g in cur_gm.index.intersection(base_gm.index):
        for col, label, kind, num, den in DRIFT_METRICS:
            src_c, src_b = (cur_gm, base_gm) if kind == "rate" else (cur_dp, base_dp)
            c, b = src_c.loc[g, col], src_b.loc[g, col]
            p = (two_prop_p(cur_gm.loc[g, num], cur_gm.loc[g, den], base_gm.loc[g, num], base_gm.loc[g, den])
                 if kind == "rate" else float("nan"))
            rows.append({"group": g, "metric": col, "label": label, "metric_kind": kind,
                         "baseline": b, "current": c, "change": c - b, "p_value": p})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- charts

def _style(ax, title, subtitle=None):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9, length=0)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title(title, loc="left", fontsize=12, color=INK, fontweight="bold", pad=22 if subtitle else 10)
    if subtitle:
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9, color=INK2)


def _fig(w=8, h=4.2):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    return fig, ax


def _colors(groups):
    return {g: SERIES[i % len(SERIES)] for i, g in enumerate(groups)}


def chart_selection(gm, month, colors, path):
    fig, ax = _fig()
    groups = list(gm.index)
    width = 0.8 / len(groups)
    x = np.arange(len(QUEUES))
    for i, g in enumerate(groups):
        vals = [gm.loc[g, f"sel_{q}"] for q in QUEUES]
        bars = ax.bar(x + (i - (len(groups) - 1) / 2) * width, vals, width * 0.92, color=colors[g], label=g,
                      edgecolor=SURFACE, linewidth=1)
        if len(groups) <= 4:
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.0%}", ha="center", fontsize=8, color=INK2)
    ax.set_xticks(x, [QUEUE_LABEL[q] for q in QUEUES])
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
    _style(ax, f"Selection rate by queue — {month}", "Share of each group's claims routed to each queue")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="upper left", bbox_to_anchor=(0, -0.08), ncol=len(groups))
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def chart_lines(trend, value_col, title, subtitle, colors, path, threshold=None, pct=False):
    fig, ax = _fig()
    months = sorted(trend["month"].unique())
    x = np.arange(len(months))
    for g, color in colors.items():
        t = trend[trend["group"] == g].set_index("month").reindex(months)
        ax.plot(x, t[value_col], color=color, linewidth=2, marker="o", markersize=5,
                markeredgecolor=SURFACE, markeredgewidth=1.5, label=g)
        last = t[value_col].iloc[-1]
        if len(colors) <= 4 and not pd.isna(last):
            ax.annotate(g, (x[-1], last), xytext=(8, 0), textcoords="offset points", va="center", fontsize=9, color=INK)
    if threshold is not None:
        ax.axhline(threshold, color=CRITICAL, linestyle="--", linewidth=1)
        ax.annotate(f"four-fifths line ({threshold:.2f})", (x[0], threshold), xytext=(0, 4),
                    textcoords="offset points", fontsize=8, color=INK2)
    ax.set_xticks(x, months)
    ax.set_xlim(-0.3, len(months) - 1 + 1.6)
    if pct:
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
    lo = min(0, trend[value_col].min())
    ax.set_ylim(lo, max(trend[value_col].max(), threshold or 0) * 1.12)
    _style(ax, title, subtitle)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="upper left", bbox_to_anchor=(0, -0.08), ncol=len(colors))
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def chart_disparity(trend, colors, threshold, path):
    """Two panels sharing one 0-to-1 scale: fast-pay and investigation impact ratios."""
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.2), dpi=150, sharey=True)
    fig.patch.set_facecolor(SURFACE)
    months = sorted(trend["month"].unique())
    x = np.arange(len(months))
    for ax, col, title in [(axes[0], "fast_pay_ratio", "Fast-pay impact ratio"),
                           (axes[1], "investigation_ratio", "Investigation impact ratio")]:
        for g, color in colors.items():
            t = trend[trend["group"] == g].set_index("month").reindex(months)
            ax.plot(x, t[col], color=color, linewidth=2, marker="o", markersize=5,
                    markeredgecolor=SURFACE, markeredgewidth=1.5, label=g)
        ax.axhline(threshold, color=CRITICAL, linestyle="--", linewidth=1)
        ax.text(x[-1], threshold - 0.05, f"four-fifths line {threshold:.2f}", ha="right", fontsize=8, color=INK2)
        ax.set_xticks(x, [mo[2:] for mo in months])
        ax.set_ylim(0, 1.1)
        _style(ax, title)
        ax.title.set_fontsize(10)
    fig.text(0.012, 0.965, "Four-fifths-rule impact ratios by month", fontsize=12, color=INK, fontweight="bold")
    fig.text(0.012, 0.925, "1.00 = treated as well as the best group; below the dashed line fails the four-fifths rule",
             fontsize=9, color=INK2)
    axes[0].legend(frameon=False, fontsize=9, labelcolor=INK2, loc="upper left", bbox_to_anchor=(0, -0.08), ncol=len(colors))
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def chart_drift(drift, month, baseline_label, colors, path):
    """Dumbbell: rolling-baseline value (hollow) to current month (filled), rates only."""
    d = drift[drift["metric_kind"] == "rate"]
    labels = [lbl for _, lbl, kind, *_ in DRIFT_METRICS if kind == "rate"]
    groups = list(colors)
    fig, ax = _fig(8, 0.55 * len(labels) * len(groups) + 1.6)
    y, yticks, ylabels = 0, [], []
    for lbl in labels:
        for g in groups:
            r = d[(d["label"] == lbl) & (d["group"] == g)]
            if r.empty:
                continue
            b, c = r["baseline"].iloc[0], r["current"].iloc[0]
            ax.plot([b, c], [y, y], color=GRID, linewidth=3, zorder=1)
            ax.scatter([b], [y], s=50, facecolor=SURFACE, edgecolor=colors[g], linewidth=2, zorder=2)
            ax.scatter([c], [y], s=50, color=colors[g], edgecolor=SURFACE, linewidth=1.5, zorder=3)
            ax.annotate(f"{(c - b) * 100:+.1f} pts", (max(b, c), y), xytext=(8, 0), textcoords="offset points",
                        va="center", fontsize=8, color=INK2)
            yticks.append(y)
            ylabels.append(f"{lbl} — {g}")
            y -= 1
        y -= 0.5
    ax.set_yticks(yticks, ylabels)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
    ax.set_xlim(0, min(1.0, d[["baseline", "current"]].max().max() * 1.25))
    _style(ax, f"Drift: {month} vs rolling baseline ({baseline_label})",
           "Hollow dot = baseline (previous three months pooled), filled dot = this month")
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def chart_no_baseline(month, path):
    fig, ax = _fig(8, 2)
    ax.axis("off")
    ax.text(0.5, 0.5, f"No drift chart for {month}: fewer than three earlier months of data for a rolling baseline.",
            ha="center", va="center", fontsize=10, color=INK2, wrap=True)
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


# --------------------------------------------------------------------------- summary

def write_summary(path, month, group_col, gm, dp, adj, flags, baseline_label, score_psi, n_claims, n_analysed, tier, cfg):
    overall = flag_level([f["level"] for f in flags])
    headline = {"FLAG": "🔴 ACTION NEEDED", "WATCH": "🟡 WATCH", "OK": "🟢 NO FLAGS"}[overall]
    action = {
        "FLAG": "Escalate to the model owner and the Chief Actuary. Ask for a written explanation of each flag "
                "and a remediation date before the next committee meeting.",
        "WATCH": "Note in the minutes and re-check next month. No escalation yet.",
        "OK": "No action. File this summary with the minutes.",
    }[overall]
    group_name = "ZIP community group" if group_col == "community_group" else group_col.replace("_", " ")
    lines = [
        f"# Triage model flag summary: {month}",
        "",
        f"**{headline}**  ·  incident tier **{tier}** (see `INCIDENT_RESPONSE.md`)  ·  "
        + (f"{n_claims:,} claims" if n_analysed == n_claims
           else f"{n_claims:,} claims, **only {n_analysed:,} analysed** ({n_claims - n_analysed:,} have no group)")
        + f"  ·  groups compared by {group_name}  ·  drift baseline: {baseline_label}",
        "",
        f"**What to do:** {action}",
        "",
        "## Flags",
        "",
    ]
    shown = [f for f in flags if f["level"] == "FLAG"] + [f for f in flags if f["level"] == "WATCH"]
    if not shown:
        lines.append("- None this month.")
    for f in shown[:9]:
        mark = "🔴 FLAG" if f["level"] == "FLAG" else "🟡 WATCH"
        lines.append(f"- {mark} · *{f['area']}*: {f['text']}")
    if len(shown) > 9:
        lines.append(f"- … and {len(shown) - 9} more in `analyzer_metrics_{month}.csv`.")
    lines += [
        "",
        "## Key numbers",
        "",
        "| Group | Claims | Fast-pay | Investigated | Fast-pay ratio | Investigation ratio | Risk-adjusted inv. gap | Investigations with no fraud |",
        "|---|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for g in gm.index:
        adj_txt = f"{adj['Investigation'][g]['ratio']:.2f}×" if adj["Investigation"].get(g) else "reference"
        lines.append(f"| {g} | {gm.loc[g, 'claims']:,} | {gm.loc[g, 'sel_fast_pay']:.1%} | {gm.loc[g, 'sel_investigation']:.1%} | "
                     f"{dp.loc[g, 'fast_pay_ratio']:.2f} | {dp.loc[g, 'investigation_ratio']:.2f} | {adj_txt} | "
                     f"{gm.loc[g, 'false_investigation_rate']:.0%} |")
    psi_txt = f"PSI {score_psi:.2f}" if not math.isnan(score_psi) else "n/a"
    lines += [
        "",
        f"Model-score drift against the baseline: {psi_txt} (below 0.10 is stable, 0.25 or more is a material shift).",
        "",
        "## How to read this",
        "",
        f"- **Impact ratio** compares a group with the best-treated group. A ratio below "
        f"{cfg['analyzer']['four_fifths_threshold']:.2f} fails the four-fifths rule. For investigation, a ratio of 0.50 "
        "means a group is investigated twice as often.",
        "- **Investigations with no fraud** is the share of investigated claims that ended paid or withdrawn. Almost all of "
        "these are honest claimants who were delayed and scrutinised.",
        "- **Risk-adjusted inv. gap** compares investigation rates after accounting for claim size, tenure, vehicle age and prior "
        "claims. 1.00 means the raw gap is fully explained by those legitimate factors.",
        "- **Drift** compares this month with the previous three months pooled. A rolling baseline absorbs a lasting change "
        "after about three months, so a drift flag that goes quiet does not mean the problem is fixed. Check the disparity flags too.",
        "- 🔴 FLAG means the threshold was breached and the difference is statistically significant (p < 0.05). 🟡 WATCH means "
        "it is near the line or could still be chance.",
        "",
        "Charts in this folder: `chart_selection_rates.png`, `chart_disparity_ratios.png`, "
        "`chart_false_investigation.png`, `chart_drift_vs_baseline.png`.",
    ]
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return overall


# --------------------------------------------------------------------------- main

def run(claims_path, zip_path, config_path, month=None, group_col="community_group", out_dir=None):
    with open(config_path) as fh:
        cfg = json.load(fh)
    a = cfg["analyzer"]
    df = load(claims_path, zip_path)
    if group_col not in df.columns:
        raise SystemExit(f"ERROR: no column '{group_col}' in the claims or ZIP reference data")
    all_df = df
    df = df[df[group_col].notna()]
    months = sorted(df["month"].unique())
    month = month or months[-1]
    if month not in months:
        raise SystemExit(f"ERROR: month {month} not found. Available: {', '.join(months)}")
    min_claims = cfg.get("min_group_claims", 100)

    # Put the monitored group first so it keeps the first colour in every chart.
    groups = sorted(df[group_col].unique(), key=lambda g: (g != cfg.get("monitored_group"), str(g)))
    colors = _colors(groups)

    trend_rows = []
    for mo in [x for x in months if x <= month]:
        gm, dp = analyse_slice(df[df["month"] == mo], group_col, min_claims)
        for g in gm.index:
            trend_rows.append({"month": mo, "group": g, **gm.loc[g].to_dict(), **dp.loc[g].to_dict()})
    trend = pd.DataFrame(trend_rows)

    cur = df[df["month"] == month]
    gm, dp = analyse_slice(cur, group_col, min_claims)
    gm, dp = gm.reindex([g for g in groups if g in gm.index]), dp.reindex([g for g in groups if g in dp.index])

    prior = [x for x in months if x < month][-a["baseline_months"]:]
    drift, score_psi, baseline_label = None, float("nan"), "not available (needs 3 earlier months)"
    if len(prior) == a["baseline_months"]:
        base = df[df["month"].isin(prior)]
        bgm, bdp = analyse_slice(base, group_col, min_claims)
        drift = drift_table(gm, dp, bgm, bdp)
        score_psi = psi(base["model_score"].to_numpy(), cur["model_score"].to_numpy())
        baseline_label = f"{prior[0]} to {prior[-1]}"

    adj = adjusted_ratios(cur, group_col, dp)
    flags = build_flags(month, gm, dp, adj, drift, score_psi, cfg, min_claims, a["baseline_months"])
    month_all = all_df[all_df["month"] == month]
    data_flag = unmapped_flag(month_all, group_col, cfg)
    if data_flag:
        flags.insert(0, data_flag)
    tier = incident_tier(flags)

    if out_dir is None:
        out_dir = os.path.join(HERE, "reports", month)
        if group_col != "community_group":
            out_dir = os.path.join(out_dir, f"by_{group_col}")
    os.makedirs(out_dir, exist_ok=True)
    chart_selection(gm, month, colors, os.path.join(out_dir, "chart_selection_rates.png"))
    chart_disparity(trend, colors, a["four_fifths_threshold"], os.path.join(out_dir, "chart_disparity_ratios.png"))
    chart_lines(trend, "false_investigation_rate", "False-investigation rate by month",
                "Share of investigated claims that did not end in confirmed fraud",
                colors, os.path.join(out_dir, "chart_false_investigation.png"), pct=True)
    if drift is not None:
        chart_drift(drift, month, baseline_label, colors, os.path.join(out_dir, "chart_drift_vs_baseline.png"))
    else:
        chart_no_baseline(month, os.path.join(out_dir, "chart_drift_vs_baseline.png"))

    summary_path = os.path.join(out_dir, f"flag_summary_{month}.md")
    overall = write_summary(summary_path, month, group_col, gm, dp, adj, flags, baseline_label, score_psi,
                            len(month_all), len(cur), tier, cfg)

    metrics = []
    for g in gm.index:
        for k, v in {**gm.loc[g].to_dict(), **dp.loc[g].to_dict()}.items():
            metrics.append({"month": month, "section": "current", "group": g, "metric": k, "value": v})
    if drift is not None:
        for _, r in drift.iterrows():
            for k in ("baseline", "change", "p_value"):
                metrics.append({"month": month, "section": f"drift_{k}", "group": r["group"], "metric": r["metric"], "value": r[k]})
        metrics.append({"month": month, "section": "drift", "group": "all", "metric": "score_psi", "value": score_psi})
    for f in flags:
        metrics.append({"month": month, "section": "flag", "group": f["area"], "metric": f["level"], "value": f["text"]})
    pd.DataFrame(metrics).to_csv(os.path.join(out_dir, f"analyzer_metrics_{month}.csv"), index=False)

    return {"month": month, "overall": overall, "tier": tier, "n_claims": len(month_all), "n_analysed": len(cur), "flags": flags, "gm": gm, "dp": dp, "drift": drift,
            "score_psi": score_psi, "trend": trend, "out_dir": out_dir, "summary": summary_path}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--month", help="YYYY-MM to analyse (default: latest in the file)")
    p.add_argument("--group-col", default="community_group",
                   help="column defining the groups to compare (default: community_group; try: state)")
    p.add_argument("--claims", default=os.path.join(HERE, "data", "claims.csv"))
    p.add_argument("--zip-ref", default=os.path.join(HERE, "data", "zip_reference.csv"))
    p.add_argument("--config", default=os.path.join(HERE, "thresholds.json"))
    p.add_argument("--out-dir", default=None)
    args = p.parse_args()

    res = run(args.claims, args.zip_ref, args.config, args.month, args.group_col, args.out_dir)
    n_flag = sum(f["level"] == "FLAG" for f in res["flags"])
    n_watch = sum(f["level"] == "WATCH" for f in res["flags"])
    print(f"\nHalcyon triage analyzer -- {res['month']}: {res['overall']}  ·  incident tier {res['tier']}  "
          f"({n_flag} flags, {n_watch} watch items)")
    if res["n_analysed"] != res["n_claims"]:
        print(f"  WARNING: only {res['n_analysed']:,} of {res['n_claims']:,} claims could be assigned to a group.")
    for f in res["flags"]:
        print(f"  [{f['level']:5}] {f['area']}: {f['text'].replace('**', '')}")
    print(f"\nOne-page summary: {res['summary']}\nCharts and metrics: {res['out_dir']}\n")


if __name__ == "__main__":
    main()
