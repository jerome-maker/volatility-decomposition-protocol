# -*- coding: utf-8 -*-
"""Reproduction checks for a pre-submission teaching notebook.

Copy into the project's teaching/ folder next to findings.csv. In the notebook:

    from repro import Register
    reg = Register("findings.csv")            # once, in Unit 0
    reg.check("T2_b_policy", beta_hat)        # numeric value
    reg.check_sign("abs_neg", beta_hat)       # "+" / "-"
    reg.check_stars("T2_star_policy", pval)   # "***" / "**" / "*" / ""
    reg.check_count("N_obs", len(df))
    reg.check_rank("rank_sector", {"Energy": 0.4, "Tech": 0.1})
    reg.check_text("period", df.date.min().year == 2008)
    reg.report()                              # final unit: table + save json

Every check prints one bilingual line so the reader sees the comparison in
place, and is recorded in repro_results.json for check_reproduction.py.

Tolerance comes from the printed precision of the manuscript value, never from
a number chosen here: "0.043" accepts anything that rounds to 0.043.
"""
import csv
import json
import math
from pathlib import Path

STATUS_ZH = {
    "reproduced": "重現",
    "reproduced_note": "重現（附註）",
    "differs": "不一致",
    "not_verifiable": "無法驗證",
}
DEFAULT_STARS = ((0.01, "***"), (0.05, "**"), (0.10, "*"))


def _decimals(s):
    s = s.strip().lstrip("+-").replace(",", "")
    if "e" in s.lower():
        return None
    return len(s.split(".")[1]) if "." in s else 0


def _num(s):
    return float(s.strip().replace(",", "").replace("−", "-").rstrip("%"))


class Register:
    def __init__(self, path="findings.csv", out="repro_results.json", stars=DEFAULT_STARS):
        self.path = Path(path)
        self.out = self.path.with_name(out) if not Path(out).is_absolute() else Path(out)
        with open(self.path, encoding="utf-8-sig", newline="") as f:
            self.rows = {r["id"]: r for r in csv.DictReader(f)}
        self.stars = stars
        self.results = {}

    # -- internals ---------------------------------------------------------
    def _row(self, fid):
        if fid not in self.rows:
            raise KeyError(f"'{fid}' is not in {self.path.name} -- register it first "
                           f"(an unregistered check is an unaudited claim)")
        return self.rows[fid]

    def _record(self, fid, computed, status, detail=""):
        row = self.rows[fid]
        if fid in self.results:
            print(f"  [warn] {fid} checked twice; keeping the latest")
        self.results[fid] = {
            "id": fid, "location": row.get("location", ""), "kind": row.get("kind", ""),
            "reported": row.get("reported", ""), "computed": computed,
            "status": status, "detail": detail,
        }
        mark = "OK " if status.startswith("reproduced") else "!! "
        print(f"{mark}{fid:<22} manuscript={row.get('reported', ''):<12} "
              f"notebook={computed!s:<14} {status} / {STATUS_ZH[status]}"
              + (f"  ({detail})" if detail else ""))
        self._save()

    def _save(self):
        self.out.write_text(json.dumps(list(self.results.values()), ensure_ascii=False,
                                       indent=1, default=str), encoding="utf-8")

    # -- checks ------------------------------------------------------------
    def check(self, fid, value, last_digit_slack=0, note=""):
        """Numeric value. last_digit_slack=1 for optimiser output (see register doc)."""
        row = self._row(fid)
        rep = row["reported"]
        d = int(row["decimals"]) if row.get("decimals", "").strip() else _decimals(rep)
        scale = float(row.get("scale") or 1)
        x = float(value) * scale
        if math.isnan(x):
            self._record(fid, "nan", "differs", "computed NaN")
            return
        r = _num(rep)
        if d is None:                                  # scientific notation: 3 sig. figs
            tol = abs(r) * 5e-3
        else:
            tol = (0.5 + last_digit_slack) * 10 ** (-d)
        shown = f"{x:.{d}f}" if d is not None else f"{x:.4g}"
        if abs(x - r) <= tol + 1e-12:
            status = "reproduced_note" if (note or last_digit_slack) else "reproduced"
            self._record(fid, shown, status, note)
        else:
            self._record(fid, shown, "differs", f"|diff|={abs(x - r):.3g} > tol={tol:.3g}"
                         + (f"; {note}" if note else ""))

    def check_sign(self, fid, value):
        rep = self._row(fid)["reported"].strip()
        got = "+" if value > 0 else "-" if value < 0 else "0"
        self._record(fid, got, "reproduced" if got == rep else "differs")

    def check_stars(self, fid, pvalue):
        rep = self._row(fid)["reported"].strip()
        got = next((s for cut, s in self.stars if pvalue < cut), "")
        self._record(fid, got or "(none)", "reproduced" if got == rep else "differs",
                            f"p={pvalue:.4g}")

    def check_count(self, fid, n):
        rep = int(_num(self._row(fid)["reported"]))
        self._record(fid, int(n), "reproduced" if int(n) == rep else "differs")

    def check_rank(self, fid, scores, descending=True):
        rep = [s.strip() for s in self._row(fid)["reported"].split(";")]
        got = [k for k, _ in sorted(scores.items(), key=lambda kv: kv[1], reverse=descending)]
        got = [g for g in got if g in rep]
        self._record(fid, ";".join(got), "reproduced" if got == rep else "differs")

    def check_text(self, fid, condition, detail=""):
        self._row(fid)
        self._record(fid, bool(condition), "reproduced" if condition else "differs",
                            detail)

    def not_verifiable(self, fid, missing):
        """Say exactly what is missing. Never a pass."""
        self._row(fid)
        self._record(fid, "-", "not_verifiable", missing)

    # -- report ------------------------------------------------------------
    def report(self):
        """Final unit: every register row, checked or not."""
        rows = []
        for fid, r in self.rows.items():
            res = self.results.get(fid)
            rows.append({
                "id": fid, "location": r.get("location", ""),
                "manuscript": r.get("reported", ""),
                "notebook": res["computed"] if res else "",
                "status": res["status"] if res else "unchecked",
                "狀態": STATUS_ZH.get(res["status"], "") if res else "未檢查",
                "detail": res["detail"] if res else "no check() call",
            })
        counts = {}
        for r in rows:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
        print("summary / 摘要:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
        try:
            import pandas as pd
            return pd.DataFrame(rows)
        except ImportError:
            return rows
