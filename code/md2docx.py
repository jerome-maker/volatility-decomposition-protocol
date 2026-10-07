"""Convert the assembled manuscript to a DSFE-compliant Word file.

House rules applied: Times New Roman 12 pt, line spacing 18 pt (the journal asks for at least 15),
tables and figures numbered sequentially through the paper, equations numbered flush left.
Equations are written as LaTeX source and must be converted with Word's equation tool before
submission; the journal requires editable equations, not images.
"""
import re, os, json, copy
from lxml import etree
import latex2mathml.converter as _l2m
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

SRC = r'J:/我的雲端硬碟/2026工作區/指導學生/柳宇軒/論文草稿_投稿版.md'
FIGDIR = r'J:/我的雲端硬碟/2026工作區/指導學生/柳宇軒/資訊階梯分析_程式與圖表/fig'
OUT = r'J:/我的雲端硬碟/2026工作區/指導學生/柳宇軒/Chou_2026_information_or_architecture.docx'
FONT = 'Times New Roman'
TAB = chr(9)
_XSL = r'C:/Program Files/Microsoft Office/root/Office16/MML2OMML.XSL'
_TRANSFORM = etree.XSLT(etree.parse(_XSL))

def latex_omml(latex):
    """LaTeX -> MathML -> OMML, so that inline maths is an editable Word equation."""
    return copy.deepcopy(_TRANSFORM(etree.fromstring(_l2m.convert(latex).encode())).getroot())

ABSTRACT = (
 "Comparisons between deep learning and econometric models in financial forecasting rarely hold the information "
 "set fixed, so a reported gain may reflect richer inputs rather than a better model. We propose a decomposition "
 "protocol that splits the out-of-sample gain into three exhaustive components—the value of high-frequency "
 "information, of exogenous forward-looking information, and of the nonlinear architecture—by building a ladder "
 "in which the deep learning model and its linear counterpart receive identical inputs. We apply it to five-day "
 "realized volatility of the SPDR S&P 500 ETF using one-minute data and option-implied indices, with a second "
 "application to the Invesco QQQ ETF. Over 2023 to 2025, exogenous option-implied information is the only "
 "component that improves QLIKE significantly, by 0.048. Holding the information set fixed, the Transformer is "
 "0.024 worse than the linear model and is not significantly better than any benchmark; an LSTM control is "
 "likewise no better, although it outperforms the Transformer. Forward-looking information contributes only "
 "within the heterogeneous autoregressive framework; in the GARCH variance equation its coefficients are "
 "estimated at zero. Statistical and economic rankings diverge: the model with the lowest QLIKE does not deliver "
 "the highest Sharpe ratio under volatility targeting, and all models pass value-at-risk backtests "
 "indistinguishably. The measured architecture effect is also fragile to choices that are seldom reported: five "
 "random seeds are insufficient for significance claims, and changing the deep learning library version moves "
 "the loss by the same magnitude as the effect itself. In a hold-out year reserved before the design was frozen "
 "the architecture component changes sign, which reinforces that conclusion. We recommend information-parity "
 "designs, ten-seed ensembles and version pinning as minimum standards.")
KEYWORDS = ("realized volatility; implied volatility term structure; HAR model; Transformer; forecast evaluation; "
            "reproducibility; random seed variation")
# figures are placed at the end of the section whose number appears here
FIGMAP = [('4', 'f1_overview.png', 'SPY 22-day realized volatility and the sample split.'),
          ('5', 'r1_ladder.png', 'Out-of-sample QLIKE and RMSE by level.'),
          ('5', 'r2_decomp.png', 'Decomposition of the QLIKE gain with 90% block bootstrap intervals.'),
          ('5', 'r4_regime.png', 'QLIKE by market condition.'),
          ('5', 'r3_pred.png', 'Forecasts and realized volatility over the evaluation period; lower panel zooms on April 2025.'),
          ('6', 'r5_econ.png', 'Volatility-targeted portfolios (left) and 5% value-at-risk violation rates (right).'),
          ('8', 'r7_asset2.png', 'Second application: QLIKE by level (left) and decomposition (right) for QQQ and SPY.'),
          ('8', 'r8_spec.png', 'Seed-level comparison of the two cross-asset parameterizations.'),
          ('9', 'r6_shap_granger.png', 'Attribution shares (left) and attribution against predictive precedence (right).')]

def setfont(run, size=12, bold=False, italic=False, color=None):
    run.font.name = FONT; run._element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
    run.font.size = Pt(size); run.bold = bold; run.italic = italic
    if color: run.font.color.rgb = RGBColor.from_string(color)

def add_runs(p, text, size=12):
    """Render **bold**, *italic* and inline $maths$."""
    for seg in re.split(r'(\$[^$]+\$)', text):
        if not seg: continue
        if seg.startswith('$') and seg.endswith('$') and len(seg) > 2:
            try:
                p._p.append(latex_omml(seg[1:-1])); continue
            except Exception:
                seg = seg.strip('$')                      # fall back to plain text
        for chunk in re.split(r'(\*\*[^*]+\*\*|(?<!\*)\*[^*]+\*(?!\*))', seg):
            if not chunk: continue
            if chunk.startswith('**') and chunk.endswith('**'): setfont(p.add_run(chunk[2:-2]), size, bold=True)
            elif chunk.startswith('*') and chunk.endswith('*'): setfont(p.add_run(chunk[1:-1]), size, italic=True)
            else: setfont(p.add_run(chunk), size)

def body(doc, text, size=12, align=None, space_after=6, indent=None, first_line=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = Pt(15); pf.line_spacing_rule = WD_LINE_SPACING.AT_LEAST
    pf.space_after = Pt(space_after)
    if first_line: pf.first_line_indent = Cm(0.84)
    if indent: pf.left_indent = Cm(indent)
    if align == 'center': p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else: p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_runs(p, text, size)
    return p

def rule(row, edges, size=8):
    """Draw only the horizontal rules a three-line table needs."""
    for c in row.cells:
        tcPr = c._tc.get_or_add_tcPr()
        for old in tcPr.findall(qn('w:tcBorders')): tcPr.remove(old)
        b = OxmlElement('w:tcBorders')
        for edge in ('top', 'bottom', 'left', 'right'):
            e = OxmlElement('w:' + edge)
            on = edge in edges
            e.set(qn('w:val'), 'single' if on else 'nil')
            if on: e.set(qn('w:sz'), str(size)); e.set(qn('w:color'), '000000')
            b.append(e)
        tcPr.append(b)

def md_table(doc, rows):
    header, data = rows[0], rows[1:]
    t = doc.add_table(rows=1 + len(data), cols=len(header)); t.style = 'Table Grid'
    t.autofit = True
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(header):
        c = t.rows[0].cells[j]; c.text = ''
        pp = c.paragraphs[0]; pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pp.paragraph_format.line_spacing = Pt(13); pp.paragraph_format.space_after = Pt(0)
        add_runs(pp, h.strip('* '), 10)
        for r in pp.runs: r.bold = True
    for i, row in enumerate(data):
        for j, v in enumerate(row):
            if j >= len(header): continue
            c = t.rows[i + 1].cells[j]; c.text = ''
            pp = c.paragraphs[0]
            pp.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
            pp.paragraph_format.line_spacing = Pt(13); pp.paragraph_format.space_after = Pt(0)
            add_runs(pp, v.strip(), 10)
    rule(t.rows[0], ('top', 'bottom'))                 # rule above the table and under the header
    for r in t.rows[1:]: rule(r, ())
    rule(t.rows[-1], ('bottom',))                      # closing rule
    return t

def main():
    md = open(SRC, encoding='utf-8').read()
    md = md.split('---\n\n', 1)[1]          # drop the Chinese cover block
    tab_labels = re.findall(r'\*\*Table (\d+\.\d+)\*\*', md)
    tab_map = {lab: str(k + 1) for k, lab in enumerate(dict.fromkeys(tab_labels))}
    for lab, new in tab_map.items():
        md = md.replace('Table ' + lab, 'Table ' + new)
    fig_map = {fn: str(k + 1) for k, (_, fn, _) in enumerate(FIGMAP)}
    for fn, new in fig_map.items():
        md = md.replace('{FIG:' + fn.replace('.png', '') + '}', 'Figure ' + new)
    print('table map:', tab_map)
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(1.9)
    sec.top_margin = sec.bottom_margin = Cm(2.5)
    st = doc.styles['Normal']; st.font.name = FONT; st.font.size = Pt(12)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)

    # ---- front matter
    body(doc, 'Research article', space_after=8).runs[0].bold = True
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.line_spacing = Pt(18); p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.AT_LEAST
    setfont(p.add_run('Information or architecture? A decomposition protocol for evaluating '
                      'deep learning gains in volatility forecasting'), 16, bold=True)
    au = doc.add_paragraph(); au.paragraph_format.space_after = Pt(8)
    setfont(au.add_run('Jerome Chih-Lung Chou'), 12, bold=True)
    sup = au.add_run('1,*'); setfont(sup, 12, bold=True); sup.font.superscript = True
    aff = doc.add_paragraph(); aff.paragraph_format.space_after = Pt(2)
    one = aff.add_run('1'); setfont(one, 12, bold=True); one.font.superscript = True
    setfont(aff.add_run(TAB + 'Graduate Institute of Finance, National Taiwan University of Science and '
                        'Technology, Taipei, Taiwan'), 12, bold=True)
    cor = doc.add_paragraph(); cor.paragraph_format.space_after = Pt(14)
    star = cor.add_run('*'); setfont(star, 12, bold=True); star.font.superscript = True
    setfont(cor.add_run(TAB + 'Correspondence: Email: jerome.chou@ntust.edu.tw.'), 12, bold=True)
    ab = body(doc, 'Abstract: ' + ABSTRACT); ab.runs[0].bold = True
    kw = body(doc, 'Keywords: ' + KEYWORDS); kw.runs[0].bold = True
    jl = body(doc, 'JEL Codes: C22, C45, C53, G17', space_after=14); jl.runs[0].bold = True

    # ---- body
    lines = md.split('\n')
    i = 0; tab_n = 0; eq_n = 0; cur_sec = '0'; pending_caption = None
    fig_counter = 0
    placed = set()
    def flush_figs(section):
        nonlocal fig_counter
        for sec_no, fname, cap in FIGMAP:
            if sec_no != section or fname in placed: continue
            placed.add(fname)
            path = os.path.join(FIGDIR, fname)
            if not os.path.exists(path):
                raise FileNotFoundError(f'figure file missing: {path}')
            fig_counter += 1
            doc.add_picture(path, width=Cm(15.5))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            cp = body(doc, f'Figure {fig_counter}. {cap}', size=12, align='center', space_after=12)
            for r in cp.runs: r.bold = True
    while i < len(lines):
        ln = lines[i]
        if ln.strip() in ('', '---'):
            i += 1; continue
        if re.search(r'[一-鿿]', ln) and ln.strip().startswith('>'):
            i += 1; continue
        if ln.startswith('# '):
            txt = ln[2:].strip()
            m = re.match(r'(\d+)\.', txt)
            if m:
                if cur_sec != '0': flush_figs(cur_sec)
                cur_sec = m.group(1)
            p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(14); p.paragraph_format.space_after = Pt(6)
            setfont(p.add_run(re.sub(r'^(\d+)[.]\s+', r'\1.' + TAB, txt)), 12, bold=True)
            i += 1; continue
        if ln.startswith('## '):
            txt = re.sub(r'^(\d+[.]\d+)[.]?\s+', r'\1.' + TAB, ln[3:].strip())
            p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(10); p.paragraph_format.space_after = Pt(4)
            setfont(p.add_run(txt), 12)
            i += 1; continue
        if ln.startswith('**Table') or re.match(r'^\*\*Table \d', ln):
            pending_caption = re.sub(r'^\*{0,2}Table\s+[\d.]+\*{0,2}\s*', '', ln.strip())   # drop the markdown label, keep the caption text
            i += 1; continue
        if ln.startswith('|'):                                   # markdown table
            block = []
            while i < len(lines) and lines[i].startswith('|'):
                row = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not re.match(r'^[-: ]+$', ''.join(row)): block.append(row)
                i += 1
            tab_n += 1
            cap = pending_caption or ''
            cap = re.sub(r'^Table [\d.]+\s*', '', cap)
            tc = body(doc, f'Table {tab_n}. {cap}', size=12, space_after=3)
            for r in tc.runs: r.bold = True
            md_table(doc, block); pending_caption = None
            doc.add_paragraph().paragraph_format.space_after = Pt(6)
            continue
        if ln.strip().startswith('$$'):                          # display equation
            buf = [ln]
            while not ln.strip().endswith('$$') or len(buf) == 1 and ln.strip() == '$$':
                i += 1; ln = lines[i]; buf.append(ln)
                if ln.strip().endswith('$$'): break
            eq = ' '.join(buf).replace('$$', '').strip()
            eq = re.sub(r'\\tag\{(\d+)\}', '', eq).strip()
            eq_n += 1
            p = doc.add_paragraph(); pf = p.paragraph_format
            pf.line_spacing = Pt(15); pf.line_spacing_rule = WD_LINE_SPACING.AT_LEAST
            pf.space_before = Pt(6); pf.space_after = Pt(6)
            pf.tab_stops.add_tab_stop(Cm(8.6), WD_TAB_ALIGNMENT.CENTER)   # equation centred
            setfont(p.add_run(f'({eq_n})' + TAB), 12)
            setfont(p.add_run(eq), 12, italic=True)
            i += 1; continue
        if re.match(r'^[-*] ', ln):                              # bullet
            body(doc, '• ' + ln[2:].strip(), indent=0.6, space_after=3)
            i += 1; continue
        if re.match(r'^\d+\. ', ln):                             # numbered
            body(doc, ln.strip(), indent=0.6, space_after=3)
            i += 1; continue
        if ln.startswith('> '):
            body(doc, ln[2:].strip(), size=11, indent=0.8); i += 1; continue
        body(doc, ln.strip(), first_line=True)
        i += 1
    flush_figs(cur_sec)
    for sec_no, fname, cap in FIGMAP:                            # anything the section sweep missed
        if fname not in placed: flush_figs(sec_no)
    assert len(placed) == len(FIGMAP), f'figures not placed: {[f for _, f, _ in FIGMAP if f not in placed]}'
    body(doc, '© 2026 the Author(s), licensee AIMS Press. This is an open access article distributed under the '
              'terms of the Creative Commons Attribution License (https://creativecommons.org/licenses/by/4.0)',
         size=11, space_after=0)
    doc.save(OUT)
    print('saved', OUT)
    print(f'tables: {tab_n} | equations: {eq_n} | figures: {fig_counter}')

if __name__ == '__main__':
    main()
