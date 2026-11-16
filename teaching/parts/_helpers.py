# -*- coding: utf-8 -*-
"""Cell helpers shared by every part module.

md()/code() wrap nbformat's constructors so the part modules stay readable;
unit_header() enforces the unit header format (node id, technique, source file,
canonical reference) so a reader can always jump from a unit back into the real
code and out to the literature.
"""
import nbformat as nbf

from parts._bilingual import bi, mono  # noqa: F401  re-exported for the parts


def md(text):
    return nbf.v4.new_markdown_cell(text.strip())


def code(src):
    return nbf.v4.new_code_cell(src.strip("\n"))


def unit_header(node, zh, en, source, ref, needs):
    """One header per unit: node id, bilingual name, source file, reference, prerequisites."""
    needs = needs or "-"
    return mono(
        f"## [{node}] {zh} / {en}\n\n"
        f"- 對應程式 source: `{source}`\n"
        f"- 文獻 reference: {ref}\n"
        f"- 先備節點 prerequisites: {needs}\n\n"
        "---"
    )
