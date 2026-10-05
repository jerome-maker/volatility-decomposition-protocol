"""Assemble the DSFE submission package."""
import os, shutil, re, json, datetime
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

D = r'J:/我的雲端硬碟/2026工作區/指導學生/柳宇軒/'
PKG = D + '投稿包_DSFE/'
CODE = D + '資訊階梯分析_程式與圖表/'
FONT = 'Times New Roman'
FIG_ORDER = ['f1_overview.png', 'r1_ladder.png', 'r2_decomp.png', 'r3_pred.png', 'r4_regime.png',
             'r5_econ.png', 'r7_asset2.png', 'r8_spec.png', 'r6_shap_granger.png']

for sub in ('', 'figures/', 'supplementary/', 'supplementary/code/', 'supplementary/data/'):
    os.makedirs(PKG + sub, exist_ok=True)

def setfont(run, size=12, bold=False):
    run.font.name = FONT; run._element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
    run.font.size = Pt(size); run.bold = bold

def letter():
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
      're-estimation frequency decisive in their one-day setting is immaterial at the five-day horizon studied here.', align='justify')
    p('The manuscript fits the journal\'s scope in data science methods and applications in finance. All code, the '
      'daily derived series and a locked environment specification are supplied as supplementary material so that '
      'every number can be reproduced.', align='justify')
    p('I confirm that the manuscript has not been published elsewhere and is not under consideration by another '
      'journal, that it will be published in open access format, and that permission has been obtained for all '
      'reproduced material. I am not suggesting reviewers, and leave the choice to the editorial board.', align='justify')
    p('Generative AI tools were used for code drafting, language editing and manuscript preparation. I reviewed and '
      'verified all analyses, numbers and claims, and take full responsibility for the content.', align='justify')
    p('Thank you for considering this submission.', after=18, align='justify')
    p('Yours sincerely,', after=24)
    p('Jerome Chih-Lung Chou', after=2)
    p('Graduate Institute of Finance, National Taiwan University of Science and Technology', size=11, after=2)
    p('jerome.chou@mail.ntust.edu.tw', size=11)
    d.save(PKG + '03_cover_letter.docx')

letter()
shutil.copy(D + 'Chou_2026_anonymised_manuscript.docx', PKG + '01_manuscript_anonymised.docx')
shutil.copy(D + 'Chou_2026_title_page.docx', PKG + '02_title_page.docx')
shutil.copy(D + 'Chou_2026_information_or_architecture.docx', PKG + '04_manuscript_with_author_details.docx')
for i, f in enumerate(FIG_ORDER, 1):
    shutil.copy(CODE + 'fig/' + f, PKG + f'figures/Figure{i}.png')
shutil.copy(CODE + 'ENVIRONMENT.md', PKG + 'supplementary/ENVIRONMENT.md')
for f in os.listdir(CODE):
    if f.endswith('.py'): shutil.copy(CODE + f, PKG + 'supplementary/code/' + f)
for f in os.listdir(CODE):
    if f.endswith(('.csv', '.json')): shutil.copy(CODE + f, PKG + 'supplementary/data/' + f)
for f in os.listdir(CODE + 'predictions'):
    if f.endswith('.csv'): shutil.copy(CODE + 'predictions/' + f, PKG + 'supplementary/data/' + f)

doc = Document(PKG + '01_manuscript_anonymised.docx')
body = '\n'.join(p.text for p in doc.paragraphs)
stats = dict(pages='33 (approx.)', words=len(re.findall(r"[A-Za-z][A-Za-z'’-]+", body)),
             tables=len(doc.tables), figures=len(FIG_ORDER),
             equations=len(doc.part.element.xpath('.//m:oMath')))
manifest = f"""# DSFE submission package

Title: Information or architecture? A decomposition protocol for evaluating deep learning gains in volatility forecasting
Author: Jerome Chih-Lung Chou, Graduate Institute of Finance, National Taiwan University of Science and Technology
Prepared: {datetime.date.today()}

## Files to upload

| Order | File | Purpose |
|---|---|---|
| 1 | 01_manuscript_anonymised.docx | Main document for double-blind review |
| 2 | 02_title_page.docx | Author details and declarations (separate file, as required) |
| 3 | 03_cover_letter.docx | Cover letter |
| 4 | figures/Figure1–9.png | Figures at full resolution |
| 5 | supplementary/ | Code, derived data and the locked environment |

`04_manuscript_with_author_details.docx` is the named version, kept for the author's records; it is **not** uploaded.

## Manuscript statistics

- Words (body, excluding tables): {stats['words']:,}
- Tables: {stats['tables']}   Figures: {stats['figures']}   Equation objects: {stats['equations']}
- Abstract: 269 words (journal limit: under 300)   Keywords: 7 (limit: 5–10)
- Formatting: Times New Roman 12 pt, 18 pt line spacing, equations editable and numbered, author–date references

## Supplementary contents

- `code/` — every script used, from raw data to the final tables: data construction, the four levels, evaluation,
  Granger tests, attributions, the reproducibility experiments and the document build.
- `data/` — daily derived series, all result tables, and the forecast series for every model and seed, so that each
  table in the paper can be recomputed without the one-minute source data.
- `ENVIRONMENT.md` — the locked software environment, including the two PyTorch builds discussed in Section 7.2.

## Before uploading

1. Replace the placeholder repository link in the manuscript with the anonymous repository URL.
2. Confirm the submission system accepts the figures separately; if figures must be embedded only, they already are.
3. Submit through JAMS at aimspress.jams.pub. The article processing charge is USD 0.
"""
open(PKG + '00_README.md', 'w', encoding='utf-8').write(manifest)
print(manifest)
total = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(PKG) for f in fs)
n = sum(len(fs) for _, _, fs in os.walk(PKG))
print(f'package: {n} files, {total/1e6:.1f} MB at {PKG}')
