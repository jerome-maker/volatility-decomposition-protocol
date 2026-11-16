#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check that every manuscript finding was re-derived and agrees.

    python check_reproduction.py teaching/findings.csv teaching/repro_results.json
    python check_reproduction.py ... --allow T5_b_placebo,abs_pct   # researcher has seen these

Run it after executing the notebook. Exit 0 only when every register row has a
result and every result is reproduced / reproduced_note (or explicitly allowed).
Exit 1 otherwise, listing each problem -- unchecked rows first, because a
silent gap in coverage is worse than a visible difference.
"""
import argparse
import csv
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OK = {"reproduced", "reproduced_note"}

ap = argparse.ArgumentParser()
ap.add_argument("findings")
ap.add_argument("results")
ap.add_argument("--allow", default="", help="comma-separated ids accepted after review")
a = ap.parse_args()

with open(a.findings, encoding="utf-8-sig", newline="") as f:
    reg = {r["id"]: r for r in csv.DictReader(f)}
with open(a.results, encoding="utf-8") as f:
    res = {r["id"]: r for r in json.load(f)}
allow = {s.strip() for s in a.allow.split(",") if s.strip()}

unchecked = [i for i in reg if i not in res]
unknown = [i for i in res if i not in reg]
failed = [r for i, r in res.items() if i in reg and r["status"] not in OK and i not in allow]

print(f"register: {len(reg)} findings | checked: {len(reg) - len(unchecked)} | "
      f"reproduced: {sum(r['status'] in OK for r in res.values())}")
for i in unchecked:
    print(f"  UNCHECKED  {i:<22} {reg[i].get('location', '')}")
for i in unknown:
    print(f"  UNKNOWN    {i:<22} checked in notebook but not in the register")
for r in failed:
    print(f"  {r['status'].upper():<10} {r['id']:<22} {r['location']}: "
          f"manuscript {r['reported']} vs notebook {r['computed']}  {r['detail']}")
for i in sorted(allow & set(res)):
    print(f"  ALLOWED    {i:<22} {res[i]['status']} (accepted after review)")

if unchecked or unknown or failed:
    sys.exit(1)
print("reproduction: OK")
