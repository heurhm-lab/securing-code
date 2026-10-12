"""
Validation that the monitor finds the bias that was deliberately planted, and does
not raise a red alarm on control data where the bias pathway is switched off.

    python3 -m unittest discover -s tests -v
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import generate_claims  # noqa: E402
import monitor  # noqa: E402

CONFIG = os.path.join(os.path.dirname(HERE), "thresholds.json")


def build(tmp, bias):
    claims, zref, key = generate_claims.generate(bias=bias)
    d = os.path.join(tmp, "bias" if bias else "control")
    os.makedirs(d)
    claims.to_csv(os.path.join(d, "claims.csv"), index=False)
    zref.to_csv(os.path.join(d, "zip_reference.csv"), index=False)
    return d, claims, zref, key


class DatasetShape(unittest.TestCase):
    def test_spec(self):
        claims, zref, _ = generate_claims.generate()
        self.assertGreaterEqual(len(claims), 5000)
        self.assertEqual(claims["month"].nunique(), 6)
        self.assertEqual(zref["state"].nunique(), 4)
        for col in ["claim_amount", "zip3", "vehicle_age_years", "policy_tenure_years",
                    "queue_assignment", "final_outcome"]:
            self.assertIn(col, claims.columns)
        self.assertNotIn("_true_fraud", claims.columns)

    def test_fraud_does_not_depend_on_zip_once_risk_factors_are_equal(self):
        claims, zref, key = generate_claims.generate()
        df = claims.merge(zref, on="zip3").merge(key, on="claim_id")
        # Among long-tenure, no-prior-claim policies the true fraud rates should be close.
        sub = df[(df["policy_tenure_years"] >= 3) & (df["prior_claims_3yr"] == 0)]
        rates = sub.groupby("community_group")["true_fraud"].mean()
        self.assertLess(abs(rates["higher-minority"] - rates["other"]), 0.015)


class Detection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.bias_dir, *_ = build(cls.tmp.name, bias=True)
        cls.ctrl_dir, *_ = build(cls.tmp.name, bias=False)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_month(self, d, month):
        res, trend, report, metrics = monitor.run(os.path.join(d, "claims.csv"), os.path.join(d, "zip_reference.csv"),
                                                  CONFIG, month=month, out_dir=os.path.join(d, "out"))
        self.assertTrue(os.path.exists(report) and os.path.exists(metrics))
        return res, trend

    def test_biased_data_is_red_and_names_the_proxy(self):
        res, _ = self.run_month(self.bias_dir, "2026-09")
        self.assertEqual(res["status"]["risk_adjusted_investigation_ratio"], "red")
        self.assertEqual(res["status"]["investigation_hit_rate_ratio"], "red")
        proxies = [p["feature"] for p in res["proxy"] if p["likely_proxy"]]
        self.assertEqual(proxies, ["zip_risk_index"])

    def test_model_refresh_makes_it_worse(self):
        _, trend = self.run_month(self.bias_dir, "2026-09")
        before = trend[trend["month"] < "2026-07"]["risk_adjusted_investigation_ratio"].mean()
        after = trend[trend["month"] >= "2026-07"]["risk_adjusted_investigation_ratio"].mean()
        self.assertGreater(after, before * 1.2)

    def test_control_data_never_goes_red_on_adjusted_or_proxy(self):
        for month in ["2026-05", "2026-06", "2026-07", "2026-08", "2026-09"]:
            res, _ = self.run_month(self.ctrl_dir, month)
            self.assertNotEqual(res["status"]["risk_adjusted_investigation_ratio"], "red", month)
            self.assertFalse(any(p["likely_proxy"] for p in res["proxy"]), month)
            self.assertNotEqual(res["status"]["investigation_rate_ratio"], "red", month)


if __name__ == "__main__":
    unittest.main()
