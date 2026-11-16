#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble a teaching notebook from per-part modules, with guards.

Copy this into the project's teaching directory and adapt PARTS and OUT.

    python build_notebook.py              # assemble and write
    python build_notebook.py --check      # validate only, do not write
    python build_notebook.py --execute    # assemble, write, then run every cell

Why a builder rather than editing the .ipynb: a notebook is JSON that grows
past ten thousand lines. Hand-editing it risks corrupting the file or silently
dropping outputs, and produces diffs nobody can review. Assembling from
modules means one part can be rewritten without touching the rest, and gives
a natural place to hang guards.

Expected layout:

    teaching/
    ├── build_notebook.py     <- this file
    ├── parts/
    │   ├── __init__.py       (empty)
    │   ├── _helpers.py       md() / code() / unit_header()
    │   └── part0.py ...      each exposing CELLS = [...]
    └── notebook.ipynb        generated, committed WITH outputs
"""
import argparse
import re
import sys
from pathlib import Path

import nbformat as nbf

# The guard below prints the offending line, which by definition contains
# non-Latin characters. On a cp950/cp1252 console that raises UnicodeEncodeError
# and buries a clear message under a traceback -- so force UTF-8 first.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# --- adapt these two -------------------------------------------------------
from parts import (part0, part1_foundations, part2_core,          # noqa: E402
                   part3_contribution, part4_robustness, part5_report)
from parts._bilingual import check_bilingual                        # noqa: E402

PARTS = [part0, part1_foundations, part2_core, part3_contribution, part4_robustness, part5_report]
OUT = HERE / "volatility_ladder_tutorial.ipynb"
TITLE = "The information ladder in volatility forecasting: a skill-tree tutorial"
# ---------------------------------------------------------------------------

# Matplotlib's default font (DejaVu Sans) has no CJK, Arabic, Hebrew or Thai
# glyphs, so a label in any of those scripts renders as a row of empty boxes --
# silently, with no warning from matplotlib or the notebook. Figure text must
# therefore be Latin even when the surrounding narrative is not. Printed output
# and DataFrames are unaffected: they go through the HTML layer, which renders
# every script correctly.
NON_LATIN = re.compile(
    "["
    "一-鿿"      # CJK unified ideographs
    "぀-ヿ"      # hiragana, katakana
    "가-힯"      # hangul
    "֐-׿"      # hebrew
    "؀-ۿ"      # arabic
    "฀-๿"      # thai
    "]"
)
PLOT_TEXT = re.compile(
    r"(set_title|set_xlabel|set_ylabel|set_xticklabels|set_yticklabels|suptitle"
    r"|\.text\(|annotate|\blabel\s*=|legend\s*\(\s*title\s*=|set_label)"
)


def check_figure_text(nb):
    """Fail the build if any matplotlib text argument uses a non-Latin script.

    Static scanning misses labels passed through variables; the runtime glyph
    check (see references/rendering-traps.md section 5) catches those. This
    guard exists to stop the common case cheaply, at build time.
    """
    bad = [(i, line.strip())
           for i, cell in enumerate(nb.cells) if cell.cell_type == "code"
           for line in cell.source.splitlines()
           if PLOT_TEXT.search(line) and NON_LATIN.search(line)]
    if bad:
        print("\nERROR: non-Latin text in matplotlib calls -- renders as tofu boxes:")
        for i, line in bad:
            print(f"  cell {i}: {line[:100]}")
        raise SystemExit(f"{len(bad)} line(s); figure text must be Latin script")


def build():
    nb = nbf.v4.new_notebook()
    cells = []
    for mod in PARTS:
        cells.extend(mod.CELLS)
    nb.cells = cells
    nb.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
        "title": TITLE,
    }
    nbf.validate(nb)
    check_figure_text(nb)
    check_bilingual(nb)
    return nb


def execute(path):
    """Run every cell and store the outputs.

    allow_errors=True then counting failures ourselves is deliberate: raising
    on the first error tells you nothing about the other forty cells, and one
    pass that surfaces every failure is worth several that stop early.
    """
    from nbclient import NotebookClient

    nb = nbf.read(path, as_version=4)
    NotebookClient(nb, timeout=900, kernel_name="python3",
                   resources={"metadata": {"path": str(path.parent)}},
                   allow_errors=True).execute()
    nbf.write(nb, path)

    n = fails = figs = 0
    for c in nb.cells:
        if c.cell_type != "code":
            continue
        n += 1
        for o in c.get("outputs", []):
            if o.get("output_type") == "error":
                fails += 1
                print(f"  ERROR in cell: {o['ename']}: {o['evalue'][:90]}")
            if "image/png" in o.get("data", {}):
                figs += 1
    print(f"executed: {n} cells | failures: {fails} | figures: {figs}")
    return fails


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="validate only")
    ap.add_argument("--execute", action="store_true", help="run all cells after writing")
    args = ap.parse_args()

    nb = build()
    n_md = sum(1 for c in nb.cells if c.cell_type == "markdown")
    n_code = sum(1 for c in nb.cells if c.cell_type == "code")
    print(f"cells   : {len(nb.cells)}  ({n_md} markdown, {n_code} code)")
    print("figures : text checked, Latin script only")

    if args.check:
        print("validate: OK (not written)")
        sys.exit(0)

    nbf.write(nb, OUT)
    print(f"written : {OUT.name}  ({OUT.stat().st_size / 1024:.0f} KB)")

    if args.execute:
        if execute(OUT):
            sys.exit(1)
    else:
        # A rebuilt notebook has empty outputs. Committing that silently strips
        # every figure from the version readers see on GitHub.
        print("\nreminder: outputs are now empty -- rerun with --execute before committing")
