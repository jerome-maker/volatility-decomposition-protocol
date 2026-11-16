# -*- coding: utf-8 -*-
"""Bilingual markdown cells and the build guard.

Copy into teaching/parts/ as _bilingual.py, next to _helpers.py. Use bi() for
every prose cell:

    from parts._bilingual import bi
    CELLS = [bi(zh="### 原理\n固定效果移除...",
                en="### Principle\nFixed effects remove...")]

One cell, Chinese first, a rule between them. Formulas may appear in both
halves; keep them identical (the guard checks).

In build_notebook.py, after build():

    from parts._bilingual import check_bilingual
    check_bilingual(nb)
"""
import re

import nbformat as nbf

CJK = re.compile("[一-鿿]")
LATIN_WORD = re.compile(r"[A-Za-z]{3,}")
MATH = re.compile(r"\$\$.+?\$\$|\$[^$\n]+?\$", re.S)
SEP = "\n\n---\n\n"
MARK = "<!-- bilingual -->"
# Cells that legitimately carry no prose: pure formula, code-block tree, tables
# of numbers. Mark them with mono() so the guard skips them on purpose.
MONO = "<!-- mono -->"


def bi(zh, en):
    zh, en = zh.strip(), en.strip()
    if not CJK.search(zh):
        raise ValueError("bi(): zh half has no Chinese text")
    if CJK.search(MATH.sub("", en)):
        raise ValueError("bi(): en half contains Chinese outside math")
    return nbf.v4.new_markdown_cell(f"{MARK}\n**中文**\n\n{zh}{SEP}**English**\n\n{en}")


def mono(text):
    """A markdown cell exempt from the bilingual rule (tree, formula-only, header)."""
    return nbf.v4.new_markdown_cell(f"{MONO}\n{text.strip()}")


def check_bilingual(nb):
    """Fail the build if a prose cell is missing a language or the formulas drift."""
    bad = []
    for i, c in enumerate(nb.cells):
        if c.cell_type != "markdown" or c.source.startswith(MONO):
            continue
        src = c.source
        if not src.startswith(MARK):
            has_zh = bool(CJK.search(src))
            has_en = len(LATIN_WORD.findall(MATH.sub("", src))) >= 5
            if not (has_zh and has_en):
                bad.append((i, "not built with bi() and missing a language"))
            continue
        zh, _, en = src.partition(SEP)
        mz, me = sorted(MATH.findall(zh)), sorted(MATH.findall(en))
        if mz != me:
            bad.append((i, f"formulas differ between halves: zh={len(mz)} en={len(me)}"))
    if bad:
        for i, why in bad:
            print(f"  cell {i}: {why}")
        raise SystemExit(f"{len(bad)} cell(s) fail the bilingual check")
    print("bilingual: OK")
