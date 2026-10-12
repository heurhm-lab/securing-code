#!/usr/bin/env python3
"""
Demo helper: build a copy of the claims extract in which 150 September claims from
higher-minority ZIP3s carry a new ZIP3 ("486") that zip_reference.csv does not know.

This reproduces the defect where the first analyzer silently dropped those claims.

    python3 demo/make_unmapped_extract.py /tmp/claims_unmapped.csv
"""
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1] if len(sys.argv) > 1 else "claims_unmapped.csv"
claims = pd.read_csv(os.path.join(HERE, "data", "claims.csv"), dtype={"zip3": str})
zref = pd.read_csv(os.path.join(HERE, "data", "zip_reference.csv"), dtype={"zip3": str})
hm = set(zref.loc[zref["community_group"] == "higher-minority", "zip3"])
idx = claims[(claims["month"] == "2026-09") & claims["zip3"].isin(hm)].sample(150, random_state=1).index
claims.loc[idx, "zip3"] = "486"
claims.to_csv(out, index=False)
print(f"Wrote {out}: {(claims['month'] == '2026-09').sum():,} September claims, 150 of them with unmapped ZIP3 486")
