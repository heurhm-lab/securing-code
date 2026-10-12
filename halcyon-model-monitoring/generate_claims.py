#!/usr/bin/env python3
"""
Synthetic claims generator for the Halcyon Insurance claims-severity triage model.

Produces six months of auto claims (Apr-Sep 2026, ~6,300 rows) across four states,
plus a ZIP3 reference table, with a deliberately injected PROXY-BIAS PATHWAY:

  1. Every ZIP3 carries a synthetic census estimate of its minority population share.
     ZIP3s at or above 40% are labelled "higher-minority" in the reference table.
  2. The triage model uses a feature called `zip_risk_index` -- the historical SIU
     (Special Investigations Unit) referral rate for the ZIP3, indexed to 1.0. In
     higher-minority ZIP3s it is inflated (~1.8 vs ~1.0) by legacy referral
     practice, NOT by more fraud. True fraud propensity does not depend on ZIP at all.
  3. The model therefore scores those claims higher and routes them to the
     investigation queue more often, where investigations confirm fraud less often
     and some honest claimants give up (withdraw) while waiting.
  4. A model refresh on 2026-07-01 increased the weight on `zip_risk_index`, so the
     disparity gets visibly worse in Jul-Sep -- something for monthly monitoring to catch.

There is also a LEGITIMATE confound: higher-minority ZIP3s have somewhat older
vehicles and shorter policy tenure, which genuinely raise fraud risk a little.
A raw rate comparison overstates the bias; a good monitor must adjust for that.

Run with --no-bias to generate a control dataset with the pathway switched off
(used by the test suite to confirm the monitor does not cry wolf).

Outputs (to --out-dir, default ./data):
  claims.csv          the monthly extract the committee monitors
  zip_reference.csv   ZIP3 -> state, synthetic minority share, community group
  answer_key.csv      latent true-fraud flag per claim (validation only; never
                      available in production and not read by the monitor)
"""
import argparse
import os

import numpy as np
import pandas as pd

STATES = {
    "OH": [430, 432, 433, 436, 440, 441, 443, 450, 452, 456],
    "IN": [460, 461, 462, 463, 464, 467, 468, 470, 474, 478],
    "KY": [400, 401, 402, 403, 405, 406, 410, 415, 420, 425],
    "MI": [480, 481, 482, 483, 484, 488, 490, 493, 495, 497],
}
# ZIP3s designed as higher-minority, urban-core areas (2-3 per state).
HIGHER_MINORITY_ZIP3 = {432, 441, 452, 462, 463, 402, 482, 483, 484, 495}

MONTHS = pd.period_range("2026-04", "2026-09", freq="M")
MODEL_REFRESH = pd.Period("2026-07", freq="M")

INVESTIGATE_SCORE = 0.30
FAST_PAY_SCORE = 0.12
FAST_PAY_MAX_AMOUNT = 3500


def build_zip_reference(rng):
    rows = []
    for state, zips in STATES.items():
        for z in zips:
            flagged = z in HIGHER_MINORITY_ZIP3
            share = rng.uniform(0.42, 0.71) if flagged else rng.uniform(0.06, 0.31)
            rows.append({
                "zip3": f"{z:03d}",
                "state": state,
                "pct_minority_est": round(share, 3),
                "community_group": "higher-minority" if share >= 0.40 else "other",
                # Urban-core ZIP3s generate more claims.
                "_volume_weight": 2.6 if flagged else 1.0,
            })
    return pd.DataFrame(rows)


def generate(seed=20260401, bias=True, rows_per_month=1050):
    rng = np.random.default_rng(seed)
    zref = build_zip_reference(rng)
    weights = zref["_volume_weight"] / zref["_volume_weight"].sum()

    frames = []
    claim_no = 0
    for month in MONTHS:
        n = int(rows_per_month * rng.uniform(0.95, 1.07))
        z_idx = rng.choice(len(zref), size=n, p=weights.values)
        z = zref.iloc[z_idx].reset_index(drop=True)
        flagged = (z["community_group"] == "higher-minority").to_numpy()

        days = rng.integers(0, month.days_in_month, size=n)
        claim_date = month.start_time + pd.to_timedelta(days, unit="D")

        # Legitimate risk factors (with a mild, genuine difference between areas).
        vehicle_age = np.clip(rng.gamma(3.0, 2.3, n) + 1.5 * flagged, 0, 25).round().astype(int)
        tenure = np.clip(rng.exponential(np.where(flagged, 3.6, 5.5)), 0, 30).round(1)
        prior_claims = rng.poisson(0.35, n)
        # Urban-core repair labour costs more, so claims there run larger.
        amount = np.exp(rng.normal(np.log(4500) + 0.12 * flagged + 0.025 * (vehicle_age - 7), 0.85, n))
        amount = np.clip(amount, 250, 95000).round(2)

        # Latent truth: fraud depends only on legitimate factors -- never on ZIP.
        new_policy = (tenure < 1.0).astype(float)
        fraud_logit = (-3.55 + 0.6 * np.log(amount / 4500) + 0.8 * new_policy
                       + 0.35 * prior_claims + 0.05 * (vehicle_age - 7))
        true_fraud = rng.random(n) < 1 / (1 + np.exp(-fraud_logit))

        # The proxy feature: legacy SIU referral intensity by ZIP3.
        if bias:
            zip_risk_index = np.where(flagged, rng.normal(1.8, 0.12, n), rng.normal(1.0, 0.12, n))
        else:
            zip_risk_index = rng.normal(1.0, 0.12, n)
        zip_risk_index = np.clip(zip_risk_index, 0.5, 2.5).round(3)

        zip_weight = 1.2 if (bias and month >= MODEL_REFRESH) else 0.45
        score_logit = (-2.85 + 0.75 * np.log(amount / 4500) + 0.8 * new_policy
                       + 0.4 * prior_claims + 0.05 * (vehicle_age - 7)
                       + zip_weight * (zip_risk_index - 1.0)
                       + 1.7 * true_fraud  # the model has real skill
                       + rng.normal(0, 0.55, n))
        score = (1 / (1 + np.exp(-score_logit))).round(4)

        queue = np.where(score >= INVESTIGATE_SCORE, "investigation",
                         np.where((score < FAST_PAY_SCORE) & (amount <= FAST_PAY_MAX_AMOUNT),
                                  "fast_pay", "standard"))

        u = rng.random(n)
        outcome = np.full(n, "paid_in_full", dtype=object)
        inv, std = queue == "investigation", queue == "standard"
        outcome[inv & true_fraud & (u < 0.85)] = "denied_fraud_confirmed"
        outcome[inv & ~true_fraud & (u < 0.13)] = "withdrawn_by_claimant"
        outcome[std & true_fraud & (u < 0.40)] = "denied_fraud_confirmed"
        outcome[std & ~true_fraud & (u < 0.025)] = "withdrawn_by_claimant"
        # Some honest investigated claims are paid with a negotiated reduction.
        reduced = (outcome == "paid_in_full") & inv & (rng.random(n) < 0.25)
        outcome[reduced] = "paid_adjusted"

        paid = np.where(outcome == "paid_in_full", amount,
                        np.where(outcome == "paid_adjusted", amount * rng.uniform(0.7, 0.95, n), 0.0)).round(2)
        base_days = {"fast_pay": 3, "standard": 14, "investigation": 46}
        days_to_close = np.array([max(1, int(rng.gamma(2.5, base_days[q] / 2.5))) for q in queue])

        frames.append(pd.DataFrame({
            "claim_id": [f"HCL-{claim_no + i + 1:06d}" for i in range(n)],
            "claim_date": claim_date.strftime("%Y-%m-%d"),
            "month": str(month),
            "state": z["state"].values,
            "zip3": z["zip3"].values,
            "claim_amount": amount,
            "vehicle_age_years": vehicle_age,
            "policy_tenure_years": tenure,
            "prior_claims_3yr": prior_claims,
            "zip_risk_index": zip_risk_index,
            "model_version": "triage-v2.4" if month >= MODEL_REFRESH else "triage-v2.3",
            "model_score": score,
            "queue_assignment": queue,
            "final_outcome": outcome,
            "paid_amount": paid,
            "days_to_close": days_to_close,
            "_true_fraud": true_fraud,
        }))
        claim_no += n

    claims = pd.concat(frames, ignore_index=True)
    answer_key = claims[["claim_id", "_true_fraud"]].rename(columns={"_true_fraud": "true_fraud"})
    claims = claims.drop(columns="_true_fraud")
    return claims, zref.drop(columns="_volume_weight"), answer_key


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out-dir", default=os.path.join(os.path.dirname(__file__), "data"))
    p.add_argument("--seed", type=int, default=20260401)
    p.add_argument("--no-bias", action="store_true", help="switch the proxy-bias pathway off (control data)")
    args = p.parse_args()

    claims, zref, key = generate(seed=args.seed, bias=not args.no_bias)
    os.makedirs(args.out_dir, exist_ok=True)
    claims.to_csv(os.path.join(args.out_dir, "claims.csv"), index=False)
    zref.to_csv(os.path.join(args.out_dir, "zip_reference.csv"), index=False)
    key.to_csv(os.path.join(args.out_dir, "answer_key.csv"), index=False)
    print(f"Wrote {len(claims):,} claims ({claims['month'].min()} to {claims['month'].max()}) "
          f"to {args.out_dir}  [bias={'off' if args.no_bias else 'on'}]")


if __name__ == "__main__":
    main()
