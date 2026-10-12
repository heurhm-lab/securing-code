"""
Validation for analyzer.py: it must flag the planted bias, catch the July model
refresh as drift against the rolling three-month baseline, write every output,
and not raise a FLAG on control data where the bias pathway is switched off.

    python3 -m unittest discover -s tests -v
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import analyzer  # noqa: E402
import generate_claims  # noqa: E402

CONFIG = os.path.join(os.path.dirname(HERE), "thresholds.json")
OUTPUTS = ["chart_selection_rates.png", "chart_disparity_ratios.png", "chart_false_investigation.png",
           "chart_drift_vs_baseline.png"]


class Analyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dirs = {}
        for name, bias in (("bias", True), ("control", False)):
            claims, zref, _ = generate_claims.generate(bias=bias)
            d = os.path.join(cls.tmp.name, name)
            os.makedirs(d)
            claims.to_csv(os.path.join(d, "claims.csv"), index=False)
            zref.to_csv(os.path.join(d, "zip_reference.csv"), index=False)
            cls.dirs[name] = d

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_month(self, name, month, group_col="community_group"):
        d = self.dirs[name]
        out = os.path.join(d, "out", month, group_col)
        return analyzer.run(os.path.join(d, "claims.csv"), os.path.join(d, "zip_reference.csv"), CONFIG,
                            month=month, group_col=group_col, out_dir=out)

    def areas(self, res, level="FLAG"):
        return {f["area"] for f in res["flags"] if f["level"] == level}

    def test_writes_all_outputs(self):
        res = self.run_month("bias", "2026-09")
        for f in OUTPUTS + ["flag_summary_2026-09.md", "analyzer_metrics_2026-09.csv"]:
            self.assertTrue(os.path.getsize(os.path.join(res["out_dir"], f)) > 0, f)
        with open(res["summary"]) as fh:
            self.assertLessEqual(len(fh.read().splitlines()), 45, "summary must fit on one page")

    def test_selection_rates_sum_to_one(self):
        res = self.run_month("bias", "2026-09")
        gm = res["gm"]
        total = gm["sel_fast_pay"] + gm["sel_standard"] + gm["sel_investigation"]
        for v in total:
            self.assertAlmostEqual(v, 1.0)

    def test_planted_bias_is_flagged(self):
        res = self.run_month("bias", "2026-09")
        self.assertEqual(res["overall"], "FLAG")
        self.assertIn("Disparity — investigation", self.areas(res))
        self.assertIn("False investigations", self.areas(res))
        self.assertLess(res["dp"].loc["higher-minority", "investigation_ratio"], 0.8)

    def test_model_refresh_shows_as_drift(self):
        res = self.run_month("bias", "2026-07")
        drift_flags = [f for f in res["flags"] if f["area"] == "Drift" and f["level"] == "FLAG"]
        self.assertTrue(any("investigation rate" in f["text"] for f in drift_flags))

    def test_no_drift_without_three_month_baseline(self):
        res = self.run_month("bias", "2026-06")
        self.assertIsNone(res["drift"])
        self.assertTrue(os.path.exists(os.path.join(res["out_dir"], "chart_drift_vs_baseline.png")))

    def test_control_data_raises_no_flags(self):
        for month in ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"]:
            res = self.run_month("control", month)
            self.assertNotEqual(res["overall"], "FLAG", (month, [f["text"] for f in res["flags"]]))

    def test_unmapped_zip_claims_are_reported_not_silently_dropped(self):
        # Regression: claims whose ZIP3 is missing from zip_reference.csv used to vanish
        # from every comparison with no warning.
        import pandas as pd
        d = self.dirs["bias"]
        claims = pd.read_csv(os.path.join(d, "claims.csv"), dtype={"zip3": str})
        sept = claims.index[claims["month"] == "2026-09"][:150]
        claims.loc[sept, "zip3"] = "486"
        bad = os.path.join(d, "claims_unmapped.csv")
        claims.to_csv(bad, index=False)
        res = analyzer.run(bad, os.path.join(d, "zip_reference.csv"), CONFIG, month="2026-09",
                           out_dir=os.path.join(d, "out", "unmapped"))
        self.assertEqual(res["n_claims"] - res["n_analysed"], 150)
        data = [f for f in res["flags"] if f["area"] == "Data"]
        self.assertEqual(data[0]["level"], "FLAG")
        self.assertIn("486", data[0]["text"])
        with open(res["summary"]) as fh:
            self.assertIn("only", fh.read())

    def test_incident_tier(self):
        self.assertEqual(self.run_month("bias", "2026-09")["tier"], "SEV-1")
        for month in ["2026-07", "2026-08", "2026-09"]:
            self.assertIn(self.run_month("control", month)["tier"], ("SEV-3", "None"))

    def test_other_group_column(self):
        res = self.run_month("bias", "2026-09", group_col="state")
        self.assertEqual(set(res["gm"].index), {"OH", "IN", "KY", "MI"})


if __name__ == "__main__":
    unittest.main()
