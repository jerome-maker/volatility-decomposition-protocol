"""Assemble the DSFE submission package, laid out as the nine JAMS upload fields.

The field numbers and their requirements come from the journal's own upload page (step 4 of the
JAMS submission form): fields 1 and 2 are mandatory, several files must arrive as a single .zip,
and the total may not exceed 120 MB.
"""
import os, shutil, re, zipfile, datetime
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import md2docx as _M

D = r'J:/我的雲端硬碟/2026工作區/指導學生/柳宇軒/'
PKG = D + '投稿包_DSFE/'
CODE = D + '資訊階梯分析_程式與圖表/'
FONT = 'Times New Roman'
MAIL = 'jerome.chou@ntust.edu.tw'
ANON = 'https://anonymous.4open.science/r/volatility-decomposition-protocol-E6EC'
FIG_ORDER = [fn for _, fn, _ in _M.FIGMAP]          # single source of truth: the manuscript build
GRAPHICAL = 'r2_decomp.png'                         # the decomposition, the paper's central result

# scripts that would identify the author (own name, e-mail, local paths); they rebuild the Word
# files rather than the results, so the review copy goes without them
DOC_SCRIPTS = {'md2docx.py', 'eqfix.py', 'make_anon.py', 'build_package.py', 'build_repo.py',
               'submission_check.py', 'refcheck.py', 'refcheck2.py', 'refcross.py', 'docx_helpers.py',
               'build_report2.py', 'dsfe_style.py'}
LOCALPATH = 'J:/我的雲端硬碟/2026工作區/指導學生/柳宇軒/'


def setfont(run, size=12, bold=False):
    run.font.name = FONT; run._element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
    run.font.size = Pt(size); run.bold = bold


def cover_letter(path):
    d = Document()
    st = d.styles['Normal']; st.font.name = FONT; st.font.size = Pt(12)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
    sec = d.sections[0]
    for a in ('left_margin', 'right_margin', 'top_margin', 'bottom_margin'): setattr(sec, a, Cm(2.5))

    def p(txt, after=10, bold=False, align=None, size=12):
        par = d.add_paragraph(); par.paragraph_format.space_after = Pt(after)
        par.paragraph_format.line_spacing = Pt(16)
        if align == 'right': par.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        elif align == 'justify': par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        setfont(par.add_run(txt), size, bold); return par

    p(datetime.date.today().strftime('%d %B %Y'), align='right', after=18)
    p('The Editors', after=2); p('Data Science in Finance and Economics', after=18)
    p('Dear Editors,', after=12)
    p('I am submitting the manuscript "Information or architecture? A decomposition protocol for evaluating deep '
      'learning gains in volatility forecasting" for consideration as an original research article.', align='justify')
    p('Comparisons between deep learning and econometric models in financial forecasting rarely hold the information '
      'set fixed. When a neural network is given intraday measures, option-implied indices and macro-financial series '
      'that its econometric benchmark does not see, the reported gain confounds the value of the inputs with the value '
      'of the model. The paper proposes a protocol that separates them: a ladder of models whose rungs differ in the '
      'information they may use, with the deep learning model and its linear counterpart receiving identical inputs, '
      'so that the out-of-sample gain splits into three components that sum to it exactly.', align='justify')
    p('Applied to five-day realized volatility of the SPDR S&P 500 ETF, with a second application to the Invesco QQQ '
      'ETF, the protocol shows that exogenous option-implied information is the only component that improves QLIKE '
      'significantly, while neither a Transformer nor an LSTM improves on the linear model with the same inputs. Two '
      'further results qualify how such comparisons should be read: statistical and economic rankings diverge, and the '
      'architecture component is of the same order as the variation induced by the number of random seeds and by the '
      'version of the deep learning library. A hold-out year, reserved before the design was frozen and used once, '
      'reverses the sign of that component, which is reported as it stands.', align='justify')
    p('The work relates closely to Chassot and Audrino (2026), who hold the information set fixed and vary the fitting '
      'scheme, and who leave richer information sets to future research. This paper takes that step: it fixes the '
      'fitting scheme, varies the information set, and decomposes the difference. Section 8.6 reports that the '
      're-estimation frequency decisive in their one-day setting is immaterial at the five-day horizon studied here.',
      align='justify')
    p('The manuscript fits the journal\'s scope in data science methods and applications in finance. For double-blind '
      'review the manuscript carries no author details and points at an anonymised mirror of the replication material '
      f'({ANON}); all code, the daily derived series and a locked environment specification are supplied as '
      'supplementary material so that every number can be reproduced.', align='justify')
    p('I confirm that the manuscript has not been published elsewhere and is not under consideration by another '
      'journal, that it will be published in open access format, and that permission has been obtained for all '
      'reproduced material. I am not suggesting reviewers, and leave the choice to the editorial board. This research '
      'received no external funding.', align='justify')
    p('Generative AI tools (Claude, Anthropic) were used for code drafting, data processing, drafting of the manuscript '
      'text, language editing and document preparation, and in discussing analytical choices. All research decisions, '
      'analyses and interpretations were made and verified by me, and I take full responsibility for the content.',
      align='justify')
    p('Thank you for considering this submission.', after=18, align='justify')
    p('Yours sincerely,', after=24)
    p('Jerome Chih-Lung Chou', after=2)
    p('Graduate Institute of Finance, National Taiwan University of Science and Technology', size=11, after=2)
    p(MAIL, size=11)
    d.save(path)


def zip_dir(path, items):
    """items: list of (arcname, source file)."""
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for arc, src in items:
            z.write(src, arc)


def main():
    KEEP = {'00_README.md', '01_manuscript.docx', '02_manuscript.pdf', '03_graphical_abstract.png',
            '04_supplementary.zip', '06_cover_letter.docx', '07_figures.zip', '09_title_page.docx',
            'desktop.ini', '_not_uploaded', '_tmp_code'}
    for sub in ('', '_not_uploaded/'): os.makedirs(PKG + sub, exist_ok=True)
    for f in os.listdir(PKG):                       # a stale file here would be uploaded by mistake
        if f in KEEP: continue
        p = PKG + f
        try:
            shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else os.remove(p)
            print('removed stale', f)
        except OSError as e:
            print('COULD NOT REMOVE STALE FILE (close it in Word?):', f, e.strerror)

    # 1 and 2: the review copy, as Word and as PDF
    shutil.copy(D + 'Chou_2026_anonymised_manuscript.docx', PKG + '01_manuscript.docx')
    shutil.copy(D + 'Chou_2026_anonymised_manuscript.pdf', PKG + '02_manuscript.pdf')
    # 3: graphical abstract, a single figure with no caption
    shutil.copy(CODE + 'fig/' + GRAPHICAL, PKG + '03_graphical_abstract.png')
    # 4: supplementary material, one archive
    supp = [('ENVIRONMENT.md', CODE + 'ENVIRONMENT.md')]
    tmp = PKG + '_tmp_code/'
    os.makedirs(tmp, exist_ok=True)
    for f in sorted(os.listdir(CODE)):
        if not f.endswith('.py') or f in DOC_SCRIPTS: continue
        src = open(CODE + f, encoding='utf-8').read().replace(LOCALPATH, './').replace(LOCALPATH.rstrip('/'), './')
        open(tmp + f, 'w', encoding='utf-8').write(src)
        supp.append(('code/' + f, tmp + f))
    for f in sorted(os.listdir(CODE)):
        if f.endswith(('.csv', '.json')): supp.append(('results/' + f, CODE + f))
    for f in sorted(os.listdir(CODE + 'data')):
        if f.endswith(('.csv', '.json')): supp.append(('data/' + f, CODE + 'data/' + f))
    for f in sorted(os.listdir(CODE + 'predictions')):
        if f.endswith('.csv'): supp.append(('data/predictions/' + f, CODE + 'predictions/' + f))
    zip_dir(PKG + '04_supplementary.zip', supp)
    shutil.rmtree(tmp, ignore_errors=True)
    # 6: cover letter
    cover_letter(PKG + '06_cover_letter.docx')
    # 7: figures, one archive, 300 dpi
    zip_dir(PKG + '07_figures.zip',
            [(f'Figure{i}.png', CODE + 'fig/' + fn) for i, fn in enumerate(FIG_ORDER, 1)])
    # 9: material for the editor only
    shutil.copy(D + 'Chou_2026_title_page.docx', PKG + '09_title_page.docx')
    # kept out of the submission
    shutil.copy(D + 'Chou_2026_information_or_architecture.docx', PKG + '_not_uploaded/manuscript_named.docx')
    shutil.copy(D + 'Chou_2026_information_or_architecture.pdf', PKG + '_not_uploaded/manuscript_named.pdf')

    doc = Document(PKG + '01_manuscript.docx')
    body = '\n'.join(p.text for p in doc.paragraphs)
    words = len(re.findall(r"[A-Za-z][A-Za-z'’-]+", body))
    total = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(PKG) for f in fs)
    manifest = f"""# DSFE submission package

Title: Information or architecture? A decomposition protocol for evaluating deep learning gains in volatility forecasting
Author: Jerome Chih-Lung Chou, Graduate Institute of Finance, National Taiwan University of Science and Technology
Corresponding e-mail: {MAIL} (the address on the JAMS account)
Prepared: {datetime.date.today()}   Review model: double-blind

## What goes in which JAMS field (step 4 of the submission form)

| Field | Upload | File |
|---|---|---|
| 1 | Manuscript (Word/ZIP) — required | `01_manuscript.docx` (anonymised) |
| 2 | Manuscript file (PDF) — required | `02_manuscript.pdf` (anonymised) |
| 3 | Graphical abstract | `03_graphical_abstract.png` (one figure, no caption) |
| 4 | Supplementary files | `04_supplementary.zip` |
| 5 | Externally hosted supplementary files | the anonymised mirror: {ANON} |
| 6 | Cover letter | `06_cover_letter.docx` |
| 7 | Figures, graphics, images | `07_figures.zip` (PNG, 300 dpi, all ≥ 2299 px wide) |
| 8 | Funding information | none — no external funding |
| 9 | Non-published material | `09_title_page.docx` (author details and declarations) |

`_not_uploaded/` holds the named manuscript in Word and PDF, for the author's records only.

Total upload size {total / 1e6:.1f} MB, against the system's 120 MB limit.

## Manuscript statistics

- Pages: 29   Words (body, excluding tables): {words:,}
- Tables: {len(doc.tables)}   Figures: {len(FIG_ORDER)}   Equation objects: {len(doc.part.element.xpath('.//m:oMath'))}
- Abstract 269 words (limit 300), 7 keywords (limit 5–10), JEL codes given
- Formatting follows the journal's Word template: A4 with 1.9 cm side margins, Times New Roman 12 pt,
  line spacing at least 15 pt, numbered headings (level 1 bold, lower levels regular), three-line tables,
  bold table and figure captions, equations centred with the number flush left, author–date references in
  the journal's own abbreviation style, and the AIMS licence line at the end.

## Supplementary contents

- `code/` — every script needed to reproduce the results: data construction, the four levels, evaluation,
  Granger tests, attributions and the reproducibility experiments. Paths are relative. The scripts that build
  the Word files are withheld because they carry the author's details; they are in the public repository.
- `data/` — the daily derived series and the forecast series for every model and seed, so each table can be
  recomputed without the one-minute source data.
- `results/` — every result table reported in the paper.
- `ENVIRONMENT.md` — the locked software environment, including the two PyTorch builds compared in Section 7.

## Before uploading

1. Field 2 wants a PDF: `02_manuscript.pdf` is the anonymised Word file exported by Word, so its equations
   and figures match the Word copy exactly.
2. Fields 4 and 7 must each be a single archive, which is why they are shipped as .zip.
3. The APC is USD 0. The journal charges USD 80 only if the editors are asked to format the manuscript,
   which this package is prepared to avoid.
4. Step 2 of the form collects author details, including a telephone number, which does not appear in any
   file here.
"""
    open(PKG + '00_README.md', 'w', encoding='utf-8').write(manifest)
    print(manifest)
    for f in sorted(os.listdir(PKG)):
        p = PKG + f
        if os.path.isfile(p): print(f'  {f:34s} {os.path.getsize(p)/1e6:7.2f} MB')
    print(f'  total {total/1e6:.1f} MB')


if __name__ == '__main__':
    main()
